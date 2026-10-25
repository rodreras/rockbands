"""Sensor-agnostic band ratios and RGB composites for mineral exploration.

Based on https://github.com/rodreras/awesome-mining-band-ratio, with the standard band
names and multi-sensor approach of https://github.com/awesome-spectral-indices/awesome-spectral-indices.

Quick start::

    import rockbands as rb

    # 1. a ratio on one sensor, using that sensor's own band ids
    rb.sensors.s2.ferric_iron_redness(B4=red, B2=blue)
    rb.sensors.l8.ferric_iron_redness(B4=red, B2=blue)

    # 2. the same, through the generic API (works with a whole scene dict or xarray.Dataset)
    rb.compute_ratio("clay_sulphate_mica_marble", scene, sensor="l9")

    # 3. what each sensor has, and what a ratio needs
    print(rb.compare_bands(["s2", "l8", "l7"], ratio="ferric_iron_2"))
    print(rb.translate("ferric_iron_2", "s2"))
"""

from . import helpers, ratios, sensors, utils
from .errors import (
    BandNotAvailableError,
    ExpressionError,
    MiningBandRatiosError,
    MissingBandError,
    UnknownRatioError,
    UnknownSensorError,
)
from .helpers import (
    Table,
    aster_band_coverage,
    band_overlap,
    compare_bands,
    ratio_support,
    spectral_equivalence,
    translate,
)
from .ratios import CATALOGUE, compute_all, evaluate_formula, get_ratio, list_ratios
from .ratios.engine import compute as _compute
from .sensors import SENSORS, get_sensor, list_sensors
from .utils import (
    aster_dn_to_radiance,
    dn_to_reflectance,
    plot_composites,
    plot_ratios,
    split_bands,
    to_rgb_image,
)

__version__ = "0.1.0"


def compute_ratio(name, bands=None, sensor=None, **arrays):
    """Evaluate the catalogue entry ``name`` (a ratio or an RGB composite) on a sensor's bands."""
    return _compute(get_ratio(name), sensor, bands, **arrays)


def __getattr__(name):
    # Lets ``rb.ferric_iron_redness(R=..., B=...)`` work without importing every function here.
    if name in CATALOGUE:
        return getattr(ratios, name)
    raise AttributeError(f"module 'rockbands' has no attribute {name!r}")


def __dir__():
    return sorted(set(globals()) | set(CATALOGUE))
