"""Structured exception hierarchy for EnvGuard.

Every error carries machine-readable context so CI pipelines can parse
failures without scraping log text.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class EnvGuardError(Exception):
    """Base class for all EnvGuard errors."""


@dataclass
class FieldViolation:
    """A single failed constraint on a single field."""

    name: str
    message: str
    expected: Any = None


class ValidationError(EnvGuardError):
    """Raised when one or more fields fail validation."""

    def __init__(self, violations: list[FieldViolation]) -> None:
        self.violations = violations
        lines = [f"  - {v.name}: {v.message}" for v in violations]
        super().__init__(
            f"Environment validation failed ({len(violations)} violation(s)):\n"
            + "\n".join(lines)
        )


class MissingVariableError(EnvGuardError):
    """Raised when a required variable has no value from any source."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Required environment variable '{name}' is not set")


class SchemaLoadError(EnvGuardError):
    """Raised when a schema module cannot be imported or is malformed."""


@dataclass
class ScanFinding:
    """A potential leaked secret found by the static scanner."""

    path: str
    line: int
    pattern: str
    preview: str = field(repr=False, default="")
