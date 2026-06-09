"""Light creation and parameter handlers."""

from __future__ import annotations

import bpy

from ..serializers.math_types import parse_vector3, serialize_color, serialize_vector
from ..serializers.objects import serialize_object
from ..utils import context
from .registry import register_handler

VALID_LIGHT_TYPES = frozenset({"POINT", "SUN", "SPOT", "AREA"})


def _serialize_light(light: bpy.types.Light) -> dict:
    data = {
        "name": light.name,
        "type": light.type,
        "color": serialize_color(light.color),
        "energy": float(light.energy),
    }
    if light.type == "SPOT":
        data["spot_size"] = float(light.spot_size)
        data["spot_blend"] = float(light.spot_blend)
    if light.type == "AREA":
        data["shape"] = light.shape
        data["size"] = float(light.size)
        if hasattr(light, "size_y"):
            data["size_y"] = float(light.size_y)
    if light.type == "SUN":
        data["angle"] = float(light.angle)
    return data


def light_create(params: dict) -> dict:
    name = params.get("name")
    light_type = str(params.get("type", "POINT")).upper()
    if light_type not in VALID_LIGHT_TYPES:
        raise ValueError(
            f"Invalid light type '{light_type}'. Valid: {', '.join(sorted(VALID_LIGHT_TYPES))}"
        )

    location = parse_vector3(params.get("location"), (0, 0, 5))
    collection_name = params.get("collection")

    context.push_undo("BlenderAI: Create Light")

    light_data = bpy.data.lights.new(name=name or "Light", type=light_type)
    obj = bpy.data.objects.new(name or light_data.name, light_data)
    obj.location = location

    if collection_name:
        coll = context.require_collection(collection_name)
        coll.objects.link(obj)
    else:
        context.get_scene().collection.objects.link(obj)

    if "energy" in params:
        light_data.energy = float(params["energy"])
    if "color" in params and len(params["color"]) >= 3:
        light_data.color = (
            float(params["color"][0]),
            float(params["color"][1]),
            float(params["color"][2]),
        )

    result = serialize_object(obj)
    result["light"] = _serialize_light(light_data)
    return result


def light_set_params(params: dict) -> dict:
    name = params.get("name") or params.get("object")
    if not name:
        raise ValueError("name is required")

    obj = context.require_object(name)
    if obj.type != "LIGHT" or obj.data is None:
        raise ValueError(f"Object '{name}' is not a light")

    light: bpy.types.Light = obj.data

    context.push_undo("BlenderAI: Set Light Params")

    if "energy" in params:
        light.energy = float(params["energy"])
    if "color" in params and len(params["color"]) >= 3:
        light.color = (
            float(params["color"][0]),
            float(params["color"][1]),
            float(params["color"][2]),
        )
    if "location" in params:
        obj.location = parse_vector3(params["location"], tuple(obj.location))
    if "rotation_euler" in params:
        obj.rotation_euler = parse_vector3(params["rotation_euler"], tuple(obj.rotation_euler))
    if light.type == "SPOT":
        if "spot_size" in params:
            light.spot_size = float(params["spot_size"])
        if "spot_blend" in params:
            light.spot_blend = float(params["spot_blend"])
    if light.type == "AREA":
        if "shape" in params:
            light.shape = str(params["shape"])
        if "size" in params:
            light.size = float(params["size"])
        if "size_y" in params and hasattr(light, "size_y"):
            light.size_y = float(params["size_y"])
    if light.type == "SUN" and "angle" in params:
        light.angle = float(params["angle"])

    result = serialize_object(obj)
    result["light"] = _serialize_light(light)
    return result


def register() -> None:
    register_handler("light_create", light_create, mutating=True)
    register_handler("light_set_params", light_set_params, mutating=True)
