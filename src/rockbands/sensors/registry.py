"""Sensor registry and name lookup."""

from __future__ import annotations

import re
from typing import Dict, Tuple, Union

from ..errors import UnknownSensorError
from . import aster, l4, l5, l7, l8, l9, s2
from .base import Sensor

SENSORS: Dict[str, Sensor] = {m.SENSOR.key: m.SENSOR for m in (s2, l4, l5, l7, l8, l9, aster)}


def _squash(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


_LOOKUP: Dict[str, str] = {}
for _sensor in SENSORS.values():
    for _name in (_sensor.key, _sensor.name, *_sensor.aliases):
        _LOOKUP[_squash(_name)] = _sensor.key


def get_sensor(sensor: Union[str, Sensor]) -> Sensor:
    """Return a :class:`Sensor` from its key or any common spelling (``"Landsat-8"``, ``"sentinel2"``)."""
    if isinstance(sensor, Sensor):
        return sensor
    key = _squash(str(sensor))
    if key in _LOOKUP:
        return SENSORS[_LOOKUP[key]]
    hint = ""
    if key in {"l6", "landsat6"}:
        hint = " Landsat 6 failed to reach orbit, so it has no data."
    raise UnknownSensorError(f"unknown sensor {sensor!r}. Available: {', '.join(SENSORS)}.{hint}")


def list_sensors() -> Tuple[str, ...]:
    return tuple(SENSORS)
