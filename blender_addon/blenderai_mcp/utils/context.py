"""Blender context helpers."""

from __future__ import annotations

import bpy
from contextlib import contextmanager
from typing import Iterator


def get_scene() -> bpy.types.Scene:
    return bpy.context.scene


def require_scene() -> bpy.types.Scene:
    scene = get_scene()
    if scene is None:
        raise RuntimeError("No active scene in context")
    return scene


def get_view_layer() -> bpy.types.ViewLayer:
    return bpy.context.view_layer


def find_object(name: str) -> bpy.types.Object | None:
    return bpy.data.objects.get(name)


def require_object(name: str) -> bpy.types.Object:
    obj = find_object(name)
    if obj is None:
        raise LookupError(f"Object '{name}' not found")
    return obj


def require_mesh_object(name: str) -> bpy.types.Object:
    obj = require_object(name)
    if obj.type != "MESH" or obj.data is None:
        raise ValueError(f"Object '{name}' is not a mesh")
    return obj


def find_collection(name: str) -> bpy.types.Collection | None:
    return bpy.data.collections.get(name)


def require_collection(name: str) -> bpy.types.Collection:
    coll = find_collection(name)
    if coll is None:
        raise LookupError(f"Collection '{name}' not found")
    return coll


def find_material(name: str) -> bpy.types.Material | None:
    return bpy.data.materials.get(name)


def push_undo(message: str = "BlenderAI") -> None:
    bpy.ops.ed.undo_push(message=message)


@contextmanager
def temp_override(**kwargs) -> Iterator[None]:
    """Wrapper around bpy.context.temp_override for ops."""
    with bpy.context.temp_override(**kwargs):
        yield
