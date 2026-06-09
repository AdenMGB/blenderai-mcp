"""JSON Schema definitions for object MCP tools."""

from __future__ import annotations

from .common import OBJECT_SCHEMA

OBJECT_TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "object_create_primitive",
        "description": (
            "Create a mesh primitive in the active Blender scene "
            "(cube, uv_sphere, cylinder, cone, plane, torus)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "primitive": {
                    "type": "string",
                    "enum": ["cube", "uv_sphere", "cylinder", "cone", "plane", "torus"],
                    "default": "cube",
                },
                "name": {"type": "string"},
                "location": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
                "scale": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
                "collection": {"type": "string"},
            },
            "additionalProperties": False,
        },
        "outputSchema": OBJECT_SCHEMA,
    },
    {
        "name": "object_delete",
        "description": "Delete a Blender object by name.",
        "inputSchema": {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
            "additionalProperties": False,
        },
        "outputSchema": {
            "type": "object",
            "properties": {"deleted": {"type": "string"}},
            "required": ["deleted"],
        },
    },
    {
        "name": "object_rename",
        "description": "Rename a Blender object.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "new_name": {"type": "string"},
            },
            "required": ["name", "new_name"],
            "additionalProperties": False,
        },
        "outputSchema": OBJECT_SCHEMA,
    },
    {
        "name": "object_set_transform",
        "description": "Set object location, rotation_euler, and/or scale.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "location": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
                "rotation_euler": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 3,
                    "maxItems": 3,
                },
                "rotation_mode": {"type": "string"},
                "scale": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
            },
            "required": ["name"],
            "additionalProperties": False,
        },
        "outputSchema": OBJECT_SCHEMA,
    },
    {
        "name": "object_get",
        "description": "Get structured details for an object by name.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "include_mesh": {"type": "boolean", "default": False},
            },
            "required": ["name"],
            "additionalProperties": False,
        },
        "outputSchema": OBJECT_SCHEMA,
    },
    {
        "name": "object_duplicate",
        "description": "Duplicate an object and optionally assign a new name.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "new_name": {"type": "string"},
            },
            "required": ["name"],
            "additionalProperties": False,
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "object": OBJECT_SCHEMA,
                "source": {"type": "string"},
            },
            "required": ["object", "source"],
        },
    },
    {
        "name": "object_set_parent",
        "description": "Parent an object to another object, or clear parenting when parent is null.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "parent": {"type": ["string", "null"]},
                "keep_transform": {"type": "boolean", "default": True},
            },
            "required": ["name"],
            "additionalProperties": False,
        },
        "outputSchema": OBJECT_SCHEMA,
    },
    {
        "name": "collection_create",
        "description": "Create a new collection, optionally under a parent collection.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "parent": {"type": "string"},
            },
            "required": ["name"],
            "additionalProperties": False,
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "object_count": {"type": "integer"},
                "objects": {"type": "array", "items": {"type": "string"}},
                "children": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["name", "object_count", "objects", "children"],
        },
    },
    {
        "name": "collection_link_object",
        "description": "Link an object into a collection.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "collection": {"type": "string"},
                "object": {"type": "string"},
            },
            "required": ["collection", "object"],
            "additionalProperties": False,
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "collection": {"type": "string"},
                "object": {"type": "string"},
                "linked": {"type": "boolean"},
            },
            "required": ["collection", "object", "linked"],
        },
    },
    {
        "name": "collection_list",
        "description": "List collections in the Blender file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "recursive": {"type": "boolean", "default": False},
                "parent": {"type": "string"},
            },
            "additionalProperties": False,
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "collections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "object_count": {"type": "integer"},
                            "objects": {"type": "array", "items": {"type": "string"}},
                            "children": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["name", "object_count", "objects", "children"],
                    },
                },
                "count": {"type": "integer"},
            },
            "required": ["collections", "count"],
        },
    },
]
