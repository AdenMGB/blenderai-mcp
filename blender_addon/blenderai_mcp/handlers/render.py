"""Rendering and viewport capture handlers."""

from __future__ import annotations

import base64
import os
import tempfile

import bpy

from ..utils import context

VALID_ENGINES = frozenset(
    {"BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "CYCLES", "BLENDER_WORKBENCH"}
)
VALID_SHADING = frozenset({"WIREFRAME", "SOLID", "MATERIAL", "RENDERED"})


def _find_view3d() -> tuple[bpy.types.Area | None, bpy.types.Region | None]:
    screen = bpy.context.screen
    if screen is None:
        return None, None
    for area in screen.areas:
        if area.type == "VIEW_3D":
            for region in area.regions:
                if region.type == "WINDOW":
                    return area, region
    return None, None


def _png_image_payload(filepath: str, name: str = "render") -> dict:
    with open(filepath, "rb") as handle:
        encoded = base64.b64encode(handle.read()).decode("ascii")
    return {
        "name": name,
        "mime_type": "image/png",
        "data": encoded,
    }


def _image_result(filepath: str, name: str = "render") -> dict:
    abs_path = bpy.path.abspath(filepath)
    return {
        "filepath": abs_path,
        "format": "png",
        "images": [_png_image_payload(abs_path, name=name)],
    }


def viewport_capture(params: dict) -> dict:
    """Capture the 3D viewport via OpenGL render (requires GUI / VIEW_3D area)."""
    filepath = params.get("filepath")
    if not filepath:
        fd, filepath = tempfile.mkstemp(suffix=".png", prefix="blenderai_viewport_")
        os.close(fd)

    area, region = _find_view3d()
    if area is None or region is None:
        raise RuntimeError(
            "No 3D viewport found — viewport_capture requires Blender GUI with a VIEW_3D area"
        )

    scene = context.get_scene()
    scene.render.filepath = filepath
    scene.render.image_settings.file_format = "PNG"

    context.push_undo("BlenderAI: Viewport Capture")

    window = bpy.context.window
    if window is None:
        raise RuntimeError("No Blender window available for viewport capture")

    with context.temp_override(window=window, area=area, region=region):
        bpy.ops.render.opengl(write_still=True)

    abs_path = bpy.path.abspath(filepath)
    if not os.path.isfile(abs_path):
        raise RuntimeError("Viewport capture failed — no image produced")

    return _image_result(abs_path, name="viewport")


def render_still(params: dict) -> dict:
    filepath = params.get("filepath")
    if not filepath:
        fd, filepath = tempfile.mkstemp(suffix=".png", prefix="blenderai_render_")
        os.close(fd)

    scene = context.get_scene()
    scene.render.filepath = filepath
    scene.render.image_settings.file_format = "PNG"

    context.push_undo("BlenderAI: Render Still")
    bpy.ops.render.render(write_still=True)

    abs_path = bpy.path.abspath(filepath)
    if not os.path.isfile(abs_path):
        raise RuntimeError("Render still failed — no image produced")

    include_image = params.get("include_image", True)
    result: dict = {"filepath": abs_path, "format": "png", "images": []}
    if include_image:
        result["images"] = [_png_image_payload(abs_path, name="render")]
    return result


def render_set_engine(params: dict) -> dict:
    engine = params.get("engine")
    if not engine:
        raise ValueError("engine is required")
    if engine not in VALID_ENGINES:
        raise ValueError(f"Invalid engine '{engine}'. Valid: {', '.join(sorted(VALID_ENGINES))}")

    context.push_undo("BlenderAI: Set Render Engine")
    scene = context.get_scene()
    scene.render.engine = engine

    return {"engine": scene.render.engine, "scene": scene.name}


def render_set_resolution(params: dict) -> dict:
    scene = context.get_scene()

    context.push_undo("BlenderAI: Set Resolution")

    if "resolution_x" in params:
        scene.render.resolution_x = int(params["resolution_x"])
    if "resolution_y" in params:
        scene.render.resolution_y = int(params["resolution_y"])
    if "resolution_percentage" in params:
        scene.render.resolution_percentage = int(params["resolution_percentage"])

    return {
        "resolution_x": scene.render.resolution_x,
        "resolution_y": scene.render.resolution_y,
        "resolution_percentage": scene.render.resolution_percentage,
    }


def render_set_samples(params: dict) -> dict:
    if "samples" not in params:
        raise ValueError("samples is required")

    samples = int(params["samples"])
    scene = context.get_scene()
    engine = scene.render.engine

    context.push_undo("BlenderAI: Set Render Samples")

    if engine == "CYCLES":
        scene.cycles.samples = samples
    elif engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        scene.eevee.taa_render_samples = samples
    else:
        raise ValueError(f"render_set_samples is not supported for engine '{engine}'")

    return {"engine": engine, "samples": samples}


def viewport_set_shading(params: dict) -> dict:
    shading = params.get("shading") or params.get("mode")
    if not shading:
        raise ValueError("shading is required (WIREFRAME, SOLID, MATERIAL, RENDERED)")

    shading = str(shading).upper()
    if shading not in VALID_SHADING:
        raise ValueError(
            f"Invalid shading '{shading}'. Valid: {', '.join(sorted(VALID_SHADING))}"
        )

    area, _ = _find_view3d()
    if area is None:
        raise RuntimeError(
            "No 3D viewport found — viewport_set_shading requires Blender GUI"
        )

    context.push_undo("BlenderAI: Set Viewport Shading")

    for space in area.spaces:
        if space.type == "VIEW_3D":
            space.shading.type = shading
            return {"shading": space.shading.type, "area": area.type}

    raise RuntimeError("VIEW_3D space not found in viewport area")


def register() -> None:
    from .registry import register_handler

    register_handler("viewport_capture", viewport_capture, mutating=True)
    register_handler("render_still", render_still, mutating=True)
    register_handler("render_set_engine", render_set_engine, mutating=True)
    register_handler("render_set_resolution", render_set_resolution, mutating=True)
    register_handler("render_set_samples", render_set_samples, mutating=True)
    register_handler("viewport_set_shading", viewport_set_shading, mutating=True)
