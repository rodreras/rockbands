"""Compare bands across satellites and see which ratios each one can run.

These answer the practical questions behind "does this ratio transfer from sensor A to B?":

* :func:`compare_bands`      which native band plays each role (NIR, SWIR 1 ...) on each sensor
* :func:`spectral_equivalence` how much the matching bands of two sensors actually overlap
* :func:`aster_band_coverage`  which bands of other sensors cover each ASTER band
* :func:`ratio_support`      which ratios each sensor can evaluate, and what it lacks
* :func:`translate`          a ratio's formula rewritten in a sensor's native band ids
"""

from __future__ import annotations

import re
from typing import Iterable, List, Optional, Sequence, Tuple, Union

from ..ratios.api import CATALOGUE, get_ratio, list_ratios
from ..ratios.engine import Item, native_map, supported_sensors
from ..sensors.base import STANDARD_BANDS, Band, Sensor
from ..sensors.registry import SENSORS, get_sensor
from .table import Table

SensorLike = Union[str, Sensor]


def _sensors(sensors: Optional[Iterable[SensorLike]]) -> List[Sensor]:
    return [get_sensor(s) for s in sensors] if sensors is not None else list(SENSORS.values())


def _item(ratio: Union[str, Item]) -> Item:
    return get_ratio(ratio) if isinstance(ratio, str) else ratio


def _range(band: Band) -> str:
    lo, hi = band.wavelength_nm
    return f"{round(lo)}-{round(hi)}"


def _overlap_nm(a: Band, b: Band) -> float:
    return max(0.0, min(a.wavelength_nm[1], b.wavelength_nm[1]) - max(a.wavelength_nm[0], b.wavelength_nm[0]))


def _width(band: Band) -> float:
    return band.wavelength_nm[1] - band.wavelength_nm[0]


def compare_bands(
    sensors: Optional[Iterable[SensorLike]] = None,
    standards: Optional[Sequence[str]] = None,
    ratio: Union[str, Item, None] = None,
    only_common: bool = False,
    show_ranges: bool = True,
) -> Table:
    """Which native band fills each standard role on each sensor.

    >>> print(compare_bands(["s2", "l8", "l7"], standards=["B", "R", "N", "S1"]))

    Parameters
    ----------
    sensors
        Sensors to show (default: all registered).
    standards
        Roles to show (default: all, in wavelength order).
    ratio
        A ratio or composite (name or object): show only the roles it needs. For ASTER-number
        ratios this switches to :func:`aster_band_coverage`.
    only_common
        Keep only roles that every selected sensor has.
    show_ranges
        Append each band's wavelength range in nm, e.g. ``B8 (780-885)``.
    """
    chosen = _sensors(sensors)
    if ratio is not None:
        item = _item(ratio)
        if item.namespace == "aster":
            return aster_band_coverage(chosen, [v for v in item.variables])
        standards = list(item.variables)
    roles = [s for s in (standards or STANDARD_BANDS) if s in STANDARD_BANDS]
    unknown = [s for s in (standards or []) if s not in STANDARD_BANDS]
    if unknown:
        raise ValueError(f"unknown standard band name(s) {unknown}; choose from {list(STANDARD_BANDS)}")

    rows = []
    for role in roles:
        cells = []
        for sensor in chosen:
            native = sensor.native_for(role)
            if native is None:
                cells.append("-")
            else:
                band = sensor.band(native)
                cells.append(f"{native} ({_range(band)})" if show_ranges else native)
        if only_common and "-" in cells:
            continue
        label, (lo, hi) = STANDARD_BANDS[role]
        rows.append([role, label, f"{lo:g}-{hi:g}", *cells])
    title = "Band comparison (nm). '-' means the sensor has no band for that role."
    return Table(title, ["Role", "Description", "Nominal (nm)", *[s.key for s in chosen]], rows)


def band_overlap(standard: str, sensor_a: SensorLike, sensor_b: SensorLike) -> dict:
    """Spectral overlap of the bands that fill one role on two sensors.

    Returns the two band ids, the overlap width, the fraction of each band it covers, the
    intersection-over-union and the shift between band midpoints. A value near 1.0 means the
    ratio should transfer closely; low values mean the "same" ratio is only an approximation.
    """
    a, b = get_sensor(sensor_a), get_sensor(sensor_b)
    for sensor in (a, b):
        if not sensor.has(standard):
            raise ValueError(f"{sensor.name} has no band for role {standard!r}")
    band_a, band_b = a.band(standard), b.band(standard)
    overlap = _overlap_nm(band_a, band_b)
    union = _width(band_a) + _width(band_b) - overlap
    return {
        "standard": standard,
        "band_a": band_a.id,
        "band_b": band_b.id,
        "overlap_nm": overlap,
        "fraction_of_a": overlap / _width(band_a),
        "fraction_of_b": overlap / _width(band_b),
        "iou": overlap / union if union else 0.0,
        "midpoint_shift_nm": band_b.midpoint_nm - band_a.midpoint_nm,
    }


def spectral_equivalence(sensor_a: SensorLike, sensor_b: SensorLike, standards: Optional[Sequence[str]] = None) -> Table:
    """How closely the shared bands of two sensors match (see :func:`band_overlap`)."""
    a, b = get_sensor(sensor_a), get_sensor(sensor_b)
    roles = [s for s in (standards or STANDARD_BANDS) if a.has(s) and b.has(s)]
    rows = []
    for role in roles:
        o = band_overlap(role, a, b)
        rows.append([
            role, o["band_a"], o["band_b"], f"{o['overlap_nm']:g}",
            f"{o['fraction_of_a']:.0%}", f"{o['fraction_of_b']:.0%}", f"{o['iou']:.2f}", f"{o['midpoint_shift_nm']:+.0f}",
        ])
    cols = ["Role", a.key, b.key, "Overlap (nm)", f"% of {a.key}", f"% of {b.key}", "IoU", "Midpoint shift (nm)"]
    return Table(f"Spectral equivalence: {a.name} vs {b.name}", cols, rows)


def aster_band_coverage(sensors: Optional[Iterable[SensorLike]] = None, aster_bands: Optional[Sequence[str]] = None) -> Table:
    """Which bands of other sensors cover each ASTER band.

    ASTER's narrow SWIR bands (B5-B9) and thermal bands (B10-B14) fall inside, or across,
    single wide bands of Landsat and Sentinel-2 (for example B5-B8 sit inside Sentinel-2 B12), so
    ASTER ratios built from them cannot be reproduced on those sensors. The percentage is how much
    of the ASTER band the other band covers.
    """
    aster = SENSORS["aster"]
    others = [s for s in _sensors(sensors) if s.key != "aster"]
    wanted = [aster.resolve_id(b) for b in aster_bands] if aster_bands else [b.id for b in aster.bands]
    rows = []
    for band_id in wanted:
        ab = aster.band(band_id)
        cells = []
        for sensor in others:
            hits = [(b, _overlap_nm(ab, b) / _width(ab)) for b in sensor.bands]
            hits = [(b, f) for b, f in hits if f > 0]
            cells.append(", ".join(f"{b.id} ({f:.0%})" for b, f in hits) or "-")
        rows.append([ab.id, ab.name, _range(ab), *cells])
    title = "ASTER band coverage by other sensors (share of the ASTER band's range covered). '-' means none."
    return Table(title, ["ASTER", "Name", "Range (nm)", *[s.key for s in others]], rows)


def ratio_support(
    sensors: Optional[Iterable[SensorLike]] = None,
    kind: Optional[str] = None,
    category: Optional[str] = None,
) -> Table:
    """Matrix of catalogue entries by sensor: ``ok`` or the roles the sensor lacks."""
    chosen = _sensors(sensors)
    rows = []
    for item in list_ratios(kind=kind, category=category):
        cells = []
        for sensor in chosen:
            if item.namespace == "aster":
                cells.append("ok" if sensor.key == "aster" else "ASTER only")
            else:
                missing = [v for v in item.variables if not sensor.has(v)]
                cells.append("ok" if not missing else "needs " + "+".join(missing))
        rows.append([item.name, item.kind, item.formula, *cells])
    return Table("Ratio support by sensor", ["Ratio", "Kind", "Formula", *[s.key for s in chosen]], rows)


def translate(ratio: Union[str, Item], sensor: SensorLike) -> Union[str, Tuple[str, ...]]:
    """Rewrite a formula in a sensor's native band ids.

    >>> translate("clay_sulphate_mica_marble", "l8")
    '(B6/B7)/(B5/B4)'
    >>> translate("clay_sulphate_mica_marble", "s2")
    '(B11/B12)/(B8/B4)'

    Raises :class:`BandNotAvailableError` if the sensor lacks a band the formula needs.
    """
    item = _item(ratio)
    mapping = native_map(item, get_sensor(sensor))

    def rewrite(expression: str) -> str:
        return re.sub(r"[A-Za-z_][A-Za-z0-9_]*", lambda m: mapping.get(m.group(0), m.group(0)), expression)

    rewritten = tuple(rewrite(e) for e in item.expressions)
    return rewritten if item.kind == "composite" else rewritten[0]
