"""Bit counts: the same two systems with the "bit" unit symbol."""

from __future__ import annotations

from ._format import _check_count, _render
from ._hints import BYTE_SYMBOLS, bit_hint
from ._parse import _parse_with
from ._types import Rounding, System
from ._units import IEC_BIT_UNITS, SI_BIT_UNITS, UPPER_BIT_UNITS


def format_bits(
    count: int,
    *,
    system: System | None = None,
    precision: int = 2,
    rounding: Rounding = "half-up",
    unit: str | None = None,
    signed: bool = False,
    trailing_zeros: bool = False,
    decimal_point: str = ".",
    separator: str = " ",
) -> str:
    """Convert a bit count into a human size such as "1.5 Mibit" or "1.5 Mbit".

    Takes the same options as :func:`bytesz.format`. Units are written with the
    unambiguous "bit" symbol (bit, Kibit, Mibit ... or bit, kbit, Mbit ...).

    >>> format_bits(1_500_000, system="si")
    '1.5 Mbit'
    >>> format_bits(1024)
    '1 Kibit'
    """
    return _render(
        _check_count(count, signed),
        bits=True,
        system=system,
        precision=precision,
        rounding=rounding,
        unit=unit,
        trailing_zeros=trailing_zeros,
        decimal_point=decimal_point,
        separator=separator,
    )


def parse_bits(
    text: str,
    *,
    system: System | None = None,
    rounding: Rounding | None = None,
    signed: bool = False,
    decimal_point: str = ".",
) -> int:
    """Convert a human bit size such as "100 Mbit" or "1.5 Mib" into a bit count.

    Accepts the "bit" symbol (kbit, Mibit) and the short "b" symbol (kb, Mb, Kib).
    A bare number, "b" or "bit" is a count of bits. Upper case "Kb" is rejected as
    ambiguous, just like "KB" in :func:`bytesz.parse`. The other options behave
    exactly as in :func:`bytesz.parse`.

    >>> parse_bits("100 Mbit")
    100000000
    >>> parse_bits("1 Kib")
    1024
    """
    return _parse_with(
        text,
        iec=IEC_BIT_UNITS,
        si=SI_BIT_UNITS,
        extra={},
        si_pinned={},
        upper=UPPER_BIT_UNITS,
        foreign=BYTE_SYMBOLS,
        hint=bit_hint,
        what="bits",
        system=system,
        rounding=rounding,
        signed=signed,
        decimal_point=decimal_point,
    )
