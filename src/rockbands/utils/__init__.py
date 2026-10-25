"""Low-level utilities: array coercion, scaling to reflectance/radiance, display and plotting."""

from .arrays import as_mapping, coerce_array, mask_nonfinite, split_bands, stack_channels
from .display import to_rgb_image
from .plotting import plot_composites, plot_ratios
from .scaling import aster_dn_to_radiance, dn_to_reflectance

__all__ = [
    "as_mapping",
    "aster_dn_to_radiance",
    "coerce_array",
    "dn_to_reflectance",
    "mask_nonfinite",
    "plot_composites",
    "plot_ratios",
    "split_bands",
    "stack_channels",
    "to_rgb_image",
]
