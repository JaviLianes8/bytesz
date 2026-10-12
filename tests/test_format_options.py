from __future__ import annotations

import decimal

import pytest

from bytesz import (
    InvalidSizeError,
    SystemMismatchError,
    UnknownUnitError,
    convert,
    format,
    parse,
)


def test_carry_to_next_iec_unit() -> None:
    assert format(1048575) == "1 MiB"
    assert format(1024**3 - 1, precision=1) == "1 GiB"


def test_no_carry_below_the_base() -> None:
    # 999.95 KiB rounds to 1000 KiB, which is still below 1024 KiB (numfmt agrees).
    assert format(1023949, precision=1) == "1000 KiB"


def test_carry_to_next_si_unit() -> None:
    assert format(999_950, system="si", precision=1) == "1 MB"
    assert format(999_949, system="si", precision=1) == "999.9 kB"


def test_carry_stops_at_the_largest_unit() -> None:
    assert format(1024**11 - 1, precision=0) == "1024 QiB"


@pytest.mark.parametrize(
    ("rounding", "expected"),
    [
        ("half-up", "1.3 kB"),
        ("half-even", "1.2 kB"),
        ("half-down", "1.2 kB"),
        ("up", "1.3 kB"),
        ("down", "1.2 kB"),
        ("ceiling", "1.3 kB"),
        ("floor", "1.2 kB"),
    ],
)
def test_rounding_modes_on_a_tie(rounding: str, expected: str) -> None:
    result = format(1250, system="si", precision=1, rounding=rounding)  # type: ignore[arg-type]
    assert result == expected


def test_rounding_modes_on_negative_values() -> None:
    assert format(-1250, system="si", precision=1, signed=True, rounding="ceiling") == "-1.2 kB"
    assert format(-1250, system="si", precision=1, signed=True, rounding="floor") == "-1.3 kB"
    assert format(-1250, system="si", precision=1, signed=True, rounding="up") == "-1.3 kB"


def test_down_rounding_never_carries() -> None:
    assert format(1048575, rounding="down") == "1023.99 KiB"


def test_unknown_rounding_is_rejected() -> None:
    with pytest.raises(ValueError, match="rounding"):
        format(1, rounding="nearest")  # type: ignore[arg-type]


def test_forced_unit() -> None:
    assert format(1_000_000, unit="MiB") == "0.95 MiB"
    assert format(1536, unit="B") == "1536 B"
    assert format(1048575, unit="KiB") == "1024 KiB"
    assert format(5 * 10**9, system="si", unit="MB") == "5000 MB"


def test_forced_unit_picks_the_system_unless_one_is_pinned() -> None:
    assert format(5000, unit="kB") == "5 kB"
    assert format(1536, unit="KiB") == "1.5 KiB"
    with pytest.raises(SystemMismatchError, match="an SI unit but system is 'iec'"):
        format(1024, system="iec", unit="kB")
    with pytest.raises(SystemMismatchError, match="an IEC unit"):
        format(1024, system="si", unit="KiB")
    with pytest.raises(UnknownUnitError):
        format(1024, unit="KB")


def test_hostile_global_decimal_context_is_ignored() -> None:
    with decimal.localcontext() as ctx:
        ctx.traps[decimal.Inexact] = True
        ctx.Emax, ctx.Emin, ctx.prec = 10, -10, 3
        assert format(123456789012345) == "112.28 TiB"
        assert format(10**30, system="si") == "1 QB"
        assert format(1, unit="QiB", precision=31) == "0.0000000000000000000000000000008 QiB"
        assert parse("1.0000001 KiB", rounding="half-up") == 1024
        assert parse("1 QB") == 10**30
        assert convert(10**30, "B") == 10**30


def test_signed_values() -> None:
    assert format(-1536, signed=True) == "-1.5 KiB"
    assert format(-1, signed=True, unit="MiB") == "0 MiB"
    with pytest.raises(InvalidSizeError):
        format(-1536)


def test_trailing_zeros_and_separators() -> None:
    assert format(1536, precision=3, trailing_zeros=True) == "1.500 KiB"
    assert format(1024, precision=1, trailing_zeros=True) == "1.0 KiB"
    assert format(1536, separator="") == "1.5KiB"
    assert format(1536, decimal_point=",") == "1,5 KiB"


def test_bad_option_values_are_rejected() -> None:
    with pytest.raises(ValueError):
        format(1, decimal_point=";")
    with pytest.raises(ValueError):
        format(1, precision=True)
    with pytest.raises(ValueError):
        format(1, precision=1.5)  # type: ignore[arg-type]


def test_inputs_beyond_the_int_str_limit() -> None:
    # Python caps int to str conversion at 4300 digits by default; bytesz never needs it.
    assert format(10**5000, system="si", precision=0) == "1" + "0" * 4970 + " QB"


def test_huge_values_stay_exact() -> None:
    assert format(1024**10 * 3 + 1, precision=0) == "3 QiB"
    assert format(10**40, system="si") == "10000000000 QB"
    assert format(2**200 + 1, precision=0) == str(2**200 // 1024**10) + " QiB"


def test_high_precision_is_exact() -> None:
    assert format(1, unit="KiB", precision=10) == "0.0009765625 KiB"
    assert format(3, unit="QiB", precision=120).endswith("QiB")
