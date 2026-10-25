"""Sensor and band definitions.

The idea borrowed from awesome-spectral-indices: formulas are written in
*standard* band names (``R``, ``N``, ``S1`` ...) and every sensor declares which
of its native bands plays each standard role. A sensor that has no band for a
role (Landsat has no red edge) simply cannot evaluate formulas that need it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Mapping, Optional, Tuple

# Standard band names, in wavelength order, with the nominal ranges used by the
# awesome-mining-band-ratio / awesome-spectral-indices tables (nm).
STANDARD_BANDS: Mapping[str, Tuple[str, Tuple[float, float]]] = {
    "A": ("Aerosols / coastal", (400, 455)),
    "B": ("Blue", (450, 530)),
    "G": ("Green", (510, 600)),
    "R": ("Red", (620, 690)),
    "RE1": ("Red Edge 1", (695, 715)),
    "RE2": ("Red Edge 2", (730, 750)),
    "RE3": ("Red Edge 3", (765, 795)),
    "N": ("NIR", (760, 900)),
    "N2": ("NIR 2 (narrow)", (850, 880)),
    "WV": ("Water vapour", (930, 960)),
    "S1": ("SWIR 1", (1550, 1750)),
    "S2": ("SWIR 2", (2080, 2350)),
    "T": ("Thermal", (10400, 12500)),
    "T1": ("Thermal 1", (10600, 11190)),
    "T2": ("Thermal 2", (11500, 12510)),
}

_NATIVE_ID = re.compile(r"^(?:SR_|ST_)?(?:BAND_?|B)0*(\d+)([A-Z]?)$")


def normalize_band_id(raw: str) -> str:
    """Canonical spelling of a band key.

    ``"b04"``, ``"B04"``, ``"band_4"`` and Landsat Collection 2 asset names such as
    ``"SR_B4"`` all become ``"B4"``; ``"b8a"`` becomes ``"B8A"``. Standard names
    (``"nir"`` is *not* one; ``"N"``, ``"S1"``, ``"RE2"`` are) are only upper-cased.
    """
    key = str(raw).strip().upper()
    match = _NATIVE_ID.match(key)
    if match:
        return f"B{match.group(1)}{match.group(2)}"
    return key


@dataclass(frozen=True)
class Band:
    """One native band of a sensor."""

    id: str
    name: str
    wavelength_nm: Tuple[float, float]
    standard: Optional[str] = None
    resolution_m: Optional[int] = None

    @property
    def midpoint_nm(self) -> float:
        return (self.wavelength_nm[0] + self.wavelength_nm[1]) / 2

    @classmethod
    def from_center(
        cls, id: str, name: str, center_nm: float, width_nm: float, standard: Optional[str] = None,
        resolution_m: Optional[int] = None,
    ) -> "Band":
        half = width_nm / 2
        return cls(id, name, (center_nm - half, center_nm + half), standard, resolution_m)


@dataclass(frozen=True)
class Sensor:
    """A satellite sensor: its native bands and which standard roles they fill."""

    key: str
    name: str
    bands: Tuple[Band, ...]
    aliases: Tuple[str, ...] = ()
    band_aliases: Mapping[str, str] = field(default_factory=dict)
    notes: str = ""

    def __post_init__(self) -> None:
        standards = [b.standard for b in self.bands if b.standard]
        if len(standards) != len(set(standards)):
            raise ValueError(f"sensor {self.key!r} maps two bands to the same standard name")

    # -- lookups ---------------------------------------------------------
    @property
    def standards(self) -> Tuple[str, ...]:
        """Standard roles this sensor can fill, in wavelength order."""
        have = {b.standard for b in self.bands if b.standard}
        return tuple(s for s in STANDARD_BANDS if s in have)

    def resolve_id(self, raw: str) -> str:
        """Normalise a native band key and apply this sensor's aliases (e.g. ASTER ``B3N`` -> ``B3``)."""
        key = normalize_band_id(raw)
        return self.band_aliases.get(key, key)

    def band(self, id_or_standard: str) -> Band:
        key = self.resolve_id(id_or_standard)
        for b in self.bands:
            if b.id == key or b.standard == key:
                return b
        raise KeyError(f"{self.key}: no band {id_or_standard!r}")

    def native_for(self, standard: str) -> Optional[str]:
        """Native band id playing the standard role, or ``None`` if the sensor lacks it."""
        for b in self.bands:
            if b.standard == standard:
                return b.id
        return None

    def has(self, standard: str) -> bool:
        return self.native_for(standard) is not None

    def __repr__(self) -> str:  # keep reprs short in tracebacks
        return f"Sensor({self.key!r})"
