"""Catalogue entry types.

A :class:`Ratio` is one formula; a :class:`Composite` is three formulas (R, G, B channels).
Both are plain data: the maths lives in ``expression.py`` and the sensor logic in ``engine.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Tuple

from ..expression import required_names


@dataclass(frozen=True)
class Ratio:
    """One band ratio.

    ``namespace`` says what the names in ``formula`` mean:

    * ``"standard"``: standard roles (``R``, ``N``, ``S1`` ...). Runs on every sensor that
      has all the bands.
    * ``"aster"``: ASTER band numbers (``B1`` ... ``B14``). Runs on ASTER only, because the
      other sensors have no equivalent of ASTER's narrow SWIR and TIR bands.
    """

    name: str
    title: str
    formula: str
    category: str
    description: str
    references: Tuple[str, ...] = ()
    namespace: str = "standard"
    notes: str = ""

    kind: ClassVar[str] = "ratio"

    @property
    def expressions(self) -> Tuple[str, ...]:
        return (self.formula,)

    @property
    def variables(self) -> Tuple[str, ...]:
        return required_names(self.formula)


@dataclass(frozen=True)
class Composite:
    """A three-channel RGB composite whose channels are bands or ratios (R, G, B order)."""

    name: str
    title: str
    channels: Tuple[str, str, str]
    description: str
    references: Tuple[str, ...] = ()
    notes: str = ""
    category: str = "composite"
    namespace: str = "standard"

    kind: ClassVar[str] = "composite"

    @property
    def formula(self) -> str:
        return ", ".join(self.channels)

    @property
    def expressions(self) -> Tuple[str, ...]:
        return tuple(self.channels)

    @property
    def variables(self) -> Tuple[str, ...]:
        seen: dict[str, None] = {}
        for channel in self.channels:
            for name in required_names(channel):
                seen.setdefault(name, None)
        return tuple(seen)
