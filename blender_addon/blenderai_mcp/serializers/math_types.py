"""Serialize Blender math types to JSON-friendly lists."""

from __future__ import annotations

from typing import Any, Sequence


def serialize_vector(value: Sequence[float] | Any, size: int | None = None) -> list[float]:
    length = size if size is not None else len(value)
    return [float(value[i]) for i in range(length)]


def serialize_color(value: Sequence[float] | Any) -> list[float]:
    return [float(value[i]) for i in range(len(value))]


def serialize_euler(value: Any) -> list[float]:
    return [float(value.x), float(value.y), float(value.z)]


def serialize_quaternion(value: Any) -> list[float]:
    return [float(value.w), float(value.x), float(value.y), float(value.z)]


def serialize_matrix(value: Any) -> list[list[float]]:
    return [[float(cell) for cell in row] for row in value]


def parse_vector3(value: Any, default: tuple[float, float, float]) -> tuple[float, float, float]:
    if value is None:
        return default
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError("Expected a 3-element list for vector")
    return (float(value[0]), float(value[1]), float(value[2]))


def serialize_math_type(value: Any) -> list[float] | list[list[float]]:
    type_name = type(value).__name__
    if type_name == "Matrix":
        return serialize_matrix(value)
    if type_name == "Quaternion":
        return serialize_quaternion(value)
    if type_name == "Euler":
        return serialize_euler(value)
    if type_name in {"Vector", "Color"}:
        return serialize_vector(value)
    if hasattr(value, "__len__"):
        return serialize_vector(value)
    raise TypeError(f"Unsupported math type: {type_name}")
