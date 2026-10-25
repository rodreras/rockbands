"""Sentinel-2 MSI (A and B).

Wavelengths: ESA spectral-response barycentres and FWHM bandwidths for Sentinel-2A.
Sentinel-2B differs by a few nanometres.

    from rockbands.sensors import s2
    s2.ferric_iron_redness(B4=red, B2=blue)
"""

from ._namespace import make_namespace
from .base import Band, Sensor

SENSOR = Sensor(
    key="s2",
    name="Sentinel-2 MSI",
    aliases=("sentinel2", "sentinel2a", "sentinel2b", "sentinel2msi", "s2msi", "s2a", "s2b", "msi"),
    bands=(
        Band.from_center("B1", "Coastal aerosol", 442.7, 20, "A", 60),
        Band.from_center("B2", "Blue", 492.7, 65, "B", 10),
        Band.from_center("B3", "Green", 559.8, 35, "G", 10),
        Band.from_center("B4", "Red", 664.6, 30, "R", 10),
        Band.from_center("B5", "Red edge 1", 704.1, 14, "RE1", 20),
        Band.from_center("B6", "Red edge 2", 740.5, 14, "RE2", 20),
        Band.from_center("B7", "Red edge 3", 782.8, 19, "RE3", 20),
        Band.from_center("B8", "NIR", 832.8, 105, "N", 10),
        Band.from_center("B8A", "NIR narrow", 864.7, 21, "N2", 20),
        Band.from_center("B9", "Water vapour", 945.1, 19, "WV", 60),
        Band.from_center("B10", "Cirrus", 1373.5, 29, None, 60),
        Band.from_center("B11", "SWIR 1", 1613.7, 90, "S1", 20),
        Band.from_center("B12", "SWIR 2", 2202.4, 174, "S2", 20),
    ),
    notes="B10 (cirrus) is absent from Level-2A products.",
)

__getattr__, __dir__ = make_namespace(SENSOR, globals())
