"""Rendering and viewport MCP tools."""

from __future__ import annotations

from typing import Any

import mcp.types as types

from ..agent_guidance import with_agent_feedback
from ._helpers import image_content_blocks

AUTH_TOKEN_SCHEMA = {
    "type": "string",
    "description": "Optional; bridge client injects BLENDERAI_AUTH_TOKEN if omitted.",
}

IMAGE_OUTPUT = with_agent_feedback(
    {
        "type": "object",
        "properties": {
            "ok": {"type": "boolean"},
            "filepath": {"type": "string"},
            "format": {"type": "string"},
            "images": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "mime_type": {"type": "string"},
                        "data": {"type": "string", "description": "Base64-encoded PNG"},
                    },
                },
            },
            "error": {"type": "object"},
        },
        "required": ["ok"],
    }
)

RENDER_OUTPUT = with_agent_feedback(
    {
        "type": "object",
        "properties": {
            "ok": {"type": "boolean"},
            "engine": {"type": "string"},
            "resolution_x": {"type": "integer"},
            "resolution_y": {"type": "integer"},
            "resolution_percentage": {"type": "integer"},
            "samples": {"type": "integer"},
            "shading": {"type": "string"},
            "error": {"type": "object"},
        },
        "required": ["ok"],
    }
)


def _tool(name: str, description: str, input_schema: dict, output_schema: dict) -> types.Tool:
    return types.Tool(
        name=name,
        description=description,
        inputSchema=input_schema,
        outputSchema=output_schema,
    )


TOOLS = [
    _tool(
        "viewport_capture",
        (
            "VISION FEEDBACK LOOP — capture viewport PNG + base64 image for you to analyze. "
            "Call after meaningful edits (layout, materials, lighting). Requires Blender GUI. "
            "Before capture: viewport_set_shading MATERIAL or RENDERED. "
            "Compare image to goal: gaps, floating parts, proportions, colors. "
            "Returns agent_feedback with next_steps."
        ),
        {
            "type": "object",
            "properties": {
                "filepath": {"type": "string"},
                "auth_token": AUTH_TOKEN_SCHEMA,
            },
        },
        IMAGE_OUTPUT,
    ),
    _tool(
        "render_still",
        (
            "Full F12-quality render (Cycles/Eevee). Slower than viewport_capture but better "
            "lighting/shadows. Returns PNG + base64. Use for final hero shots after viewport checks."
        ),
        {
            "type": "object",
            "properties": {
                "filepath": {"type": "string"},
                "include_image": {"type": "boolean", "default": True},
                "auth_token": AUTH_TOKEN_SCHEMA,
            },
        },
        IMAGE_OUTPUT,
    ),
    _tool(
        "render_set_engine",
        "Set engine: BLENDER_EEVEE_NEXT (fast preview), CYCLES (realistic), BLENDER_WORKBENCH.",
        {
            "type": "object",
            "properties": {
                "engine": {"type": "string"},
                "auth_token": AUTH_TOKEN_SCHEMA,
            },
            "required": ["engine"],
        },
        RENDER_OUTPUT,
    ),
    _tool(
        "render_set_resolution",
        "Set output resolution. Lower % for faster test renders.",
        {
            "type": "object",
            "properties": {
                "resolution_x": {"type": "integer"},
                "resolution_y": {"type": "integer"},
                "resolution_percentage": {"type": "integer"},
                "auth_token": AUTH_TOKEN_SCHEMA,
            },
        },
        RENDER_OUTPUT,
    ),
    _tool(
        "render_set_samples",
        "More samples = less noise (Cycles). Use 16-32 for tests, 128+ for finals.",
        {
            "type": "object",
            "properties": {
                "samples": {"type": "integer"},
                "auth_token": AUTH_TOKEN_SCHEMA,
            },
            "required": ["samples"],
        },
        RENDER_OUTPUT,
    ),
    _tool(
        "viewport_set_shading",
        (
            "Set viewport display: WIREFRAME (topology), SOLID (grey), MATERIAL (see colors), "
            "RENDERED (approx final). Use MATERIAL before viewport_capture to verify materials."
        ),
        {
            "type": "object",
            "properties": {
                "shading": {
                    "type": "string",
                    "enum": ["WIREFRAME", "SOLID", "MATERIAL", "RENDERED"],
                },
                "auth_token": AUTH_TOKEN_SCHEMA,
            },
            "required": ["shading"],
        },
        RENDER_OUTPUT,
    ),
]

TOOL_HANDLERS: dict[str, str] = {tool.name: tool.name for tool in TOOLS}

IMAGE_TOOLS = frozenset({"viewport_capture", "render_still"})


def format_result(data: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, **data}


def extra_content_blocks(data: dict[str, Any]) -> list[dict[str, Any]]:
    return image_content_blocks(data)
