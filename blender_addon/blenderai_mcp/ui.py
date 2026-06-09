"""N-panel UI for BlenderAI MCP bridge."""

import bpy

from .bridge import server


class BLENDERAI_PT_panel(bpy.types.Panel):
    bl_label = "BlenderAI MCP"
    bl_idname = "BLENDERAI_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BlenderAI"

    def draw(self, context):
        layout = self.layout
        prefs = context.preferences.addons[__package__].preferences

        box = layout.box()
        box.label(text="Bridge Server", icon="WORLD")

        if server.is_running():
            box.label(text=f"Status: {server.get_status()}", icon="CHECKMARK")
            box.operator("blenderai.stop_server", icon="PAUSE")
        else:
            box.label(text="Status: Stopped", icon="CANCEL")
            box.operator("blenderai.start_server", icon="PLAY")

        box.label(text=f"Port: {prefs.port}")
        if not prefs.auth_token:
            box.label(text="Set auth token in Preferences!", icon="ERROR")


class BLENDERAI_OT_start_server(bpy.types.Operator):
    bl_idname = "blenderai.start_server"
    bl_label = "Start Server"
    bl_description = "Start the BlenderAI MCP TCP bridge"

    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        if not prefs.auth_token:
            self.report({"ERROR"}, "Configure auth token in addon preferences first")
            return {"CANCELLED"}
        server.start_server(host="127.0.0.1", port=prefs.port)
        self.report({"INFO"}, f"Server starting on 127.0.0.1:{prefs.port}")
        return {"FINISHED"}


class BLENDERAI_OT_stop_server(bpy.types.Operator):
    bl_idname = "blenderai.stop_server"
    bl_label = "Stop Server"
    bl_description = "Stop the BlenderAI MCP TCP bridge"

    def execute(self, context):
        server.stop_server()
        self.report({"INFO"}, "Server stopped")
        return {"FINISHED"}


classes = (
    BLENDERAI_PT_panel,
    BLENDERAI_OT_start_server,
    BLENDERAI_OT_stop_server,
)
