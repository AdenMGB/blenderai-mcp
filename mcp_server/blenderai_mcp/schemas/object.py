"""JSON Schema definitions for object MCP tools."""

from __future__ import annotations

from ..agent_guidance import with_agent_feedback
from .common import OBJECT_SCHEMA

OBJECT_TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "object_create_primitive",
        "description": (
            "Create a mesh primitive: cube, uv_sphere, cylinder, cone, plane, torus. "
            "Returns world bounds (min/max/center) — ALWAYS check bounds.min[2] for ground contact "
            "and bounds overlap when stacking parts (e.g. trunk top z should meet foliage bottom z). "
            "Default primitives are unit-sized; use scale for size. "
            "After creating: material_assign + viewport_capture to verify."
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
        "outputSchema": with_agent_feedback(OBJECT_SCHEMA),
    },
    {
        "name": "object_delete",
        "description": (
            "Delete object by name. Use to remove default Cube/Light clutter. "
            "Check scene_get_summary.object_count after."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
            "additionalProperties": False,
        },
        "outputSchema": with_agent_feedback(
            {
                "type": "object",
                "properties": {"ok": {"type": "boolean"}, "deleted": {"type": "string"}},
                "required": ["ok", "deleted"],
            }
        ),
    },
    {
        "name": "object_rename",
        "description": "Rename an object. Prefer clear names (Tree_Trunk, Wall_North) for batch_execute clarity.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "new_name": {"type": "string"},
            },
            "required": ["name", "new_name"],
            "additionalProperties": False,
        },
        "outputSchema": with_agent_feedback(OBJECT_SCHEMA),
    },
    {
        "name": "object_set_transform",
        "description": (
            "Set location, rotation_euler, and/or scale in world space. "
            "Response includes updated bounds — use bounds.min[2]/max[2] to fix floating gaps "
            "between connected parts. Prefer this over object_set_parent for layout."
        ),
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
        "outputSchema": with_agent_feedback(OBJECT_SCHEMA),
    },
    {
        "name": "object_get",
        "description": (
            "Get one object with location, scale, dimensions, world bounds, materials, parent. "
            "Use bounds to debug structure. Set include_mesh=true for vert/face counts only."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "include_mesh": {"type": "boolean", "default": False},
            },
            "required": ["name"],
            "additionalProperties": False,
        },
        "outputSchema": with_agent_feedback(OBJECT_SCHEMA),
    },
    {
        "name": "object_duplicate",
        "description": "Duplicate object (mesh data copied). Good for forests, arrays of props.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "new_name": {"type": "string"},
            },
            "required": ["name"],
            "additionalProperties": False,
        },
        "outputSchema": with_agent_feedback(
            {
                "type": "object",
                "properties": {
                    "ok": {"type": "boolean"},
                    "object": OBJECT_SCHEMA,
                    "source": {"type": "string"},
                },
                "required": ["ok", "object", "source"],
            }
        ),
    },
    {
        "name": "object_set_parent",
        "description": (
            "Parent child to parent object. WARNING: can confuse world bounds — prefer keeping "
            "separate objects with object_set_transform for stylized props. "
            "If parenting: always verify with object_get bounds + viewport_capture after."
        ),
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
        "outputSchema": with_agent_feedback(OBJECT_SCHEMA),
    },
    {
        "name": "collection_create",
        "description": "Create collection for organizing objects (Environment, Characters, Lights).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "parent": {"type": "string"},
            },
            "required": ["name"],
            "additionalProperties": False,
        },
        "outputSchema": with_agent_feedback(
            {
                "type": "object",
                "properties": {
                    "ok": {"type": "boolean"},
                    "name": {"type": "string"},
                    "object_count": {"type": "integer"},
                    "objects": {"type": "array", "items": {"type": "string"}},
                    "children": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["ok", "name", "object_count", "objects", "children"],
            }
        ),
    },
    {
        "name": "collection_link_object",
        "description": "Add object to a collection without moving it.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "collection": {"type": "string"},
                "object": {"type": "string"},
            },
            "required": ["collection", "object"],
            "additionalProperties": False,
        },
        "outputSchema": with_agent_feedback(
            {
                "type": "object",
                "properties": {
                    "ok": {"type": "boolean"},
                    "collection": {"type": "string"},
                    "object": {"type": "string"},
                    "linked": {"type": "boolean"},
                },
                "required": ["ok", "collection", "object", "linked"],
            }
        ),
    },
    {
        "name": "collection_list",
        "description": "List all collections and their objects.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "recursive": {"type": "boolean", "default": False},
                "parent": {"type": "string"},
            },
            "additionalProperties": False,
        },
        "outputSchema": with_agent_feedback(
            {
                "type": "object",
                "properties": {
                    "ok": {"type": "boolean"},
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
                "required": ["ok", "collections", "count"],
            }
        ),
    },
]
