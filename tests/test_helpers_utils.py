import numpy as np
import pytest

import rockbands as rb
from rockbands.errors import BandNotAvailableError


def test_compare_bands_table():
    t = rb.compare_bands(["s2", "l8", "l7"], standards=["N", "S1"])
    rows = {r["Role"]: r for r in t.to_dicts()}
    assert rows["N"]["s2"].startswith("B8 ") and rows["N"]["l8"].startswith("B5 ") and rows["N"]["l7"].startswith("B4 ")
    assert rows["S1"]["s2"].startswith("B11 ") and rows["S1"]["l8"].startswith("B6 ")
    assert "| Role |" in t.to_markdown() and "Role" in str(t)


def test_compare_bands_gaps_and_only_common():
    t = rb.compare_bands(["s2", "l8"], standards=["RE1", "N2", "N"])
    assert {r["Role"]: r["l8"] for r in t.to_dicts()}["RE1"] == "-"
    common = rb.compare_bands(["s2", "l8"], standards=["RE1", "N2", "N"], only_common=True)
    assert [r["Role"] for r in common.to_dicts()] == ["N"]


def test_compare_bands_for_a_ratio_shows_only_needed_roles():
    t = rb.compare_bands(["s2", "l7"], ratio="clay_sulphate_mica_marble")
    assert {r["Role"] for r in t.to_dicts()} == {"S1", "S2", "N", "R"}


def test_compare_bands_for_aster_ratio_shows_coverage():
    t = rb.compare_bands(["s2", "l8"], ratio="aster_kaolinite")
    rows = {r["ASTER"]: r for r in t.to_dicts()}
    assert set(rows) == {"B5", "B7"}
    assert rows["B5"]["s2"] == "B12 (100%)" and rows["B5"]["l8"] == "B7 (100%)"  # README: ASTER 5-7 fall inside S2 B12


def test_aster_band_coverage_outside_window():
    t = rb.aster_band_coverage(["s2"], ["B9", "B1"])
    rows = {r["ASTER"]: r["s2"] for r in t.to_dicts()}
    assert rows["B9"] == "-"
    assert rows["B1"] == "B2 (7%), B3 (44%)"  # ASTER green straddles S2 blue and green: not a clean match


def test_band_overlap_values():
    same = rb.band_overlap("N", "l8", "l9")
    assert same["iou"] == pytest.approx(1.0) and same["midpoint_shift_nm"] == 0
    wide_vs_narrow = rb.band_overlap("N", "s2", "l8")  # S2 B8 is far wider than OLI B5
    assert wide_vs_narrow["fraction_of_b"] == pytest.approx(1.0)
    assert wide_vs_narrow["fraction_of_a"] < 0.4 and wide_vs_narrow["iou"] < 0.4
    with pytest.raises(ValueError):
        rb.band_overlap("RE1", "s2", "l8")


def test_spectral_equivalence_skips_roles_one_sensor_lacks():
    t = rb.spectral_equivalence("s2", "l7")
    roles = [r["Role"] for r in t.to_dicts()]
    assert roles == ["B", "G", "R", "N", "S1", "S2"]


def test_ratio_support_matrix():
    t = rb.ratio_support(["s2", "l8", "l7", "aster"], kind="ratio")
    rows = {r["Ratio"]: r for r in t.to_dicts()}
    assert rows["moisture_index"]["l8"] == "needs N2" and rows["moisture_index"]["s2"] == "ok"
    assert rows["aster_kaolinite"]["s2"] == "ASTER only" and rows["aster_kaolinite"]["aster"] == "ok"
    assert rows["iron_sulphate"]["l7"] == "needs A"
    assert len(rb.ratio_support(kind="composite")) == 17


def test_translate():
    assert rb.translate("clay_sulphate_mica_marble", "l8") == "(B6/B7)/(B5/B4)"
    assert rb.translate("clay_sulphate_mica_marble", "s2") == "(B11/B12)/(B8/B4)"
    assert rb.translate("clay_sulphate_mica_marble", "l7") == "(B5/B7)/(B4/B3)"
    assert rb.translate("geology", "l8") == ("B7", "B4", "B2")
    assert rb.translate("aster_kaolinite", "aster") == "B7/B5"
    with pytest.raises(BandNotAvailableError):
        rb.translate("moisture_index", "l8")


def test_list_ratios_filters():
    names = {i.name for i in rb.list_ratios(sensor="l7", category="iron")}
    assert names == {"ferric_iron_redness", "ferric_iron_2", "ferrous_iron"}
    assert all(i.kind == "composite" for i in rb.list_ratios(kind="composite"))


def test_dn_to_reflectance():
    out = rb.dn_to_reflectance(np.array([0, 10000, 30000], dtype=np.uint16), "l8")
    np.testing.assert_allclose(out[1:], [10000 * 0.0000275 - 0.2, 30000 * 0.0000275 - 0.2], rtol=1e-6)
    assert np.isnan(out[0])
    out = rb.dn_to_reflectance(np.array([0, 2000, 11000]), "s2", clip=(0, 1))
    np.testing.assert_allclose(out[1:], [0.1, 1.0])
    out = rb.dn_to_reflectance(np.array([2000]), "s2", boa_add_offset=0)
    np.testing.assert_allclose(out, [0.2])
    with pytest.raises(ValueError):
        rb.dn_to_reflectance(np.array([1]), "aster")


def test_split_bands_and_rgb_image():
    stack = np.random.default_rng(0).uniform(size=(3, 6, 7))
    bands = rb.split_bands(stack, ["B2", "B3", "B4"])
    np.testing.assert_array_equal(bands["B3"], stack[1])
    with pytest.raises(ValueError):
        rb.split_bands(stack, ["B2", "B3"])
    img = rb.to_rgb_image(stack)
    assert img.shape == (6, 7, 3) and img.min() >= 0 and img.max() <= 1
    scene = rb.split_bands(np.random.default_rng(1).uniform(0.1, 0.5, (6, 5, 5)), ["B2", "B3", "B4", "B5", "B6", "B7"])
    assert rb.to_rgb_image(rb.sensors.l8.geology(scene)).shape == (5, 5, 3)
