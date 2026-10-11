"""Unit tables for the IEC (1024) and SI (1000) size systems.

Each table is exact and case sensitive. The byte suffix "B" is shared by both
systems and always sits at exponent zero. The IEC suffixes carry the "i" marker
(KiB, MiB); the SI suffixes do not (kB, MB). Any other spelling is either an
unknown unit or an ambiguous one, never a silent guess.
"""

from __future__ import annotations

from typing import Final

IEC_BASE: Final = 1024
SI_BASE: Final = 1000

IEC_SUFFIXES: Final = ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB")
SI_SUFFIXES: Final = ("B", "kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")

IEC_UNITS: Final[dict[str, int]] = {suffix: exp for exp, suffix in enumerate(IEC_SUFFIXES)}
SI_UNITS: Final[dict[str, int]] = {suffix: exp for exp, suffix in enumerate(SI_SUFFIXES)}

# Upper cased spellings, used only to tell an ambiguous casing (KB, Kib) apart
# from an entirely unknown unit.
UPPER_UNITS: Final = {s.upper() for s in IEC_SUFFIXES} | {s.upper() for s in SI_SUFFIXES}
