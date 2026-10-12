"""Unit tables for the IEC (1024) and SI (1000) size systems.

Each table is exact and case sensitive. The byte suffix "B" is shared by both
systems and always sits at exponent zero. The IEC suffixes carry the "i" marker
(KiB, MiB); the SI suffixes do not (kB, MB). Any other spelling is either an
unknown unit or an ambiguous one, never a silent guess.

The tables reach the prefixes adopted in 2022 by the CGPM (ronna R = 1000**9,
quetta Q = 1000**10) and their binary partners from IEC 80000-13:2025 (robi
Ri = 1024**9, quebi Qi = 1024**10). Sources: https://www.bipm.org/en/measurement-units/si-prefixes
and https://physics.nist.gov/cuu/Units/binary.html.
"""

from __future__ import annotations

from typing import Final

IEC_BASE: Final = 1024
SI_BASE: Final = 1000

IEC_PREFIXES: Final = ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi", "Yi", "Ri", "Qi")
SI_PREFIXES: Final = ("", "k", "M", "G", "T", "P", "E", "Z", "Y", "R", "Q")

IEC_SUFFIXES: Final = tuple(prefix + "B" for prefix in IEC_PREFIXES)
SI_SUFFIXES: Final = tuple(prefix + "B" for prefix in SI_PREFIXES)
IEC_BIT_SUFFIXES: Final = tuple(prefix + "bit" for prefix in IEC_PREFIXES)
SI_BIT_SUFFIXES: Final = tuple(prefix + "bit" for prefix in SI_PREFIXES)

IEC_UNITS: Final[dict[str, int]] = {suffix: exp for exp, suffix in enumerate(IEC_SUFFIXES)}
SI_UNITS: Final[dict[str, int]] = {suffix: exp for exp, suffix in enumerate(SI_SUFFIXES)}

# Bare IEC prefixes ("1.5Mi", as written by `numfmt --to=iec-i`) only ever mean
# a binary multiple, so they are accepted wherever IEC units are.
IEC_BARE: Final[dict[str, int]] = {p: exp for exp, p in enumerate(IEC_PREFIXES) if p}

# Bare SI prefixes ("1.5M", as written by `numfmt --to=si`). "M" alone is read
# as 1024**2 by `numfmt --from=iec`, so these are accepted only when the caller
# pins system="si". Upper case "K" is accepted there too, as numfmt does.
SI_BARE: Final[dict[str, int]] = {p: exp for exp, p in enumerate(SI_PREFIXES) if p}
SI_BARE_PINNED: Final[dict[str, int]] = {**SI_BARE, "K": 1}

# Legacy binary spellings: upper case prefix plus "B", or the bare upper case
# prefix, read as powers of 1024. JEDEC defines only K, M and G this way "to
# reflect common usage"; operating systems extend the habit upwards. Used only
# when the caller opts in with legacy=True.
_LEGACY_PREFIXES: Final = ("K", "M", "G", "T", "P", "E", "Z", "Y", "R", "Q")
LEGACY_UNITS: Final[dict[str, int]] = {
    **{p + "B": exp for exp, p in enumerate(_LEGACY_PREFIXES, start=1)},
    **{p: exp for exp, p in enumerate(_LEGACY_PREFIXES, start=1)},
}

# Upper cased spellings, used only to tell an ambiguous casing (KB, Kib) apart
# from an entirely unknown unit.
UPPER_UNITS: Final = (
    {s.upper() for s in IEC_SUFFIXES}
    | {s.upper() for s in SI_SUFFIXES}
    | {s.upper() for s in LEGACY_UNITS}
    | {s.upper() for s in IEC_BARE}
)

# Bit units for parse_bits: the long "bit" symbol and the short "b" symbol.
# "Kb" and bare upper case prefixes stay ambiguous, exactly as "KB" does.
IEC_BIT_UNITS: Final[dict[str, int]] = {
    **{s: exp for exp, s in enumerate(IEC_BIT_SUFFIXES)},
    **{p + "b": exp for exp, p in enumerate(IEC_PREFIXES)},
}
SI_BIT_UNITS: Final[dict[str, int]] = {
    **{s: exp for exp, s in enumerate(SI_BIT_SUFFIXES)},
    **{p + "b": exp for exp, p in enumerate(SI_PREFIXES)},
}
UPPER_BIT_UNITS: Final = {s.upper() for s in IEC_BIT_UNITS} | {s.upper() for s in SI_BIT_UNITS}
