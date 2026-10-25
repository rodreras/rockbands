"""Landsat 5 TM. Wavelengths from the USGS band-designation table.

    from rockbands.sensors import l5
    l5.ferric_iron_redness(B3=red, B1=blue)
"""

from ._namespace import make_namespace
from .base import Band, Sensor

SENSOR = Sensor(
    key="l5",
    name="Landsat 5 TM",
    aliases=("landsat5", "tm5"),
    bands=(
        Band("B1", "Blue", (450, 520), "B", 30),
        Band("B2", "Green", (520, 600), "G", 30),
        Band("B3", "Red", (630, 690), "R", 30),
        Band("B4", "NIR", (760, 900), "N", 30),
        Band("B5", "SWIR 1", (1550, 1750), "S1", 30),
        Band("B6", "Thermal", (10400, 12500), "T", 120),
        Band("B7", "SWIR 2", (2080, 2350), "S2", 30),
    ),
)

__getattr__, __dir__ = make_namespace(SENSOR, globals())
