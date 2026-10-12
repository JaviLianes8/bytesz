# bytesz guide

This guide explains the rules `bytesz` follows and why. The short version: the unit
alone decides the meaning, arithmetic is exact, and nothing ambiguous is guessed.

## Two systems

| Factor | IEC symbol | IEC name | SI symbol | SI name | SI factor |
| ------ | ---------- | -------- | --------- | ------- | --------- |
| 1024^1 | KiB | kibibyte | kB | kilobyte | 1000^1 |
| 1024^2 | MiB | mebibyte | MB | megabyte | 1000^2 |
| 1024^3 | GiB | gibibyte | GB | gigabyte | 1000^3 |
| 1024^4 | TiB | tebibyte | TB | terabyte | 1000^4 |
| 1024^5 | PiB | pebibyte | PB | petabyte | 1000^5 |
| 1024^6 | EiB | exbibyte | EB | exabyte | 1000^6 |
| 1024^7 | ZiB | zebibyte | ZB | zettabyte | 1000^7 |
| 1024^8 | YiB | yobibyte | YB | yottabyte | 1000^8 |
| 1024^9 | RiB | robibyte | RB | ronnabyte | 1000^9 |
| 1024^10 | QiB | quebibyte | QB | quettabyte | 1000^10 |

- The IEC binary prefixes were approved in December 1998 and published as an
  amendment to IEC 60027-2; NIST documents them at
  https://physics.nist.gov/cuu/Units/binary.html. NIST notes that they are not part
  of the SI and that the symbol is `Ki`, not `ki`.
- Zebi and yobi were added in 2005. Ronna and quetta joined the SI in 2022
  (https://www.bipm.org/en/measurement-units/si-prefixes), and their binary partners
  robi and quebi were adopted in IEC 80000-13:2025.
- The SI kilo is a lower case `k`. `bytesz` writes `kB` and refuses `KB` by default.

## Case rules

Units are case sensitive because case carries meaning: `B` is a byte, `b` is a bit,
`k` is kilo, `Ki` is kibi. `parse` accepts exactly the symbols above plus `B`, the
bare IEC prefixes (`1.5Mi`, as `numfmt --to=iec-i` writes them), and a bare number.
Anything that only matches when case is ignored (`KB`, `kib`, `Mb`, `GIB`) raises
`AmbiguousUnitError`; anything else raises `UnknownUnitError`. Whitespace between the
number and the unit is optional (`1.5GB` and `512 MiB` both work).

## The legacy "KB = 1024" usage

Before 1999, and still today in places, `KB`, `MB` and `GB` meant powers of 1024.
JEDEC keeps those definitions for semiconductor memory, saying they are "included
only to reflect common usage", and several operating systems label sizes that way.
NIST also recalls the "1.44 MB" diskette, which holds 1 474 560 bytes: 1440 times
1024, a third meaning of megabyte. So `KB` really is ambiguous, and `bytesz` will not
pick a side for you. If your input comes from such a source, say so:

```python
from bytesz import parse

parse("4 GB", legacy=True)  # 4294967296
parse("4G", legacy=True)  # 4294967296, bare prefixes as numfmt --from=iec reads them
parse("4 kB", legacy=True)  # 4000, lower case k is never legacy
```

`legacy=True` cannot be combined with `system="si"`. Pinning `system="si"` on its
own makes bare prefixes (`1.5M`, `2K`) mean powers of 1000, as `numfmt --from=si` does.

## Bits

`parse` rejects `Mb` because a bit rate mistaken for a byte size is off by a factor
of eight. Use `parse_bits` and `format_bits` for bit counts. They write the
unambiguous `bit` symbol (`kbit`, `Mibit`) and also read the short `b` form (`kb`,
`Mb`, `Kib`). Upper case `Kb` stays ambiguous there too.

## Rounding and carry

`format` picks the largest unit that keeps the number at one or more, rounds to
`precision` decimals (default 2) and drops trailing zeros unless
`trailing_zeros=True`. If rounding pushes the number up to the base, it carries:
1048575 bytes is `1 MiB`, not `1024 KiB`. Note what that means for IEC: 999.95 KiB
rounds to `1000 KiB` at one decimal, and that is correct, because 1000 KiB is still
below 1024 KiB. In SI, 999.95 kB does carry to `1 MB`. GNU `numfmt` behaves the same.

| bytesz rounding | ties | numfmt `--round` |
| --------------- | ---- | ---------------- |
| `half-up` (default) | away from zero | `nearest` |
| `half-even` | to the even digit | none |
| `half-down` | toward zero | none |
| `up` | away from zero always | `from-zero` |
| `down` | toward zero always | `towards-zero` |
| `ceiling` | toward positive infinity | `up` |
| `floor` | toward negative infinity | `down` |

Note that `numfmt` defaults to `from-zero` while `bytesz` defaults to `half-up`.
Pass `unit="MiB"` to force a unit; there is no carry then. `convert(count, unit)`
gives the exact `Decimal` value with no rounding at all.

## Fractions when parsing

`parse("1.5 B")` raises `FractionalBytesError`: half a byte is a bug in the input.
Pass a rounding mode when you would rather round: `parse("0.1 KiB",
rounding="half-up")` is 102.

## Exactness and huge values

All arithmetic is integer or `Decimal` with enough precision for the input, so
`parse("123456789012345678901234567890 QiB")` is exact and
`parse(format(n, precision=110)) == n` holds for any `n`. Every power of 1000 or 1024
divides into a terminating decimal, so `convert` never rounds.

## Signs and separators

Negative values are refused unless `signed=True`, which also allows a leading `+`
when parsing. `decimal_point=","` reads and writes a comma; it is never inferred
from the locale. `separator` sets the text between number and unit when formatting.

## Errors

| Error | Raised when | Subclass of |
| ----- | ----------- | ----------- |
| `ByteszError` | base class | `ValueError` |
| `InvalidSizeError` | malformed input, a sign without `signed=True` | `ByteszError` |
| `AmbiguousUnitError` | `KB`, `Mb`, `kib`, bare `M` without a pinned system | `ByteszError` |
| `UnknownUnitError` | not a size unit at all | `InvalidSizeError` |
| `SystemMismatchError` | an SI unit with `system="iec"` or the reverse | `InvalidSizeError` |
| `FractionalBytesError` | not a whole byte and no `rounding` | `InvalidSizeError` |

Each carries `.text` (the input) and `.unit` (the unit involved) when known. Bad
option values (an unknown `system` or `rounding`) raise a plain `ValueError`, and a
non-string input to `parse` raises `TypeError`.

## Command line

```
bytesz format [--system iec|si] [--precision N] [--rounding MODE] [--unit U]
              [--signed] [--trailing-zeros] [--separator S] [--decimal-point ,]
              [--bits] [--field N] [VALUES ...]
bytesz parse  [--system iec|si] [--legacy] [--rounding MODE] [--signed]
              [--decimal-point ,] [--bits] [--field N] [VALUES ...]
```

With no values, each line of stdin is one value. `--field N` converts only the Nth
whitespace separated field and keeps the rest of the line, so a size in that field
must be written without an inner space (`1.5MiB`). The first error stops the run,
goes to stderr, and the exit status is 1; usage errors exit with 2.
