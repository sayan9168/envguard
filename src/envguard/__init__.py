"""EnvGuard: production-grade environment configuration toolkit.

Public API:
    Schema, Field, EnvGuardError, ValidationError, MissingVariableError
"""

from .errors import EnvGuardError, MissingVariableError, ValidationError
from .schema import Field, Schema

__version__ = "1.0.0"
__all__ = [
    "Field",
    "Schema",
    "EnvGuardError",
    "ValidationError",
    "MissingVariableError",
]
