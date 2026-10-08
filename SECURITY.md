# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| 1.x | Yes |
| < 1.0 | No |

## Reporting a Vulnerability

Please report vulnerabilities privately via GitHub Security Advisories:
https://github.com/sayan9168/envguard/security/advisories/new

Do not open public issues for security problems. You can expect:
- Acknowledgement within 72 hours
- A remediation plan within 14 days for confirmed issues
- Credit in the release notes (unless you prefer anonymity)

## Threat Model

EnvGuard is designed around three security guarantees:

1. **Secret values are never persisted in plaintext.** Drift snapshots store
   SHA-256 hashes of fields marked `secret=True`; plaintext never touches disk.
2. **Secret values are never rendered.** Logs, CLI output, diffs, and exception
   messages mask secrets as `****`.
3. **Validation is deterministic.** No network access, no dynamic imports of
   config, no code execution during validation — schema files are the only
   user code executed, and only when explicitly loaded by the operator.

If any of these guarantees can be violated, that is a security issue — report it.
