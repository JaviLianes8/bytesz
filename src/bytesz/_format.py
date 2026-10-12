"""Render an exact integer number of bytes (or bits) as a human readable size."""

from __future__ import annotations

from decimal import Decimal, localcontext

from ._errors import InvalidSizeError, UnknownUnitError
from ._types import Rounding, System, check_decimal_point, check_system, rounding_mode
from ._units import (
    IEC_BASE,
    IEC_BIT_SUFFIXES,
    IEC_SUFFIXES,
    SI_BASE,
    SI_BIT_SUFFIXES,
    SI_SUFFIXES,
)


def _table(system: str, bits: bool) -> tuple[int, tuple[str, ...]]:
    check_system(system)
    if system == "iec":
        return IEC_BASE, IEC_BIT_SUFFIXES if bits else IEC_SUFFIXES
    return SI_BASE, SI_BIT_SUFFIXES if bits else SI_SUFFIXES


def _exact(count: int, base: int, exponent: int) -> Decimal:
    """Return count / base**exponent exactly; every such quotient terminates."""
    digits = len(str(abs(count))) + 10 * exponent + 2
    with localcontext() as ctx:
        ctx.prec = digits
        return Decimal(count) / (Decimal(base) ** exponent)


def _check_count(count: object, signed: bool) -> int:
    if isinstance(count, bool) or not isinstance(count, int):
        raise InvalidSizeError("byte count must be an int")
    if count < 0 and not signed:
        raise InvalidSizeError("byte count must not be negative; pass signed=True to allow it")
    return count


def _text(value: Decimal, trailing_zeros: bool, decimal_point: str) -> str:
    """Render a decimal without exponent notation, optionally trimming zeros."""
    text = f"{value:f}"
    if not trailing_zeros and "." in text:
        text = text.rstrip("0").rstrip(".")
    if text.lstrip("-").strip("0.") == "":
        text = text.lstrip("-")  # never print "-0"
    return text.replace(".", decimal_point)


def _render(
    count: int,
    *,
    bits: bool,
    system: str,
    precision: int,
    rounding: str,
    unit: str | None,
    trailing_zeros: bool,
    decimal_point: str,
    separator: str,
) -> str:
    base, suffixes = _table(system, bits)
    if isinstance(precision, bool) or not isinstance(precision, int) or precision < 0:
        raise ValueError("precision must be a non-negative int")
    mode = rounding_mode(rounding)
    check_decimal_point(decimal_point)
    step = Decimal(1).scaleb(-precision)

    if unit is not None:
        if unit not in suffixes:
            raise UnknownUnitError(f"{unit!r} is not a {system} unit", unit=unit)
        exponent = suffixes.index(unit)
    else:
        exponent = 0
        magnitude = abs(count)
        while exponent < len(suffixes) - 1 and base ** (exponent + 1) <= magnitude:
            exponent += 1

    while True:
        scaled = _exact(count, base, exponent)
        with localcontext() as ctx:
            ctx.prec = len(str(abs(count))) + precision + 2
            rounded = scaled.quantize(step, rounding=mode)
        # Carry: 1023.999 KiB rounds to 1024.00 KiB, which is 1 MiB.
        if unit is None and abs(rounded) >= base and exponent < len(suffixes) - 1:
            exponent += 1
            continue
        break
    return f"{_text(rounded, trailing_zeros, decimal_point)}{separator}{suffixes[exponent]}"


def format(
    count: int,
    *,
    system: System = "iec",
    precision: int = 2,
    rounding: Rounding = "half-up",
    unit: str | None = None,
    signed: bool = False,
    trailing_zeros: bool = False,
    decimal_point: str = ".",
    separator: str = " ",
) -> str:
    """Convert a byte count into a human size such as "1.5 KiB".

    ``system`` is "iec" (1024 based: KiB, MiB ... QiB) or "si" (1000 based: kB,
    MB ... QB). The largest unit that keeps the number at or above one is chosen,
    the value is rounded to ``precision`` decimals with ``rounding``, and if the
    rounded value reaches the next unit it carries over (1048575 is "1 MiB", not
    "1024 KiB"). Trailing zeros are dropped unless ``trailing_zeros`` is true.

    ``unit`` forces one unit of the chosen system, such as "MiB", with no carry.
    ``signed`` allows negative counts. ``decimal_point`` is "." or ",".
    ``separator`` goes between number and unit (" " by default, "" for "1.5KiB").

    >>> format(1572864)
    '1.5 MiB'
    >>> format(1234567, system="si")
    '1.23 MB'
    >>> format(1048575)
    '1 MiB'
    >>> format(1536, unit="B")
    '1536 B'
    """
    return _render(
        _check_count(count, signed),
        bits=False,
        system=system,
        precision=precision,
        rounding=rounding,
        unit=unit,
        trailing_zeros=trailing_zeros,
        decimal_point=decimal_point,
        separator=separator,
    )
