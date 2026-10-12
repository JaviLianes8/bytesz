"""Exact conversion of a byte or bit count into one named unit."""

from __future__ import annotations

from decimal import Decimal, localcontext

from ._errors import InvalidSizeError, UnknownUnitError
from ._format import _exact
from ._units import (
    IEC_BASE,
    IEC_BIT_SUFFIXES,
    IEC_SUFFIXES,
    SI_BASE,
    SI_BIT_SUFFIXES,
    SI_SUFFIXES,
)

_UNITS: dict[str, tuple[int, int]] = {
    **{unit: (IEC_BASE, exp) for exp, unit in enumerate(IEC_SUFFIXES)},
    **{unit: (SI_BASE, exp) for exp, unit in enumerate(SI_SUFFIXES)},
    **{unit: (IEC_BASE, exp) for exp, unit in enumerate(IEC_BIT_SUFFIXES)},
    **{unit: (SI_BASE, exp) for exp, unit in enumerate(SI_BIT_SUFFIXES)},
}


def convert(count: int, unit: str) -> Decimal:
    """Return ``count`` expressed in ``unit`` as an exact :class:`~decimal.Decimal`.

    ``unit`` is any IEC or SI byte unit ("KiB", "MB", "QiB") or bit unit ("Mibit",
    "kbit"); for a bit unit, ``count`` is a number of bits. Nothing is rounded:
    every power of 1000 or 1024 divides into a terminating decimal. Negative counts
    are allowed because the result is a plain number, not a size label.

    >>> convert(1536, "KiB")
    Decimal('1.5')
    >>> convert(1, "KiB")
    Decimal('0.0009765625')
    """
    if isinstance(count, bool) or not isinstance(count, int):
        raise InvalidSizeError("count must be an int")
    if unit not in _UNITS:
        raise UnknownUnitError(f"unknown size unit {unit!r}", unit=unit)
    base, exponent = _UNITS[unit]
    if count == 0:
        return Decimal(0)
    exact = _exact(count, base, exponent)
    with localcontext() as ctx:
        ctx.prec = len(exact.as_tuple().digits)  # normalize must not round
        return exact.normalize()
