"""Mesh editing handlers using bmesh."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import bmesh
import bpy

from ..serializers.math_types import parse_vector3, serialize_vector
from ..utils import context
from .registry import register_handler

DEFAULT_MAX_VERTS = 5000
DEFAULT_MAX_FACES = 5000


def _bounds_from_coords(coords: list[tuple[float, float, float]]) -> dict[str, list[float]]:
    if not coords:
        return {"min": [0.0, 0.0, 0.0], "max": [0.0, 0.0, 0.0]}
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    zs = [c[2] for c in coords]
    return {
        "min": [min(xs), min(ys), min(zs)],
        "max": [max(xs), max(ys), max(zs)],
    }


def _bounds_from_mesh(mesh: bpy.types.Mesh) -> dict[str, list[float]]:
    if not mesh.vertices:
        return {"min": [0.0, 0.0, 0.0], "max": [0.0, 0.0, 0.0]}
    coords = [(v.co.x, v.co.y, v.co.z) for v in mesh.vertices]
    return _bounds_from_coords(coords)


def _mesh_summary(mesh: bpy.types.Mesh, obj_name: str | None = None) -> dict[str, Any]:
    return {
        "object": obj_name,
        "vertex_count": len(mesh.vertices),
        "face_count": len(mesh.polygons),
        "edge_count": len(mesh.edges),
        "bounds": _bounds_from_mesh(mesh),
    }


@contextmanager
def _bmesh_session(obj: bpy.types.Object, mesh: bpy.types.Mesh) -> Iterator[bmesh.types.BMesh]:
    """Load mesh into bmesh, apply edits, write back. Handles object and edit mode."""
    in_edit = obj.mode == "EDIT"
    if in_edit:
        bm = bmesh.from_edit_mesh(mesh)
        bm.faces.ensure_lookup_table()
        bm.verts.ensure_lookup_table()
        try:
            yield bm
            bmesh.update_edit_mesh(mesh, loop_triangles=True, destructive=True)
        finally:
            pass
    else:
        bm = bmesh.new()
        try:
            bm.from_mesh(mesh)
            bm.faces.ensure_lookup_table()
            bm.verts.ensure_lookup_table()
            yield bm
            bm.to_mesh(mesh)
            mesh.update()
        finally:
            bm.free()


def mesh_create_from_verts_faces(params: dict[str, Any]) -> dict[str, Any]:
    vertices = params.get("vertices")
    faces = params.get("faces")
    if not vertices or not isinstance(vertices, list):
        raise ValueError("vertices must be a non-empty list of [x, y, z]")
    if not faces or not isinstance(faces, list):
        raise ValueError("faces must be a non-empty list of vertex index lists")

    name = params.get("name") or "Mesh"
    collection_name = params.get("collection")

    mesh = bpy.data.meshes.new(name)
    vert_coords = [parse_vector3(v, (0.0, 0.0, 0.0)) for v in vertices]
    mesh.from_pydata(vert_coords, [], [tuple(int(i) for i in face) for face in faces])
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    if collection_name:
        coll = bpy.data.collections.get(collection_name)
        if coll is None:
            raise LookupError(f"Collection '{collection_name}' not found")
        coll.objects.link(obj)
    else:
        context.require_scene().collection.objects.link(obj)

    return _mesh_summary(mesh, obj.name)


def mesh_get_geometry(params: dict[str, Any]) -> dict[str, Any]:
    obj = context.require_mesh_object(params["object"])
    mesh: bpy.types.Mesh = obj.data

    vert_offset = int(params.get("vert_offset", 0))
    face_offset = int(params.get("face_offset", 0))
    max_verts = int(params.get("max_verts", DEFAULT_MAX_VERTS))
    max_faces = int(params.get("max_faces", DEFAULT_MAX_FACES))

    if vert_offset < 0 or face_offset < 0:
        raise ValueError("vert_offset and face_offset must be >= 0")
    if max_verts < 0 or max_faces < 0:
        raise ValueError("max_verts and max_faces must be >= 0")

    total_verts = len(mesh.vertices)
    total_faces = len(mesh.polygons)

    vert_end = min(vert_offset + max_verts, total_verts)
    face_end = min(face_offset + max_faces, total_faces)

    vertices = [
        serialize_vector(mesh.vertices[i].co, 3)
        for i in range(vert_offset, vert_end)
    ]
    faces = [
        [int(v) for v in mesh.polygons[i].vertices]
        for i in range(face_offset, face_end)
    ]

    result = _mesh_summary(mesh, obj.name)
    result.update(
        {
            "vertices": vertices,
            "faces": faces,
            "vert_offset": vert_offset,
            "face_offset": face_offset,
            "verts_returned": len(vertices),
            "faces_returned": len(faces),
            "has_more_verts": vert_end < total_verts,
            "has_more_faces": face_end < total_faces,
            "next_vert_offset": vert_end if vert_end < total_verts else None,
            "next_face_offset": face_end if face_end < total_faces else None,
        }
    )
    return result


def mesh_set_vertices(params: dict[str, Any]) -> dict[str, Any]:
    obj = context.require_mesh_object(params["object"])
    mesh: bpy.types.Mesh = obj.data
    updates = params.get("vertices")
    if not updates or not isinstance(updates, list):
        raise ValueError("vertices must be a non-empty list of {index, co}")

    with _bmesh_session(obj, mesh) as bm:
        for item in updates:
            if not isinstance(item, dict):
                raise ValueError("Each vertex update must be an object with index and co")
            index = int(item["index"])
            co = parse_vector3(item.get("co") or item.get("position"), (0.0, 0.0, 0.0))
            if index < 0 or index >= len(bm.verts):
                raise ValueError(f"Vertex index {index} out of range")
            bm.verts[index].co = co

    return _mesh_summary(mesh, obj.name)


def mesh_extrude_region(params: dict[str, Any]) -> dict[str, Any]:
    obj = context.require_mesh_object(params["object"])
    mesh: bpy.types.Mesh = obj.data
    face_indices = params.get("face_indices") or params.get("faces")
    if not face_indices or not isinstance(face_indices, list):
        raise ValueError("face_indices must be a non-empty list of face indices")

    offset = parse_vector3(params.get("offset"), (0.0, 0.0, 1.0))
    extruded_faces = 0

    with _bmesh_session(obj, mesh) as bm:
        selected = []
        for idx in face_indices:
            face_idx = int(idx)
            if face_idx < 0 or face_idx >= len(bm.faces):
                raise ValueError(f"Face index {face_idx} out of range")
            selected.append(bm.faces[face_idx])

        result = bmesh.ops.extrude_face_region(bm, geom=selected)
        new_geom = result.get("geom", [])
        verts_moved = [g for g in new_geom if isinstance(g, bmesh.types.BMVert)]
        if verts_moved:
            bmesh.ops.translate(bm, vec=offset, verts=verts_moved)
        extruded_faces = len(selected)

    summary = _mesh_summary(mesh, obj.name)
    summary["extruded_faces"] = extruded_faces
    return summary


def mesh_subdivide(params: dict[str, Any]) -> dict[str, Any]:
    obj = context.require_mesh_object(params["object"])
    mesh: bpy.types.Mesh = obj.data
    cuts = int(params.get("cuts", 1))
    if cuts < 1:
        raise ValueError("cuts must be >= 1")

    face_indices = params.get("face_indices")
    with _bmesh_session(obj, mesh) as bm:
        if face_indices:
            geom = []
            for idx in face_indices:
                face_idx = int(idx)
                if face_idx < 0 or face_idx >= len(bm.faces):
                    raise ValueError(f"Face index {face_idx} out of range")
                geom.append(bm.faces[face_idx])
        else:
            geom = list(bm.faces)

        bmesh.ops.subdivide_edges(
            bm,
            edges=[e for f in geom for e in f.edges],
            cuts=cuts,
            use_grid_fill=True,
        )

    return _mesh_summary(mesh, obj.name)


def mesh_merge_vertices(params: dict[str, Any]) -> dict[str, Any]:
    obj = context.require_mesh_object(params["object"])
    mesh: bpy.types.Mesh = obj.data
    distance = float(params.get("distance", 0.001))
    if distance < 0:
        raise ValueError("distance must be >= 0")

    merged = 0
    with _bmesh_session(obj, mesh) as bm:
        before = len(bm.verts)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=distance)
        merged = before - len(bm.verts)

    summary = _mesh_summary(mesh, obj.name)
    summary["merged_count"] = merged
    return summary


def mesh_add_uv_layer(params: dict[str, Any]) -> dict[str, Any]:
    obj = context.require_mesh_object(params["object"])
    mesh: bpy.types.Mesh = obj.data
    layer_name = params.get("name") or "UVMap"

    if layer_name in mesh.uv_layers:
        raise ValueError(f"UV layer '{layer_name}' already exists")

    mesh.uv_layers.new(name=layer_name)
    summary = _mesh_summary(mesh, obj.name)
    summary["uv_layer"] = layer_name
    summary["uv_layers"] = [uv.name for uv in mesh.uv_layers]
    return summary


def mesh_smooth_shade(params: dict[str, Any]) -> dict[str, Any]:
    obj = context.require_mesh_object(params["object"])
    mesh: bpy.types.Mesh = obj.data
    smooth = bool(params.get("smooth", True))

    if obj.mode == "EDIT":
        with _bmesh_session(obj, mesh) as bm:
            for face in bm.faces:
                face.smooth = smooth
    else:
        for poly in mesh.polygons:
            poly.use_smooth = smooth

    summary = _mesh_summary(mesh, obj.name)
    summary["smooth"] = smooth
    return summary


def modifier_add_mirror(params: dict[str, Any]) -> dict[str, Any]:
    obj = context.require_mesh_object(params["object"])
    name = params.get("name") or "Mirror"
    mod = obj.modifiers.new(name=name, type="MIRROR")
    axis = (params.get("axis") or "X").upper()
    axis_map = {"X": 0, "Y": 1, "Z": 2}
    if axis not in axis_map:
        raise ValueError("axis must be X, Y, or Z")
    mod.use_axis[axis_map[axis]] = True
    if "merge_threshold" in params:
        mod.merge_threshold = float(params["merge_threshold"])

    summary = _mesh_summary(obj.data, obj.name)
    summary["modifier"] = mod.name
    summary["modifier_type"] = mod.type
    return summary


def modifier_add_array(params: dict[str, Any]) -> dict[str, Any]:
    obj = context.require_mesh_object(params["object"])
    name = params.get("name") or "Array"
    mod = obj.modifiers.new(name=name, type="ARRAY")
    if "count" in params:
        mod.count = int(params["count"])
    if "offset" in params:
        offset = parse_vector3(params["offset"], (1.0, 0.0, 0.0))
        mod.relative_offset_displace[0] = offset[0]
        mod.relative_offset_displace[1] = offset[1]
        mod.relative_offset_displace[2] = offset[2]

    summary = _mesh_summary(obj.data, obj.name)
    summary["modifier"] = mod.name
    summary["modifier_type"] = mod.type
    return summary


def modifier_add_subdivision(params: dict[str, Any]) -> dict[str, Any]:
    obj = context.require_mesh_object(params["object"])
    name = params.get("name") or "Subdivision"
    mod = obj.modifiers.new(name=name, type="SUBSURF")
    if "levels" in params:
        mod.levels = int(params["levels"])
    if "render_levels" in params:
        mod.render_levels = int(params["render_levels"])

    summary = _mesh_summary(obj.data, obj.name)
    summary["modifier"] = mod.name
    summary["modifier_type"] = mod.type
    return summary


def register() -> None:
    handlers = (
        ("mesh_create_from_verts_faces", mesh_create_from_verts_faces, True, "Create mesh from vertices and faces"),
        ("mesh_get_geometry", mesh_get_geometry, False, "Get paginated mesh geometry"),
        ("mesh_set_vertices", mesh_set_vertices, True, "Update vertex positions by index"),
        ("mesh_extrude_region", mesh_extrude_region, True, "Extrude faces by offset vector"),
        ("mesh_subdivide", mesh_subdivide, True, "Subdivide mesh faces"),
        ("mesh_merge_vertices", mesh_merge_vertices, True, "Merge vertices within distance"),
        ("mesh_add_uv_layer", mesh_add_uv_layer, True, "Add a UV layer"),
        ("mesh_smooth_shade", mesh_smooth_shade, True, "Set smooth or flat shading"),
        ("modifier_add_mirror", modifier_add_mirror, True, "Add mirror modifier"),
        ("modifier_add_array", modifier_add_array, True, "Add array modifier"),
        ("modifier_add_subdivision", modifier_add_subdivision, True, "Add subdivision surface modifier"),
    )
    for name, fn, mutating, description in handlers:
        register_handler(name, fn, mutating=mutating, description=description)
