from __future__ import annotations

import io
import os
import subprocess
import sys
from pathlib import Path

import pytest

import bytesz
from bytesz import __version__
from bytesz._cli import main


def run(argv: list[str], monkeypatch: pytest.MonkeyPatch, stdin: str = "") -> int:
    monkeypatch.setattr(sys, "stdin", io.StringIO(stdin))
    return main(argv)


def test_format_arguments(capsys: pytest.CaptureFixture[str], mp: pytest.MonkeyPatch) -> None:
    assert run(["format", "1572864", "1234567", "--system", "si"], mp) == 0
    assert capsys.readouterr().out == "1.57 MB\n1.23 MB\n"


def test_format_options(capsys: pytest.CaptureFixture[str], mp: pytest.MonkeyPatch) -> None:
    argv = ["format", "1536", "--precision", "3", "--trailing-zeros", "--separator", ""]
    assert run([*argv, "--decimal-point", ","], mp) == 0
    assert capsys.readouterr().out == "1,500KiB\n"
    assert run(["format", "--unit", "MiB", "1000000"], mp) == 0
    assert capsys.readouterr().out == "0.95 MiB\n"
    assert run(["format", "--rounding", "down", "1048575"], mp) == 0
    assert capsys.readouterr().out == "1023.99 KiB\n"
    assert run(["format", "--signed", "--", "-2048"], mp) == 0
    assert capsys.readouterr().out == "-2 KiB\n"
    assert run(["format", "--bits", "--system", "si", "1500000"], mp) == 0
    assert capsys.readouterr().out == "1.5 Mbit\n"


def test_parse_arguments(capsys: pytest.CaptureFixture[str], mp: pytest.MonkeyPatch) -> None:
    assert run(["parse", "1.5 MiB", "2GB"], mp) == 0
    assert capsys.readouterr().out == "1572864\n2000000000\n"
    assert run(["parse", "--legacy", "4KB"], mp) == 0
    assert capsys.readouterr().out == "4096\n"
    assert run(["parse", "--bits", "100Mbit"], mp) == 0
    assert capsys.readouterr().out == "100000000\n"
    assert run(["parse", "--rounding", "half-up", "1.5 B"], mp) == 0
    assert capsys.readouterr().out == "2\n"
    assert run(["parse", "--system", "si", "1.5M"], mp) == 0
    assert capsys.readouterr().out == "1500000\n"


def test_stdin_lines(capsys: pytest.CaptureFixture[str], mp: pytest.MonkeyPatch) -> None:
    assert run(["format"], mp, "1024\r\n2048\n") == 0
    assert capsys.readouterr().out == "1 KiB\n2 KiB\n"


def test_field_keeps_the_rest(capsys: pytest.CaptureFixture[str], mp: pytest.MonkeyPatch) -> None:
    lines = "4096\tdocs\n1572864   build/out\n"
    assert run(["format", "--field", "1"], mp, lines) == 0
    assert capsys.readouterr().out == "4 KiB\tdocs\n1.5 MiB   build/out\n"
    assert run(["parse", "--field", "2"], mp, "a 1.5MiB z\n") == 0
    assert capsys.readouterr().out == "a 1572864 z\n"


def test_errors_go_to_stderr(capsys: pytest.CaptureFixture[str], mp: pytest.MonkeyPatch) -> None:
    assert run(["parse", "1 KiB", "1 KB", "2 KiB"], mp) == 1
    captured = capsys.readouterr()
    assert captured.out == "1024\n"
    assert captured.err.startswith("bytesz: error: 'KB' is ambiguous")
    assert run(["format", "1.5"], mp) == 1
    assert "not an integer count" in capsys.readouterr().err
    assert run(["format", "--field", "3"], mp, "1 2\n") == 1
    assert "no field 3" in capsys.readouterr().err
    assert run(["format", "--unit", "kB", "5000"], mp) == 0
    assert capsys.readouterr().out == "5 kB\n"


def test_messages_name_flags(capsys: pytest.CaptureFixture[str], mp: pytest.MonkeyPatch) -> None:
    assert run(["format", "--", "-5"], mp) == 1
    assert "pass --signed" in capsys.readouterr().err
    assert run(["format", "+5"], mp) == 1
    assert "pass --signed" in capsys.readouterr().err
    assert run(["parse", "4KB"], mp) == 1
    assert "pass --legacy" in capsys.readouterr().err
    assert run(["parse", "1 Kibit"], mp) == 1
    assert "add --bits" in capsys.readouterr().err
    assert run(["parse", "--bits", "1 kB"], mp) == 1
    assert "drop --bits" in capsys.readouterr().err


def test_integers_are_strict(capsys: pytest.CaptureFixture[str], mp: pytest.MonkeyPatch) -> None:
    for token in ("1_024", "1.0", chr(0x661), "1e3"):
        assert run(["format", token], mp) == 1
        assert "not an integer count" in capsys.readouterr().err
    assert run(["format", "--signed", "+1024"], mp) == 0
    assert capsys.readouterr().out == "1 KiB\n"


def test_blank_lines_and_bom(capsys: pytest.CaptureFixture[str], mp: pytest.MonkeyPatch) -> None:
    assert run(["format"], mp, "﻿1024\r\n\r\n  \n2048\n") == 0
    assert capsys.readouterr().out == "1 KiB\n\n  \n2 KiB\n"
    assert run(["format", "--field", "2"], mp, "a 1024\n\n") == 0
    assert capsys.readouterr().out == "a 1 KiB\n\n"


def test_usage_errors_exit_2(capsys: pytest.CaptureFixture[str], mp: pytest.MonkeyPatch) -> None:
    for argv in (
        [],
        ["format", "--field", "0", "1"],
        ["format", "--system", "x", "1"],
        ["format", "--precision", "-1", "5"],
        ["format", "--unit", "XB", "5"],
        ["format", "--system", "iec", "--unit", "kB", "5"],
        ["format", "--bits", "--unit", "MiB", "5"],
    ):
        with pytest.raises(SystemExit) as caught:
            run(argv, mp)
        assert caught.value.code == 2
    assert "--unit 'XB' is not one of" in capsys.readouterr().err


def test_closed_pipe_is_quiet() -> None:
    reader = subprocess.Popen(
        [sys.executable, "-c", "import sys; sys.stdin.readline()"],
        stdin=subprocess.PIPE,
    )
    writer = subprocess.run(
        [sys.executable, "-m", "bytesz", "format"],
        input=b"".join(b"%d\n" % n for n in range(300_000)),
        stdout=reader.stdin,
        stderr=subprocess.PIPE,
        env={**os.environ, "PYTHONPATH": str(Path(bytesz.__file__).parents[1])},
        timeout=300,
    )
    assert reader.stdin is not None
    reader.stdin.close()
    reader.wait(timeout=60)
    assert writer.stderr == b""
    assert writer.returncode in (0, 1)


def test_help_and_version(capsys: pytest.CaptureFixture[str], mp: pytest.MonkeyPatch) -> None:
    with pytest.raises(SystemExit):
        run(["--help"], mp)
    out = capsys.readouterr().out
    assert "bytesz format 1572864" in out
    assert "--field" in out
    with pytest.raises(SystemExit):
        run(["--version"], mp)
    assert capsys.readouterr().out.strip() == f"bytesz {__version__}"


def test_python_dash_m_entry_point() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "bytesz", "format", "1048575"],
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, "PYTHONPATH": str(Path(bytesz.__file__).parents[1])},
    )
    assert result.stdout.strip() == "1 MiB"


@pytest.fixture
def mp(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    return monkeypatch
