"""Exceptions raised by rockbands."""

from __future__ import annotations


class MiningBandRatiosError(Exception):
    """Base class for every error raised by this package."""


class UnknownSensorError(MiningBandRatiosError, LookupError):
    """The sensor name is not registered."""


class UnknownRatioError(MiningBandRatiosError, LookupError):
    """The ratio or composite name is not in the catalogue."""


class BandNotAvailableError(MiningBandRatiosError):
    """The sensor has no band for a spectral region the ratio needs.

    Example: asking for a ratio that needs a red-edge band on Landsat.
    """


class MissingBandError(MiningBandRatiosError):
    """The sensor supports the ratio, but the caller did not supply an array for a band."""


class ExpressionError(MiningBandRatiosError, ValueError):
    """A formula string is malformed or uses something outside the allowed grammar."""
