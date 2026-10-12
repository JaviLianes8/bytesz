from __future__ import annotations

from decimal import Decimal

import pytest

from bytesz import (
    AmbiguousUnitError,
    FractionalBytesError,
    InvalidSizeError,
    SystemMismatchError,
    UnknownUnitError,
    convert,
    format_bits,
    parse_bits,
)


def test_parse_bits_long_and_short_symbols() -> None:
    assert parse_bits("100 Mbit") == 100_000_000
    assert parse_bits("100 Mb") == 100_000_000
    assert parse_bits("1 Kibit") == 1024
    assert parse_bits("1 Kib") == 1024
    assert parse_bits("8 b") == 8
    assert parse_bits("8 bit") == 8
    assert parse_bits("8") == 8
    assert parse_bits("1 kb") == 1000
    assert parse_bits("1 Qbit") == 10**30


def test_parse_bits_ambiguity_and_errors() -> None:
    for text in ("1 Kb", "1 MB", "1 B"):
        with pytest.raises(AmbiguousUnitError):
            parse_bits(text)
    with pytest.raises(UnknownUnitError):
        parse_bits("1 bytes")
    with pytest.raises(SystemMismatchError):
        parse_bits("1 Mibit", system="si")
    with pytest.raises(FractionalBytesError, match="bits"):
        parse_bits("1.5 bit")
    assert parse_bits("1.5 bit", rounding="half-even") == 2
    assert parse_bits("-1 kbit", signed=True) == -1000


def test_format_bits() -> None:
    assert format_bits(1024) == "1 Kibit"
    assert format_bits(1_500_000, system="si") == "1.5 Mbit"
    assert format_bits(7) == "7 bit"
    assert format_bits(1048575) == "1 Mibit"
    assert format_bits(1000, system="si", unit="Mbit", precision=3) == "0.001 Mbit"
    with pytest.raises(UnknownUnitError):
        format_bits(1, unit="MiB")
    with pytest.raises(InvalidSizeError):
        format_bits(-1)


def test_bits_round_trip() -> None:
    for count in (0, 1, 8, 1000, 1024, 10**12, 1024**10):
        for system in ("iec", "si"):
            text = format_bits(count, system=system, precision=40)  # type: ignore[arg-type]
            assert parse_bits(text, system=system) == count  # type: ignore[arg-type]


def test_convert_is_exact() -> None:
    assert convert(1536, "KiB") == Decimal("1.5")
    assert convert(1, "KiB") == Decimal("0.0009765625")
    assert convert(1, "QiB") * 1024**10 == 1
    assert convert(1_500_000, "MB") == Decimal("1.5")
    assert convert(8, "bit") == 8
    assert convert(1_000_000, "Mbit") == 1
    assert convert(0, "GiB") == 0
    assert convert(-2048, "KiB") == -2
    big = 10**40 + 1
    assert convert(big, "B") == big
    assert convert(big, "kB") == Decimal("1" + "0" * 37 + ".001")


def test_convert_rejects_bad_input() -> None:
    with pytest.raises(UnknownUnitError):
        convert(1, "KB")
    with pytest.raises(InvalidSizeError):
        convert(1.5, "KiB")  # type: ignore[arg-type]
    with pytest.raises(InvalidSizeError):
        convert(True, "KiB")
