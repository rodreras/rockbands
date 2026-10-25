"""The ratio catalogue.

Every ratio and composite is available here as a function, e.g.::

    from rockbands import ratios
    ratios.ferric_iron_redness(R=red, B=blue)                  # standard band names
    ratios.ferric_iron_redness(bands, sensor="l8")             # native band ids of a sensor
    ratios.aster_kaolinite(B7=b7, B5=b5)                       # ASTER band numbers
    ratios.geology(bands, sensor="s2")                         # RGB composite, shape (3, rows, cols)
"""

from .api import (
    CATALOGUE,
    bind,
    compute_all,
    evaluate_formula,
    get_ratio,
    list_ratios,
    make_function,
    names_supported_on,
)
from .base import Composite, Ratio
from .engine import compute, native_map, supported_sensors

for _name, _item in CATALOGUE.items():
    globals()[_name] = make_function(_item)

__all__ = [
    "CATALOGUE",
    "Composite",
    "Ratio",
    "bind",
    "compute",
    "compute_all",
    "evaluate_formula",
    "get_ratio",
    "list_ratios",
    "make_function",
    "names_supported_on",
    "native_map",
    "supported_sensors",
    *CATALOGUE,
]
