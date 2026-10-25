"""Helpers for looking at composites."""

from __future__ import annotations

from typing import Any

import numpy as np


def to_rgb_image(composite: Any, low: float = 2.0, high: float = 98.0) -> np.ndarray:
    """Percentile-stretch a ``(3, rows, cols)`` composite into a ``(rows, cols, 3)`` image in [0, 1].

    Ratio composites have no natural display range, so each channel is stretched
    between its ``low`` and ``high`` percentiles (NaNs ignored). The result can be
    passed straight to ``matplotlib.pyplot.imshow``.
    """
    data = np.asarray(composite, dtype=float)
    if data.ndim != 3 or data.shape[0] != 3:
        raise ValueError(f"expected a (3, rows, cols) composite, got shape {data.shape}")
    out = np.empty_like(data)
    for i in range(3):
        channel = data[i]
        if np.isfinite(channel).any():
            lo, hi = np.nanpercentile(channel, [low, high])
        else:
            lo = hi = 0.0
        out[i] = np.clip((channel - lo) / (hi - lo), 0, 1) if hi > lo else np.zeros_like(channel)
    return np.moveaxis(np.nan_to_num(out), 0, -1)
