"""Public type aliases and the rounding mode table."""

from __future__ import annotations

import decimal
from typing import Final, Literal

System = Literal["iec", "si"]
"""A size system: "iec" (powers of 1024, KiB) or "si" (powers of 1000, kB)."""

Rounding = Literal["half-up", "half-even", "half-down", "up", "down", "ceiling", "floor"]
"""How a value is rounded to the requested precision.

"half-up" rounds ties away from zero (numfmt ``nearest``), "half-even" rounds ties
to the even digit, "half-down" rounds ties toward zero, "up" rounds away from
zero (numfmt ``from-zero``), "down" truncates toward zero (numfmt
``towards-zero``), "ceiling" rounds toward positive infinity (numfmt ``up``) and
"floor" toward negative infinity (numfmt ``down``).
"""

ROUNDING_MODES: Final[dict[str, str]] = {
    "half-up": decimal.ROUND_HALF_UP,
    "half-even": decimal.ROUND_HALF_EVEN,
    "half-down": decimal.ROUND_HALF_DOWN,
    "up": decimal.ROUND_UP,
    "down": decimal.ROUND_DOWN,
    "ceiling": decimal.ROUND_CEILING,
    "floor": decimal.ROUND_FLOOR,
}


def rounding_mode(rounding: str) -> str:
    """Return the ``decimal`` rounding constant for a public rounding name."""
    try:
        return ROUNDING_MODES[rounding]
    except KeyError:
        names = ", ".join(repr(name) for name in ROUNDING_MODES)
        raise ValueError(f"unknown rounding {rounding!r}; use one of {names}") from None


def check_system(system: object) -> None:
    """Reject anything that is not "iec" or "si"."""
    if system not in ("iec", "si"):
        raise ValueError(f"unknown system {system!r}; use 'iec' or 'si'")


def check_decimal_point(decimal_point: object) -> None:
    """Accept only "." or "," as the decimal separator."""
    if decimal_point not in (".", ","):
        raise ValueError(f"decimal_point must be '.' or ',', not {decimal_point!r}")
