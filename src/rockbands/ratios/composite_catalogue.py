"""RGB composites and ratio composites, from awesome-mining-band-ratio.

Channels are given in R, G, B display order and use standard band names.
"""

from __future__ import annotations

from .base import Composite

_SRC = ("awesome-mining-band-ratio, 'RGB Composition and Band Ratio' table",)

COMPOSITES = (
    # -- plain band composites -------------------------------------------------
    Composite("natural_colour", "Natural colour", ("R", "G", "B"), "True-colour view.", _SRC),
    Composite("colour_infrared", "Colour infrared (vegetation)", ("N", "R", "G"), "Vegetation shows red.", _SRC),
    Composite("false_colour_urban", "False colour (urban)", ("S2", "S1", "R"), "Urban false colour.", _SRC),
    Composite("agriculture", "Agriculture", ("S1", "N", "B"), "Agriculture composite.", _SRC),
    Composite("geology", "Geology", ("S2", "R", "B"), "Geology composite.", _SRC),
    Composite("bathymetric", "Bathymetric", ("R", "G", "A"), "Bathymetric composite. Needs the coastal/aerosol band.", _SRC),
    Composite("atmospheric_penetration", "Atmospheric penetration", ("S2", "S1", "N2"), "Atmospheric penetration. Needs the narrow NIR band.", _SRC),
    Composite("swir_composite", "SWIR", ("S2", "N2", "R"), "SWIR composite. Needs the narrow NIR band.", _SRC),
    Composite("swir_2_composite", "SWIR-2", ("B", "S1", "S2"), "SWIR-2 composite.", _SRC),
    # -- ratio composites ------------------------------------------------------
    Composite("ross_smail_getech", "Ross Smail / Getech", ("S1/R", "R/B", "S2/S1"), "Ratio composite attributed to Ross Smail / Getech.", _SRC),
    Composite("gad_kusky_1", "Gad and Kusky 1", ("S1/R", "S2/S1", "S1/B"), "Ratio composite after Gad and Kusky.", _SRC),
    Composite("gad_kusky_2", "Gad and Kusky 2", ("S2/S1", "S1/N", "R/B"), "Ratio composite after Gad and Kusky; serpentinites in dark brown-green.", _SRC),
    Composite("zohair_2019", "Zohair et al. 2019", ("S1/S2", "S1/N", "R/B"), "Ratio composite after Zohair et al. (2019); serpentinites in dark brown.", _SRC),
    Composite("pour", "Pour", ("R/B", "R/S1", "S1/S2"), "Ratio composite after Pour; serpentinites in yellow.", _SRC),
    Composite("sultan_gomez", "Sultan 1986 / Gomez 2005", ("S1/S2", "S1/B", "(S1/N)*(R/N)"), "Ratio composite after Sultan (1986) / Gomez (2005).", _SRC),
    Composite("abrams_1983", "Abrams 1983", ("S1/S2", "N/S1", "R/B"), "Ratio composite after Abrams (1983): ultramafic / basic-mafic / felsic.", _SRC),
    Composite("mineral_map", "Mineral map", ("S2/N", "N/S2", "S1/R"), "Mineral map composite, as listed in the source table.", _SRC),
)
