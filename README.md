# bytesz

Strict two-way conversion between byte counts and human sizes with explicit IEC and SI units.
Typed, exact (integer and `Decimal` arithmetic only), zero dependencies, with a small CLI.

## Install

```
pip install bytesz
```

## Usage

```python
from bytesz import format, parse

# Human size to an exact integer number of bytes. The unit picks the system.
parse("1.5 MiB")  # 1572864     (IEC, 1024 based)
parse("1.5 MB")  # 1500000     (SI, 1000 based)
parse("512 B")  # 512
parse("2048")  # 2048        (a bare number is bytes)

# Bytes back to a human size, for whichever system you ask for.
format(1572864)  # "1.5 MiB"   (IEC is the default)
format(1500000, system="si")  # "1.5 MB"
format(1234567, system="si", precision=2)  # "1.23 MB"
format(1048575)  # "1 MiB"     (rounding carries into the next unit)
```

It refuses to guess:

```python
from bytesz import AmbiguousUnitError, FractionalBytesError, SystemMismatchError, parse

parse("1 KB")  # AmbiguousUnitError: KB could mean kB (1000) or KiB (1024)
parse("100 Mb")  # AmbiguousUnitError: a lower case b means bits, see parse_bits
parse("1.5 B")  # FractionalBytesError: not a whole number of bytes
parse("1 kB", system="iec")  # SystemMismatchError: an SI unit under a pinned IEC system
```

Every input error is a `ByteszError` (a `ValueError`) carrying `.text` and `.unit`. Bad
option values raise a plain `ValueError`, and a non-string input to `parse` a `TypeError`.

## Options

```python
from bytesz import convert, format, format_bits, parse, parse_bits

# Formatting
format(1250, system="si", precision=1, rounding="half-even")  # "1.2 kB"
format(1_000_000, unit="MiB")  # "0.95 MiB"
format(5000, unit="kB")  # "5 kB" (the unit picks the system)
format(-1536, signed=True)  # "-1.5 KiB"
format(1536, precision=3, trailing_zeros=True)  # "1.500 KiB"
format(1536, decimal_point=",", separator="")  # "1,5KiB"

# Parsing
parse("1.0005 kB", rounding="half-up")  # 1001
parse("1,5 MiB", decimal_point=",")  # 1572864
parse("-2 KiB", signed=True)  # -2048
parse("1.5M", system="si")  # 1500000 (bare prefixes, as numfmt writes them)
parse("1.5Mi")  # 1572864 (bare IEC prefix)
parse("4 GB", legacy=True)  # 4294967296 (JEDEC style KB/MB/GB = 1024, opt-in)

# Bits, with the unambiguous "bit" symbol
parse_bits("100 Mbit")  # 100000000
format_bits(1_500_000, system="si")  # "1.5 Mbit"

# Exact value in one unit, no rounding at all
convert(1, "KiB")  # Decimal("0.0009765625")
```

Rounding modes: `half-up` (default, ties away from zero), `half-even`, `half-down`,
`up`, `down`, `ceiling`, `floor`. Units reach the 2022 SI prefixes `RB` and `QB` and
the IEC 80000-13:2025 prefixes `RiB` and `QiB`.

## Command line

```
bytesz format 1572864                 # 1.5 MiB
bytesz format --system si 1234567     # 1.23 MB
bytesz parse "1.5 MiB" 2GB            # 1572864, 2000000000
bytesz parse --legacy 4KB             # 4096
du -b * | bytesz format --field 1     # rewrite one column, like numfmt --field
```

Values come from the arguments or, when there are none, one per line from stdin.
Errors go to stderr with exit status 1. `bytesz --help` lists every option.

## Why

Human byte sizes are a well known trap: `KB` means 1000 bytes to a disk vendor and
1024 bytes to an operating system, and most libraries quietly pick one. The popular
options lean on guessing or only go one way: `humanize` and `hurry.filesize` format
numbers but do not parse them back, `humanfriendly` parses but treats `KB` and `KiB`
as the same 1024 based value, and `bitmath` mixes bits and bytes with a broad API.

`bytesz` is deliberately narrow and strict. The unit alone decides the system, both
directions are exact, and anything ambiguous or fractional is rejected with a clear
error instead of being rounded, unless you ask for rounding. Reach for it when a
wrong factor of 1024 would be a real bug, such as quotas, billing, or on-disk
accounting. With matching `--round` and `--format=%.Nf`, its formatting agrees with
GNU `numfmt` (checked in the test suite on seeded values), except where `numfmt` itself
drifts because it divides in floating point.

See [GUIDE.md](GUIDE.md) for the rules in depth.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
