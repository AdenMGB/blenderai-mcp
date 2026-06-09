"""JSON Schema definitions for scene MCP tools."""

from __future__ import annotations

from .common import OBJECT_SCHEMA

SCENE_TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "ping",
        "description": "Check connectivity to the Blender addon bridge.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "outputSchema": {
            "type": "object",
            "properties": {
                "pong": {"type": "boolean"},
                "blender_version": {"type": "string"},
            },
            "required": ["pong", "blender_version"],
        },
    },
    {
        "name": "scene_get_summary",
        "description": "Get a summary of the active Blender scene.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "outputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "frame_current": {"type": "integer"},
                "frame_start": {"type": "integer"},
                "frame_end": {"type": "integer"},
                "render_engine": {"type": "string"},
                "resolution_x": {"type": "integer"},
                "resolution_y": {"type": "integer"},
                "resolution_percentage": {"type": "integer"},
                "object_count": {"type": "integer"},
                "collection_count": {"type": "integer"},
                "material_count": {"type": "integer"},
                "selected_objects": {"type": "array", "items": {"type": "string"}},
                "active_object": {"type": ["string", "null"]},
            },
            "required": ["name", "frame_current", "object_count"],
        },
    },
    {
        "name": "scene_list_objects",
        "description": "List all objects, optionally filtered by Blender object type.",
        "inputSchema": {
            "type": "object",
            "properties": {"type": {"type": "string"}},
            "additionalProperties": False,
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "objects": {"type": "array", "items": OBJECT_SCHEMA},
                "count": {"type": "integer"},
            },
            "required": ["objects", "count"],
        },
    },
    {
        "name": "scene_list_collections",
        "description": "List collections in the scene.",
        "inputSchema": {
            "type": "object",
            "properties": {"recursive": {"type": "boolean", "default": False}},
            "additionalProperties": False,
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "collections": {"type": "array", "items": {"type": "object"}},
                "count": {"type": "integer"},
            },
            "required": ["collections", "count"],
        },
    },
    {
        "name": "selection_get",
        "description": "Get currently selected objects and the active object.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "outputSchema": {
            "type": "object",
            "properties": {
                "selected": {"type": "array", "items": OBJECT_SCHEMA},
                "count": {"type": "integer"},
                "active": {"type": ["string", "null"]},
            },
            "required": ["selected", "count", "active"],
        },
    },
    {
        "name": "selection_set",
        "description": "Select objects by name list and optionally set the active object.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "objects": {"type": "array", "items": {"type": "string"}},
                "active": {"type": "string"},
            },
            "required": ["objects"],
            "additionalProperties": False,
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "selected": {"type": "array", "items": {"type": "string"}},
                "count": {"type": "integer"},
                "active": {"type": ["string", "null"]},
            },
            "required": ["selected", "count", "active"],
        },
    },
]
