"""Light MCP tools."""

from __future__ import annotations

from typing import Any

import mcp.types as types

from ..agent_guidance import with_agent_feedback

AUTH_TOKEN_SCHEMA = {
    "type": "string",
    "description": "Optional; bridge client injects BLENDERAI_AUTH_TOKEN if omitted.",
}

LIGHT_OUTPUT = with_agent_feedback(
    {
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
)


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
        (
            "Add light: SUN (outdoor key), AREA (soft studio), SPOT (accent), POINT (bulb). "
            "Three-point setup: SUN key + AREA fill + low AREA rim. "
            "viewport_set_shading RENDERED or render_still to judge lighting."
        ),
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
        "Tune energy, color, spot angle/size. Re-capture viewport after lighting changes.",
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
