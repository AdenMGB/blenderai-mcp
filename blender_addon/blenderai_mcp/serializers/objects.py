"""Object serialization."""

from __future__ import annotations

import bpy
from mathutils import Vector

from .math_types import serialize_matrix, serialize_vector


def compute_bounds(obj: bpy.types.Object) -> dict[str, list[float]]:
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    mins = [
        min(corner.x for corner in corners),
        min(corner.y for corner in corners),
        min(corner.z for corner in corners),
    ]
    maxs = [
        max(corner.x for corner in corners),
        max(corner.y for corner in corners),
        max(corner.z for corner in corners),
    ]
    return {
        "min": [float(v) for v in mins],
        "max": [float(v) for v in maxs],
        "center": [float((mins[i] + maxs[i]) / 2) for i in range(3)],
    }


def serialize_object(obj: bpy.types.Object, include_mesh: bool = False) -> dict:
    data: dict = {
        "name": obj.name,
        "uuid": str(obj.session_uid),
        "type": obj.type,
        "location": serialize_vector(obj.location, 3),
        "rotation_euler": serialize_vector(obj.rotation_euler, 3),
        "scale": serialize_vector(obj.scale, 3),
        "dimensions": serialize_vector(obj.dimensions, 3),
        "bounds": compute_bounds(obj),
        "rotation_mode": obj.rotation_mode,
        "visible": obj.visible_get(),
        "matrix_world": serialize_matrix(obj.matrix_world),
        "parent": obj.parent.name if obj.parent else None,
        "collections": [collection.name for collection in obj.users_collection],
    }

    if obj.type == "MESH" and include_mesh and obj.data:
        mesh: bpy.types.Mesh = obj.data
        data["mesh"] = {
            "vertices": len(mesh.vertices),
            "edges": len(mesh.edges),
            "polygons": len(mesh.polygons),
        }

    materials = []
    if obj.type == "MESH" and obj.data:
        for slot in obj.material_slots:
            materials.append(slot.material.name if slot.material else None)
    data["materials"] = materials

    return data
