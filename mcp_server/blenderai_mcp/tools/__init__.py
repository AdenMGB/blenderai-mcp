"""Aggregate MCP tool definitions and bridge method routing."""

from __future__ import annotations

import mcp.types as types

from ..schemas.object import OBJECT_TOOL_DEFINITIONS
from ..schemas.scene import SCENE_TOOL_DEFINITIONS
from . import camera, execute, light, material, mesh, render

_TOOL_MODULES = (camera, execute, light, material, mesh, render)

_HANDLERS: dict[str, str] = {}
for _module in _TOOL_MODULES:
    _HANDLERS.update(getattr(_module, "TOOL_HANDLERS", {}))

for _spec in (*SCENE_TOOL_DEFINITIONS, *OBJECT_TOOL_DEFINITIONS):
    _HANDLERS[_spec["name"]] = _spec["name"]


def _tools_from_definitions(definitions: list[dict]) -> list[types.Tool]:
    return [
        types.Tool(
            name=spec["name"],
            description=spec["description"],
            inputSchema=spec["inputSchema"],
            outputSchema=spec.get("outputSchema", {"type": "object"}),
        )
        for spec in definitions
    ]


def all_tools() -> list[types.Tool]:
    tools: list[types.Tool] = []
    for module in _TOOL_MODULES:
        tools.extend(getattr(module, "TOOLS", []))
    tools.extend(_tools_from_definitions(SCENE_TOOL_DEFINITIONS))
    tools.extend(_tools_from_definitions(OBJECT_TOOL_DEFINITIONS))
    return tools


def get_tool_handler(name: str) -> str | None:
    return _HANDLERS.get(name)
