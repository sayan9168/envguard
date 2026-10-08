# EnvGuard

[![CI](https://github.com/sayan9168/envguard/actions/workflows/ci.yml/badge.svg)](https://github.com/sayan9168/envguard/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

**EnvGuard** is a production-grade toolkit for validating, securing, and monitoring environment configuration. It catches missing variables, type mismatches, leaked secrets, and configuration drift *before* they take your service down at 3 AM.

## Why EnvGuard?

Most production outages traced to configuration share three root causes:

1. **Untyped env vars** — everything is a string until it explodes at runtime.
2. **Silent drift** — staging and production configs diverge and nobody notices.
3. **Secret leakage** — API keys accidentally committed, logged, or dumped in error reports.

EnvGuard solves all three with a declarative schema, deterministic validation, drift snapshots, and built-in secret redaction.

## Features

- **Declarative schemas** — define type, default, required/optional, regex, and choices per variable
- **Type coercion & validation** — `str`, `int`, `float`, `bool`, `url`, `email`, `enum`, `list[T]`
- **Secret redaction** — sensitive values are masked in logs, reports, and exception messages
- **Drift detection** — snapshot a known-good config and diff any environment against it
- **Multiple sources** — process env, `.env` files, and JSON config with layered precedence
- **Fail-fast CLI** — `envguard validate`, `envguard snapshot`, `envguard diff` for CI gates
- **Zero runtime dependencies** — pure stdlib, ships as a single pip package
- **Typed config object** — attribute access with static typing via `TypedDict` protocol

## Installation

```bash
pip install envguard
```

From source:

```bash
git clone https://github.com/sayan9168/envguard.git
cd envguard
pip install -e ".[dev]"
```

## Quick Start

### 1. Define a schema

```python
from envguard import Schema, Field

schema = Schema({
    "DATABASE_URL": Field.url(required=True, secret=True),
    "PORT": Field.int(default=8000, min_value=1, max_value=65535),
    "DEBUG": Field.bool(default=False),
    "LOG_LEVEL": Field.enum(["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO"),
    "ALLOWED_HOSTS": Field.list_of("str", default=["localhost"]),
    "SUPPORT_EMAIL": Field.email(required=True),
})
```

### 2. Validate at startup

```python
config = schema.load()  # raises EnvGuardError on any violation

print(config.PORT)          # 8000 (int, not str)
print(config.DATABASE_URL)  # "postgresql://****" in logs, raw value in memory
```

### 3. Detect drift

```bash
# Snapshot a known-good environment
envguard snapshot --schema schema.py --out snapshots/production.json

# In CI or on deploy, fail if anything drifted
envguard diff --snapshot snapshots/production.json
```

```text
DRIFT DETECTED (2 changed, 1 added, 1 removed)
  ~ LOG_LEVEL        "INFO" -> "DEBUG"
  ~ MAX_CONNECTIONS  "50" -> "500"
  + NEW_FLAG         (not in snapshot)
  - LEGACY_TIMEOUT   (missing from environment)
```

### 4. Gate your CI pipeline

```yaml
- name: Validate environment
  run: envguard validate --schema config/schema.py --strict
```

## Precedence Model

Values are resolved in order (highest wins):

1. Process environment (`os.environ`)
2. Explicit overrides passed to `Schema.load(overrides={...})`
3. `.env` file (if configured)
4. Schema defaults

## Security Model

- Fields marked `secret=True` are **never** rendered in logs, diffs, or tracebacks — only `****`.
- `envguard scan` performs static analysis over your repo to detect hardcoded secret patterns (AWS keys, JWTs, private keys, and 20+ more signatures).
- Drift snapshots hash secret values (SHA-256) instead of storing them in plaintext.

See [SECURITY.md](SECURITY.md) for the threat model and disclosure policy.

## CLI Reference

| Command | Description |
|---|---|
| `envguard validate` | Validate the current environment against a schema |
| `envguard snapshot` | Capture a redacted snapshot of resolved config |
| `envguard diff` | Compare environment against a snapshot |
| `envguard scan` | Scan the repository for leaked secrets |
| `envguard docs` | Generate Markdown config documentation from a schema |

Every command supports `--json` for machine-readable output.

## Project Structure

```text
envguard/
├── src/envguard/
│   ├── schema.py       # Declarative schema + field types
│   ├── loader.py       # Layered source resolution
│   ├── validators.py   # Type coercion and constraint checks
│   ├── drift.py        # Snapshot capture and diff engine
│   ├── scanner.py      # Secret-pattern static scanner
│   ├── errors.py       # Structured exception hierarchy
│   └── cli.py          # argparse-based CLI entrypoint
├── tests/              # pytest suite (unit + integration)
├── .github/workflows/  # CI: lint, typecheck, test matrix, release
├── docs/               # Generated config docs + guides
└── examples/           # Real-world usage examples
```

## Development

```bash
pip install -e ".[dev]"

make lint        # ruff + mypy
make test        # pytest with coverage
make check       # everything CI runs, locally
```

Requires Python 3.10+.

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).

## License

[MIT](LICENSE) © 2026 Sayan Mahata
