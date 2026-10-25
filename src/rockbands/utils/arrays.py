"""Array helpers that work with numpy, xarray, dask and plain numbers."""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

import numpy as np


def coerce_array(x: Any) -> Any:
    """Prepare one band for arithmetic.

    * Python numbers and sequences become numpy float arrays/scalars.
    * Integer and boolean arrays become float32. Raw digital numbers are often
      ``uint16``; subtracting them directly would wrap around (``5 - 10`` gives
      65531), which silently corrupts normalised differences.
    * Float arrays, xarray and dask objects pass through untouched, so
      coordinates, CRS metadata and lazy graphs survive.
    """
    if isinstance(x, (bool, int, float)):
        return np.float64(x)
    if isinstance(x, (list, tuple)):
        return np.asarray(x, dtype=float)
    dtype = getattr(x, "dtype", None)
    if dtype is not None and (np.issubdtype(dtype, np.integer) or np.issubdtype(dtype, np.bool_)):
        return x.astype(np.float32)
    return x


def mask_nonfinite(result: Any) -> Any:
    """Replace +/-inf (division by zero) with NaN, keeping the input's container type."""
    if isinstance(result, (int, float)):  # also np.float64
        value = float(result)
        return value if math.isfinite(value) else float("nan")
    finite = np.isfinite(result)
    if hasattr(result, "where"):  # xarray / pandas keep their coordinates
        return result.where(finite)
    return np.where(finite, result, np.nan)


def split_bands(stack: Any, band_ids: Sequence[str], axis: int = 0) -> dict[str, Any]:
    """Turn a ``(bands, rows, cols)`` array into ``{band_id: 2-D array}``.

    Handy for ``rasterio``'s ``dataset.read()``::

        bands = split_bands(src.read(), ["B2", "B3", "B4", "B8", "B11", "B12"])
    """
    stack = np.asarray(stack) if not hasattr(stack, "shape") else stack
    if stack.shape[axis] != len(band_ids):
        raise ValueError(
            f"stack has {stack.shape[axis]} layers along axis {axis} but {len(band_ids)} band ids were given"
        )
    return {band_id: np.take(stack, i, axis=axis) for i, band_id in enumerate(band_ids)}


def stack_channels(channels: Sequence[Any]) -> Any:
    """Stack channels into one object with a leading ``channel`` axis.

    xarray inputs stay xarray (new ``channel`` dimension); everything else becomes numpy.
    """
    first = channels[0]
    if hasattr(first, "dims") and hasattr(first, "coords"):
        import xarray as xr  # only imported when the caller is already using xarray

        return xr.concat(list(channels), dim="channel")
    return np.stack([np.asarray(c) for c in channels], axis=0)


def as_mapping(bands: Any) -> Mapping[str, Any]:
    """Accept dict, xarray.Dataset, pandas.DataFrame or any mapping-like object of bands."""
    if bands is None:
        return {}
    if hasattr(bands, "keys") and hasattr(bands, "__getitem__"):
        return {str(k): bands[k] for k in bands.keys()}
    raise TypeError(
        "bands must be a mapping of band id -> array (dict, xarray.Dataset, DataFrame, ...), "
        f"got {type(bands).__name__}"
    )
