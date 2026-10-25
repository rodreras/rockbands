"""Public catalogue API: lookup, listing, and the callable wrapper around every entry."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional, Union

from ..errors import MissingBandError, UnknownRatioError
from ..sensors.base import Sensor
from ..sensors.registry import get_sensor
from .aster_catalogue import RATIOS as _ASTER
from .base import Composite, Ratio
from .composite_catalogue import COMPOSITES as _COMPOSITES
from .engine import Item, compute, native_map, supported_sensors
from .generic_catalogue import RATIOS as _GENERIC

CATALOGUE: Dict[str, Item] = {}
for _item in (*_GENERIC, *_COMPOSITES, *_ASTER):
    if _item.name in CATALOGUE:  # guards against copy-paste mistakes when adding entries
        raise RuntimeError(f"duplicate catalogue name {_item.name!r}")
    CATALOGUE[_item.name] = _item


def get_ratio(name: str) -> Item:
    """Look up a ratio or composite by name."""
    try:
        return CATALOGUE[name]
    except KeyError:
        close = [n for n in CATALOGUE if name.lower() in n or n in name.lower()][:5]
        hint = f" Did you mean: {', '.join(close)}?" if close else ""
        raise UnknownRatioError(f"unknown ratio {name!r}.{hint} See list_ratios().") from None


def list_ratios(
    sensor: Union[str, Sensor, None] = None,
    category: Optional[str] = None,
    kind: Optional[str] = None,
) -> List[Item]:
    """Catalogue entries, optionally filtered.

    ``sensor`` keeps only entries that sensor can evaluate, ``category`` is one of
    ``iron``, ``clay``, ``carbonate_mafic``, ``silicate``, ``silica``, ``general``,
    ``composite``; ``kind`` is ``"ratio"`` or ``"composite"``.
    """
    sensor_obj = get_sensor(sensor) if sensor is not None else None
    out = []
    for item in CATALOGUE.values():
        if category is not None and item.category != category:
            continue
        if kind is not None and item.kind != kind:
            continue
        if sensor_obj is not None and sensor_obj.key not in supported_sensors(item):
            continue
        out.append(item)
    return out


def names_supported_on(sensor: Sensor) -> List[str]:
    return [item.name for item in list_ratios(sensor)]


def _docstring(item: Item, sensor: Optional[Sensor]) -> str:
    lines = [f"{item.title}.", "", item.description, "", f"Formula: ``{item.formula}``"]
    if sensor is not None:
        try:
            mapping = native_map(item, sensor)
            lines.append(f"On {sensor.name}: needs " + ", ".join(
                f"{native} ({std})" if native != std else native for std, native in mapping.items()
            ))
        except Exception:
            lines.append(f"{sensor.name} cannot evaluate this (missing band).")
    else:
        lines.append("Needs: " + ", ".join(item.variables))
    lines.append("Runs on: " + (", ".join(supported_sensors(item)) or "no registered sensor"))
    if item.references:
        lines.append("References: " + "; ".join(item.references))
    if item.notes:
        lines.append("Note: " + item.notes)
    lines += ["", "Parameters: pass a mapping of bands and/or keyword arrays; extra bands are ignored.",
              "Division by zero gives NaN."]
    return "\n".join(lines)


def make_function(item: Item, sensor: Optional[Sensor] = None) -> Callable[..., Any]:
    """Wrap a catalogue entry in a plain function.

    Unbound (``sensor=None``): ``f(bands=None, /, *, sensor=None, **arrays)``.
    Bound to a sensor: ``f(bands=None, /, **arrays)``.
    """
    if sensor is None:
        def func(bands: Any = None, /, *, sensor: Union[str, Sensor, None] = None, **arrays: Any) -> Any:
            return compute(item, sensor, bands, **arrays)
        func.__module__ = "rockbands.ratios"
    else:
        bound = sensor

        def func(bands: Any = None, /, **arrays: Any) -> Any:  # type: ignore[misc]
            return compute(item, bound, bands, **arrays)
        func.__module__ = f"rockbands.sensors.{bound.key}"
    func.__name__ = func.__qualname__ = item.name
    func.__doc__ = _docstring(item, sensor)
    func.ratio = item  # type: ignore[attr-defined]
    func.sensor = sensor  # type: ignore[attr-defined]
    return func


@lru_cache(maxsize=None)
def _bind(name: str, sensor_key: str) -> Callable[..., Any]:
    return make_function(get_ratio(name), get_sensor(sensor_key))


def bind(name: str, sensor: Union[str, Sensor]) -> Callable[..., Any]:
    """The ratio ``name`` as a function fixed to ``sensor``."""
    return _bind(name, get_sensor(sensor).key)


def compute_all(
    bands: Any,
    sensor: Union[str, Sensor],
    kind: Optional[str] = None,
    category: Optional[str] = None,
    on_missing: str = "skip",
) -> Dict[str, Any]:
    """Evaluate every catalogue entry the sensor supports and return ``{name: result}``.

    ``kind`` (``"ratio"`` or ``"composite"``) and ``category`` filter the catalogue as in
    :func:`list_ratios`. If ``bands`` lacks a band some entry needs, that entry is skipped
    (``on_missing="skip"``, the default) or raises :class:`MissingBandError` (``"raise"``).
    """
    if on_missing not in {"skip", "raise"}:
        raise ValueError("on_missing must be 'skip' or 'raise'")
    out: Dict[str, Any] = {}
    for item in list_ratios(sensor=sensor, kind=kind, category=category):
        try:
            out[item.name] = compute(item, sensor, bands)
        except MissingBandError:
            if on_missing == "raise":
                raise
    return out


def evaluate_formula(
    formula: str,
    bands: Any = None,
    sensor: Union[str, Sensor, None] = None,
    **arrays: Any,
) -> Any:
    """Evaluate any formula written in standard band names, e.g. ``"(S1/S2)/(N/R)"``.

    The discovery tool: try a ratio from a paper on any sensor without adding it to the catalogue.
    """
    adhoc = Ratio("custom", "Custom formula", formula, "custom", "User-supplied formula.")
    return compute(adhoc, sensor, bands, **arrays)
