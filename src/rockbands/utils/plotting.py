"""Quick-look plots for ratio and composite results (needs matplotlib)."""

from __future__ import annotations

import math
from typing import Any, Mapping, Tuple

import numpy as np

from .display import to_rgb_image


def _title(name: str) -> str:
    from ..ratios.api import CATALOGUE

    return CATALOGUE[name].title if name in CATALOGUE else name


def _grid(n: int, ncols: int, panel: Tuple[float, float]):
    import matplotlib.pyplot as plt

    ncols = max(1, min(ncols, n))
    nrows = math.ceil(n / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(panel[0] * ncols, panel[1] * nrows), squeeze=False)
    for ax in axes.flat[n:]:
        ax.set_visible(False)
    return fig, axes.flat


def plot_ratios(
    results: Mapping[str, Any],
    ncols: int = 4,
    cmap: str = "viridis",
    percentiles: Tuple[float, float] = (2, 98),
    panel_size: Tuple[float, float] = (3.6, 3.2),
):
    """Grid of single-band ratio maps, each stretched between its own percentiles.

    ``results`` is a ``{name: 2-D array}`` mapping such as the output of ``compute_all``.
    Returns the matplotlib figure.
    """
    fig, axes = _grid(len(results), ncols, panel_size)
    for ax, (name, array) in zip(axes, results.items()):
        data = np.asarray(array, dtype=float)
        lo, hi = np.nanpercentile(data, percentiles) if np.isfinite(data).any() else (0.0, 1.0)
        image = ax.imshow(data, cmap=cmap, vmin=lo, vmax=hi)
        ax.set_title(_title(name), fontsize=9)
        ax.axis("off")
        fig.colorbar(image, ax=ax, shrink=0.7)
    fig.tight_layout()
    return fig


def plot_composites(
    results: Mapping[str, Any],
    ncols: int = 4,
    percentiles: Tuple[float, float] = (2, 98),
    panel_size: Tuple[float, float] = (3.4, 3.2),
):
    """Grid of RGB composites (each ``(3, rows, cols)``), percentile-stretched per channel."""
    fig, axes = _grid(len(results), ncols, panel_size)
    for ax, (name, array) in zip(axes, results.items()):
        ax.imshow(to_rgb_image(array, *percentiles))
        ax.set_title(_title(name), fontsize=9)
        ax.axis("off")
    fig.tight_layout()
    return fig
