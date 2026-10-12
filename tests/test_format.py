import pytest

from bytesz import InvalidSizeError, format


def test_zero_is_bytes() -> None:
    assert format(0) == "0 B"


def test_small_counts_stay_in_bytes() -> None:
    assert format(512, system="iec") == "512 B"
    assert format(999, system="si") == "999 B"


def test_iec_scales_by_1024() -> None:
    assert format(1024, system="iec") == "1 KiB"
    assert format(1536, system="iec") == "1.5 KiB"
    assert format(1024**2, system="iec") == "1 MiB"


def test_si_scales_by_1000() -> None:
    assert format(1000, system="si") == "1 kB"
    assert format(1500, system="si") == "1.5 kB"
    assert format(1_000_000, system="si") == "1 MB"


def test_default_system_is_iec() -> None:
    assert format(1024) == "1 KiB"


def test_precision_controls_decimals() -> None:
    assert format(1234567, system="si", precision=2) == "1.23 MB"
    assert format(1234567, system="si", precision=0) == "1 MB"
    assert format(1536, system="iec", precision=3) == "1.5 KiB"


def test_rounding_is_half_up() -> None:
    assert format(1126, system="si", precision=1) == "1.1 kB"
    assert format(1150, system="si", precision=1) == "1.2 kB"


def test_largest_unit_is_capped() -> None:
    assert format(1024**9, system="iec") == "1 RiB"
    assert format(1024**11, system="iec") == "1024 QiB"
    assert format(1000**11, system="si") == "1000 QB"


def test_negative_is_rejected() -> None:
    with pytest.raises(InvalidSizeError):
        format(-1)


def test_non_int_is_rejected() -> None:
    with pytest.raises(InvalidSizeError):
        format(1.5)  # type: ignore[arg-type]
    with pytest.raises(InvalidSizeError):
        format(True)


def test_unknown_system_is_rejected() -> None:
    with pytest.raises(ValueError):
        format(1024, system="metric")  # type: ignore[arg-type]


def test_negative_precision_is_rejected() -> None:
    with pytest.raises(ValueError):
        format(1024, precision=-1)
