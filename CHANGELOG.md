# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0]

### Added

- The 2022 SI prefixes ronna and quetta (`RB`, `QB`) and the IEC 80000-13:2025
  prefixes robi and quebi (`RiB`, `QiB`).
- `format` options (also on `format_bits`): `system` may be omitted and then follows
  `unit` (default IEC); `rounding` (`half-up`, `half-even`, `half-down`, `up`, `down`,
  `ceiling`, `floor`), `unit` to force one unit, `signed`, `trailing_zeros`,
  `decimal_point` and `separator`.
- `parse` options: `rounding` for values that are not whole bytes, `signed`,
  `decimal_point`, and an opt-in `legacy` mode that reads `KB`, `MB`, `GB` (and bare
  `K`, `M`, `G`) as powers of 1024. Bare IEC prefixes (`1.5Mi`) are accepted, and bare
  SI prefixes (`1.5M`) when `system="si"` is pinned, matching `numfmt` output.
- `parse_bits` and `format_bits` for bit counts with the `bit` symbol.
- `convert(count, unit)` for the exact `Decimal` value in one unit.
- Typed errors `UnknownUnitError`, `SystemMismatchError` and `FractionalBytesError`,
  all subclasses of `InvalidSizeError`; every error carries `.text` and `.unit`.
- `System` and `Rounding` type aliases, `IEC_SUFFIXES` and `SI_SUFFIXES`.
- A `bytesz` command with `format` and `parse` subcommands, stdin input and a
  numfmt style `--field` option. Also runnable as `python -m bytesz`.
- GUIDE.md.

### Changed

- Rounding now carries into the next unit: `format(1048575)` is `"1 MiB"` instead of
  `"1024 KiB"`.
- Counts of 1024**9 bytes and above now use `RiB` and `QiB` (and `RB`, `QB` for SI)
  instead of large numbers of `YiB`.
- A lower case `b` in `parse` now explains that it means bits, and a bit unit such
  as `Kibit` raises `UnknownUnitError` pointing at `parse_bits`.

### Fixed

- Parsing stays exact for long inputs and the largest units; the default decimal
  context used to round products above 28 digits.
- Arithmetic runs in a private decimal context, so a caller's global settings
  (traps, precision, exponent limits) no longer change or break the results.

## [0.1.0]

- `parse` turns a human size into an exact integer number of bytes, choosing the
  system from the unit: IEC suffixes (KiB, MiB) use 1024 and SI suffixes (kB, MB)
  use 1000.
- `format` turns a byte count into a human size for either system with a chosen
  precision.
- Strict by design: ambiguous spellings such as `KB` raise `AmbiguousUnitError`,
  and inputs that do not land on a whole byte raise `InvalidSizeError`.
- `system` can pin `parse` to one system so the other is rejected.
