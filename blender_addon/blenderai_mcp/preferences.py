"""Addon preferences — auth token, port, server state."""

from __future__ import annotations

import secrets

import bpy
from bpy.props import IntProperty, StringProperty
from bpy.types import AddonPreferences

ADDON_PACKAGE = __package__


class BlenderAIPreferences(AddonPreferences):
    bl_idname = ADDON_PACKAGE

    auth_token: StringProperty(
        name="Auth Token",
        description="Bearer token required by the external MCP server",
        subtype="PASSWORD",
        default="",
    )

    port: IntProperty(
        name="Port",
        description="TCP port for the local bridge server",
        default=9876,
        min=1024,
        max=65535,
    )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.prop(self, "port")
        row = layout.row()
        row.prop(self, "auth_token")
        row.operator("blenderai.regenerate_token", text="", icon="FILE_REFRESH")
        layout.label(text="Bind address is always 127.0.0.1", icon="INFO")


class BLENDERAI_OT_regenerate_token(bpy.types.Operator):
    bl_idname = "blenderai.regenerate_token"
    bl_label = "Regenerate Auth Token"
    bl_description = "Generate a new random auth token"

    def execute(self, context: bpy.types.Context) -> set[str]:
        prefs = get_preferences()
        prefs.auth_token = secrets.token_urlsafe(32)
        self.report({"INFO"}, "Auth token regenerated")
        return {"FINISHED"}


classes = (
    BlenderAIPreferences,
    BLENDERAI_OT_regenerate_token,
)


def get_preferences() -> BlenderAIPreferences:
    return bpy.context.preferences.addons[ADDON_PACKAGE].preferences


def ensure_auth_token() -> None:
    prefs = get_preferences()
    if not prefs.auth_token:
        prefs.auth_token = secrets.token_urlsafe(32)


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
