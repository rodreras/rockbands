import numpy as np
import pytest

import rockbands as rb
from rockbands.errors import MissingBandError
from conftest import make_scene


def test_compute_all_matches_individual_calls(sensor):
    scene = make_scene(sensor)
    ratios = rb.compute_all(scene, sensor, kind="ratio")
    composites = rb.compute_all(scene, sensor, kind="composite")
    assert set(ratios) == {i.name for i in rb.list_ratios(sensor, kind="ratio")}
    assert set(composites) == {i.name for i in rb.list_ratios(sensor, kind="composite")}
    for name, value in {**ratios, **composites}.items():
        np.testing.assert_allclose(value, rb.compute_ratio(name, scene, sensor=sensor))


def test_compute_all_missing_bands():
    scene = make_scene(rb.get_sensor("s2"))
    del scene["B1"]
    names = set(rb.compute_all(scene, "s2"))
    assert "iron_sulphate" not in names and "ferric_iron_redness" in names
    with pytest.raises(MissingBandError):
        rb.compute_all(scene, "s2", on_missing="raise")
    with pytest.raises(ValueError):
        rb.compute_all(scene, "s2", on_missing="nope")


def test_sensor_from_stac_platform_strings():
    for platform, key in [("sentinel-2a", "s2"), ("sentinel-2b", "s2"), ("landsat-8", "l8"), ("LANDSAT_8", "l8"),
                          ("LANDSAT_9", "l9"), ("landsat-9", "l9")]:
        assert rb.get_sensor(platform).key == key


def test_aster_dn_to_radiance():
    dn = np.array([0, 1, 101], dtype=np.uint8)
    out = rb.aster_dn_to_radiance(dn, "B1")
    assert np.isnan(out[0])
    np.testing.assert_allclose(out[1:], [0.0, 100 * 1.688], rtol=1e-6)
    np.testing.assert_allclose(rb.aster_dn_to_radiance(np.array([11]), "B3N", gain="HGH"), [10 * 0.423])
    np.testing.assert_allclose(rb.aster_dn_to_radiance(np.array([11]), "B13", gain="HGH"), [10 * 5.693e-3])
    np.testing.assert_allclose(rb.aster_dn_to_radiance(np.array([11]), "B9", gain="lo2"), [10 * 0.265])
    with pytest.raises(ValueError):
        rb.aster_dn_to_radiance(dn, "B1", gain="LO2")
    with pytest.raises(ValueError):
        rb.aster_dn_to_radiance(dn, "B15")


def test_aster_radiance_does_not_wrap_for_uint8():
    out = rb.aster_dn_to_radiance(np.array([1], dtype=np.uint8), "B4")
    np.testing.assert_allclose(out, [0.0])


def test_dn_to_reflectance_with_xarray():
    xr = pytest.importorskip("xarray")
    da = xr.DataArray(np.array([[0, 2000], [11000, 1500]], dtype=np.uint16), dims=("y", "x"))
    out = rb.dn_to_reflectance(da, rb.get_sensor("s2"))
    assert isinstance(out, xr.DataArray) and out.dims == ("y", "x")
    np.testing.assert_allclose(out.values[0, 1], 0.1)
    assert np.isnan(out.values[0, 0])


def test_plot_helpers_return_figures():
    plt = pytest.importorskip("matplotlib.pyplot")
    plt.switch_backend("Agg")
    scene = make_scene(rb.get_sensor("l8"), shape=(12, 14))
    fig = rb.plot_ratios(rb.compute_all(scene, "l8", kind="ratio"), ncols=3)
    assert len(fig.axes) >= 7
    fig2 = rb.plot_composites(rb.compute_all(scene, "l8", kind="composite"), ncols=5)
    assert fig2.axes
    plt.close("all")
    with_nans = np.full((4, 4), np.nan)
    rb.plot_ratios({"all_nan": with_nans})
    plt.close("all")
