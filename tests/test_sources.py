"""Golden values copied from sources fetched on 2026-10-12.

NIST, Prefixes for binary multiples, https://physics.nist.gov/cuu/Units/binary.html
(table "Examples and comparisons with SI prefixes"):
    1 MiB = 2^20 B = 1 048 576 B
    1 MB = 10^6 B = 1 000 000 B
    1 GiB = 2^30 B = 1 073 741 824 B
    1 GB = 10^9 B = 1 000 000 000 B
    1 Kibit = 2^10 bit = 1024 bit
    1 kbit = 10^3 bit = 1000 bit

BIPM, SI prefixes, https://www.bipm.org/en/measurement-units/si-prefixes:
    quetta Q 10^30, ronna R 10^27

IEC 80000-13:2025 binary prefixes robi Ri = 1024^9 and quebi Qi = 1024^10, as
reported by https://en.wikipedia.org/w/index.php?title=Binary_prefix&action=raw
"""

from __future__ import annotations

import pytest

from bytesz import AmbiguousUnitError, format, format_bits, parse, parse_bits

NIST_BYTES = [
    ("1 MiB", 1_048_576),
    ("1 MB", 1_000_000),
    ("1 GiB", 1_073_741_824),
    ("1 GB", 1_000_000_000),
]
NIST_BITS = [("1 Kibit", 1024), ("1 kbit", 1000)]


@pytest.mark.parametrize(("text", "count"), NIST_BYTES)
def test_nist_byte_examples(text: str, count: int) -> None:
    assert parse(text) == count
    system = "iec" if "i" in text else "si"
    assert format(count, system=system) == text  # type: ignore[arg-type]


@pytest.mark.parametrize(("text", "count"), NIST_BITS)
def test_nist_bit_examples(text: str, count: int) -> None:
    assert parse_bits(text) == count
    system = "iec" if "Ki" in text else "si"
    assert format_bits(count, system=system) == text  # type: ignore[arg-type]


def test_nist_symbol_is_ki_not_lower_case_ki() -> None:
    # NIST: "the symbol Ki is used for 2^10 rather than ki".
    assert parse("1 KiB") == 1024
    with pytest.raises(AmbiguousUnitError):
        parse("1 kiB")


def test_2022_si_prefixes() -> None:
    assert parse("1 RB") == 10**27
    assert parse("1 QB") == 10**30
    assert format(10**27, system="si") == "1 RB"
    assert format(10**30, system="si") == "1 QB"


def test_2025_iec_prefixes() -> None:
    assert parse("1 RiB") == 1024**9
    assert parse("1 QiB") == 1024**10
    assert format(1024**9) == "1 RiB"
    assert format(1024**10) == "1 QiB"
