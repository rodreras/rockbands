"""One module per satellite: ``s2``, ``l4``, ``l5``, ``l7``, ``l8``, ``l9``, ``aster``.

Each module holds the sensor's band map (``SENSOR``) and exposes every ratio in the
catalogue bound to that sensor::

    from rockbands.sensors import s2, l8
    s2.ferric_iron_redness(B4=red, B2=blue)
    l8.ferric_iron_redness(B4=red, B2=blue)
"""

from . import aster, l4, l5, l7, l8, l9, s2
from .base import STANDARD_BANDS, Band, Sensor, normalize_band_id
from .registry import SENSORS, get_sensor, list_sensors

__all__ = [
    "SENSORS",
    "STANDARD_BANDS",
    "Band",
    "Sensor",
    "aster",
    "get_sensor",
    "l4",
    "l5",
    "l7",
    "l8",
    "l9",
    "list_sensors",
    "normalize_band_id",
    "s2",
]
