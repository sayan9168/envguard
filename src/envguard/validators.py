"""Type coercion and constraint validators.

All validators are pure functions: same input, same output, no side effects.
"""

from __future__ import annotations

import re
from typing import Any

_URL_RE = re.compile(
    r"^(?:[a-z][a-z0-9+.-]*)://"  # scheme
    r"(?:[^\s:@/]+(?::[^\s@/]*)?@)?"  # optional auth
    r"[A-Za-z0-9._~-]+"  # host
    r"(?::\d{1,5})?"  # optional port
    r"(?:/[^\s]*)?$"  # optional path
)
_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

_TRUE_TOKENS = {"1", "true", "yes", "on"}
_FALSE_TOKENS = {"0", "false", "no", "off"}


def coerce_str(value: str, **_constraints: Any) -> str:
    return value


def coerce_int(
    value: str,
    *,
    min_value: int | None = None,
    max_value: int | None = None,
    **_kw: Any,
) -> int:
    try:
        parsed = int(value, 10)
    except ValueError:
        raise ValueError(f"expected an integer, got {value!r}") from None
    if min_value is not None and parsed < min_value:
        raise ValueError(f"must be >= {min_value}, got {parsed}")
    if max_value is not None and parsed > max_value:
        raise ValueError(f"must be <= {max_value}, got {parsed}")
    return parsed


def coerce_float(
    value: str,
    *,
    min_value: float | None = None,
    max_value: float | None = None,
    **_kw: Any,
) -> float:
    try:
        parsed = float(value)
    except ValueError:
        raise ValueError(f"expected a number, got {value!r}") from None
    if min_value is not None and parsed < min_value:
        raise ValueError(f"must be >= {min_value}, got {parsed}")
    if max_value is not None and parsed > max_value:
        raise ValueError(f"must be <= {max_value}, got {parsed}")
    return parsed


def coerce_bool(value: str, **_kw: Any) -> bool:
    lowered = value.strip().lower()
    if lowered in _TRUE_TOKENS:
        return True
    if lowered in _FALSE_TOKENS:
        return False
    raise ValueError(
        f"expected a boolean ({'|'.join(sorted(_TRUE_TOKENS | _FALSE_TOKENS))}), got {value!r}"
    )


def coerce_url(value: str, **_kw: Any) -> str:
    if not _URL_RE.match(value):
        raise ValueError(f"expected a valid URL, got {value!r}")
    return value


def coerce_email(value: str, **_kw: Any) -> str:
    if not _EMAIL_RE.match(value):
        raise ValueError(f"expected a valid email address, got {value!r}")
    return value


def coerce_pattern(value: str, *, pattern: str, **_kw: Any) -> str:
    if not re.fullmatch(pattern, value):
        raise ValueError(f"must match pattern {pattern!r}, got {value!r}")
    return value


def make_enum_coercer(choices: list[str]):
    def coerce(value: str, **_kw: Any) -> str:
        if value not in choices:
            raise ValueError(f"must be one of {choices}, got {value!r}")
        return value

    return coerce


def make_list_coercer(item_type: str):
    item_coercer = {
        "str": coerce_str,
        "int": coerce_int,
        "float": coerce_float,
        "bool": coerce_bool,
    }.get(item_type)
    if item_coercer is None:
        raise ValueError(f"unsupported list item type: {item_type!r}")

    def coerce(value: str, **_kw: Any) -> list[Any]:
        if not value.strip():
            return []
        return [item_coercer(part.strip()) for part in value.split(",")]

    return coerce
