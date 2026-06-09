"""Light MCP tools."""

from __future__ import annotations

from typing import Any

import mcp.types as types

AUTH_TOKEN_SCHEMA = {
    "type": "string",
    "description": "Optional; bridge client injects BLENDERAI_AUTH_TOKEN if omitted.",
}

LIGHT_OUTPUT = {
    "type": "object",
    "properties": {
        "ok": {"type": "boolean"},
        "name": {"type": "string"},
        "type": {"type": "string"},
        "light": {"type": "object"},
        "error": {"type": "object"},
    },
    "required": ["ok"],
}


def _tool(name: str, description: str, input_schema: dict) -> types.Tool:
    return types.Tool(
        name=name,
        description=description,
        inputSchema=input_schema,
        outputSchema=LIGHT_OUTPUT,
    )


TOOLS = [
    _tool(
        "light_create",
        "Create a light (POINT, SUN, SPOT, or AREA).",
        {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["POINT", "SUN", "SPOT", "AREA"],
                    "default": "POINT",
                },
                "name": {"type": "string"},
                "location": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
                "energy": {"type": "number"},
                "color": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
                "collection": {"type": "string"},
                "auth_token": AUTH_TOKEN_SCHEMA,
            },
        },
    ),
    _tool(
        "light_set_params",
        "Set parameters on an existing light object.",
        {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "energy": {"type": "number"},
                "color": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
                "location": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
                "rotation_euler": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
                "spot_size": {"type": "number"},
                "spot_blend": {"type": "number"},
                "size": {"type": "number"},
                "angle": {"type": "number"},
                "auth_token": AUTH_TOKEN_SCHEMA,
            },
            "required": ["name"],
        },
    ),
]

TOOL_HANDLERS: dict[str, str] = {tool.name: tool.name for tool in TOOLS}


def format_result(data: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, **data}
