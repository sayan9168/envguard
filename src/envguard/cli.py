"""Command-line interface: validate, snapshot, diff, scan, docs."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

from . import __version__
from .drift import diff_snapshot, take_snapshot
from .errors import EnvGuardError
from .scanner import scan_tree
from .schema import Schema


def _load_schema(module_path: str) -> Schema:
    """Import a Python file and return its top-level `schema` object."""
    path = Path(module_path)
    if not path.is_file():
        raise EnvGuardError(f"schema file not found: {path}")
    spec = importlib.util.spec_from_file_location("envguard_user_schema", path)
    if spec is None or spec.loader is None:
        raise EnvGuardError(f"cannot load schema module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    schema = getattr(module, "schema", None)
    if not isinstance(schema, Schema):
        raise EnvGuardError(f"{path} must define a top-level `schema = Schema({{...}})` object")
    return schema


def _emit(payload: object, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, default=str))
    else:
        print(payload)


def _cmd_validate(args: argparse.Namespace) -> int:
    schema = _load_schema(args.schema)
    config = schema.load(env_file=args.env_file)
    _emit(config.as_dict(), as_json=args.json)
    return 0


def _cmd_snapshot(args: argparse.Namespace) -> int:
    schema = _load_schema(args.schema)
    snap = take_snapshot(schema, args.out, env_file=args.env_file)
    _emit(f"Snapshot written to {args.out} ({len(snap['values'])} entries)" if not args.json else snap,
          as_json=args.json)
    return 0


def _cmd_diff(args: argparse.Namespace) -> int:
    schema = _load_schema(args.schema)
    report = diff_snapshot(schema, args.snapshot, env_file=args.env_file)
    _emit(report.to_dict() if args.json else report.render(), as_json=args.json)
    return 1 if report.has_drift else 0


def _cmd_scan(args: argparse.Namespace) -> int:
    findings = scan_tree(args.path)
    if args.json:
        _emit([f.__dict__ for f in findings], as_json=True)
    elif findings:
        for f in findings:
            print(f"{f.path}:{f.line}: [{f.pattern}] {f.preview}")
        print(f"\n{len(findings)} potential secret(s) found.")
    else:
        print("No leaked secrets found.")
    return 1 if findings else 0


def _cmd_docs(args: argparse.Namespace) -> int:
    schema = _load_schema(args.schema)
    lines = ["# Configuration Reference\n",
             "| Variable | Type | Required | Default | Secret | Description |",
             "|---|---|---|---|---|---|"]
    for name, f in schema.fields.items():
        lines.append(
            f"| `{name}` | {f.type} | {'yes' if f.required else 'no'} | "
            f"{f.default if f.default is not None else '—'} | "
            f"{'yes' if f.secret else 'no'} | {f.description or '—'} |"
        )
    output = "\n".join(lines)
    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"Docs written to {args.out}")
    else:
        print(output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envguard",
        description="Validate, snapshot, and audit environment configuration.",
    )
    parser.add_argument("--version", action="version", version=f"envguard {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--schema", required=True, help="Path to a Python file defining `schema`")
        p.add_argument("--env-file", default=None, help="Optional .env file")
        p.add_argument("--json", action="store_true", help="Machine-readable output")

    p = sub.add_parser("validate", help="Validate the current environment")
    common(p)
    p.set_defaults(func=_cmd_validate)

    p = sub.add_parser("snapshot", help="Write a redacted config snapshot")
    common(p)
    p.add_argument("--out", required=True, help="Snapshot output path")
    p.set_defaults(func=_cmd_snapshot)

    p = sub.add_parser("diff", help="Diff environment against a snapshot")
    common(p)
    p.add_argument("--snapshot", required=True, help="Snapshot file to compare against")
    p.set_defaults(func=_cmd_diff)

    p = sub.add_parser("scan", help="Scan a directory for leaked secrets")
    p.add_argument("--path", default=".", help="Directory to scan")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=_cmd_scan)

    p = sub.add_parser("docs", help="Generate Markdown config documentation")
    common(p)
    p.add_argument("--out", default=None, help="Output file (default: stdout)")
    p.set_defaults(func=_cmd_docs)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except EnvGuardError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
