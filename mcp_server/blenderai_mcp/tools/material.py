"""Material MCP tools."""

from __future__ import annotations

from typing import Any

import mcp.types as types

from ..agent_guidance import with_agent_feedback

AUTH_TOKEN_SCHEMA = {
    "type": "string",
    "description": "Optional; bridge client injects BLENDERAI_AUTH_TOKEN if omitted.",
}

MATERIAL_OUTPUT = with_agent_feedback(
    {
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
)


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
        (
            "Create a node-based material with Principled BSDF. Set base_color [R,G,B,A]. "
            "Then material_assign to objects. For wood/metal/glass: material_set_principled "
            "(metallic, roughness, emission). Advanced shader nodes (Noise, Voronoi, Mix, Bump, "
            "Normal Map, HDRI environment) via execute_python. Always viewport_set_shading MATERIAL "
            "then viewport_capture to see colors."
        ),
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
        (
            "Assign material to mesh object slot (default 0). "
            "If viewport stays grey, call viewport_set_shading MATERIAL then viewport_capture."
        ),
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
        (
            "Tune Principled BSDF: base_color, metallic (0-1), roughness (0-1), "
            "emission_color, emission_strength for glow. Glass: low roughness, metallic 0. "
            "Metal: metallic 1, low roughness. Leaves: green base_color, high roughness."
        ),
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
        (
            "Inspect material: principled values + full node_tree summary (nodes, links, sockets). "
            "Use before editing complex shaders. Build node graphs with execute_python when you "
            "need Noise/Voronoi/MixRGB/Bump/Mapping nodes."
        ),
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
