"""Agent-oriented tool descriptions and post-call feedback enrichment."""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Shared schema fragment — include on tool outputSchema definitions
# ---------------------------------------------------------------------------

AGENT_FEEDBACK_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "next_steps": {"type": "array", "items": {"type": "string"}},
        "verify_with": {"type": "string"},
        "warnings": {"type": "array", "items": {"type": "string"}},
        "capabilities_hint": {"type": "string"},
    },
}

STANDARD_OK_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "ok": {"type": "boolean"},
        "agent_feedback": AGENT_FEEDBACK_SCHEMA,
        "error": {"type": "object"},
    },
    "required": ["ok"],
}


def with_agent_feedback(schema: dict[str, Any]) -> dict[str, Any]:
    """Merge agent_feedback + ok into an existing output schema."""
    props = dict(schema.get("properties", {}))
    props.setdefault("ok", {"type": "boolean"})
    props["agent_feedback"] = AGENT_FEEDBACK_SCHEMA
    return {**schema, "properties": props, "required": schema.get("required", ["ok"])}


def _bounds_height(bounds: dict) -> float | None:
    try:
        return float(bounds["max"][2]) - float(bounds["min"][2])
    except (KeyError, TypeError, IndexError):
        return None


def _bounds_top(bounds: dict) -> float | None:
    try:
        return float(bounds["max"][2])
    except (KeyError, TypeError, IndexError):
        return None


def _bounds_bottom(bounds: dict) -> float | None:
    try:
        return float(bounds["min"][2])
    except (KeyError, TypeError, IndexError):
        return None


def enrich_result(tool_name: str, data: dict[str, Any]) -> dict[str, Any]:
    """Add agent_feedback block so models know what to do next."""
    feedback: dict[str, Any] = {
        "summary": "",
        "next_steps": [],
        "verify_with": "",
        "warnings": [],
        "capabilities_hint": "",
    }

    if tool_name == "ping":
        ver = data.get("blender_version", "?")
        feedback["summary"] = f"Blender bridge live ({ver})."
        feedback["next_steps"] = ["scene_get_summary", "viewport_capture"]
        feedback["verify_with"] = "scene_get_summary"

    elif tool_name == "scene_get_summary":
        count = data.get("object_count", 0)
        feedback["summary"] = f"Scene '{data.get('name')}' has {count} objects."
        feedback["next_steps"] = ["scene_list_objects", "selection_get"]
        feedback["verify_with"] = "viewport_capture"
        feedback["capabilities_hint"] = (
            "Use batch_execute to create multiple objects, then viewport_capture to visually verify."
        )

    elif tool_name == "object_create_primitive":
        name = data.get("name", "object")
        b = data.get("bounds", {})
        bottom = _bounds_bottom(b)
        feedback["summary"] = f"Created {data.get('primitive', 'primitive')} '{name}'."
        feedback["next_steps"] = [
            "Check bounds.min[2] — should sit on ground (≈0) unless floating intentionally",
            "material_create + material_assign for color",
            "viewport_capture to verify proportions",
        ]
        feedback["verify_with"] = "viewport_capture"
        if bottom is not None and bottom < -0.05:
            feedback["warnings"].append(
                f"Object bottom z={bottom:.3f} is below ground — raise location or adjust scale."
            )
        elif bottom is not None and bottom > 0.15:
            feedback["warnings"].append(
                f"Object bottom z={bottom:.3f} is floating — lower location so bounds.min[2] ≈ 0."
            )
        feedback["capabilities_hint"] = (
            "Stack primitives with overlapping bounds (use bounds.max/min z). "
            "Avoid object_set_parent until fixed — use world-space object_set_transform instead."
        )

    elif tool_name == "object_set_transform":
        name = data.get("name", "object")
        b = data.get("bounds", {})
        feedback["summary"] = f"Updated transform on '{name}'."
        feedback["next_steps"] = [
            "Compare bounds.min/max against neighboring objects for gaps",
            "viewport_capture after grouping related moves",
        ]
        feedback["verify_with"] = "object_get"
        top, bottom = _bounds_top(b), _bounds_bottom(b)
        if top is not None and bottom is not None:
            feedback["summary"] += f" World z: {bottom:.2f} → {top:.2f}."

    elif tool_name == "object_set_parent":
        feedback["summary"] = f"Parent set on '{data.get('name')}'."
        feedback["warnings"].append(
            "Parenting can shift perceived world positions. Prefer object_set_transform in world "
            "space for layout; use object_get bounds to confirm overlap after parenting."
        )
        feedback["verify_with"] = "viewport_capture"

    elif tool_name == "batch_execute":
        results = data.get("results", [])
        ok_count = sum(1 for r in results if r.get("ok"))
        fail = [r for r in results if not r.get("ok")]
        feedback["summary"] = f"Batch: {ok_count}/{len(results)} calls succeeded."
        if fail:
            for r in fail[:3]:
                feedback["warnings"].append(
                    f"Step {r.get('index')}: {r.get('method')} — {r.get('error', 'failed')}"
                )
        feedback["next_steps"] = [
            "viewport_capture once after the batch (not after every step)",
            "object_get on key objects to validate bounds overlap",
        ]
        feedback["verify_with"] = "viewport_capture"

    elif tool_name in ("viewport_capture", "render_still"):
        feedback["summary"] = "Image captured — inspect composition, gaps, materials, lighting."
        feedback["next_steps"] = [
            "Describe what you see vs. goal; fix with object_set_transform / materials",
            "If grey/untextured: viewport_set_shading MATERIAL then recapture",
            "If too dark: light_create AREA or SUN + render_set_engine CYCLES for quality",
        ]
        feedback["verify_with"] = "viewport_capture"
        feedback["capabilities_hint"] = (
            "Shader nodes: material_create → material_set_principled (base_color, metallic, "
            "roughness, emission). material_get returns node tree summary. Advanced node graphs "
            "(Noise, Voronoi, Mix, Bump, normal maps) via execute_python with confirm_destructive. "
            "Geometry Nodes & modifiers: modifier_add_subdivision, mirror, array; mesh_extrude_region."
        )

    elif tool_name == "viewport_set_shading":
        feedback["summary"] = f"Viewport shading: {data.get('shading', 'updated')}."
        feedback["next_steps"] = ["viewport_capture to see materials/lighting accurately"]

    elif tool_name.startswith("material_"):
        feedback["summary"] = f"Material op '{tool_name}' on '{data.get('name', data.get('material', ''))}'."
        feedback["next_steps"] = [
            "viewport_set_shading MATERIAL then viewport_capture",
            "material_get to inspect node tree",
            "material_set_principled for metallic/roughness/emission tweaks",
        ]
        feedback["capabilities_hint"] = (
            "Principled BSDF supports base_color, metallic, roughness, emission, alpha. "
            "For procedural wood/grass/sky: build shader node trees in Python (ShaderNodeTexNoise, "
            "ShaderNodeTexVoronoi, ShaderNodeMix, ShaderNodeBump) via execute_python."
        )

    elif tool_name.startswith("mesh_") or tool_name.startswith("modifier_"):
        obj = data.get("object", "")
        vc = data.get("vertex_count", "?")
        fc = data.get("face_count", "?")
        feedback["summary"] = f"Mesh '{obj}': {vc} verts, {fc} faces."
        feedback["next_steps"] = ["viewport_capture", "mesh_get_geometry with max_verts if needed"]
        feedback["verify_with"] = "viewport_capture"

    elif tool_name == "execute_python":
        if data.get("executed"):
            feedback["summary"] = "Python executed in Blender."
            if data.get("stdout"):
                feedback["next_steps"].append("Read stdout in response before next action")
        else:
            feedback["summary"] = "Python execution failed — read error.traceback."
            feedback["warnings"].append(data.get("error", {}).get("message", "unknown error"))

    elif tool_name.startswith("light_") or tool_name.startswith("camera_"):
        feedback["summary"] = f"Updated {tool_name.replace('_', ' ')}."
        feedback["next_steps"] = ["viewport_capture", "render_still for final quality check"]
        feedback["capabilities_hint"] = (
            "Three-point lighting: SUN key + AREA fill + low AREA rim. "
            "camera_frame_objects before viewport_capture for framing."
        )

    else:
        feedback["summary"] = f"{tool_name} completed."
        feedback["next_steps"] = ["viewport_capture to verify visually"]
        feedback["verify_with"] = "viewport_capture"

    data = dict(data)
    data["agent_feedback"] = feedback
    return data
