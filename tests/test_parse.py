import pytest

from bytesz import AmbiguousUnitError, InvalidSizeError, parse


def test_bare_number_is_bytes() -> None:
    assert parse("1024") == 1024


def test_plain_byte_suffix() -> None:
    assert parse("512 B") == 512


def test_iec_suffix_uses_1024() -> None:
    assert parse("1 KiB") == 1024
    assert parse("1 MiB") == 1024 * 1024


def test_si_suffix_uses_1000() -> None:
    assert parse("1 kB") == 1000
    assert parse("1 MB") == 1_000_000


def test_fractional_iec_resolving_to_whole_bytes() -> None:
    assert parse("1.5 MiB") == 1572864


def test_whitespace_is_optional() -> None:
    assert parse("2GiB") == 2 * 1024**3
    assert parse("  3 kB  ") == 3000


def test_pinned_system_accepts_its_own_units() -> None:
    assert parse("1 KiB", system="iec") == 1024
    assert parse("1 kB", system="si") == 1000


def test_pinned_system_rejects_the_other_system() -> None:
    with pytest.raises(InvalidSizeError):
        parse("1 kB", system="iec")
    with pytest.raises(InvalidSizeError):
        parse("1 KiB", system="si")


def test_byte_suffix_works_under_any_pinned_system() -> None:
    assert parse("7 B", system="iec") == 7
    assert parse("7", system="si") == 7


def test_ambiguous_unit_is_rejected() -> None:
    with pytest.raises(AmbiguousUnitError):
        parse("1 KB")


def test_wrong_casing_is_ambiguous_not_silently_accepted() -> None:
    with pytest.raises(AmbiguousUnitError):
        parse("1 kib")
    with pytest.raises(AmbiguousUnitError):
        parse("1 Mb")


def test_non_integer_byte_count_is_rejected() -> None:
    with pytest.raises(InvalidSizeError):
        parse("1.5 B")
    with pytest.raises(InvalidSizeError):
        parse("1.0005 kB")


def test_unknown_unit_is_rejected() -> None:
    with pytest.raises(InvalidSizeError):
        parse("3 furlongs")


def test_garbage_is_rejected() -> None:
    for text in ("", "abc", "1,5 MiB", "-1 kB", "MiB"):
        with pytest.raises(InvalidSizeError):
            parse(text)


def test_unknown_system_argument_is_rejected() -> None:
    with pytest.raises(ValueError):
        parse("1 kB", system="metric")  # type: ignore[arg-type]
