"""Camera creation and framing handlers."""

from __future__ import annotations

import bpy

from ..serializers.math_types import parse_vector3
from ..serializers.objects import serialize_object
from ..utils import context
from .registry import register_handler


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


def camera_create(params: dict) -> dict:
    name = params.get("name")
    location = parse_vector3(params.get("location"), (0, -10, 5))
    rotation_euler = params.get("rotation_euler")
    collection_name = params.get("collection")
    focal_length = params.get("focal_length")

    context.push_undo("BlenderAI: Create Camera")

    cam_data = bpy.data.cameras.new(name=name or "Camera")
    if focal_length is not None:
        cam_data.lens = float(focal_length)

    obj = bpy.data.objects.new(name or cam_data.name, cam_data)
    obj.location = location
    if rotation_euler:
        obj.rotation_euler = parse_vector3(rotation_euler, tuple(obj.rotation_euler))

    if collection_name:
        coll = context.require_collection(collection_name)
        coll.objects.link(obj)
    else:
        context.get_scene().collection.objects.link(obj)

    if params.get("set_active", False):
        context.get_view_layer().objects.active = obj
        context.get_scene().camera = obj

    result = serialize_object(obj)
    result["camera"] = {
        "lens": float(cam_data.lens),
        "sensor_width": float(cam_data.sensor_width),
        "clip_start": float(cam_data.clip_start),
        "clip_end": float(cam_data.clip_end),
    }
    return result


def camera_set_focal_length(params: dict) -> dict:
    name = params.get("name") or params.get("camera")
    focal_length = params.get("focal_length") or params.get("lens")
    if not name:
        raise ValueError("name is required")
    if focal_length is None:
        raise ValueError("focal_length is required")

    obj = context.require_object(name)
    if obj.type != "CAMERA" or obj.data is None:
        raise ValueError(f"Object '{name}' is not a camera")

    context.push_undo("BlenderAI: Set Camera Focal Length")
    cam: bpy.types.Camera = obj.data
    cam.lens = float(focal_length)

    result = serialize_object(obj)
    result["camera"] = {"lens": float(cam.lens)}
    return result


def camera_frame_objects(params: dict) -> dict:
    camera_name = params.get("camera") or params.get("name")
    object_names = params.get("objects") or params.get("object_names")
    if not camera_name:
        raise ValueError("camera is required")
    if not object_names or not isinstance(object_names, list):
        raise ValueError("objects must be a non-empty list of object names")

    camera = context.require_object(camera_name)
    if camera.type != "CAMERA":
        raise ValueError(f"Object '{camera_name}' is not a camera")

    targets = []
    for object_name in object_names:
        obj = context.require_object(str(object_name))
        targets.append(obj)

    area, region = _find_view3d()
    if area is None or region is None:
        raise RuntimeError(
            "No 3D viewport found — camera_frame_objects requires Blender GUI"
        )

    window = bpy.context.window
    if window is None:
        raise RuntimeError("No Blender window available for camera framing")

    context.push_undo("BlenderAI: Frame Objects in Camera")

    view_layer = context.get_view_layer()
    for obj in view_layer.objects:
        obj.select_set(False)
    for obj in targets:
        obj.select_set(True)
    view_layer.objects.active = camera

    with context.temp_override(
        window=window,
        area=area,
        region=region,
        scene=context.get_scene(),
        view_layer=view_layer,
    ):
        bpy.ops.view3d.camera_to_view_selected()

    result = serialize_object(camera)
    result["framed_objects"] = [obj.name for obj in targets]
    return result


def register() -> None:
    register_handler("camera_create", camera_create, mutating=True)
    register_handler("camera_set_focal_length", camera_set_focal_length, mutating=True)
    register_handler("camera_frame_objects", camera_frame_objects, mutating=True)
