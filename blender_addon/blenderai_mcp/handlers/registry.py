"""Handler registry for bridge method dispatch."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

HandlerFn = Callable[[dict[str, Any]], Any]


@dataclass(frozen=True)
class Handler:
    name: str
    fn: HandlerFn
    mutating: bool = False
    description: str = ""


_handlers: dict[str, Handler] = {}

# Method name -> handler function (updated by register_handler).
HANDLER_MAP: dict[str, HandlerFn] = {}


def register_handler(
    name: str,
    fn: HandlerFn,
    *,
    mutating: bool = False,
    description: str = "",
) -> None:
    _handlers[name] = Handler(name=name, fn=fn, mutating=mutating, description=description)
    HANDLER_MAP[name] = fn


def unregister_handler(name: str) -> None:
    _handlers.pop(name, None)
    HANDLER_MAP.pop(name, None)


def get_handler(name: str) -> Handler | None:
    return _handlers.get(name)


def get_all_handlers() -> dict[str, HandlerFn]:
    return {name: handler.fn for name, handler in _handlers.items()}


def list_methods() -> list[str]:
    return sorted(_handlers.keys())


def clear_handlers() -> None:
    _handlers.clear()
    HANDLER_MAP.clear()


def register_all_handlers() -> None:
    from . import camera, collection, execute, light, material, mesh, object, render, scene, selection

    clear_handlers()
    scene.register()
    object.register()
    collection.register()
    selection.register()
    material.register()
    render.register()
    light.register()
    camera.register()
    mesh.register()
    execute.register()


def unregister_all_handlers() -> None:
    clear_handlers()
