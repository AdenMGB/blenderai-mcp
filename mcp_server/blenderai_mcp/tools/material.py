"""Material MCP tools."""

from __future__ import annotations

from typing import Any

import mcp.types as types

AUTH_TOKEN_SCHEMA = {
    "type": "string",
    "description": "Optional; bridge client injects BLENDERAI_AUTH_TOKEN if omitted.",
}

MATERIAL_OUTPUT = {
    "type": "object",
    "properties": {
        "ok": {"type": "boolean"},
        "name": {"type": "string"},
        "use_nodes": {"type": "boolean"},
        "principled": {"type": "object"},
        "node_tree": {"type": "object"},
        "error": {"type": "object"},
    },
    "required": ["ok"],
}


def _tool(name: str, description: str, input_schema: dict) -> types.Tool:
    return types.Tool(
        name=name,
        description=description,
        inputSchema=input_schema,
        outputSchema=MATERIAL_OUTPUT,
    )


TOOLS = [
    _tool(
        "material_create",
        "Create a new principled material.",
        {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "base_color": {"type": "array", "items": {"type": "number"}},
                "auth_token": AUTH_TOKEN_SCHEMA,
            },
            "required": ["name"],
        },
    ),
    _tool(
        "material_assign",
        "Assign a material to a mesh object slot.",
        {
            "type": "object",
            "properties": {
                "object": {"type": "string"},
                "material": {"type": "string"},
                "slot": {"type": "integer", "default": 0},
                "auth_token": AUTH_TOKEN_SCHEMA,
            },
            "required": ["object", "material"],
        },
    ),
    _tool(
        "material_set_principled",
        "Set principled BSDF properties (base_color, metallic, roughness, emission).",
        {
            "type": "object",
            "properties": {
                "material": {"type": "string"},
                "base_color": {"type": "array", "items": {"type": "number"}},
                "metallic": {"type": "number"},
                "roughness": {"type": "number"},
                "emission": {},
                "emission_color": {"type": "array", "items": {"type": "number"}},
                "emission_strength": {"type": "number"},
                "auth_token": AUTH_TOKEN_SCHEMA,
            },
            "required": ["material"],
        },
    ),
    _tool(
        "material_get",
        "Get material details including node tree summary.",
        {
            "type": "object",
            "properties": {
                "material": {"type": "string"},
                "auth_token": AUTH_TOKEN_SCHEMA,
            },
            "required": ["material"],
        },
    ),
]

TOOL_HANDLERS: dict[str, str] = {tool.name: tool.name for tool in TOOLS}


def format_result(data: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, **data}
