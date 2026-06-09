"""Shared helpers for MCP tool responses."""

from __future__ import annotations

from typing import Any


def tool_response(data: dict[str, Any], summary: str | None = None) -> dict[str, Any]:
    """Build MCP tool result with structuredContent and optional image blocks."""
    content: list[dict[str, Any]] = [
        {"type": "text", "text": summary or _default_summary(data)},
    ]
    content.extend(image_content_blocks(data))
    return {"structuredContent": data, "content": content}


def image_content_blocks(data: dict[str, Any]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for image in data.get("images") or []:
        if not isinstance(image, dict):
            continue
        encoded = image.get("data")
        if not encoded:
            continue
        blocks.append(
            {
                "type": "image",
                "data": encoded,
                "mimeType": image.get("mime_type", "image/png"),
            }
        )

    legacy = data.get("image_base64")
    if legacy and not blocks:
        blocks.append({"type": "image", "data": legacy, "mimeType": "image/png"})

    return blocks


def _default_summary(data: dict[str, Any]) -> str:
    if "filepath" in data:
        return f"Saved image to {data['filepath']}"
    if "name" in data:
        return str(data["name"])
    return str(data)
