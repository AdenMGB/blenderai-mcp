"""MCP stdio server — exposes Blender bridge methods as MCP tools."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .agent_guidance import enrich_result
from .client import BlenderBridgeError, get_client
from .tools import all_tools, get_tool_handler
from .tools import execute as execute_tools
from .tools import material as material_tools
from .tools import mesh as mesh_tools
from .tools import render as render_tools
from .tools._helpers import image_content_blocks

app = Server("blenderai")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return all_tools()


async def _call_bridge(method: str, params: dict[str, Any] | None = None) -> Any:
    return await asyncio.to_thread(get_client().call, method, params or {})


def _format_tool_result(name: str, data: dict[str, Any]) -> dict[str, Any]:
    if name == "ping":
        result = {
            "ok": True,
            "pong": data.get("pong", True),
            "blender_version": data.get("blender_version", ""),
        }
    elif name == "execute_python":
        result = execute_tools.format_result(data)
    elif name.startswith("mesh_") or name.startswith("modifier_"):
        result = mesh_tools.format_result(data)
    elif name.startswith("material_"):
        result = material_tools.format_result(data)
    elif name in render_tools.IMAGE_TOOLS or name.startswith("render_") or name.startswith("viewport_"):
        result = render_tools.format_result(data)
    else:
        result = {"ok": True, **data}

    return enrich_result(name, result)


def _error_result(code: str, message: str) -> dict[str, Any]:
    return enrich_result(
        "error",
        {
            "ok": False,
            "error": {"code": code, "message": message},
        },
    )


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> types.CallToolResult:
    try:
        bridge_method = get_tool_handler(name)
        if bridge_method is None:
            result = _error_result("METHOD_NOT_FOUND", f"Unknown tool: {name}")
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=json.dumps(result))],
                structuredContent=result,
                isError=True,
            )

        data = await _call_bridge(bridge_method, arguments)
        result = _format_tool_result(name, data)

        content: list[types.TextContent | types.ImageContent] = [
            types.TextContent(type="text", text=json.dumps(result, indent=2))
        ]

        if name in render_tools.IMAGE_TOOLS:
            for block in image_content_blocks(data):
                content.append(
                    types.ImageContent(
                        type="image",
                        data=block["data"],
                        mimeType=block.get("mimeType", "image/png"),
                    )
                )

        return types.CallToolResult(
            content=content,
            structuredContent=result,
            isError=not result.get("ok", True),
        )

    except BlenderBridgeError as exc:
        result = _error_result(exc.code, exc.message)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=json.dumps(result, indent=2))],
            structuredContent=result,
            isError=True,
        )
