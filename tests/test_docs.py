"""The examples in the docstrings, README and GUIDE are executed, not just read."""

from __future__ import annotations

import doctest
import re
from pathlib import Path

import pytest

import bytesz
from bytesz import _bits, _convert, _format, _parse

ROOT = Path(__file__).resolve().parents[1]
RESULT = re.compile(r'^(?P<call>\S.*?\))\s+# (?P<want>"[^"]*"|Decimal\("[^"]*"\)|\S+)')


@pytest.mark.parametrize("module", [_bits, _convert, _format, _parse])
def test_docstring_examples(module: object) -> None:
    result = doctest.testmod(module, verbose=False)  # type: ignore[arg-type]
    assert result.attempted > 0
    assert result.failed == 0


@pytest.mark.parametrize("name", ["README.md", "GUIDE.md"])
def test_markdown_examples(name: str) -> None:
    """Lines shaped like ``call(...)  # value`` must evaluate to that value."""
    namespace = {name: getattr(bytesz, name) for name in bytesz.__all__}
    checked = 0
    for line in (ROOT / name).read_text(encoding="utf-8").splitlines():
        match = RESULT.match(line)
        if match is None or not match["call"].startswith(("parse", "format", "convert")):
            continue
        want = match["want"].rstrip(",")
        try:
            got = eval(match["call"], namespace)  # the repository's own docs
        except bytesz.ByteszError as error:
            assert want.rstrip(":") == type(error).__name__, line
        else:
            assert repr(got).replace("'", '"') == want, line
        checked += 1
    assert checked >= 3
