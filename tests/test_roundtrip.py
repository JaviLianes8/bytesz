import pytest

from bytesz import format, parse

IEC_CASES = [0, 1, 512, 1024, 1536, 1024**2, 3 * 1024**3, 1024**4]
SI_CASES = [0, 1, 500, 1000, 1500, 1_000_000, 3 * 1000**3, 1000**4]


@pytest.mark.parametrize("count", IEC_CASES)
def test_iec_round_trip(count: int) -> None:
    assert parse(format(count, system="iec"), system="iec") == count


@pytest.mark.parametrize("count", SI_CASES)
def test_si_round_trip(count: int) -> None:
    assert parse(format(count, system="si"), system="si") == count


def test_systems_disagree_on_the_same_text() -> None:
    assert parse("1 kB") != parse("1 KiB")
