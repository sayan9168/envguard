"""Drift detection: snapshot a known-good config, diff later environments.

Secret values are stored as SHA-256 hashes, never plaintext.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .schema import Schema

SNAPSHOT_FORMAT = "envguard/v1"


def _hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(str(value).encode()).hexdigest()


def take_snapshot(schema: Schema, path: str | Path, **load_kwargs: Any) -> dict[str, Any]:
    """Resolve the current environment and write a redacted snapshot."""
    config = schema.load(**load_kwargs)
    secrets = config._secrets  # intentional: internal build of snapshot
    values = {
        key: (_hash(val) if key in secrets and val is not None else val)
        for key, val in config._values.items()
    }
    snapshot = {"format": SNAPSHOT_FORMAT, "values": values}
    Path(path).write_text(json.dumps(snapshot, indent=2, sort_keys=True), encoding="utf-8")
    return snapshot


@dataclass
class DriftReport:
    changed: dict[str, tuple[Any, Any]] = field(default_factory=dict)
    added: dict[str, Any] = field(default_factory=dict)
    removed: dict[str, Any] = field(default_factory=dict)

    @property
    def has_drift(self) -> bool:
        return bool(self.changed or self.added or self.removed)

    def to_dict(self) -> dict[str, Any]:
        return {
            "changed": {k: {"old": a, "new": b} for k, (a, b) in self.changed.items()},
            "added": self.added,
            "removed": self.removed,
            "has_drift": self.has_drift,
        }

    def render(self) -> str:
        if not self.has_drift:
            return "No drift detected."
        lines = [
            f"DRIFT DETECTED ({len(self.changed)} changed, "
            f"{len(self.added)} added, {len(self.removed)} removed)"
        ]
        for key, (old, new) in sorted(self.changed.items()):
            lines.append(f"  ~ {key}: {old!r} -> {new!r}")
        for key in sorted(self.added):
            lines.append(f"  + {key} (not in snapshot)")
        for key in sorted(self.removed):
            lines.append(f"  - {key} (missing from environment)")
        return "\n".join(lines)


def diff_snapshot(schema: Schema, snapshot_path: str | Path, **load_kwargs: Any) -> DriftReport:
    """Compare the current environment against a stored snapshot."""
    raw = json.loads(Path(snapshot_path).read_text(encoding="utf-8"))
    if raw.get("format") != SNAPSHOT_FORMAT:
        raise ValueError(f"Unsupported snapshot format: {raw.get('format')!r}")
    old: dict[str, Any] = raw["values"]

    config = schema.load(**load_kwargs)
    new = {
        key: (_hash(val) if key in config._secrets and val is not None else val)
        for key, val in config._values.items()
    }

    report = DriftReport()
    for key in old.keys() | new.keys():
        in_old, in_new = key in old, key in new
        if in_old and not in_new:
            report.removed[key] = old[key]
        elif in_new and not in_old:
            report.added[key] = new[key]
        elif old[key] != new[key]:
            report.changed[key] = (old[key], new[key])
    return report
