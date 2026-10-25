"""Every catalogue entry on every sensor: runs where it should, refuses where it should."""

import numpy as np
import pytest
from conftest import make_scene

import rockbands as rb
from rockbands.errors import BandNotAvailableError
from rockbands.ratios import CATALOGUE, compute, supported_sensors


def test_catalogue_size():
    kinds = [i.kind for i in CATALOGUE.values()]
    assert kinds.count("ratio") == 8 + 25  # generic + ASTER
    assert kinds.count("composite") == 17


@pytest.mark.parametrize("name", list(CATALOGUE))
def test_runs_on_supported_sensors_and_refuses_others(name, sensor):
    item = CATALOGUE[name]
    scene = make_scene(sensor)
    if sensor.key in supported_sensors(item):
        out = compute(item, sensor, scene)
        expected_shape = (3, 4, 5) if item.kind == "composite" else (4, 5)
        assert out.shape == expected_shape
        assert np.isfinite(out).all()
    else:
        with pytest.raises(BandNotAvailableError):
            compute(item, sensor, scene)


@pytest.mark.parametrize("name", [n for n, i in CATALOGUE.items() if i.namespace == "standard"])
def test_native_ids_and_standard_names_agree(name):
    """The point of the design: one formula, same numbers whichever way the bands are addressed."""
    item = CATALOGUE[name]
    for key in supported_sensors(item):
        sensor = rb.get_sensor(key)
        scene = make_scene(sensor)
        by_native = compute(item, sensor, scene)
        by_standard = compute(item, None, {sensor.band(native).standard: arr for native, arr in scene.items()
                                           if sensor.band(native).standard})
        np.testing.assert_allclose(by_native, by_standard)


# Independent transcription of the ASTER table (not shared with the catalogue code).
ASTER_EXPECTED = {
    "ferric_iron": lambda b: b[2] / b[1],
    "ferrous_iron": lambda b: (b[5] / b[3]) + (b[1] / b[2]),
    "gossan": lambda b: b[4] / b[2],
    "ferrous_silicates": lambda b: b[5] / b[4],
    "ferric_oxides": lambda b: b[4] / b[3],
    "carbonate_chlorite_epidote": lambda b: (b[7] + b[9]) / b[8],
    "carbonate_index": lambda b: b[13] / b[14],
    "epidote_chlorite_amphibole": lambda b: (b[6] + b[9]) / (b[7] + b[8]),
    "amphibole_mgoh": lambda b: (b[6] + b[9]) / b[8],
    "amphibole": lambda b: b[6] / b[8],
    "dolomite": lambda b: (b[6] + b[8]) / b[7],
    "hydroxyl_index": lambda b: (b[7] / b[6]) * (b[4] / b[6]),
    "kaolinite_index": lambda b: (b[4] / b[5]) * (b[8] / b[6]),
    "alunite_index": lambda b: (b[7] / b[5]) * (b[7] / b[8]),
    "calcite_index": lambda b: (b[6] / b[8]) * (b[9] / b[8]),
    "phyllic_alteration": lambda b: (b[5] + b[7]) / b[6],
    "alunite_kaolinite": lambda b: (b[4] + b[6]) / b[5],
    "muscovite": lambda b: b[7] / b[6],
    "kaolinite": lambda b: b[7] / b[5],
    "clay": lambda b: (b[5] * b[7]) / (b[6] * b[6]),
    "quartz_index": lambda b: b[14] / b[12],
    "quartz_ninomiya": lambda b: (b[11] / b[10]) * (b[11] / b[12]),
    "basic_degree_index": lambda b: b[12] / b[13],
    "silica": lambda b: b[13] / b[10],
    "silica_index": lambda b: (b[11] * b[11]) / (b[10] * b[12]),
}


def test_aster_expected_covers_whole_table():
    assert set(f"aster_{n}" for n in ASTER_EXPECTED) == {n for n in CATALOGUE if n.startswith("aster_")}


@pytest.mark.parametrize("name", ASTER_EXPECTED)
def test_aster_formulas(name):
    rng = np.random.default_rng(1)
    b = {i: rng.uniform(0.1, 1.0, (3, 3)) for i in range(1, 15)}
    got = rb.ratios.__dict__[f"aster_{name}"]({f"B{i}": v for i, v in b.items()})
    np.testing.assert_allclose(got, ASTER_EXPECTED[name](b))


def test_generic_formulas():
    rng = np.random.default_rng(2)
    r = {k: rng.uniform(0.1, 1.0, (3, 3)) for k in ["A", "B", "G", "R", "N", "N2", "S1", "S2"]}
    f = rb.ratios
    np.testing.assert_allclose(f.ferric_iron_redness(**r), r["R"] / r["B"])
    np.testing.assert_allclose(f.ferric_iron_2(**r), (r["R"] / r["B"]) * ((r["R"] + r["S1"]) / r["N"]))
    np.testing.assert_allclose(f.ferrous_iron(**r), (r["G"] + r["S1"]) / (r["R"] + r["N"]))
    np.testing.assert_allclose(f.clay_sulphate_mica_marble(**r), (r["S1"] / r["S2"]) / (r["N"] / r["R"]))
    np.testing.assert_allclose(f.iron_sulphate(**r), (r["B"] / r["A"]) - (r["N"] / r["R"]))
    np.testing.assert_allclose(f.ndvi(**r), (r["N"] - r["R"]) / (r["N"] + r["R"]))
    np.testing.assert_allclose(f.moisture_index(**r), (r["N2"] - r["S1"]) / (r["N2"] + r["S1"]))
    np.testing.assert_allclose(f.ndwi(**r), (r["G"] - r["N"]) / (r["G"] + r["N"]))


def test_composite_channels_in_rgb_order():
    rng = np.random.default_rng(3)
    r = {k: rng.uniform(0.1, 1.0, (2, 2)) for k in ["B", "G", "R", "N", "S1", "S2"]}
    out = rb.ratios.sultan_gomez(**r)
    np.testing.assert_allclose(out[0], r["S1"] / r["S2"])
    np.testing.assert_allclose(out[1], r["S1"] / r["B"])
    np.testing.assert_allclose(out[2], (r["S1"] / r["N"]) * (r["R"] / r["N"]))


def test_sensor_support_matches_readme_table():
    """README: red edge, N2, WV and aerosol bands exist only where the table says so."""
    sup = {n: set(supported_sensors(CATALOGUE[n])) for n in ("moisture_index", "iron_sulphate", "ferric_iron_redness")}
    assert sup["moisture_index"] == {"s2"}
    assert sup["iron_sulphate"] == {"s2", "l8", "l9"}  # needs A: no aerosol band on TM/ETM+ or ASTER
    assert sup["ferric_iron_redness"] == {"s2", "l4", "l5", "l7", "l8", "l9"}
    assert "aster" in supported_sensors(CATALOGUE["ferrous_iron"])  # G, R, N, S1 all map on ASTER
