"""Material creation and principled BSDF handlers."""

from __future__ import annotations

from typing import Any

import bpy

from ..serializers.math_types import serialize_color
from ..utils import context
from .registry import register_handler

# Blender 4.2+ / 5.x Principled BSDF socket indices (language-independent).
PI_BASE_COLOR = 0
PI_METALLIC = 1
PI_ROUGHNESS = 2
PI_EMISSION_COLOR = 26
PI_EMISSION_STRENGTH = 27


def _get_or_create_principled(material: bpy.types.Material) -> bpy.types.ShaderNodeBsdfPrincipled:
    if not material.use_nodes or not material.node_tree:
        material.use_nodes = True
    nodes = material.node_tree.nodes
    principled = None
    for node in nodes:
        if node.type == "BSDF_PRINCIPLED":
            principled = node
            break
    if principled is None:
        principled = nodes.new("ShaderNodeBsdfPrincipled")
        principled.location = (0, 0)
        output = None
        for node in nodes:
            if node.type == "OUTPUT_MATERIAL":
                output = node
                break
        if output is None:
            output = nodes.new("ShaderNodeOutputMaterial")
            output.location = (300, 0)
        material.node_tree.links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    return principled


def _set_input_color(node: bpy.types.Node, index: int, values: list | tuple) -> None:
    node.inputs[index].default_value = (
        float(values[0]),
        float(values[1]),
        float(values[2]),
        float(values[3]) if len(values) > 3 else 1.0,
    )


def _apply_emission(principled: bpy.types.ShaderNodeBsdfPrincipled, emission: Any) -> None:
    if emission is None:
        return
    if isinstance(emission, (int, float)):
        principled.inputs[PI_EMISSION_STRENGTH].default_value = float(emission)
        return
    if isinstance(emission, (list, tuple)):
        if len(emission) >= 3:
            _set_input_color(principled, PI_EMISSION_COLOR, emission)
        if len(emission) == 1:
            principled.inputs[PI_EMISSION_STRENGTH].default_value = float(emission[0])
        return
    if isinstance(emission, dict):
        if "color" in emission:
            _set_input_color(principled, PI_EMISSION_COLOR, emission["color"])
        if "strength" in emission:
            principled.inputs[PI_EMISSION_STRENGTH].default_value = float(emission["strength"])


def serialize_material(mat: bpy.types.Material) -> dict[str, Any]:
    data: dict[str, Any] = {
        "name": mat.name,
        "use_nodes": mat.use_nodes,
    }
    if mat.use_nodes and mat.node_tree:
        principled = None
        for node in mat.node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                principled = node
                break
        if principled:
            data["principled"] = {
                "base_color": serialize_color(principled.inputs[PI_BASE_COLOR].default_value),
                "metallic": float(principled.inputs[PI_METALLIC].default_value),
                "roughness": float(principled.inputs[PI_ROUGHNESS].default_value),
                "emission_color": serialize_color(
                    principled.inputs[PI_EMISSION_COLOR].default_value
                ),
                "emission_strength": float(
                    principled.inputs[PI_EMISSION_STRENGTH].default_value
                ),
            }
    return data


def _serialize_node_tree(mat: bpy.types.Material) -> dict[str, Any]:
    if not mat.use_nodes or not mat.node_tree:
        return {"nodes": [], "links": []}

    tree = mat.node_tree
    nodes = []
    for node in tree.nodes:
        nodes.append(
            {
                "name": node.name,
                "type": node.type,
                "label": node.label,
                "inputs": [
                    {
                        "index": index,
                        "identifier": socket.identifier,
                        "name": socket.name,
                        "type": socket.type,
                    }
                    for index, socket in enumerate(node.inputs)
                ],
                "outputs": [
                    {
                        "index": index,
                        "identifier": socket.identifier,
                        "name": socket.name,
                        "type": socket.type,
                    }
                    for index, socket in enumerate(node.outputs)
                ],
            }
        )

    links = []
    for link in tree.links:
        links.append(
            {
                "from_node": link.from_node.name,
                "from_socket": link.from_socket.identifier,
                "to_node": link.to_node.name,
                "to_socket": link.to_socket.identifier,
            }
        )

    return {"nodes": nodes, "links": links}


def material_create(params: dict) -> dict:
    name = params.get("name")
    if not name:
        raise ValueError("name is required")

    if context.find_material(name):
        raise ValueError(f"Material '{name}' already exists")

    context.push_undo("BlenderAI: Create Material")
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True

    base_color = params.get("base_color")
    if base_color and len(base_color) >= 3:
        principled = _get_or_create_principled(mat)
        _set_input_color(principled, PI_BASE_COLOR, base_color)

    return serialize_material(mat)


def material_assign(params: dict) -> dict:
    object_name = params.get("object") or params.get("name")
    material_name = params.get("material")
    slot_index = int(params.get("slot", 0))

    if not object_name or not material_name:
        raise ValueError("object and material are required")

    obj = context.require_object(object_name)
    if obj.type != "MESH":
        raise ValueError(f"Object '{object_name}' is not a mesh")

    mat = context.find_material(material_name)
    if mat is None:
        raise LookupError(f"Material '{material_name}' not found")

    context.push_undo("BlenderAI: Assign Material")

    while len(obj.material_slots) <= slot_index:
        obj.data.materials.append(None)

    obj.material_slots[slot_index].material = mat

    return {
        "object": obj.name,
        "material": mat.name,
        "slot": slot_index,
    }


def material_set_principled(params: dict) -> dict:
    material_name = params.get("material") or params.get("name")
    if not material_name:
        raise ValueError("material name is required")

    mat = context.find_material(material_name)
    if mat is None:
        raise LookupError(f"Material '{material_name}' not found")

    context.push_undo("BlenderAI: Set Principled BSDF")
    principled = _get_or_create_principled(mat)

    if "base_color" in params:
        _set_input_color(principled, PI_BASE_COLOR, params["base_color"])
    if "metallic" in params:
        principled.inputs[PI_METALLIC].default_value = float(params["metallic"])
    if "roughness" in params:
        principled.inputs[PI_ROUGHNESS].default_value = float(params["roughness"])
    if "emission" in params:
        _apply_emission(principled, params["emission"])
    if "emission_color" in params:
        _set_input_color(principled, PI_EMISSION_COLOR, params["emission_color"])
    if "emission_strength" in params:
        principled.inputs[PI_EMISSION_STRENGTH].default_value = float(
            params["emission_strength"]
        )

    return serialize_material(mat)


def material_get(params: dict) -> dict:
    material_name = params.get("material") or params.get("name")
    if not material_name:
        raise ValueError("material name is required")

    mat = context.find_material(material_name)
    if mat is None:
        raise LookupError(f"Material '{material_name}' not found")

    data = serialize_material(mat)
    data["node_tree"] = _serialize_node_tree(mat)
    return data


def register() -> None:
    register_handler("material_create", material_create, mutating=True)
    register_handler("material_assign", material_assign, mutating=True)
    register_handler("material_set_principled", material_set_principled, mutating=True)
    register_handler("material_get", material_get)
