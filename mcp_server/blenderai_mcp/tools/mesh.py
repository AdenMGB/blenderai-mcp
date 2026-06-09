"""MCP tools for mesh editing."""

from __future__ import annotations

from typing import Any

import mcp.types as types

AUTH_TOKEN_SCHEMA = {
    "type": "string",
    "description": "Optional; bridge client injects BLENDERAI_AUTH_TOKEN if omitted.",
}

OBJECT_NAME_SCHEMA = {
    "type": "string",
    "description": "Target mesh object name.",
}

MESH_SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "ok": {"type": "boolean"},
        "object": {"type": "string"},
        "vertex_count": {"type": "integer"},
        "face_count": {"type": "integer"},
        "edge_count": {"type": "integer"},
        "bounds": {
            "type": "object",
            "properties": {
                "min": {"type": "array", "items": {"type": "number"}},
                "max": {"type": "array", "items": {"type": "number"}},
            },
        },
        "error": {"type": "object"},
    },
    "required": ["ok"],
}

MESH_CREATE_INPUT = {
    "type": "object",
    "properties": {
        "vertices": {
            "type": "array",
            "items": {
                "type": "array",
                "items": {"type": "number"},
                "minItems": 3,
                "maxItems": 3,
            },
            "description": "Vertex positions [[x,y,z], ...]",
        },
        "faces": {
            "type": "array",
            "items": {
                "type": "array",
                "items": {"type": "integer"},
                "minItems": 3,
            },
            "description": "Face vertex index lists",
        },
        "name": {"type": "string"},
        "collection": {"type": "string"},
        "auth_token": AUTH_TOKEN_SCHEMA,
    },
    "required": ["vertices", "faces"],
}

MESH_GET_GEOMETRY_INPUT = {
    "type": "object",
    "properties": {
        "object": OBJECT_NAME_SCHEMA,
        "vert_offset": {"type": "integer", "default": 0},
        "face_offset": {"type": "integer", "default": 0},
        "max_verts": {"type": "integer", "default": 5000},
        "max_faces": {"type": "integer", "default": 5000},
        "auth_token": AUTH_TOKEN_SCHEMA,
    },
    "required": ["object"],
}

MESH_SET_VERTICES_INPUT = {
    "type": "object",
    "properties": {
        "object": OBJECT_NAME_SCHEMA,
        "vertices": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer"},
                    "co": {
                        "type": "array",
                        "items": {"type": "number"},
                        "minItems": 3,
                        "maxItems": 3,
                    },
                },
                "required": ["index", "co"],
            },
        },
        "auth_token": AUTH_TOKEN_SCHEMA,
    },
    "required": ["object", "vertices"],
}

MESH_EXTRUDE_INPUT = {
    "type": "object",
    "properties": {
        "object": OBJECT_NAME_SCHEMA,
        "face_indices": {"type": "array", "items": {"type": "integer"}},
        "offset": {
            "type": "array",
            "items": {"type": "number"},
            "minItems": 3,
            "maxItems": 3,
            "description": "Extrusion offset [x,y,z]",
        },
        "auth_token": AUTH_TOKEN_SCHEMA,
    },
    "required": ["object", "face_indices"],
}

MESH_SUBDIVIDE_INPUT = {
    "type": "object",
    "properties": {
        "object": OBJECT_NAME_SCHEMA,
        "cuts": {"type": "integer", "default": 1},
        "face_indices": {"type": "array", "items": {"type": "integer"}},
        "auth_token": AUTH_TOKEN_SCHEMA,
    },
    "required": ["object"],
}

MESH_MERGE_INPUT = {
    "type": "object",
    "properties": {
        "object": OBJECT_NAME_SCHEMA,
        "distance": {"type": "number", "default": 0.001},
        "auth_token": AUTH_TOKEN_SCHEMA,
    },
    "required": ["object"],
}

MESH_UV_INPUT = {
    "type": "object",
    "properties": {
        "object": OBJECT_NAME_SCHEMA,
        "name": {"type": "string", "default": "UVMap"},
        "auth_token": AUTH_TOKEN_SCHEMA,
    },
    "required": ["object"],
}

MESH_SMOOTH_INPUT = {
    "type": "object",
    "properties": {
        "object": OBJECT_NAME_SCHEMA,
        "smooth": {"type": "boolean", "default": True},
        "auth_token": AUTH_TOKEN_SCHEMA,
    },
    "required": ["object"],
}

MODIFIER_MIRROR_INPUT = {
    "type": "object",
    "properties": {
        "object": OBJECT_NAME_SCHEMA,
        "name": {"type": "string"},
        "axis": {"type": "string", "enum": ["X", "Y", "Z"], "default": "X"},
        "merge_threshold": {"type": "number"},
        "auth_token": AUTH_TOKEN_SCHEMA,
    },
    "required": ["object"],
}

MODIFIER_ARRAY_INPUT = {
    "type": "object",
    "properties": {
        "object": OBJECT_NAME_SCHEMA,
        "name": {"type": "string"},
        "count": {"type": "integer"},
        "offset": {
            "type": "array",
            "items": {"type": "number"},
            "minItems": 3,
            "maxItems": 3,
        },
        "auth_token": AUTH_TOKEN_SCHEMA,
    },
    "required": ["object"],
}

MODIFIER_SUBDIV_INPUT = {
    "type": "object",
    "properties": {
        "object": OBJECT_NAME_SCHEMA,
        "name": {"type": "string"},
        "levels": {"type": "integer"},
        "render_levels": {"type": "integer"},
        "auth_token": AUTH_TOKEN_SCHEMA,
    },
    "required": ["object"],
}


def _mesh_tool(name: str, description: str, input_schema: dict) -> types.Tool:
    return types.Tool(
        name=name,
        description=description,
        inputSchema=input_schema,
        outputSchema=MESH_SUMMARY_SCHEMA,
    )


TOOLS = [
    _mesh_tool(
        "mesh_create_from_verts_faces",
        "Create a mesh object from vertex positions and face index lists.",
        MESH_CREATE_INPUT,
    ),
    _mesh_tool(
        "mesh_get_geometry",
        "Read mesh vertices and faces with pagination (max_verts/max_faces).",
        MESH_GET_GEOMETRY_INPUT,
    ),
    _mesh_tool(
        "mesh_set_vertices",
        "Update vertex positions by index using bmesh.",
        MESH_SET_VERTICES_INPUT,
    ),
    _mesh_tool(
        "mesh_extrude_region",
        "Extrude selected faces by an offset vector via bmesh.",
        MESH_EXTRUDE_INPUT,
    ),
    _mesh_tool(
        "mesh_subdivide",
        "Subdivide mesh faces (all or by face_indices).",
        MESH_SUBDIVIDE_INPUT,
    ),
    _mesh_tool(
        "mesh_merge_vertices",
        "Merge vertices within a distance threshold.",
        MESH_MERGE_INPUT,
    ),
    _mesh_tool(
        "mesh_add_uv_layer",
        "Add a UV layer to a mesh.",
        MESH_UV_INPUT,
    ),
    _mesh_tool(
        "mesh_smooth_shade",
        "Set smooth or flat shading on mesh faces.",
        MESH_SMOOTH_INPUT,
    ),
    _mesh_tool(
        "modifier_add_mirror",
        "Add a mirror modifier to a mesh object.",
        MODIFIER_MIRROR_INPUT,
    ),
    _mesh_tool(
        "modifier_add_array",
        "Add an array modifier to a mesh object.",
        MODIFIER_ARRAY_INPUT,
    ),
    _mesh_tool(
        "modifier_add_subdivision",
        "Add a subdivision surface modifier.",
        MODIFIER_SUBDIV_INPUT,
    ),
]

TOOL_HANDLERS: dict[str, str] = {tool.name: tool.name for tool in TOOLS}


def format_result(data: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, **data}
