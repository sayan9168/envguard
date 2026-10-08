"""Declarative schema definition and the resolved typed config object."""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Any, Callable

from . import validators
from .errors import FieldViolation, MissingVariableError, ValidationError

REDACTED = "****"


@dataclass(frozen=True)
class Field:
    """Definition of a single environment variable.

    Attributes:
        type: Logical type name used by the loader to pick a coercer.
        required: If True and no source provides a value, loading fails.
        default: Fallback value (already coerced, or a raw string).
        secret: If True, the value is redacted everywhere outside memory.
        description: Human-readable documentation for generated docs.
        constraints: Extra keyword constraints passed to the coercer.
    """

    type: str = "str"
    required: bool = False
    default: Any = None
    secret: bool = False
    description: str = ""
    constraints: dict[str, Any] = dc_field(default_factory=dict)
    _coercer: Callable[..., Any] | None = dc_field(default=None, repr=False, compare=False)

    # ---- fluent constructors -------------------------------------------------
    @classmethod
    def str(cls, **kw: Any) -> "Field":
        return cls(type="str", _coercer=validators.coerce_str, **kw)

    @classmethod
    def int(cls, **kw: Any) -> "Field":
        return cls(type="int", _coercer=validators.coerce_int, **kw)

    @classmethod
    def float(cls, **kw: Any) -> "Field":
        return cls(type="float", _coercer=validators.coerce_float, **kw)

    @classmethod
    def bool(cls, **kw: Any) -> "Field":
        return cls(type="bool", _coercer=validators.coerce_bool, **kw)

    @classmethod
    def url(cls, **kw: Any) -> "Field":
        return cls(type="url", _coercer=validators.coerce_url, **kw)

    @classmethod
    def email(cls, **kw: Any) -> "Field":
        return cls(type="email", _coercer=validators.coerce_email, **kw)

    @classmethod
    def pattern(cls, regex: str, **kw: Any) -> "Field":
        constraints = dict(kw.pop("constraints", {}) or {})
        constraints["pattern"] = regex
        return cls(type="pattern", constraints=constraints, _coercer=validators.coerce_pattern, **kw)

    @classmethod
    def enum(cls, choices: list[str], **kw: Any) -> "Field":
        return cls(type="enum", constraints={"choices": choices},
                   _coercer=validators.make_enum_coercer(choices), **kw)

    @classmethod
    def list_of(cls, item_type: str, **kw: Any) -> "Field":
        return cls(type=f"list[{item_type}]",
                   _coercer=validators.make_list_coercer(item_type), **kw)


class Config:
    """Resolved, validated, immutable configuration with attribute access."""

    __slots__ = ("_values", "_secrets")

    def __init__(self, values: dict[str, Any], secrets: set[str]) -> None:
        object.__setattr__(self, "_values", values)
        object.__setattr__(self, "_secrets", secrets)

    def __getattr__(self, name: str) -> Any:
        try:
            return self._values[name]
        except KeyError:
            raise AttributeError(name) from None

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("Config is immutable")

    def as_dict(self, *, redact_secrets: bool = True) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in self._values.items():
            if redact_secrets and key in self._secrets:
                out[key] = REDACTED
            else:
                out[key] = value
        return out

    def __repr__(self) -> str:
        return f"Config({self.as_dict()!r})"


class Schema:
    """A named collection of fields that can load and validate an environment."""

    def __init__(self, fields: dict[str, Field]) -> None:
        if not fields:
            raise ValueError("Schema must define at least one field")
        self.fields = fields

    def load(
        self,
        env: dict[str, str] | None = None,
        overrides: dict[str, str] | None = None,
        env_file: str | None = None,
    ) -> Config:
        """Resolve all fields and return a typed Config.

        Precedence: env > overrides > env_file > default.
        """
        from .loader import parse_env_file

        file_values: dict[str, str] = parse_env_file(env_file) if env_file else {}
        overrides = overrides or {}

        import os
        env = dict(os.environ if env is None else env)

        resolved: dict[str, Any] = {}
        secrets: set[str] = set()
        violations: list[FieldViolation] = []

        for name, fld in self.fields.items():
            raw = env.get(name) or overrides.get(name) or file_values.get(name)

            if raw is None:
                if fld.default is not None:
                    resolved[name] = fld.default
                    continue
                if fld.required:
                    violations.append(
                        FieldViolation(name, "required variable is not set")
                    )
                    continue
                resolved[name] = None
                continue

            try:
                coercer = fld._coercer or validators.coerce_str
                resolved[name] = coercer(raw, **fld.constraints)
            except ValueError as exc:
                violations.append(FieldViolation(name, str(exc)))

            if fld.secret:
                secrets.add(name)

        if violations:
            raise ValidationError(violations)
        return Config(resolved, secrets)

    def require(self, name: str) -> str:
        """Convenience accessor: return one required raw variable or raise."""
        import os
        value = os.environ.get(name)
        if value is None:
            raise MissingVariableError(name)
        return value
