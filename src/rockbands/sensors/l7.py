"""Landsat 7 ETM+. Wavelengths from the USGS band-designation table.

Note the band order: SWIR 2 is B7 but the thermal band is B6.

    from rockbands.sensors import l7
    l7.ferric_iron_redness(B3=red, B1=blue)
"""

from ._namespace import make_namespace
from .base import Band, Sensor

SENSOR = Sensor(
    key="l7",
    name="Landsat 7 ETM+",
    aliases=("landsat7", "etm", "etmplus"),
    bands=(
        Band("B1", "Blue", (450, 520), "B", 30),
        Band("B2", "Green", (520, 600), "G", 30),
        Band("B3", "Red", (630, 690), "R", 30),
        Band("B4", "NIR", (770, 900), "N", 30),
        Band("B5", "SWIR 1", (1550, 1750), "S1", 30),
        Band("B6", "Thermal", (10400, 12500), "T", 60),
        Band("B7", "SWIR 2", (2090, 2350), "S2", 30),
        Band("B8", "Panchromatic", (520, 900), None, 15),
    ),
)

__getattr__, __dir__ = make_namespace(SENSOR, globals())
