"""Camera MCP tools."""

from __future__ import annotations

from typing import Any

import mcp.types as types

AUTH_TOKEN_SCHEMA = {
    "type": "string",
    "description": "Optional; bridge client injects BLENDERAI_AUTH_TOKEN if omitted.",
}

CAMERA_OUTPUT = {
    "type": "object",
    "properties": {
        "ok": {"type": "boolean"},
        "name": {"type": "string"},
        "camera": {"type": "object"},
        "framed_objects": {"type": "array", "items": {"type": "string"}},
        "error": {"type": "object"},
    },
    "required": ["ok"],
}


def _tool(name: str, description: str, input_schema: dict) -> types.Tool:
    return types.Tool(
        name=name,
        description=description,
        inputSchema=input_schema,
        outputSchema=CAMERA_OUTPUT,
    )


TOOLS = [
    _tool(
        "camera_create",
        "Create a camera object.",
        {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "location": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
                "rotation_euler": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
                "focal_length": {"type": "number"},
                "collection": {"type": "string"},
                "set_active": {"type": "boolean", "default": False},
                "auth_token": AUTH_TOKEN_SCHEMA,
            },
        },
    ),
    _tool(
        "camera_set_focal_length",
        "Set a camera focal length in millimeters.",
        {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "focal_length": {"type": "number"},
                "auth_token": AUTH_TOKEN_SCHEMA,
            },
            "required": ["name", "focal_length"],
        },
    ),
    _tool(
        "camera_frame_objects",
        "Frame objects in the camera view (requires Blender GUI).",
        {
            "type": "object",
            "properties": {
                "camera": {"type": "string"},
                "objects": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                "auth_token": AUTH_TOKEN_SCHEMA,
            },
            "required": ["camera", "objects"],
        },
    ),
]

TOOL_HANDLERS: dict[str, str] = {tool.name: tool.name for tool in TOOLS}


def format_result(data: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, **data}
