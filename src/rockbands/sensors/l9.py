"""Landsat 9 OLI-2/TIRS-2. USGS lists the same nominal band designations as Landsat 8.

    from rockbands.sensors import l9
    l9.ferric_iron_redness(B4=red, B2=blue)
"""

from ._namespace import make_namespace
from .base import Band, Sensor

SENSOR = Sensor(
    key="l9",
    name="Landsat 9 OLI-2/TIRS-2",
    aliases=("landsat9", "oli2"),
    bands=(
        Band("B1", "Coastal aerosol", (430, 450), "A", 30),
        Band("B2", "Blue", (450, 510), "B", 30),
        Band("B3", "Green", (530, 590), "G", 30),
        Band("B4", "Red", (640, 670), "R", 30),
        Band("B5", "NIR", (850, 880), "N", 30),
        Band("B6", "SWIR 1", (1570, 1650), "S1", 30),
        Band("B7", "SWIR 2", (2110, 2290), "S2", 30),
        Band("B8", "Panchromatic", (500, 680), None, 15),
        Band("B9", "Cirrus", (1360, 1380), None, 30),
        Band("B10", "Thermal 1 (TIRS-2)", (10600, 11190), "T1", 100),
        Band("B11", "Thermal 2 (TIRS-2)", (11500, 12510), "T2", 100),
    ),
)

__getattr__, __dir__ = make_namespace(SENSOR, globals())
