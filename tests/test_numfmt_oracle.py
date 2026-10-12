"""Seeded cross-check of ``format`` against GNU coreutils ``numfmt``.

The oracle is GNU numfmt run through WSL. On Ubuntu 26.04 the plain ``numfmt``
is the uutils port, so the GNU binary is looked up as ``gnunumfmt`` first. The
test is skipped, with the reason, when neither is reachable.
"""

from __future__ import annotations

import random
import shutil
import subprocess
from decimal import Decimal

import pytest

from bytesz import convert, format, parse

# numfmt --round names for the bytesz rounding modes they share.
NUMFMT_ROUND = {
    "half-up": "nearest",
    "up": "from-zero",
    "down": "towards-zero",
    "ceiling": "up",
    "floor": "down",
}
EDGES = [0, 1, 999, 1000, 1023, 1024, 1536, 999950, 1023949, 1048575, 1048576, -1048575]


def _numfmt_command() -> list[str] | None:
    if shutil.which("wsl") is None:
        return None
    for name in ("gnunumfmt", "numfmt"):
        try:
            probe = subprocess.run(
                ["wsl", "-e", name, "--version"], capture_output=True, text=True, timeout=60
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        if probe.returncode == 0 and "GNU coreutils" in probe.stdout:
            return ["wsl", "-e", name]
    return None


NUMFMT = _numfmt_command()
pytestmark = pytest.mark.skipif(NUMFMT is None, reason="GNU numfmt via WSL is not available")


def _samples() -> list[int]:
    rng = random.Random(20261012)
    drawn = [rng.randrange(2 ** rng.randrange(1, 53)) * rng.choice((1, -1)) for _ in range(400)]
    return drawn + EDGES


def _numfmt(numbers: list[int], to: str, rounding: str, precision: int) -> list[str]:
    assert NUMFMT is not None
    result = subprocess.run(
        [*NUMFMT, f"--to={to}", f"--round={rounding}", f"--format=%.{precision}f"],
        # Bytes, not text: text mode on Windows would send "\r\n" line ends.
        input="\n".join(str(n) for n in numbers).encode("ascii"),
        capture_output=True,
        timeout=120,
        check=True,
    )
    return result.stdout.decode("utf-8").split()


@pytest.mark.parametrize(("system", "to"), [("iec", "iec-i"), ("si", "si")])
@pytest.mark.parametrize("precision", [0, 1, 2, 3])
@pytest.mark.parametrize("rounding", sorted(NUMFMT_ROUND))
def test_format_agrees_with_gnu_numfmt(system: str, to: str, precision: int, rounding: str) -> None:
    numbers = _samples()
    expected = _numfmt(numbers, to, NUMFMT_ROUND[rounding], precision)
    assert len(expected) == len(numbers)
    for number, oracle in zip(numbers, expected, strict=True):
        mine = format(
            number,
            system=system,  # type: ignore[arg-type]
            precision=precision,
            rounding=rounding,  # type: ignore[arg-type]
            signed=True,
            trailing_zeros=True,
            separator="",
        )
        # numfmt writes a bare prefix ("1.5Ki", "2k") and nothing for bytes.
        if mine.removesuffix("B") != oracle:
            _assert_numfmt_float_artefact(number, mine, precision)


def _assert_numfmt_float_artefact(number: int, mine: str, precision: int) -> None:
    """Accept a disagreement only where numfmt's long double arithmetic is to blame.

    numfmt divides in binary floating point, so a value that sits exactly on the
    requested precision (1023 / 1000 = 1.023) can land a hair to either side and a
    directed rounding mode then moves it by one step (numfmt prints 1.024k for
    ``--round=up``). bytesz divides exactly, so in that case its digits must equal
    the exact quotient.
    """
    split = next(i for i, c in enumerate(mine) if c.isalpha())
    value, unit = mine[:split], mine[split:]
    exact = convert(number, unit)
    assert exact == exact.quantize(Decimal(1).scaleb(-precision)), (number, mine)
    assert Decimal(value) == exact, (number, mine)


@pytest.mark.parametrize(("to", "suffix"), [("iec-i", "Ri"), ("iec-i", "Qi"), ("si", "Q")])
def test_parse_reads_numfmt_output(to: str, suffix: str) -> None:
    assert NUMFMT is not None
    base = 1024 if to == "iec-i" else 1000
    exponent = {"Ri": 9, "Qi": 10, "Q": 10}[suffix]
    numbers = [3 * base**exponent, 3 * base**exponent // 2]
    out = _numfmt(numbers, to, "nearest", 1)
    for number, text in zip(numbers, out, strict=True):
        assert text.endswith(suffix)
        assert parse(text, system="si" if to == "si" else "iec") == number
