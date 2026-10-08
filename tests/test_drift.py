import json

from envguard import Field, Schema
from envguard.drift import diff_snapshot, take_snapshot


def make_schema() -> Schema:
    return Schema({
        "MODE": Field.enum(["a", "b"], default="a"),
        "KEY": Field.str(required=True, secret=True),
    })


def test_snapshot_hashes_secrets(tmp_path):
    out = tmp_path / "snap.json"
    take_snapshot(make_schema(), out, env={}, overrides={"KEY": "plainsecret"})
    data = json.loads(out.read_text())
    assert data["values"]["KEY"].startswith("sha256:")
    assert "plainsecret" not in out.read_text()


def test_no_drift(tmp_path):
    out = tmp_path / "snap.json"
    schema = make_schema()
    take_snapshot(schema, out, env={}, overrides={"KEY": "k"})
    report = diff_snapshot(schema, out, env={}, overrides={"KEY": "k"})
    assert not report.has_drift


def test_drift_detected(tmp_path):
    out = tmp_path / "snap.json"
    schema = make_schema()
    take_snapshot(schema, out, env={"MODE": "a"}, overrides={"KEY": "k"})
    report = diff_snapshot(schema, out, env={"MODE": "b"}, overrides={"KEY": "different"})
    assert report.has_drift
    assert "MODE" in report.changed
    assert "KEY" in report.changed  # hash mismatch
