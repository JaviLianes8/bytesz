"""Error hints and cross-family checks for parse and parse_bits."""

from __future__ import annotations

from typing import Final

from ._units import (
    IEC_BARE,
    IEC_BIT_SUFFIXES,
    IEC_SUFFIXES,
    LEGACY_UNITS,
    SI_BARE_PINNED,
    SI_BIT_SUFFIXES,
    SI_SUFFIXES,
)

# Units of the other family: a bit unit given to parse, a byte unit to parse_bits.
BIT_SYMBOLS: Final = {s: "a bit unit; use parse_bits for bits" for s in IEC_BIT_SUFFIXES[1:]}
BIT_SYMBOLS.update({s: "a bit unit; use parse_bits for bits" for s in SI_BIT_SUFFIXES})
BYTE_SYMBOLS: Final = {
    s: "a byte unit; use parse for bytes"
    for s in (*IEC_SUFFIXES, *SI_SUFFIXES, *IEC_BARE, *(u for u in LEGACY_UNITS if u.endswith("B")))
}


def byte_hint(suffix: str, system: str | None, legacy: bool) -> str:
    """Explain an ambiguous byte unit, suggesting only options that would work."""
    if suffix.endswith("b"):
        return "a lower case 'b' usually means bits (see parse_bits); for bytes use MB or MiB"
    can_legacy = suffix in LEGACY_UNITS and system != "si" and not legacy
    if not suffix.endswith("B"):
        options = []
        if suffix in SI_BARE_PINNED and system is None and not legacy:
            options.append("system='si' reads it as a power of 1000")
        if can_legacy:
            options.append("legacy=True reads it as a power of 1024")
        options.append("write a full unit such as kB or KiB")
        return "it is a bare prefix; " + (
            ", or ".join(options)
            if len(options) < 3
            else f"{options[0]}, {options[1]}, or {options[2]}"
        )
    text = "use kB/MB for 1000 or KiB/MiB for 1024"
    return text + (", or pass legacy=True for the JEDEC reading" if can_legacy else "")


def bit_hint(suffix: str, system: str | None, legacy: bool) -> str:
    """Explain an ambiguous bit unit."""
    return "use kbit/Mbit (or kb/Mb) for 1000, Kibit/Mibit (or Kib/Mib) for 1024"
