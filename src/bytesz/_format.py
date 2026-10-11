"""Render an exact integer number of bytes as a human readable size."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from ._errors import InvalidSizeError
from ._units import IEC_BASE, IEC_SUFFIXES, SI_BASE, SI_SUFFIXES

System = str  # "iec" or "si"


def _trim(value: Decimal) -> str:
    """Render a decimal without exponent notation or trailing zeros."""
    text = f"{value:f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def format(count: int, *, system: System = "iec", precision: int = 2) -> str:
    """Convert a byte count into a human size such as "1.5 KiB".

    ``system`` is "iec" (1024 based: KiB, MiB) or "si" (1000 based: kB, MB).
    The largest unit that keeps the number at or above one is chosen, then the
    value is rounded to ``precision`` decimals and any trailing zeros are dropped.
    """
    if isinstance(count, bool) or not isinstance(count, int):
        raise InvalidSizeError("byte count must be an int")
    if count < 0:
        raise InvalidSizeError("byte count must not be negative")
    if precision < 0:
        raise ValueError("precision must not be negative")

    if system == "iec":
        base, suffixes = IEC_BASE, IEC_SUFFIXES
    elif system == "si":
        base, suffixes = SI_BASE, SI_SUFFIXES
    else:
        raise ValueError(f"unknown system {system!r}; use 'iec' or 'si'")

    exponent = 0
    while exponent < len(suffixes) - 1 and base ** (exponent + 1) <= count:
        exponent += 1

    scaled = Decimal(count) / (Decimal(base) ** exponent)
    step = Decimal(1).scaleb(-precision)
    rounded = scaled.quantize(step, rounding=ROUND_HALF_UP)
    return f"{_trim(rounded)} {suffixes[exponent]}"
