from __future__ import annotations

import pytest

from bytesz import (
    AmbiguousUnitError,
    ByteszError,
    FractionalBytesError,
    InvalidSizeError,
    SystemMismatchError,
    UnknownUnitError,
    parse,
)


def test_rounding_turns_fractional_bytes_into_whole_ones() -> None:
    assert parse("1.5 B", rounding="half-up") == 2
    assert parse("1.5 B", rounding="half-even") == 2
    assert parse("2.5 B", rounding="half-even") == 2
    assert parse("1.0005 kB", rounding="down") == 1000
    assert parse("1.0005 kB", rounding="up") == 1001
    assert parse("0.1 KiB", rounding="half-up") == 102


def test_without_rounding_fractions_raise_a_typed_error() -> None:
    with pytest.raises(FractionalBytesError) as caught:
        parse("1.5 B")
    assert caught.value.text == "1.5 B"
    assert caught.value.unit == "B"
    assert isinstance(caught.value, InvalidSizeError)


def test_signed_values() -> None:
    assert parse("-1.5 KiB", signed=True) == -1536
    assert parse("+2 kB", signed=True) == 2000
    assert parse("-0", signed=True) == 0
    assert parse("-1.5 B", signed=True, rounding="floor") == -2
    with pytest.raises(InvalidSizeError):
        parse("+2 kB")


def test_comma_decimal_point() -> None:
    assert parse("1,5 MiB", decimal_point=",") == 1572864
    assert parse("1,5MB", decimal_point=",") == 1_500_000
    with pytest.raises(InvalidSizeError):
        parse("1.5 MiB", decimal_point=",")
    with pytest.raises(ValueError):
        parse("1 B", decimal_point="_")


def test_number_shapes() -> None:
    assert parse("0.5 KiB") == 512
    assert parse("0007 B") == 7
    for text in (
        ".5 KiB",
        "2. KiB",
        "1.",
        "1e3 B",
        "1 000 B",
        "1_000 B",
        chr(0x661) + " B",
        ".",
        "1..5 B",
    ):
        with pytest.raises(InvalidSizeError):
            parse(text)


def test_non_string_input_is_a_type_error() -> None:
    with pytest.raises(TypeError):
        parse(1024)  # type: ignore[arg-type]


def test_bare_iec_prefixes_from_numfmt() -> None:
    assert parse("1.5Mi") == 1572864
    assert parse("2Ki", system="iec") == 2048
    with pytest.raises(SystemMismatchError):
        parse("2Ki", system="si")


def test_bare_si_prefixes_need_a_pinned_system() -> None:
    assert parse("1.5M", system="si") == 1_500_000
    assert parse("2k", system="si") == 2000
    assert parse("2K", system="si") == 2000
    with pytest.raises(AmbiguousUnitError):
        parse("1.5M")
    with pytest.raises(AmbiguousUnitError, match="bare prefix"):
        parse("2k")


def test_hints_suggest_only_options_that_work() -> None:
    with pytest.raises(AmbiguousUnitError) as caught:
        parse("1 k", legacy=True)
    assert "legacy" not in str(caught.value)
    with pytest.raises(AmbiguousUnitError) as caught:
        parse("2M", system="iec")
    assert "system='si'" not in str(caught.value)
    assert "legacy=True" in str(caught.value)
    with pytest.raises(AmbiguousUnitError) as caught:
        parse("1.5 m")
    assert "system=" not in str(caught.value)
    assert "legacy" not in str(caught.value)


def test_bit_units_point_at_parse_bits() -> None:
    with pytest.raises(UnknownUnitError, match="parse_bits"):
        parse("1 Kibit")


def test_legacy_reads_upper_case_units_as_binary() -> None:
    assert parse("1 KB", legacy=True) == 1024
    assert parse("1 MB", legacy=True) == 1024**2
    assert parse("1.5 GB", legacy=True) == 3 * 1024**3 // 2
    assert parse("1 QB", legacy=True) == 1024**10
    assert parse("4K", legacy=True) == 4096
    assert parse("4M", legacy=True, system="iec") == 4 * 1024**2
    assert parse("1 kB", legacy=True) == 1000
    assert parse("1 MiB", legacy=True) == 1024**2


def test_legacy_cannot_pin_si() -> None:
    with pytest.raises(ValueError, match="legacy"):
        parse("1 KB", legacy=True, system="si")


def test_lower_case_b_hint_points_at_bits() -> None:
    with pytest.raises(AmbiguousUnitError, match="parse_bits"):
        parse("100 Mb")


def test_error_attributes() -> None:
    with pytest.raises(AmbiguousUnitError) as ambiguous:
        parse("1 KB")
    assert (ambiguous.value.text, ambiguous.value.unit) == ("1 KB", "KB")
    with pytest.raises(UnknownUnitError) as unknown:
        parse("3 furlongs")
    assert unknown.value.unit == "furlongs"
    with pytest.raises(SystemMismatchError) as mismatch:
        parse("1 kB", system="iec")
    assert mismatch.value.unit == "kB"
    with pytest.raises(InvalidSizeError) as garbage:
        parse("abc")
    assert garbage.value.text == "abc"
    assert garbage.value.unit is None


def test_every_error_is_a_bytesz_error_and_a_value_error() -> None:
    for text in ("1 KB", "3 furlongs", "1.5 B", "abc"):
        with pytest.raises(ByteszError):
            parse(text)
        with pytest.raises(ValueError):
            parse(text)


def test_huge_inputs_stay_exact() -> None:
    digits = "123456789012345678901234567890"
    assert parse(f"{digits} QiB") == int(digits) * 1024**10
    assert parse(f"{digits}.5 QB") == int(digits) * 10**30 + 5 * 10**29
    assert parse("0.000000000000000000000000000001 QB") == 1
