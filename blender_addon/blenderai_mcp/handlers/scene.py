"""Scene introspection handlers."""

from __future__ import annotations

from typing import Any

import bpy

from ..serializers.objects import serialize_object
from ..serializers.scene import serialize_collection, serialize_scene_summary
from ..utils import context
from .registry import register_handler


def ping(params: dict[str, Any]) -> dict[str, Any]:
    return {"pong": True, "blender_version": bpy.app.version_string}


def scene_get_summary(params: dict[str, Any]) -> dict[str, Any]:
    return serialize_scene_summary(context.get_scene())


def scene_list_objects(params: dict[str, Any]) -> dict[str, Any]:
    type_filter = params.get("type")
    objects = []
    for obj in bpy.data.objects:
        if type_filter and obj.type != type_filter:
            continue
        objects.append(serialize_object(obj))
    return {"objects": objects, "count": len(objects)}


def scene_list_collections(params: dict[str, Any]) -> dict[str, Any]:
    recursive = bool(params.get("recursive", False))
    collections = [
        serialize_collection(coll, recursive=recursive) for coll in bpy.data.collections
    ]
    return {"collections": collections, "count": len(collections)}


def register() -> None:
    register_handler("ping", ping)
    register_handler("scene_get_summary", scene_get_summary)
    register_handler("scene_list_objects", scene_list_objects)
    register_handler("scene_list_collections", scene_list_collections)
