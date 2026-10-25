"""ASTER band ratios, from the 'Aster Band Ratios' table of awesome-mining-band-ratio.

Formulas use ASTER band numbers (B1..B14, with B3 = 3N). "92% cfd" in the source is kept
as "92% confidence" in the description.

Input units follow the cited papers: reflectance (or any consistent unit, since ratios
cancel gain) for VNIR/SWIR, and radiance or emissivity for TIR.
"""

from __future__ import annotations

from .base import Ratio

_SWIR_NOTE = "Uses SWIR bands (B4-B9): only valid for scenes acquired before 1 April 2008, when the SWIR detectors failed."
_TIR_NOTE = "Uses thermal bands (B10-B14): supply emissivity or radiance consistently, as in the cited work."


def _aster(name, title, formula, category, description, references, extra_note=""):
    from ..expression import required_names

    numbers = {int(v[1:]) for v in required_names(formula)}
    notes = []
    if numbers & set(range(4, 10)):
        notes.append(_SWIR_NOTE)
    if numbers & set(range(10, 15)):
        notes.append(_TIR_NOTE)
    if extra_note:
        notes.append(extra_note)
    return Ratio(
        name=f"aster_{name}",
        title=title,
        formula=formula,
        category=category,
        description=description,
        references=tuple(r.strip() for r in references.split(";")),
        namespace="aster",
        notes=" ".join(notes),
    )


RATIOS = (
    # -- Iron minerals ---------------------------------------------------
    _aster("ferric_iron", "Ferric iron (Fe3+)", "B2/B1", "iron", "Ferric iron, Fe3+.",
           "Rowan and Mars, 2003; Hewson et al., 2001, 2004a"),
    _aster("ferrous_iron", "Ferrous iron (Fe2+)", "(B5/B3)+(B1/B2)", "iron", "Ferrous iron, Fe2+.",
           "Rowan and Mars, 2003"),
    _aster("gossan", "Gossan", "B4/B2", "iron", "Gossan.", "Volesky et al., 2003"),
    _aster("ferrous_silicates", "Ferrous silicates", "B5/B4", "iron",
           "Ferrous silicates (biotite, chlorite, amphibolite); Cu-Au alteration.", "Hewson et al., 2001, 2004a"),
    _aster("ferric_oxides", "Ferric oxides", "B4/B3", "iron", "Ferric oxides.", "Hewson et al., 2001, 2004a"),
    # -- Carbonates / mafic minerals ------------------------------------------
    _aster("carbonate_chlorite_epidote", "Carbonate / chlorite / epidote", "(B7+B9)/B8", "carbonate_mafic",
           "Carbonate, chlorite and epidote.", "Rowan and Mars, 2003"),
    _aster("carbonate_index", "Carbonate index", "B13/B14", "carbonate_mafic",
           "Carbonate index: exoskarn (calcite/dolomite), 92% confidence.",
           "Bierwirth, 2002; Nimoyima (spelling as in the source table)"),
    _aster("epidote_chlorite_amphibole", "Epidote / chlorite / amphibole", "(B6+B9)/(B7+B8)", "carbonate_mafic",
           "Epidote, chlorite and amphibole (endoskarn).", "Hewson et al., 2001, 2004a"),
    _aster("amphibole_mgoh", "Amphibole / MgOH", "(B6+B9)/B8", "carbonate_mafic",
           "Amphibole / MgOH; can also respond to other MgOH minerals or carbonate.", "Hewson et al., 2001, 2004a"),
    _aster("amphibole", "Amphibole", "B6/B8", "carbonate_mafic", "Amphibole.", "Bierwirth, 2002"),
    _aster("dolomite", "Dolomite", "(B6+B8)/B7", "carbonate_mafic", "Dolomite.", "Rowan and Mars, 2003"),
    _aster("hydroxyl_index", "Hydroxyl group index (OHI)", "(B7/B6)*(B4/B6)", "carbonate_mafic",
           "Hydroxyl group index (OHI), 92% confidence.", "Ninomiya, 2002"),
    _aster("kaolinite_index", "Kaolinite index (KLI)", "(B4/B5)*(B8/B6)", "carbonate_mafic",
           "Kaolinite index (KLI), 92% confidence.", "Ninomiya, 2002"),
    _aster("alunite_index", "Alunite index (ALI)", "(B7/B5)*(B7/B8)", "carbonate_mafic",
           "Alunite index (ALI), 92% confidence.", "Ninomiya, 2002"),
    _aster("calcite_index", "Calcite index (CLI)", "(B6/B8)*(B9/B8)", "carbonate_mafic",
           "Calcite index (CLI).", "Ninomiya, 2002"),
    # -- Silicates -----------------------------------------------------------
    _aster("phyllic_alteration", "Phyllic alteration", "(B5+B7)/B6", "silicate",
           "Sericite / muscovite / illite / smectite (phyllic alteration).",
           "Rowan and Mars, 2003; Hewson et al., 2001, 2004a"),
    _aster("alunite_kaolinite", "Alunite / kaolinite", "(B4+B6)/B5", "silicate",
           "Alunite / kaolinite (pyrophyllite), 92% confidence.", "Rowan and Mars, 2003"),
    _aster("muscovite", "Muscovite", "B7/B6", "silicate", "Muscovite, 92% confidence.", "Hewson et al., 2001, 2004a"),
    _aster("kaolinite", "Kaolinite", "B7/B5", "silicate", "Kaolinite, 92% confidence.", "Hewson et al., 2001, 2004a"),
    _aster("clay", "Clay", "(B5*B7)/(B6*B6)", "silicate", "Clay, 92% confidence.", "Bierwirth, 2002"),
    # -- Silica (SiO2) ---------------------------------------------------------
    _aster("quartz_index", "Quartz index", "B14/B12", "silica", "Quartz-rich rocks (Qz index).", "Rowan and Mars, 2003"),
    _aster("quartz_ninomiya", "Quartz (Ninomiya)", "(B11/B10)*(B11/B12)", "silica", "Quartz, 92% confidence.",
           "Ninomiya, 2003a"),
    _aster("basic_degree_index", "Basic degree index", "B12/B13", "silica",
           "Silica: basic degree index (gnt).",
           "Ninomiya, 2002; Bierwirth, 2002; Hewson et al., 2001, 2004a"),
    _aster("silica", "Silica", "B13/B10", "silica", "Silica.", "Hewson et al., 2001, 2004a"),
    _aster("silica_index", "Silica index", "(B11*B11)/(B10*B12)", "silica", "Silica index, 92% confidence.",
           "Ninomiya, 2002",
           extra_note="The source table prints this as '(B11xB11)(B10B12)'; it is implemented as B11^2 / (B10*B12)."),
)
