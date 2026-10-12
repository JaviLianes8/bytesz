# Local quality gate. Run before every commit. No CI runs in the cloud.
$ErrorActionPreference = "Stop"

ruff format --check .
ruff check .
mypy --strict src tests
pytest
python scripts/e2e_wheel.py
