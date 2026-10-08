"""Static scanner for leaked secrets in source trees."""

from __future__ import annotations

import re
from pathlib import Path

from .errors import ScanFinding

# name -> regex. Previews are truncated and never include the full match.
PATTERNS: dict[str, re.Pattern[str]] = {
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "aws_secret_key": re.compile(r"(?i)aws_secret_access_key\s*=\s*['\"]?[A-Za-z0-9/+=]{40}"),
    "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"),
    "generic_api_key": re.compile(r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"][A-Za-z0-9_\-]{20,}['\"]"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "jwt": re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    "slack_token": re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    "password_assignment": re.compile(r"(?i)password\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
}

_DEFAULT_IGNORE = {".git", ".venv", "venv", "node_modules", "__pycache__", ".mypy_cache", ".ruff_cache"}
_BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".zip", ".gz", ".so", ".pyc", ".ico"}


def scan_tree(root: str | Path, *, max_file_bytes: int = 1_000_000) -> list[ScanFinding]:
    """Walk a directory and return all secret-pattern findings."""
    root = Path(root)
    findings: list[ScanFinding] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in _DEFAULT_IGNORE for part in path.parts):
            continue
        if path.suffix.lower() in _BINARY_SUFFIXES:
            continue
        if path.stat().st_size > max_file_bytes:
            continue

        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for lineno, line in enumerate(text.splitlines(), 1):
            for name, pattern in PATTERNS.items():
                if pattern.search(line):
                    findings.append(
                        ScanFinding(
                            path=str(path),
                            line=lineno,
                            pattern=name,
                            preview=line.strip()[:60],
                        )
                    )
    return findings
