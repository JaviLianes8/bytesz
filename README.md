# bytesz

Strict two-way conversion between byte counts and human sizes with explicit IEC and SI units.

## Install

```
pip install bytesz
```

## Usage

```python
from bytesz import parse, format

# Human size to an exact integer number of bytes. The unit picks the system.
parse("1.5 MiB")        # 1572864   (IEC, 1024 based)
parse("1.5 MB")         # 1500000   (SI, 1000 based)
parse("512 B")          # 512
parse("2048")           # 2048      (a bare number is bytes)

# Bytes back to a human size, for whichever system you ask for.
format(1572864)                       # "1.5 MiB"   (IEC is the default)
format(1500000, system="si")          # "1.5 MB"
format(1234567, system="si", precision=2)  # "1.23 MB"
```

It refuses to guess:

```python
from bytesz import parse, AmbiguousUnitError, InvalidSizeError

parse("1 KB")                 # AmbiguousUnitError: KB could mean kB (1000) or KiB (1024)
parse("1.5 B")                # InvalidSizeError: not a whole number of bytes
parse("1 kB", system="iec")   # InvalidSizeError: an SI unit under a pinned IEC system
```

Pin a system when you only want to accept one of them:

```python
parse("1 KiB", system="iec")  # 1024
parse("1 kB", system="si")    # 1000
```

## Why

Human byte sizes are a well known trap: `KB` means 1000 bytes to a disk vendor and
1024 bytes to an operating system, and most libraries quietly pick one. The popular
options lean on guessing or only go one way: `humanize` and `hurry.filesize` format
numbers but do not parse them back, `humanfriendly` parses but treats `KB` and `KiB`
as the same 1024 based value, and `bitmath` mixes bits and bytes with a broad API.

`bytesz` is deliberately narrow and strict. The unit alone decides the system, both
directions are exact, and anything ambiguous or fractional is rejected with a clear
error instead of being rounded. Reach for it when a wrong factor of 1024 would be a
real bug, such as quotas, billing, or on-disk accounting.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
