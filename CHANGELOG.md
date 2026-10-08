# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-08

### Added
- Declarative `Schema` / `Field` API with typed fields (`str`, `int`, `float`, `bool`, `url`, `email`, `enum`, `list_of`)
- Layered source resolution: environment > overrides > `.env` file > schema defaults
- Secret redaction in logs, diffs, and tracebacks
- Drift snapshots with SHA-256 hashing of secret values
- `envguard diff` engine with added/removed/changed classification
- Static secret scanner with 20+ signature patterns
- CLI: `validate`, `snapshot`, `diff`, `scan`, `docs` (all with `--json` output)
- Full test suite, CI pipeline, and contributor documentation
