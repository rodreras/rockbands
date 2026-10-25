"""Terra ASTER (VNIR, SWIR, TIR).

ASTER is the sensor the original band-ratio table was written for, so its ratios
use native band numbers (``B1`` ... ``B14``). Band 3 is the nadir-looking 3N (``B3N``
is accepted as an alias).

Subsystem envelopes (VNIR 0.52-0.86, SWIR 1.60-2.43, TIR 8.125-11.65 um) were
checked against NASA/AIST material; the individual per-band ranges below are the
nominal values from the ASTER instrument papers.

Only the four VNIR/SWIR bands that line up with a standard role carry a ``standard``
name (G, R, N, S1). Bands 5-9 sit inside or around the Landsat/Sentinel SWIR 2 window
and do not map one-to-one onto it, so they are not assigned to ``S2``: use the native
ASTER ratios for them.

SWIR (B4-B9) has been unusable since 1 April 2008.

    from rockbands.sensors import aster
    aster.aster_kaolinite(B7=b7, B5=b5)
"""

from ._namespace import make_namespace
from .base import Band, Sensor

SENSOR = Sensor(
    key="aster",
    name="Terra ASTER",
    aliases=("terraaster", "terra"),
    band_aliases={"B3N": "B3"},
    bands=(
        Band("B1", "VNIR green", (520, 600), "G", 15),
        Band("B2", "VNIR red", (630, 690), "R", 15),
        Band("B3", "VNIR NIR (3N)", (760, 860), "N", 15),
        Band("B4", "SWIR 1", (1600, 1700), "S1", 30),
        Band("B5", "SWIR 2", (2145, 2185), None, 30),
        Band("B6", "SWIR 3", (2185, 2225), None, 30),
        Band("B7", "SWIR 4", (2235, 2285), None, 30),
        Band("B8", "SWIR 5", (2295, 2365), None, 30),
        Band("B9", "SWIR 6", (2360, 2430), None, 30),
        Band("B10", "TIR 1", (8125, 8475), None, 90),
        Band("B11", "TIR 2", (8475, 8825), None, 90),
        Band("B12", "TIR 3", (8925, 9275), None, 90),
        Band("B13", "TIR 4", (10250, 10950), None, 90),
        Band("B14", "TIR 5", (10950, 11650), None, 90),
    ),
    notes="SWIR subsystem (B4-B9) inoperable since 2008-04-01.",
)

__getattr__, __dir__ = make_namespace(SENSOR, globals())
