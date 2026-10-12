"""Contract over the complete promise of bytesz, checked on seeded random data.

1. Exact both ways: with enough precision (10 decimals per IEC step),
   parse(format(n)) == n for every n.
2. The number shown is below the base unless the largest unit is reached.
3. Rounding error is bounded by half a step (nearest modes) or one step (directed).
4. Directed modes round the way they say: down never grows the magnitude.
5. format is monotonic in its input for any fixed options.
6. The unit alone decides the system: the same digits under KiB and kB differ.
7. Strictness: ambiguous and fractional inputs raise, never guess.
"""

from __future__ import annotations

import random
from decimal import Decimal

import pytest

from bytesz import (
    IEC_SUFFIXES,
    SI_SUFFIXES,
    AmbiguousUnitError,
    FractionalBytesError,
    convert,
    format,
    parse,
)

RNG = random.Random(80000_13)
COUNTS = [RNG.randrange(10 ** RNG.randrange(1, 36)) for _ in range(300)]
SYSTEMS = {"iec": (1024, IEC_SUFFIXES), "si": (1000, SI_SUFFIXES)}


def _split(text: str) -> tuple[Decimal, str]:
    number, unit = text.split(" ")
    return Decimal(number), unit


@pytest.mark.parametrize("system", sorted(SYSTEMS))
def test_exact_round_trip(system: str) -> None:
    for count in COUNTS:
        text = format(count, system=system, precision=110)  # type: ignore[arg-type]
        assert parse(text, system=system) == count  # type: ignore[arg-type]


@pytest.mark.parametrize("system", sorted(SYSTEMS))
@pytest.mark.parametrize("precision", [0, 1, 2])
def test_number_stays_below_the_base(system: str, precision: int) -> None:
    base, suffixes = SYSTEMS[system]
    for count in COUNTS:
        number, unit = _split(format(count, system=system, precision=precision))  # type: ignore[arg-type]
        assert unit in suffixes
        assert number < base or unit == suffixes[-1]
        assert number >= 1 or count == 0 or unit == "B"


@pytest.mark.parametrize("rounding", ["half-up", "half-even", "half-down"])
def test_nearest_modes_err_by_at_most_half_a_step(rounding: str) -> None:
    for count in COUNTS:
        number, unit = _split(format(count, precision=2, rounding=rounding))  # type: ignore[arg-type]
        assert abs(number - convert(count, unit)) <= Decimal("0.005")


@pytest.mark.parametrize("rounding", ["up", "down", "ceiling", "floor"])
def test_directed_modes_go_the_right_way(rounding: str) -> None:
    for count in COUNTS:
        number, unit = _split(format(count, precision=1, rounding=rounding, unit="MiB"))  # type: ignore[arg-type]
        exact = convert(count, unit)
        assert abs(number - exact) < Decimal("0.1")
        if rounding in ("down", "floor"):
            assert number <= exact
        else:
            assert number >= exact


@pytest.mark.parametrize("system", sorted(SYSTEMS))
def test_format_is_monotonic(system: str) -> None:
    base, suffixes = SYSTEMS[system]
    shown = []
    for count in sorted(COUNTS):
        number, unit = _split(format(count, system=system))  # type: ignore[arg-type]
        shown.append(number * Decimal(base) ** suffixes.index(unit))
    assert shown == sorted(shown)


def test_unit_alone_decides_the_system() -> None:
    for exponent in range(1, 11):
        iec, si = IEC_SUFFIXES[exponent], SI_SUFFIXES[exponent]
        assert parse(f"3 {iec}") == 3 * 1024**exponent
        assert parse(f"3 {si}") == 3 * 1000**exponent


def test_strictness_never_guesses() -> None:
    for spelling in ("KB", "Kb", "kib", "KIB", "mB", "Mb", "gb"):
        with pytest.raises(AmbiguousUnitError):
            parse(f"1 {spelling}")
    for count in COUNTS[:50]:
        with pytest.raises(FractionalBytesError):
            parse(f"{count}.5 B")
