"""Multi-sensor ratios, from the 'Landsat and Sentinel' section of awesome-mining-band-ratio.

Formulas use the standard band names of awesome-spectral-indices (A, B, G, R, N, N2, S1, S2 ...),
so one definition runs on Sentinel-2, Landsat 4/5/7/8/9 (and ASTER where its bands allow).
"""

from __future__ import annotations

from .base import Ratio

_SRC = "awesome-mining-band-ratio, 'RGB Composition and Band Ratio' table"

RATIOS = (
    Ratio("ferric_iron_redness", "Ferric iron 'redness'", "R/B", "iron",
          "Red over blue: highlights ferric iron (iron oxides) as a 'redness' index.", (_SRC,)),
    Ratio("ferric_iron_2", "Ferric iron 2", "(R/B)*((R+S1)/N)", "iron",
          "Redness weighted by the SWIR1+red over NIR term; a second ferric iron ratio.", (_SRC,)),
    Ratio("ferrous_iron", "Ferrous iron", "(G+S1)/(R+N)", "iron",
          "Ferrous iron. The source table comments that it targets coarse-grained ferric iron.", (_SRC,)),
    Ratio("clay_sulphate_mica_marble", "Clay, sulphate, mica, marble", "(S1/S2)/(N/R)", "clay",
          "SWIR1/SWIR2 normalised by NIR/red: clay, sulphate, mica and marble.", (_SRC,)),
    Ratio("iron_sulphate", "Iron sulphate", "(B/A)-(N/R)", "iron",
          "(Blue/aerosol) minus (NIR/red): iron sulphate. Needs the coastal/aerosol band.", (_SRC,)),
    Ratio("ndvi", "Vegetation index (NDVI)", "(N-R)/(N+R)", "general",
          "Normalised difference vegetation index, listed in the source for masking vegetation.", (_SRC,)),
    Ratio("moisture_index", "Moisture index", "(N2-S1)/(N2+S1)", "general",
          "Normalised difference of narrow NIR and SWIR1. Needs the narrow NIR band (Sentinel-2 B8A).", (_SRC,)),
    Ratio("ndwi", "NDWI", "(G-N)/(G+N)", "general", "Normalised difference water index (McFeeters form).", (_SRC,)),
)
