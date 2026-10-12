"""Parse a human readable size into an exact integer number of bytes (or bits)."""

from __future__ import annotations

import re
from collections.abc import Mapping
from decimal import Decimal, localcontext

from ._errors import (
    AmbiguousUnitError,
    ByteszError,
    FractionalBytesError,
    InvalidSizeError,
    SystemMismatchError,
    UnknownUnitError,
)
from ._types import Rounding, System, check_decimal_point, rounding_mode
from ._units import (
    IEC_BARE,
    IEC_BASE,
    IEC_UNITS,
    LEGACY_UNITS,
    SI_BARE_PINNED,
    SI_BASE,
    SI_UNITS,
    UPPER_UNITS,
)

_PATTERNS = {
    point: re.compile(
        rf"^\s*([+-]?)([0-9]+(?:{re.escape(point)}[0-9]*)?|{re.escape(point)}[0-9]+)"
        r"\s*([A-Za-z]*)\s*$"
    )
    for point in (".", ",")
}


def _factor(
    suffix: str,
    *,
    iec: Mapping[str, int],
    si: Mapping[str, int],
    extra: Mapping[str, int],
    si_pinned: Mapping[str, int],
    upper: set[str] | frozenset[str],
    system: str | None,
    hint: str,
) -> int:
    """Return the multiplier for a suffix, honouring an optional pinned system."""
    if suffix == "" or iec.get(suffix) == 0 or si.get(suffix) == 0:
        return 1
    if suffix in extra:
        return int(IEC_BASE ** extra[suffix])
    if suffix in iec:
        if system == "si":
            raise SystemMismatchError(f"{suffix!r} is an IEC unit but system is 'si'", unit=suffix)
        return int(IEC_BASE ** iec[suffix])
    if system == "si" and suffix in si_pinned:
        return int(SI_BASE ** si_pinned[suffix])
    if suffix in si:
        if system == "iec":
            raise SystemMismatchError(f"{suffix!r} is an SI unit but system is 'iec'", unit=suffix)
        return int(SI_BASE ** si[suffix])
    if suffix.upper() in upper:
        raise AmbiguousUnitError(f"{suffix!r} is ambiguous; {hint}", unit=suffix)
    raise UnknownUnitError(f"unknown size unit {suffix!r}", unit=suffix)


def _parse_with(
    text: str,
    *,
    iec: Mapping[str, int],
    si: Mapping[str, int],
    extra: Mapping[str, int],
    si_pinned: Mapping[str, int],
    upper: set[str] | frozenset[str],
    what: str,
    system: str | None,
    rounding: str | None,
    signed: bool,
    decimal_point: str,
) -> int:
    if system not in (None, "iec", "si"):
        raise ValueError(f"unknown system {system!r}; use 'iec', 'si' or None")
    check_decimal_point(decimal_point)
    mode = None if rounding is None else rounding_mode(rounding)
    if not isinstance(text, str):
        raise TypeError(f"size must be a str, not {type(text).__name__}")

    match = _PATTERNS[decimal_point].match(text)
    if match is None:
        raise InvalidSizeError(f"cannot parse size {text!r}", text=text)
    sign, number, suffix = match.groups()
    if sign and not signed:
        raise InvalidSizeError(f"{text!r} has a sign; pass signed=True to allow it", text=text)

    unit = "b" if what == "bits" else "B"
    hint = (
        f"use k{unit}/M{unit} for 1000 or Ki{unit}/Mi{unit} for 1024"
        if what == "bits"
        else "use kB/MB for 1000, KiB/MiB for 1024, or pass legacy=True"
    )
    if what == "bytes" and not suffix.endswith(("B", "b")):
        hint = "a bare prefix needs system='si' (1000) or legacy=True (1024); or write kB or KiB"
    if what == "bytes" and suffix.endswith("b"):
        hint = "a lower case 'b' usually means bits (see parse_bits); for bytes use MB or MiB"

    try:
        factor = _factor(
            suffix,
            iec=iec,
            si=si,
            extra=extra,
            si_pinned=si_pinned,
            upper=upper,
            system=system,
            hint=hint,
        )
    except ByteszError as error:
        error.text = text
        raise

    digits = number.replace(decimal_point, ".")
    with localcontext() as ctx:
        ctx.prec = len(digits) + len(str(factor)) + 2
        total = Decimal(digits) * factor
        if sign == "-":
            total = -total
        if total != total.to_integral_value():
            if mode is None:
                raise FractionalBytesError(
                    f"{text!r} is not a whole number of {what}", text=text, unit=suffix
                )
            total = total.quantize(Decimal(1), rounding=mode)
    return int(total)


def parse(
    text: str,
    *,
    system: System | None = None,
    rounding: Rounding | None = None,
    signed: bool = False,
    decimal_point: str = ".",
    legacy: bool = False,
) -> int:
    """Convert a human size such as "1.5 MiB" into an exact number of bytes.

    The unit decides the system: IEC suffixes (KiB, MiB ... QiB, or the bare
    Ki, Mi written by ``numfmt --to=iec-i``) use 1024 and SI suffixes (kB, MB ...
    QB) use 1000. A bare number, or "B", is a count of bytes. Units are case
    sensitive: "KB", "Mb" and "kib" raise :class:`AmbiguousUnitError`.

    ``system`` accepts one system only; the other raises
    :class:`SystemMismatchError`. Pinning "si" also accepts bare prefixes such as
    "1.5M" or "2K", as ``numfmt --from=si`` does.

    ``rounding`` rounds a value that is not a whole byte instead of raising
    :class:`FractionalBytesError`. ``signed`` allows a leading "+" or "-".
    ``decimal_point`` is "." or ",". ``legacy`` reads the JEDEC style upper case
    units (KB, MB, GB ... and bare K, M, G) as powers of 1024; "kB" stays 1000.

    >>> parse("1.5 MiB")
    1572864
    >>> parse("1.5 MB")
    1500000
    >>> parse("1 MB", legacy=True)
    1048576
    """
    if legacy and system == "si":
        raise ValueError("legacy=True reads units as powers of 1024; it cannot pin system='si'")
    return _parse_with(
        text,
        iec={**IEC_UNITS, **IEC_BARE},
        si=SI_UNITS,
        extra=LEGACY_UNITS if legacy else {},
        si_pinned=SI_BARE_PINNED,
        upper=UPPER_UNITS,
        what="bytes",
        system=system,
        rounding=rounding,
        signed=signed,
        decimal_point=decimal_point,
    )
