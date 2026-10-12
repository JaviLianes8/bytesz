"""Exceptions raised by bytesz.

Every input error is a ``ValueError`` through :class:`ByteszError`, so callers
that only care about "bad input" can catch one class. Bad option values raise a
plain ``ValueError`` and a non-string input raises ``TypeError``. The narrower classes carry the
offending ``text`` and ``unit`` for messages and logs.
"""

from __future__ import annotations


class ByteszError(ValueError):
    """Base class for every error raised by bytesz.

    ``text`` is the input that failed, when there was one, and ``unit`` the unit
    involved, when there was one. Both default to ``None``.
    """

    def __init__(self, message: str, *, text: str | None = None, unit: str | None = None) -> None:
        super().__init__(message)
        self.text = text
        self.unit = unit


class InvalidSizeError(ByteszError):
    """The input is malformed, negative, or not a whole number of bytes."""


class AmbiguousUnitError(ByteszError):
    """The unit does not name one system unambiguously, for example 'KB'."""


class UnknownUnitError(InvalidSizeError):
    """The unit is not a size unit at all, for example 'furlongs'."""


class SystemMismatchError(InvalidSizeError):
    """The unit belongs to the other system than the one the caller pinned."""


class FractionalBytesError(InvalidSizeError):
    """The value does not land on a whole byte (or bit) and no rounding was asked for."""
