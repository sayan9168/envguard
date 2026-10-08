# Contributing to EnvGuard

Thanks for your interest in contributing. This document explains the workflow.

## Setup

```bash
git clone https://github.com/sayan9168/envguard.git
cd envguard
pip install -e ".[dev]"
make check   # lint + typecheck + tests — must pass before opening a PR
```

## Workflow

1. Fork the repository and create a branch from `main`:
   `git checkout -b feat/my-change` (or `fix/`, `docs/`, `chore/`).
2. Write tests for any behavioral change. We do not merge untested logic.
3. Keep commits small and imperative: `Add enum validation for list fields`.
4. Run `make check` locally, then open a pull request against `main`.
5. A maintainer will review within a few days. CI must be green to merge.

## Standards

- **Style**: enforced by Ruff (lint + format). No manual formatting debates.
- **Types**: the codebase is `mypy --strict` clean. New code must be too.
- **Dependencies**: the runtime package stays dependency-free. Dev tools only in `[dev]`.
- **Commits**: follow [Conventional Commits](https://www.conventionalcommits.org/) where practical.

## Reporting Bugs

Open an issue using the bug template. Include:
- Python version and OS
- A minimal schema/config that reproduces the problem
- Expected vs. actual behavior

## Security Issues

Do **not** open public issues for vulnerabilities. See [SECURITY.md](SECURITY.md).
