"""RNA property serialization helpers (Phase 0 stubs)."""

from __future__ import annotations

from typing import Any

from .math_types import serialize_math_type


def serialize_rna_value(value: Any) -> Any:
    """Convert a simple RNA property value to JSON-safe data."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [serialize_rna_value(item) for item in value]
    type_name = type(value).__name__
    if type_name in {"Vector", "Color", "Euler", "Quaternion", "Matrix"}:
        return serialize_math_type(value)
    return str(value)
