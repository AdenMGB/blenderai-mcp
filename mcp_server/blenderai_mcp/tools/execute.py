"""MCP tools for guarded Python execution and batching."""

from __future__ import annotations

from typing import Any

import mcp.types as types

from ..agent_guidance import with_agent_feedback

EXECUTE_PYTHON_INPUT = {
    "type": "object",
    "properties": {
        "code": {
            "type": "string",
            "description": (
                "Python to run in Blender (bpy available). Set `result = {...}` to return data. "
                "Use for advanced shader node graphs, geometry nodes, physics — not for simple transforms."
            ),
        },
        "confirm_destructive": {
            "type": "boolean",
            "description": "Must be true to run.",
        },
        "auth_token": {
            "type": "string",
            "description": "Optional; bridge client injects BLENDERAI_AUTH_TOKEN if omitted.",
        },
    },
    "required": ["code", "confirm_destructive"],
}

EXECUTE_PYTHON_OUTPUT = with_agent_feedback(
    {
        "type": "object",
        "properties": {
            "ok": {"type": "boolean"},
            "executed": {"type": "boolean"},
            "stdout": {"type": "string"},
            "stderr": {"type": "string"},
            "result": {},
            "error": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "message": {"type": "string"},
                    "traceback": {"type": "string"},
                },
            },
        },
        "required": ["ok"],
    }
)

BATCH_EXECUTE_INPUT = {
    "type": "object",
    "properties": {
        "calls": {
            "type": "array",
            "description": (
                "List of {method, params} bridge calls. Preferred for multi-step builds "
                "(tree, room, material pass). One viewport_capture after the batch."
            ),
            "items": {
                "type": "object",
                "properties": {
                    "method": {"type": "string"},
                    "params": {"type": "object"},
                },
                "required": ["method"],
            },
        },
        "auth_token": {
            "type": "string",
            "description": "Optional; bridge client injects BLENDERAI_AUTH_TOKEN if omitted.",
        },
    },
    "required": ["calls"],
}

BATCH_EXECUTE_OUTPUT = with_agent_feedback(
    {
        "type": "object",
        "properties": {
            "ok": {"type": "boolean"},
            "count": {"type": "integer"},
            "results": {"type": "array", "items": {"type": "object"}},
        },
        "required": ["ok", "count", "results"],
    }
)

TOOLS = [
    types.Tool(
        name="execute_python",
        description=(
            "ESCAPE HATCH for bpy code not covered by typed tools. Requires confirm_destructive=true. "
            "Best for: shader node trees (Noise, Voronoi, Mix, Bump, TexImage), geometry nodes, "
            "custom operators, physics. Prefer typed tools for objects/materials/mesh when available. "
            "Read stdout/stderr/error.traceback in response. Then viewport_capture."
        ),
        inputSchema=EXECUTE_PYTHON_INPUT,
        outputSchema=EXECUTE_PYTHON_OUTPUT,
    ),
    types.Tool(
        name="batch_execute",
        description=(
            "Run multiple bridge methods in ONE round-trip. Ideal workflow: "
            "batch [creates, transforms, materials] → viewport_capture → adjust. "
            "Each result has ok/data/error per step. Response includes agent_feedback summary."
        ),
        inputSchema=BATCH_EXECUTE_INPUT,
        outputSchema=BATCH_EXECUTE_OUTPUT,
    ),
]

TOOL_HANDLERS = {
    "execute_python": "execute_python",
    "batch_execute": "batch_execute",
}


def format_result(data: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, **data}
