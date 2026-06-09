"""Selection handlers."""

from __future__ import annotations

from ..serializers.objects import serialize_object
from ..utils import context


def selection_get(params: dict) -> dict:
    view_layer = context.get_view_layer()
    selected = [serialize_object(obj) for obj in view_layer.objects if obj.select_get()]
    active = view_layer.objects.active
    return {
        "selected": selected,
        "count": len(selected),
        "active": active.name if active else None,
    }


def selection_set(params: dict) -> dict:
    names = params.get("objects") or params.get("names")
    if not isinstance(names, list):
        raise ValueError("objects must be a list of object names")

    view_layer = context.get_view_layer()
    context.push_undo("BlenderAI: Set Selection")

    for obj in view_layer.objects:
        obj.select_set(False)

    selected_objects = []
    for name in names:
        if not isinstance(name, str):
            raise ValueError("Each object name must be a string")
        obj = context.require_object(name)
        obj.select_set(True)
        selected_objects.append(obj)

    active_name = params.get("active")
    if active_name:
        view_layer.objects.active = context.require_object(active_name)
    elif selected_objects:
        view_layer.objects.active = selected_objects[-1]

    active = view_layer.objects.active
    return {
        "selected": [obj.name for obj in selected_objects],
        "count": len(selected_objects),
        "active": active.name if active else None,
    }


def register() -> None:
    from .registry import register_handler

    register_handler("selection_get", selection_get)
    register_handler("selection_set", selection_set, mutating=True)
