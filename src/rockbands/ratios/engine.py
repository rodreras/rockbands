"""Resolves a catalogue entry against a sensor and evaluates it on band arrays."""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Tuple, Union

from ..errors import BandNotAvailableError, MissingBandError
from ..expression import evaluate
from ..sensors.base import STANDARD_BANDS, Sensor, normalize_band_id
from ..sensors.registry import SENSORS, get_sensor
from ..utils.arrays import as_mapping, coerce_array, stack_channels
from .base import Composite, Ratio

Item = Union[Ratio, Composite]


def _supports(item: Item, sensor: Sensor) -> bool:
    if item.namespace == "aster":
        return sensor.key == "aster"
    return all(sensor.has(v) for v in item.variables)


def supported_sensors(item: Item) -> Tuple[str, ...]:
    """Keys of every registered sensor that can evaluate the item."""
    return tuple(key for key, sensor in SENSORS.items() if _supports(item, sensor))


def _describe(standard: str) -> str:
    label, (lo, hi) = STANDARD_BANDS[standard]
    return f"{standard} ({label}, {lo:g}-{hi:g} nm)"


def native_map(item: Item, sensor: Optional[Sensor]) -> Dict[str, str]:
    """Map each formula variable to the sensor's native band id (identity when there is no sensor)."""
    variables = item.variables
    if item.namespace == "aster":
        if sensor is not None and sensor.key != "aster":
            raise BandNotAvailableError(
                f"'{item.name}' is defined on ASTER band numbers ({', '.join(variables)}), which {sensor.name} "
                f"does not have. It only runs on ASTER."
            )
        return {v: v for v in variables}
    if sensor is None:
        return {v: v for v in variables}
    missing = [v for v in variables if not sensor.has(v)]
    if missing:
        runnable = ", ".join(supported_sensors(item)) or "none"
        raise BandNotAvailableError(
            f"'{item.name}' needs {'; '.join(_describe(m) for m in missing)}, "
            f"which {sensor.name} does not have. Sensors that can run it: {runnable}."
        )
    return {v: sensor.native_for(v) for v in variables}  # type: ignore[misc]


def _resolver(item: Item, sensor: Optional[Sensor]) -> Callable[[str], str]:
    if sensor is not None:
        return sensor.resolve_id
    if item.namespace == "aster":
        return SENSORS["aster"].resolve_id
    return normalize_band_id


def compute(item: Item, sensor: Union[str, Sensor, None] = None, bands: Any = None, **kwargs: Any) -> Any:
    """Evaluate a ratio or composite.

    ``bands`` (any mapping of band id -> array) and ``kwargs`` are merged; keys may be the
    sensor's native ids (``B4``, ``b04``, ``SR_B4``) or standard names (``R``). With no
    ``sensor`` the keys must be standard names (or ASTER numbers for ASTER ratios).
    Extra bands in the mapping are ignored, so you can pass a whole scene.
    """
    sensor_obj = get_sensor(sensor) if sensor is not None else None
    mapping = native_map(item, sensor_obj)
    resolve = _resolver(item, sensor_obj)

    supplied: Dict[str, Any] = {}
    for source in (as_mapping(bands), kwargs):
        for key, value in source.items():
            supplied[resolve(key)] = value

    arrays: Dict[str, Any] = {}
    missing = []
    for variable in item.variables:
        for candidate in dict.fromkeys((variable, mapping[variable])):
            key = resolve(candidate)
            if key in supplied:
                arrays[variable] = coerce_array(supplied[key])
                break
        else:
            missing.append(variable)

    if missing:
        wanted = ", ".join(
            f"{mapping[v]} ({v})" if mapping[v] != v else v for v in item.variables
        )
        absent = ", ".join(mapping[v] if mapping[v] != v else v for v in missing)
        hint = (
            "" if sensor_obj is not None or item.namespace == "aster"
            else " No sensor was given, so use standard names (R, N, S1 ...) or pass sensor='s2' / 'l8' / ..."
        )
        raise MissingBandError(
            f"'{item.name}' needs {wanted}; missing {absent}. Got: {sorted(supplied) or 'nothing'}.{hint}"
        )

    results = [evaluate(expr, arrays) for expr in item.expressions]
    return stack_channels(results) if item.kind == "composite" else results[0]
