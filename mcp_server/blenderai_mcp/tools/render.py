"""Rendering and viewport MCP tools."""

from __future__ import annotations

from typing import Any

import mcp.types as types

from ._helpers import image_content_blocks

AUTH_TOKEN_SCHEMA = {
    "type": "string",
    "description": "Optional; bridge client injects BLENDERAI_AUTH_TOKEN if omitted.",
}

IMAGE_OUTPUT = {
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

RENDER_OUTPUT = {
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
        "Capture the 3D viewport as PNG (requires Blender GUI with VIEW_3D area).",
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
        "Render a still image using scene render settings; returns filepath and base64 PNG.",
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
        "Set render engine (BLENDER_EEVEE_NEXT, CYCLES, BLENDER_WORKBENCH).",
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
        "Set render resolution.",
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
        "Set render samples for Cycles or Eevee.",
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
        "Set viewport shading (WIREFRAME, SOLID, MATERIAL, RENDERED). Requires GUI.",
        {
            "type": "object",
            "properties": {
                "shading": {"type": "string"},
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
