"""Convert raw product values to surface reflectance before computing ratios.

Ratios of mixed-up units (one band scaled, another not) are meaningless, and
additive offsets change a ratio's value, so scaling must be applied first.
"""

from __future__ import annotations

from typing import Any, Optional, Tuple

import numpy as np

from ..sensors.base import Sensor
from ..sensors.registry import get_sensor
from .arrays import coerce_array

# Landsat Collection 2 Level-2 surface reflectance: refl = DN * 0.0000275 - 0.2
_LANDSAT_C2_SCALE = 0.0000275
_LANDSAT_C2_OFFSET = -0.2


def dn_to_reflectance(
    array: Any,
    sensor: "str | Sensor",
    *,
    nodata: Optional[float] = 0,
    boa_add_offset: float = -1000.0,
    clip: Optional[Tuple[float, float]] = None,
) -> Any:
    """Scale Level-2 digital numbers to surface reflectance.

    Parameters
    ----------
    array
        One band of raw product values.
    sensor
        ``"s2"`` (Sentinel-2 L2A) or ``"l4"``/``"l5"``/``"l7"``/``"l8"``/``"l9"``
        (Landsat Collection 2 Level-2 surface reflectance).
    nodata
        Raw value treated as no-data and returned as NaN. Both products use 0.
        Pass ``None`` to disable.
    boa_add_offset
        Sentinel-2 only. Processing baseline 04.00 (January 2022) and later adds
        an offset of -1000 to L2A values (``reflectance = (DN + offset) / 10000``).
        Use ``0`` for older baselines.
    clip
        Optional ``(low, high)`` to clip the result, e.g. ``(0, 1)``.

    ASTER is not handled here: its VNIR/SWIR products come as reflectance or
    radiance depending on the product level, so scale it with the product's own
    metadata.
    """
    sensor = get_sensor(sensor)
    band = coerce_array(array)
    if sensor.key == "s2":
        scaled = (band + boa_add_offset) / 10000.0
    elif sensor.key in {"l4", "l5", "l7", "l8", "l9"}:
        scaled = band * _LANDSAT_C2_SCALE + _LANDSAT_C2_OFFSET
    else:
        raise ValueError(
            f"dn_to_reflectance does not know the scaling of sensor {sensor.key!r}. "
            "For ASTER L1T use aster_dn_to_radiance."
        )

    if nodata is not None:
        invalid = band == nodata
        scaled = scaled.where(~invalid) if hasattr(scaled, "where") else np.where(invalid, np.nan, scaled)
    if clip is not None:
        scaled = scaled.clip(*clip) if hasattr(scaled, "clip") else np.clip(scaled, *clip)
    return scaled


# ASTER unit conversion coefficients, W/(m^2 sr um) per DN (ASTER L1T Product Guide, Table 2-3).
_ASTER_UCC = {
    "B1": {"HGH": 0.676, "NOR": 1.688, "LO1": 2.25},
    "B2": {"HGH": 0.708, "NOR": 1.415, "LO1": 1.89},
    "B3": {"HGH": 0.423, "NOR": 0.862, "LO1": 1.15},
    "B4": {"HGH": 0.1087, "NOR": 0.2174, "LO1": 0.290, "LO2": 0.290},
    "B5": {"HGH": 0.0348, "NOR": 0.0696, "LO1": 0.0925, "LO2": 0.409},
    "B6": {"HGH": 0.0313, "NOR": 0.0625, "LO1": 0.0830, "LO2": 0.390},
    "B7": {"HGH": 0.0299, "NOR": 0.0597, "LO1": 0.0795, "LO2": 0.332},
    "B8": {"HGH": 0.0209, "NOR": 0.0417, "LO1": 0.0556, "LO2": 0.245},
    "B9": {"HGH": 0.0159, "NOR": 0.0318, "LO1": 0.0424, "LO2": 0.265},
    # TIR has a single gain setting.
    "B10": {"NOR": 6.822e-3},
    "B11": {"NOR": 6.780e-3},
    "B12": {"NOR": 6.590e-3},
    "B13": {"NOR": 5.693e-3},
    "B14": {"NOR": 5.225e-3},
}


def aster_dn_to_radiance(array: Any, band: str, gain: str = "NOR") -> Any:
    """Convert one ASTER L1T band from digital numbers to at-sensor radiance.

    ``radiance = (DN - 1) * UCC`` in W/(m^2 sr um), with the unit conversion coefficient
    (UCC) of the band's gain setting. DN 0 is the fill value and becomes NaN.

    Parameters
    ----------
    band
        ASTER band id (``"B1"`` ... ``"B14"``; ``"B3N"`` is accepted).
    gain
        ``"HGH"``, ``"NOR"`` (default), ``"LO1"`` or ``"LO2"``. VNIR and SWIR bands record a gain
        setting per scene and band (in the product metadata), and the wrong one rescales that band
        and therefore every ratio that uses it. TIR has a single gain, so ``gain`` is ignored there.
    """
    band_id = get_sensor("aster").resolve_id(band)
    try:
        table = _ASTER_UCC[band_id]
    except KeyError:
        raise ValueError(f"unknown ASTER band {band!r}; expected B1 ... B14") from None
    key = "NOR" if band_id in {"B10", "B11", "B12", "B13", "B14"} else str(gain).upper()
    if key not in table:
        raise ValueError(f"ASTER {band_id} has no gain setting {gain!r}; choose from {sorted(table)}")
    dn = coerce_array(array)
    radiance = (dn - 1.0) * table[key]
    invalid = dn == 0
    return radiance.where(~invalid) if hasattr(radiance, "where") else np.where(invalid, np.nan, radiance)
