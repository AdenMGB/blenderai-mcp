"""Object lifecycle handlers."""

from __future__ import annotations

import bpy
import bmesh

from ..serializers.math_types import parse_vector3
from ..serializers.objects import serialize_object
from ..utils import context

PRIMITIVE_TYPES = frozenset(
    {"cube", "uv_sphere", "sphere", "cylinder", "cone", "plane", "torus"}
)


def _build_primitive_mesh(primitive: str, mesh_name: str) -> bpy.types.Mesh:
    bm = bmesh.new()
    try:
        if primitive in {"cube"}:
            bmesh.ops.create_cube(bm, size=1.0)
        elif primitive in {"uv_sphere", "sphere"}:
            bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=0.5)
        elif primitive == "cylinder":
            bmesh.ops.create_cone(
                bm,
                cap_ends=True,
                cap_tris=False,
                segments=32,
                radius1=0.5,
                radius2=0.5,
                depth=1.0,
            )
        elif primitive == "cone":
            bmesh.ops.create_cone(
                bm,
                cap_ends=True,
                cap_tris=False,
                segments=32,
                radius1=0.5,
                radius2=0.0,
                depth=1.0,
            )
        elif primitive == "plane":
            bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.0)
        elif primitive == "torus":
            bmesh.ops.create_torus(
                bm,
                major_segments=48,
                minor_segments=12,
                major_radius=0.5,
                minor_radius=0.25,
            )
        else:
            raise ValueError(f"Unsupported primitive: {primitive}")

        mesh = bpy.data.meshes.new(mesh_name)
        bm.to_mesh(mesh)
        mesh.update()
        return mesh
    finally:
        bm.free()


def _link_object(obj: bpy.types.Object, collection_name: str | None) -> None:
    if collection_name:
        coll = context.require_collection(collection_name)
        coll.objects.link(obj)
    else:
        context.get_scene().collection.objects.link(obj)


def object_create_primitive(params: dict) -> dict:
    primitive = (params.get("primitive") or params.get("type") or "cube").lower()
    if primitive not in PRIMITIVE_TYPES:
        raise ValueError(
            f"Invalid primitive '{primitive}'. "
            f"Valid: {', '.join(sorted(PRIMITIVE_TYPES))}"
        )

    name = params.get("name") or primitive.capitalize()
    location = parse_vector3(params.get("location"), (0.0, 0.0, 0.0))
    scale = parse_vector3(params.get("scale"), (1.0, 1.0, 1.0))
    collection_name = params.get("collection")

    context.push_undo("BlenderAI: Create Primitive")

    mesh = _build_primitive_mesh(primitive, name)
    mesh.name = name
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    obj.scale = scale
    _link_object(obj, collection_name)

    result = serialize_object(obj)
    result["primitive"] = primitive
    return result


def object_delete(params: dict) -> dict:
    name = params.get("name")
    if not name:
        raise ValueError("name is required")

    obj = context.require_object(name)
    context.push_undo("BlenderAI: Delete Object")

    data = obj.data
    bpy.data.objects.remove(obj, do_unlink=True)
    if data and data.users == 0:
        if isinstance(data, bpy.types.Mesh):
            bpy.data.meshes.remove(data)
        elif isinstance(data, bpy.types.Curve):
            bpy.data.curves.remove(data)

    return {"deleted": name}


def object_rename(params: dict) -> dict:
    name = params.get("name")
    new_name = params.get("new_name")
    if not name or not new_name:
        raise ValueError("name and new_name are required")

    obj = context.require_object(name)
    context.push_undo("BlenderAI: Rename Object")
    obj.name = new_name
    if obj.data:
        obj.data.name = new_name
    return serialize_object(obj)


def object_set_transform(params: dict) -> dict:
    name = params.get("name")
    if not name:
        raise ValueError("name is required")

    obj = context.require_object(name)
    context.push_undo("BlenderAI: Set Transform")

    if "location" in params:
        obj.location = parse_vector3(params["location"], tuple(obj.location))
    if "rotation_euler" in params:
        obj.rotation_euler = parse_vector3(params["rotation_euler"], tuple(obj.rotation_euler))
    if "rotation_mode" in params:
        obj.rotation_mode = str(params["rotation_mode"])
    if "scale" in params:
        obj.scale = parse_vector3(params["scale"], tuple(obj.scale))

    return serialize_object(obj)


def object_get(params: dict) -> dict:
    name = params.get("name")
    if not name:
        raise ValueError("name is required")
    obj = context.require_object(name)
    include_mesh = bool(params.get("include_mesh", False))
    return serialize_object(obj, include_mesh=include_mesh)


def object_duplicate(params: dict) -> dict:
    name = params.get("name")
    if not name:
        raise ValueError("name is required")

    obj = context.require_object(name)
    context.push_undo("BlenderAI: Duplicate Object")

    new_obj = obj.copy()
    if obj.data is not None:
        new_obj.data = obj.data.copy()

    new_name = params.get("new_name")
    if new_name:
        new_obj.name = new_name

    for coll in obj.users_collection:
        coll.objects.link(new_obj)

    return {"object": serialize_object(new_obj), "source": name}


def object_set_parent(params: dict) -> dict:
    name = params.get("name") or params.get("object")
    if not name:
        raise ValueError("name is required")

    obj = context.require_object(name)
    parent_name = params.get("parent")
    keep_transform = bool(params.get("keep_transform", True))

    context.push_undo("BlenderAI: Set Parent")

    if not parent_name:
        if keep_transform:
            matrix_world = obj.matrix_world.copy()
            obj.parent = None
            obj.matrix_world = matrix_world
        else:
            obj.parent = None
    else:
        parent = context.require_object(parent_name)
        if parent == obj:
            raise ValueError("Object cannot be parented to itself")
        if keep_transform:
            world_matrix = obj.matrix_world.copy()
            obj.parent = parent
            obj.matrix_world = world_matrix
        else:
            obj.parent = parent

    return serialize_object(obj)


def register() -> None:
    from .registry import register_handler

    register_handler("object_create_primitive", object_create_primitive, mutating=True)
    register_handler("object_delete", object_delete, mutating=True)
    register_handler("object_rename", object_rename, mutating=True)
    register_handler("object_set_transform", object_set_transform, mutating=True)
    register_handler("object_get", object_get)
    register_handler("object_duplicate", object_duplicate, mutating=True)
    register_handler("object_set_parent", object_set_parent, mutating=True)
