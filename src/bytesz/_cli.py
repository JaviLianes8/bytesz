"""Command line interface: ``bytesz format`` and ``bytesz parse``."""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Callable, Sequence

from . import __version__
from ._bits import format_bits, parse_bits
from ._cli_support import INTEGER, check_usage, cli_words, inputs, stop_on_closed_pipe
from ._errors import ByteszError
from ._format import format as format_size
from ._parse import parse
from ._types import ROUNDING_MODES

_EPILOG = """\
examples:
  bytesz format 1572864                 # 1.5 MiB
  bytesz format --system si 1234567     # 1.23 MB
  bytesz format --unit MiB 1000000      # 0.95 MiB
  bytesz parse "1.5 MiB" 2GB            # 1572864 and 2000000000
  bytesz parse --legacy 4KB             # 4096
  bytesz parse --bits 100Mbit           # 100000000
  du -b * | bytesz format --field 1     # rewrite the first column, like numfmt

Values come from the arguments, or one per line from stdin when there are none.
With --field N only the Nth whitespace separated field of each line is converted
and the rest of the line is kept as it is. Errors go to stderr with exit status 1.
"""


def _common(sub: argparse.ArgumentParser) -> None:
    sub.add_argument("values", nargs="*", help="values to convert (default: read stdin)")
    sub.add_argument("--rounding", choices=sorted(ROUNDING_MODES), help="rounding mode")
    sub.add_argument("--signed", action="store_true", help="allow negative values")
    sub.add_argument(
        "--decimal-point",
        default=".",
        choices=[".", ","],
        metavar="{.|,}",
        help="decimal separator: . (default) or ,",
    )
    sub.add_argument("--bits", action="store_true", help="count bits instead of bytes")
    sub.add_argument("--field", type=int, metavar="N", help="convert only field N (1 based)")


def build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for the ``bytesz`` command."""
    parser = argparse.ArgumentParser(
        prog="bytesz",
        description="Convert byte counts to and from human sizes (IEC KiB or SI kB).",
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"bytesz {__version__}")
    subs = parser.add_subparsers(dest="command", required=True, metavar="{format,parse}")
    fmt = subs.add_parser(
        "format",
        help="byte count to human size",
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    fmt.add_argument("--system", choices=["iec", "si"], help="default: from --unit, else iec")
    fmt.add_argument("--precision", type=int, default=2, help="decimals (default: 2)")
    fmt.add_argument("--unit", help="force one unit, such as MiB")
    fmt.add_argument("--trailing-zeros", action="store_true", help="keep zeros, as in 1.50")
    fmt.add_argument("--separator", default=" ", help="text between number and unit")
    _common(fmt)
    par = subs.add_parser(
        "parse",
        help="human size to byte count",
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    par.add_argument("--system", choices=["iec", "si"], help="accept only this system")
    par.add_argument("--legacy", action="store_true", help="read KB, MB, GB as powers of 1024")
    _common(par)
    return parser


def _converter(args: argparse.Namespace) -> Callable[[str], str]:
    if args.command == "format":
        render = format_bits if args.bits else format_size

        def convert_format(token: str) -> str:
            token = token.strip()
            if not INTEGER.fullmatch(token):
                raise ByteszError(f"not an integer count: {token!r}")
            if token.startswith("+") and not args.signed:
                raise ByteszError(f"{token!r} has a sign; pass --signed to allow it")
            return render(
                int(token),
                system=args.system,
                precision=args.precision,
                rounding=args.rounding or "half-up",
                unit=args.unit,
                signed=args.signed,
                trailing_zeros=args.trailing_zeros,
                decimal_point=args.decimal_point,
                separator=args.separator,
            )

        return convert_format

    def convert_parse(token: str) -> str:
        if args.bits:
            value = parse_bits(
                token,
                system=args.system,
                rounding=args.rounding,
                signed=args.signed,
                decimal_point=args.decimal_point,
            )
        else:
            value = parse(
                token,
                system=args.system,
                rounding=args.rounding,
                signed=args.signed,
                decimal_point=args.decimal_point,
                legacy=args.legacy,
            )
        return str(value)

    return convert_parse


def _replace_field(line: str, field: int, convert: Callable[[str], str]) -> str:
    if not line.strip():
        return line
    spans = [m.span() for m in re.finditer(r"\S+", line)]
    if field > len(spans):
        raise ByteszError(f"line has no field {field}: {line!r}")
    start, end = spans[field - 1]
    return line[:start] + convert(line[start:end]) + line[end:]


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line interface and return the exit status."""
    parser = build_parser()
    args = parser.parse_args(argv)
    check_usage(parser, args)
    convert = _converter(args)
    try:
        for item in inputs(args.values, sys.stdin):
            field = args.field
            if not item.strip():
                out = item  # blank lines pass through
            elif field is None:
                out = convert(item)
            else:
                out = _replace_field(item, field, convert)
            sys.stdout.write(out + "\n")
        sys.stdout.flush()
    except (ByteszError, ValueError) as error:
        sys.stdout.flush()
        sys.stderr.write(f"bytesz: error: {cli_words(str(error))}\n")
        return 1
    except OSError as error:
        return stop_on_closed_pipe(error)
    return 0
