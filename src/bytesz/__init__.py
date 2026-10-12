"""Strict two-way conversion between byte counts and human sizes with explicit IEC and SI units.

``parse`` turns "1.5 MiB" into 1572864 and ``format`` turns 1572864 back into
"1.5 MiB". The unit alone decides the system: IEC units (KiB, MiB) are powers of
1024 and SI units (kB, MB) are powers of 1000. Ambiguous spellings such as "KB"
are rejected unless the caller opts into the legacy reading.
"""

from __future__ import annotations

from ._bits import format_bits, parse_bits
from ._convert import convert
from ._errors import (
    AmbiguousUnitError,
    ByteszError,
    FractionalBytesError,
    InvalidSizeError,
    SystemMismatchError,
    UnknownUnitError,
)
from ._format import format
from ._parse import parse
from ._types import Rounding, System
from ._units import IEC_SUFFIXES, SI_SUFFIXES

__version__ = "0.2.0"

__all__ = [
    "IEC_SUFFIXES",
    "SI_SUFFIXES",
    "AmbiguousUnitError",
    "ByteszError",
    "FractionalBytesError",
    "InvalidSizeError",
    "Rounding",
    "System",
    "SystemMismatchError",
    "UnknownUnitError",
    "convert",
    "format",
    "format_bits",
    "parse",
    "parse_bits",
]
