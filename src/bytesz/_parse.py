"""Parse a human readable size into an exact integer number of bytes."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from ._errors import AmbiguousUnitError, InvalidSizeError
from ._units import IEC_BASE, IEC_UNITS, SI_BASE, SI_UNITS, UPPER_UNITS

System = str  # "iec" or "si"

_PATTERN = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*([A-Za-z]*)\s*$")


def _factor(suffix: str, system: System | None) -> Decimal:
    """Return the byte multiplier for a suffix, honouring an optional pinned system."""
    if suffix in ("", "B"):
        return Decimal(1)

    in_iec = suffix in IEC_UNITS
    in_si = suffix in SI_UNITS

    if system == "iec":
        if in_iec:
            return Decimal(IEC_BASE) ** IEC_UNITS[suffix]
        if in_si:
            raise InvalidSizeError(f"{suffix!r} is an SI unit but system is 'iec'")
    elif system == "si":
        if in_si:
            return Decimal(SI_BASE) ** SI_UNITS[suffix]
        if in_iec:
            raise InvalidSizeError(f"{suffix!r} is an IEC unit but system is 'si'")
    else:
        if in_iec:
            return Decimal(IEC_BASE) ** IEC_UNITS[suffix]
        if in_si:
            return Decimal(SI_BASE) ** SI_UNITS[suffix]

    if suffix.upper() in UPPER_UNITS:
        raise AmbiguousUnitError(f"{suffix!r} is ambiguous; use kB/MB for 1000 or KiB/MiB for 1024")
    raise InvalidSizeError(f"unknown size unit {suffix!r}")


def parse(text: str, *, system: System | None = None) -> int:
    """Convert a human size such as "1.5 MiB" into an exact number of bytes.

    The unit decides the system: IEC suffixes (KiB, MiB) use 1024 and SI suffixes
    (kB, MB) use 1000. A bare number, or "B", is a count of bytes. Pass ``system``
    to accept one system only. Ambiguous spellings like "KB" and inputs that do not
    land on a whole byte are rejected rather than rounded.
    """
    if system not in (None, "iec", "si"):
        raise ValueError(f"unknown system {system!r}; use 'iec', 'si' or None")

    match = _PATTERN.match(text)
    if match is None:
        raise InvalidSizeError(f"cannot parse size {text!r}")

    number, suffix = match.group(1), match.group(2)
    try:
        amount = Decimal(number)
    except InvalidOperation as error:  # pragma: no cover - guarded by the pattern
        raise InvalidSizeError(f"cannot parse number {number!r}") from error

    total = amount * _factor(suffix, system)
    if total != total.to_integral_value():
        raise InvalidSizeError(f"{text!r} is not a whole number of bytes")
    return int(total)
