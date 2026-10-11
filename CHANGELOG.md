# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0]

- `parse` turns a human size into an exact integer number of bytes, choosing the
  system from the unit: IEC suffixes (KiB, MiB) use 1024 and SI suffixes (kB, MB)
  use 1000.
- `format` turns a byte count into a human size for either system with a chosen
  precision.
- Strict by design: ambiguous spellings such as `KB` raise `AmbiguousUnitError`,
  and inputs that do not land on a whole byte raise `InvalidSizeError`.
- `system` can pin `parse` to one system so the other is rejected.
