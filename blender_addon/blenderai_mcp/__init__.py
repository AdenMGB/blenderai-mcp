"""BlenderAI MCP addon — TCP bridge to Blender's main thread."""

import bpy

from . import preferences, ui
from .bridge import server as bridge_server
from .handlers import register_handlers, unregister_handlers

bl_info = {
    "name": "BlenderAI MCP",
    "author": "BlenderAI",
    "version": (0, 1, 0),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar > BlenderAI",
    "description": "TCP bridge for external MCP server access to Blender",
    "category": "Development",
}


def register() -> None:
    register_handlers()
    preferences.register()
    for cls in ui.classes:
        bpy.utils.register_class(cls)
    preferences.ensure_auth_token()


def unregister() -> None:
    bridge_server.stop_server()
    unregister_handlers()
    for cls in reversed(ui.classes):
        bpy.utils.unregister_class(cls)
    preferences.unregister()


if __name__ == "__main__":
    register()
