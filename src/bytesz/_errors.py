"""Exceptions raised by bytesz."""

from __future__ import annotations


class ByteszError(ValueError):
    """Base class for every error raised by bytesz."""


class InvalidSizeError(ByteszError):
    """The input is malformed, negative, or not a whole number of bytes."""


class AmbiguousUnitError(ByteszError):
    """The unit does not name one system unambiguously, for example 'KB'."""
