# Improvement round for bytesz 0.2.0

Progress:
- [x] Brainstorm ranked improvements (this file)
- [x] Unit tables: 2022 SI prefixes (ronna, quetta) and IEC 80000-13:2025 (robi, quebi)
- [x] Format: rounding modes with carry, forced unit, signed values, decimal point, trailing zeros
- [x] Parse: rounding of fractional bytes, signed values, decimal point, opt-in JEDEC legacy units
- [x] Bits: parse_bits and format_bits
- [x] Typed errors with attributes, exported type aliases, exact convert()
- [x] CLI (`bytesz format`, `bytesz parse`, numfmt-like `--field` over stdin)
- [x] Docs: README, GUIDE, CHANGELOG, docstrings
- [x] Gates: ruff format, ruff check, mypy --strict, pytest
- [x] Contracts, seeded cross-check against GNU numfmt, real wheel e2e
- [x] Pull request opened (#2)
- [x] Independent review findings fixed, guard clean

## Sources (fetched 2026-10-12)

- NIST, Prefixes for binary multiples: https://physics.nist.gov/cuu/Units/binary.html
  (Ki, Mi, Gi, Ti, Pi, Ei; "1 MiB = 2^20 B = 1 048 576 B"; "the symbol Ki is used
  for 2^10 rather than ki"; binary prefixes are not part of the SI; history of the
  1 024 000 byte "1.44 MB" diskette.)
- BIPM, SI prefixes: https://www.bipm.org/en/measurement-units/si-prefixes
  (ronna 10^27, quetta 10^30, adopted 2022.)
- Wikipedia, Binary prefix (raw wikitext):
  https://en.wikipedia.org/w/index.php?title=Binary_prefix&action=raw
  (zebi and yobi added in 2005; robi Ri = 1024^9 and quebi Qi = 1024^10 adopted in
  IEC 80000-13:2025; JEDEC keeps K, M, G in the binary sense "only to reflect common
  usage".)
- Oracle: GNU coreutils 9.7 `numfmt` (`gnunumfmt` in WSL Ubuntu 26.04, where the
  default `numfmt` is the uutils port). Observed: the default rounding is
  `from-zero`; a value that rounds up to the base carries to the next unit
  (1048575 -> `1.0Mi`); 1023949 -> `1000Ki` because 999.95 KiB rounds to 1000 KiB,
  which is still below 1024 KiB; `--to=iec-i` reaches `Ri` and `Qi`; `--to=si`
  uses lower-case `k`.

## Ranked improvements

1. **Carry on rounding (bug).** `format(1048575)` printed `1024 KiB`. When the
   rounded value reaches the base, move up one unit (`1 MiB`), as numfmt does. Note
   for IEC that 999.95 KiB rounding to `1000 KiB` is correct: it is below 1024 KiB.
   For SI, 999.95 kB at one decimal does carry to `1 MB`.
2. **2022 prefixes.** Add `RB`, `QB` (SI) and `RiB`, `QiB` (IEC) to both tables.
3. **Rounding modes.** `rounding=` with `half-up` (default, ties away from zero,
   same as numfmt `nearest`), `half-even`, `up` (numfmt `from-zero`), `down`
   (numfmt `towards-zero`), `ceiling`, `floor`.
4. **Forced unit and exact conversion.** `format(..., unit="MiB")` and
   `convert(count, "MiB") -> Decimal` with no rounding at all.
5. **Fractional bytes on parse, opt-in.** `parse(..., rounding="half-up")` rounds
   instead of raising; the default stays strict.
6. **Signed values, opt-in.** `signed=True` on both sides for deltas.
7. **Decimal separator.** `decimal_point=","` on both sides for locales that use a
   comma; never inferred.
8. **Trailing zeros and separator.** `trailing_zeros=True` keeps `1.50 KiB`;
   `separator=""` gives `1.5KiB`.
9. **Bits.** `parse_bits` and `format_bits` with `bit` symbols (`kbit`, `Mibit`,
   and the short `Mb`, `Kib` spellings inside the bit functions only). `parse` keeps
   rejecting `Mb` so a bit rate never silently becomes a byte size.
10. **JEDEC legacy, opt-in and named.** `parse(..., legacy=True)` reads `KB`, `MB`,
    `GB` (and `K`, `M`, `G`) as powers of 1024, as JEDEC and many operating systems
    do. Off by default.
11. **Typed errors.** `UnknownUnitError`, `SystemMismatchError`,
    `FractionalBytesError`, all subclasses of `InvalidSizeError`, carrying the
    offending text and unit. Existing `except` clauses keep working.
12. **Typed aliases.** Export `System` and `Rounding` as `Literal` types.
13. **CLI.** `bytesz format`, `bytesz parse`, values from arguments or stdin,
    `--field N` to rewrite one whitespace column like `numfmt --field`.
14. **Docs.** GUIDE.md covering systems, rounding, carry, legacy usage, and errors.

Out of scope: guessing a system from context, long names such as "kilobyte" (they
carry the same ambiguity as `KB`), and locale detection.
