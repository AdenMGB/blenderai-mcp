"""Scene serialization."""

from __future__ import annotations

import bpy

from .objects import serialize_object


def serialize_scene_summary(scene: bpy.types.Scene) -> dict:
    view_layer = bpy.context.view_layer
    selected = [obj.name for obj in view_layer.objects if obj.select_get()]

    return {
        "name": scene.name,
        "frame_current": scene.frame_current,
        "frame_start": scene.frame_start,
        "frame_end": scene.frame_end,
        "render_engine": scene.render.engine,
        "resolution_x": scene.render.resolution_x,
        "resolution_y": scene.render.resolution_y,
        "resolution_percentage": scene.render.resolution_percentage,
        "object_count": len(bpy.data.objects),
        "collection_count": len(bpy.data.collections),
        "material_count": len(bpy.data.materials),
        "selected_objects": selected,
        "active_object": view_layer.objects.active.name if view_layer.objects.active else None,
    }


def serialize_collection(coll: bpy.types.Collection, recursive: bool = False) -> dict:
    data = {
        "name": coll.name,
        "object_count": len(coll.objects),
        "objects": [obj.name for obj in coll.objects],
        "children": [c.name for c in coll.children],
    }
    if recursive:
        data["children_detail"] = [
            serialize_collection(child, recursive=True) for child in coll.children
        ]
    return data
