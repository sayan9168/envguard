"""Layered source loading: process env, overrides, and .env files."""

from __future__ import annotations

from pathlib import Path


def parse_env_file(path: str | Path) -> dict[str, str]:
    """Parse a .env file into a dict.

    Supports comments, blank lines, `export` prefixes, and quoted values.
    "quotes" are stripped but not interpolated — no shell evaluation, ever.
    """
    values: dict[str, str] = {}
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f".env file not found: {file_path}")

    for lineno, line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        if "=" not in line:
            raise ValueError(f"{file_path}:{lineno}: malformed line (expected KEY=VALUE)")
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        values[key] = value
    return values
