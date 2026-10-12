"""End to end check: build the wheel, install it in a throwaway venv, drive `bytesz`.

Run from the repository root:  python scripts/e2e_wheel.py
Needs the `build` package (it is in the dev extras). Exits non-zero on any mismatch.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# (arguments, stdin, expected stdout, expected exit status)
CASES: list[tuple[list[str], str, str, int]] = [
    (["format", "1572864"], "", "1.5 MiB\n", 0),
    (["format", "1048575"], "", "1 MiB\n", 0),
    (
        ["format", "--system", "si", "--precision", "1", "1234567", "999950"],
        "",
        "1.2 MB\n1 MB\n",
        0,
    ),
    (["format", "--unit", "MiB", "1000000"], "", "0.95 MiB\n", 0),
    (["format", "1267650600228229401496703205376"], "", "1 QiB\n", 0),
    (["format", "--bits", "--system", "si", "1500000"], "", "1.5 Mbit\n", 0),
    (
        ["parse", "1.5 MiB", "2GB", "1 RiB"],
        "",
        "1572864\n2000000000\n1237940039285380274899124224\n",
        0,
    ),
    (["parse", "--legacy", "4KB"], "", "4096\n", 0),
    (["parse", "--decimal-point", ",", "1,5 kB"], "", "1500\n", 0),
    (["format", "--field", "1"], "4096\tdocs\n1572864 build\n", "4 KiB\tdocs\n1.5 MiB build\n", 0),
    (["parse"], "1 KiB\n1 MiB\n", "1024\n1048576\n", 0),
    (["parse", "1 KB"], "", "", 1),
    (["format", "abc"], "", "", 1),
    (["format", "--system", "metric", "1"], "", "", 2),
]


def run(command: list[str], stdin: str = "") -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(command, input=stdin.encode(), capture_output=True, timeout=300)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="bytesz-e2e-") as tmp:
        work = Path(tmp)
        built = run([sys.executable, "-m", "build", "--wheel", "--outdir", str(work), str(ROOT)])
        if built.returncode != 0:
            sys.stderr.write(built.stderr.decode(errors="replace"))
            return 1
        wheel = next(work.glob("bytesz-*.whl"))
        venv.create(work / "venv", with_pip=True)
        scripts = work / "venv" / ("Scripts" if sys.platform == "win32" else "bin")
        python = scripts / ("python.exe" if sys.platform == "win32" else "python")
        installed = run([str(python), "-m", "pip", "install", "--no-index", "-q", str(wheel)])
        if installed.returncode != 0:
            sys.stderr.write(installed.stderr.decode(errors="replace"))
            return 1
        exe = scripts / ("bytesz.exe" if sys.platform == "win32" else "bytesz")
        failures = 0
        for argv, stdin, want, status in CASES:
            got = run([str(exe), *argv], stdin)
            out = got.stdout.decode().replace("\r\n", "\n")
            err = got.stderr.decode()
            ok = got.returncode == status and out == want and (status == 0) == (err == "")
            print(("ok   " if ok else "FAIL ") + " ".join(argv), f"-> {got.returncode}")
            if not ok:
                failures += 1
                print(f"     stdout={out!r} stderr={err!r}")
        probe = (
            "import importlib.resources as r, bytesz;"
            "assert r.files('bytesz').joinpath('py.typed').is_file();"
            "print(bytesz.__version__, bytesz.__file__)"
        )
        typed = run([str(python), "-I", "-c", probe])
        print("installed:", typed.stdout.decode().strip() or typed.stderr.decode())
        failures += typed.returncode != 0
        print(f"wheel: {wheel.name}; failures: {failures}")
        return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
