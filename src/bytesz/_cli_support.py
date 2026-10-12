"""Helpers for the command line: input lines, usage checks, wording, closed pipes."""

from __future__ import annotations

import argparse
import errno
import os
import re
import sys
from collections.abc import Iterator, Sequence
from typing import Final, TextIO

from ._units import IEC_BIT_SUFFIXES, IEC_SUFFIXES, SI_BIT_SUFFIXES, SI_SUFFIXES

INTEGER: Final = re.compile(r"[+-]?[0-9]+")

_UNITS: Final[dict[tuple[bool, str | None], tuple[str, ...]]] = {
    (False, "iec"): IEC_SUFFIXES,
    (False, "si"): SI_SUFFIXES,
    (False, None): IEC_SUFFIXES + SI_SUFFIXES[1:],
    (True, "iec"): IEC_BIT_SUFFIXES,
    (True, "si"): SI_BIT_SUFFIXES,
    (True, None): IEC_BIT_SUFFIXES + SI_BIT_SUFFIXES[1:],
}

# Library messages name keyword arguments; the command line names flags.
_CLI_WORDS: Final = (
    ("signed=True", "--signed"),
    ("legacy=True", "--legacy"),
    ("system='si'", "--system si"),
    ("system='iec'", "--system iec"),
    ("system is 'si'", "--system is si"),
    ("system is 'iec'", "--system is iec"),
    ("use parse_bits for bits", "add --bits for bits"),
    ("see parse_bits", "see --bits"),
    ("use parse for bytes", "drop --bits for bytes"),
)


def inputs(values: Sequence[str], stdin: TextIO) -> Iterator[str]:
    """Yield the argument values, or each stdin line without its line end or a BOM."""
    if values:
        yield from values
        return
    for number, line in enumerate(stdin):
        yield (line.removeprefix("\ufeff") if number == 0 else line).rstrip("\r\n")


def cli_words(message: str) -> str:
    """Say option names the way the command line spells them."""
    for api, flag in _CLI_WORDS:
        message = message.replace(api, flag)
    return message


def check_usage(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    """Reject bad option values as usage errors (exit status 2)."""
    if args.field is not None and args.field < 1:
        parser.error("--field must be 1 or more")
    if args.command != "format":
        return
    if args.precision < 0:
        parser.error("--precision must be 0 or more")
    units = _UNITS[(args.bits, args.system)]
    if args.unit is not None and args.unit not in units:
        parser.error(f"--unit {args.unit!r} is not one of: {', '.join(units)}")


def stop_on_closed_pipe(error: OSError) -> int:
    """Stop quietly when the reader went away (``| head``), as Python's docs advise."""
    if not isinstance(error, BrokenPipeError) and error.errno not in (errno.EPIPE, errno.EINVAL):
        raise error
    os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
    return 1
