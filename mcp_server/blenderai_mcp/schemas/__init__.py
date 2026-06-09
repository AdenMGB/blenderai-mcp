"""JSON Schema definitions for MCP tools."""

from .common import BOUNDS_SCHEMA, OBJECT_SCHEMA, VECTOR3_SCHEMA
from .object import OBJECT_TOOL_DEFINITIONS
from .scene import SCENE_TOOL_DEFINITIONS

PING_INPUT_SCHEMA = {
    "type": "object",
    "properties": {},
    "additionalProperties": False,
}

PING_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "ok": {"type": "boolean"},
        "pong": {"type": "boolean"},
        "blender_version": {"type": "string"},
        "error": {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "message": {"type": "string"},
            },
            "required": ["code", "message"],
        },
    },
    "required": ["ok"],
}

SCENE_GET_SUMMARY_INPUT_SCHEMA = {
    "type": "object",
    "properties": {},
    "additionalProperties": False,
}

SCENE_GET_SUMMARY_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "ok": {"type": "boolean"},
        "name": {"type": "string"},
        "frame_start": {"type": "integer"},
        "frame_end": {"type": "integer"},
        "frame_current": {"type": "integer"},
        "engine": {"type": "string"},
        "object_count": {"type": "integer"},
        "error": {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "message": {"type": "string"},
            },
            "required": ["code", "message"],
        },
    },
    "required": ["ok"],
}

__all__ = [
    "BOUNDS_SCHEMA",
    "OBJECT_SCHEMA",
    "VECTOR3_SCHEMA",
    "OBJECT_TOOL_DEFINITIONS",
    "SCENE_TOOL_DEFINITIONS",
    "PING_INPUT_SCHEMA",
    "PING_OUTPUT_SCHEMA",
    "SCENE_GET_SUMMARY_INPUT_SCHEMA",
    "SCENE_GET_SUMMARY_OUTPUT_SCHEMA",
]
