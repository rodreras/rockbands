"""Input handling: band key spellings, dtypes, zero division, xarray, errors."""

import warnings

import numpy as np
import pytest

import rockbands as rb
from rockbands.errors import (
    BandNotAvailableError,
    ExpressionError,
    MissingBandError,
    UnknownRatioError,
    UnknownSensorError,
)
from rockbands.expression import evaluate, required_names
from rockbands.sensors import aster, l7, l8, s2


def test_band_key_spellings():
    red, blue = np.array([0.4]), np.array([0.2])
    for keys in ({"B4": red, "B2": blue}, {"b04": red, "b02": blue}, {"SR_B4": red, "SR_B2": blue},
                 {"band_4": red, "band_2": blue}, {"R": red, "B": blue}, {"r": red, "b": blue}):
        np.testing.assert_allclose(l8.ferric_iron_redness(keys), [2.0])
    np.testing.assert_allclose(s2.moisture_index(B8a=np.array([0.5]), B11=np.array([0.3])), [0.25])


def test_extra_bands_in_scene_are_ignored():
    scene = {f"B{i}": np.full((2, 2), 0.3) for i in range(1, 12)}
    assert l8.ndvi(scene).shape == (2, 2)


def test_kwargs_override_mapping():
    out = l8.ferric_iron_redness({"B4": np.array([1.0]), "B2": np.array([1.0])}, B4=np.array([3.0]))
    np.testing.assert_allclose(out, [3.0])


def test_integer_dn_does_not_wrap_around():
    """uint16 5 - 10 would give 65531; inputs must be promoted to float first."""
    n, r = np.array([5], dtype=np.uint16), np.array([10], dtype=np.uint16)
    np.testing.assert_allclose(l8.ndvi(B5=n, B4=r), [(5 - 10) / (5 + 10)])


def test_division_by_zero_is_nan_without_warnings():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        out = l8.ferric_iron_redness(B4=np.array([1.0, 0.0]), B2=np.array([0.0, 0.0]))
    assert np.isnan(out).all()
    assert np.isnan(rb.ferric_iron_redness(R=1.0, B=0.0))  # plain Python numbers too


def test_scalars_and_lists():
    np.testing.assert_allclose(rb.ferric_iron_redness(R=[2.0, 4.0], B=[1.0, 2.0]), [2.0, 2.0])


def test_xarray_keeps_coordinates_and_accepts_dataset():
    xr = pytest.importorskip("xarray")
    coords = {"y": [10, 20], "x": [1, 2, 3]}
    ds = xr.Dataset({f"B{i}": (("y", "x"), np.full((2, 3), 0.1 * i)) for i in (2, 3, 4, 5, 6, 7)}, coords=coords)
    out = l8.ferric_iron_redness(ds)
    assert isinstance(out, xr.DataArray) and out.dims == ("y", "x")
    np.testing.assert_array_equal(out["x"], [1, 2, 3])
    np.testing.assert_allclose(out, 0.4 / 0.2)
    comp = l8.geology(ds)
    assert comp.dims == ("channel", "y", "x") and comp.shape == (3, 2, 3)
    assert isinstance(l8.ndvi(ds), xr.DataArray)


def test_aster_alias_and_native_numbers():
    b = {f"B{i}": np.full((2, 2), 0.1 * i) for i in range(1, 15)}
    b_3n = {("B3N" if k == "B3" else k): v for k, v in b.items()}
    np.testing.assert_allclose(aster.aster_ferric_oxides(b_3n), aster.aster_ferric_oxides(b))
    np.testing.assert_allclose(rb.ratios.aster_kaolinite(B7=b["B7"], B5=b["B5"]), b["B7"] / b["B5"])


def test_aster_ratio_on_other_sensor_is_refused_with_reason():
    with pytest.raises(BandNotAvailableError, match="only runs on ASTER"):
        s2.aster_kaolinite(B7=np.ones(2), B5=np.ones(2))


def test_generic_ratio_on_aster_uses_vnir_swir_roles():
    g, r, n, s1 = (np.full(2, v) for v in (0.2, 0.3, 0.5, 0.4))
    np.testing.assert_allclose(aster.ferrous_iron(B1=g, B4=s1, B2=r, B3=n), (0.2 + 0.4) / (0.3 + 0.5))
    with pytest.raises(BandNotAvailableError):
        aster.ferric_iron_redness(B2=r, B1=g)  # ASTER has no blue


def test_missing_band_message():
    with pytest.raises(MissingBandError) as exc:
        l8.ferric_iron_redness(B4=np.ones(2))
    assert "B2" in str(exc.value) and "missing" in str(exc.value)
    with pytest.raises(MissingBandError, match="standard names"):
        rb.ferric_iron_redness(B4=np.ones(2), B2=np.ones(2))  # native ids with no sensor


def test_unknown_sensor_and_ratio():
    with pytest.raises(UnknownSensorError, match="Landsat 6 failed"):
        rb.get_sensor("l6")
    with pytest.raises(UnknownRatioError, match="ferric_iron_redness"):
        rb.get_ratio("ferric_iron")
    with pytest.raises(AttributeError):
        l8.not_a_ratio
    assert rb.get_sensor("Landsat-8") is l8.SENSOR and rb.get_sensor("Sentinel 2") is s2.SENSOR


def test_sensor_module_namespace():
    assert "ferric_iron_redness" in dir(l7) and "moisture_index" not in dir(l7)
    assert not hasattr(l7, "__wrapped__")
    from rockbands.sensors.s2 import ferric_iron_redness  # from-import goes through __getattr__

    assert ferric_iron_redness.__name__ == "ferric_iron_redness"


def test_custom_formula():
    out = rb.evaluate_formula("(S1-S2)/(S1+S2)", sensor="l8", B6=np.array([0.4]), B7=np.array([0.2]))
    np.testing.assert_allclose(out, [(0.4 - 0.2) / (0.4 + 0.2)])


def test_expression_grammar_is_restricted():
    assert required_names("(S1/S2)/(N/R)") == ("S1", "S2", "N", "R")
    for bad in ("__import__('os').system('x')", "a.b", "a[0]", "lambda: 1", "a if b else c", "open('f')", "x and y"):
        with pytest.raises(ExpressionError):
            evaluate(bad, {"a": 1.0, "b": 1.0, "x": 1.0, "y": 1.0, "c": 1.0})
    with pytest.raises(ExpressionError):
        evaluate("1 +", {})
