"""Makes ``rockbands.sensors.s2.<ratio_name>(...)`` work.

Each sensor module calls ``make_namespace`` and exposes the result as its
module-level ``__getattr__`` and ``__dir__`` (PEP 562). The ratio functions are
therefore not copied into every sensor folder: they are bound to the sensor on
first access, and tab-completion in IPython/Jupyter lists what the sensor supports.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Tuple

from .base import Sensor


def make_namespace(sensor: Sensor, module_globals: Dict[str, Any]) -> Tuple[Callable[[str], Any], Callable[[], List[str]]]:
    def __getattr__(name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        from ..errors import UnknownRatioError
        from ..ratios.api import bind

        try:
            return bind(name, sensor)
        except UnknownRatioError:
            raise AttributeError(f"sensor module {sensor.key!r} has no attribute or ratio {name!r}") from None

    def __dir__() -> List[str]:
        from ..ratios.api import names_supported_on

        return sorted(set(module_globals) | set(names_supported_on(sensor)))

    return __getattr__, __dir__
