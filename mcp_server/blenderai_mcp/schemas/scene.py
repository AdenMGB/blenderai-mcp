"""JSON Schema definitions for scene MCP tools."""

from __future__ import annotations

from ..agent_guidance import with_agent_feedback
from .common import OBJECT_SCHEMA

SCENE_TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "ping",
        "description": (
            "Health check — call FIRST every session. Confirms Blender bridge is running. "
            "Returns blender_version. If this fails, start the addon server in Blender (N-panel → BlenderAI)."
        ),
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "outputSchema": with_agent_feedback(
            {
                "type": "object",
                "properties": {
                    "ok": {"type": "boolean"},
                    "pong": {"type": "boolean"},
                    "blender_version": {"type": "string"},
                },
                "required": ["ok", "pong", "blender_version"],
            }
        ),
    },
    {
        "name": "scene_get_summary",
        "description": (
            "Fast scene overview: object count, frame range, render engine, resolution, selection. "
            "Use before editing to understand context. Response includes agent_feedback.next_steps. "
            "Pair with viewport_capture for visual confirmation."
        ),
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "outputSchema": with_agent_feedback(
            {
                "type": "object",
                "properties": {
                    "ok": {"type": "boolean"},
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
                "required": ["ok", "name", "frame_current", "object_count"],
            }
        ),
    },
    {
        "name": "scene_list_objects",
        "description": (
            "List objects with transforms and world bounds (min/max/center). "
            "Filter by type: MESH, LIGHT, CAMERA, EMPTY. "
            "Use bounds to check overlap/gaps between parts — critical for multi-part models (trees, buildings)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"type": {"type": "string"}},
            "additionalProperties": False,
        },
        "outputSchema": with_agent_feedback(
            {
                "type": "object",
                "properties": {
                    "ok": {"type": "boolean"},
                    "objects": {"type": "array", "items": OBJECT_SCHEMA},
                    "count": {"type": "integer"},
                },
                "required": ["ok", "objects", "count"],
            }
        ),
    },
    {
        "name": "scene_list_collections",
        "description": "List scene collections and child hierarchy. Use before collection_link_object.",
        "inputSchema": {
            "type": "object",
            "properties": {"recursive": {"type": "boolean", "default": False}},
            "additionalProperties": False,
        },
        "outputSchema": with_agent_feedback(
            {
                "type": "object",
                "properties": {
                    "ok": {"type": "boolean"},
                    "collections": {"type": "array", "items": {"type": "object"}},
                    "count": {"type": "integer"},
                },
                "required": ["ok", "collections", "count"],
            }
        ),
    },
    {
        "name": "selection_get",
        "description": (
            "Get selected objects with full bounds. Use to see what the user has picked in the viewport."
        ),
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "outputSchema": with_agent_feedback(
            {
                "type": "object",
                "properties": {
                    "ok": {"type": "boolean"},
                    "selected": {"type": "array", "items": OBJECT_SCHEMA},
                    "count": {"type": "integer"},
                    "active": {"type": ["string", "null"]},
                },
                "required": ["ok", "selected", "count", "active"],
            }
        ),
    },
    {
        "name": "selection_set",
        "description": (
            "Select objects by name and optionally set active. "
            "Required before camera_frame_objects on a selection."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "objects": {"type": "array", "items": {"type": "string"}},
                "active": {"type": "string"},
            },
            "required": ["objects"],
            "additionalProperties": False,
        },
        "outputSchema": with_agent_feedback(
            {
                "type": "object",
                "properties": {
                    "ok": {"type": "boolean"},
                    "selected": {"type": "array", "items": {"type": "string"}},
                    "count": {"type": "integer"},
                    "active": {"type": ["string", "null"]},
                },
                "required": ["ok", "selected", "count", "active"],
            }
        ),
    },
]
