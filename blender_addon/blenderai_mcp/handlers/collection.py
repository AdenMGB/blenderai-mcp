"""Collection handlers."""

from __future__ import annotations

import bpy

from ..serializers.scene import serialize_collection
from ..utils import context


def collection_create(params: dict) -> dict:
    name = params.get("name")
    if not name:
        raise ValueError("name is required")

    if context.find_collection(name):
        raise ValueError(f"Collection '{name}' already exists")

    context.push_undo("BlenderAI: Create Collection")
    coll = bpy.data.collections.new(name)

    parent_name = params.get("parent")
    if parent_name:
        parent = context.require_collection(parent_name)
        parent.children.link(coll)
    else:
        context.get_scene().collection.children.link(coll)

    return serialize_collection(coll)


def collection_link_object(params: dict) -> dict:
    collection_name = params.get("collection")
    object_name = params.get("object") or params.get("name")
    if not collection_name or not object_name:
        raise ValueError("collection and object are required")

    coll = context.require_collection(collection_name)
    obj = context.require_object(object_name)

    context.push_undo("BlenderAI: Link Object to Collection")
    if obj.name not in coll.objects:
        coll.objects.link(obj)

    return {
        "collection": coll.name,
        "object": obj.name,
        "linked": True,
    }


def collection_list(params: dict) -> dict:
    recursive = bool(params.get("recursive", False))
    parent_name = params.get("parent")

    if parent_name:
        parent = context.require_collection(parent_name)
        collections = [serialize_collection(parent, recursive=recursive)]
    else:
        collections = [
            serialize_collection(coll, recursive=recursive) for coll in bpy.data.collections
        ]

    return {"collections": collections, "count": len(collections)}


def register() -> None:
    from .registry import register_handler

    register_handler("collection_create", collection_create, mutating=True)
    register_handler("collection_link_object", collection_link_object, mutating=True)
    register_handler("collection_list", collection_list)
