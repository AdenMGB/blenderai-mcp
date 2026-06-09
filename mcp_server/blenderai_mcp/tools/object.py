"""Object and collection MCP tools."""

from __future__ import annotations

from typing import Any

import mcp.types as types

from ..schemas.object import OBJECT_TOOL_DEFINITIONS

AUTH_TOKEN_SCHEMA = {
    "type": "string",
    "description": "Optional; bridge client injects BLENDERAI_AUTH_TOKEN if omitted.",
}

OBJECT_OUTPUT = {
    "type": "object",
    "properties": {
        "ok": {"type": "boolean"},
        "error": {"type": "object"},
    },
    "required": ["ok"],
}


def _tool(name: str, description: str, input_schema: dict, output_schema: dict) -> types.Tool:
    properties = dict(input_schema.get("properties", {}))
    properties.setdefault("auth_token", AUTH_TOKEN_SCHEMA)
    schema = {**input_schema, "properties": properties}
    return types.Tool(
        name=name,
        description=description,
        inputSchema=schema,
        outputSchema=output_schema,
    )


TOOLS = [
    _tool(defn["name"], defn["description"], defn["inputSchema"], defn["outputSchema"])
    for defn in OBJECT_TOOL_DEFINITIONS
]

TOOL_HANDLERS: dict[str, str] = {tool.name: tool.name for tool in TOOLS}


def format_result(data: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, **data}
