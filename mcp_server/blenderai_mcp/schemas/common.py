"""Shared JSON Schema fragments for MCP tools."""

VECTOR3_SCHEMA = {
    "type": "array",
    "items": {"type": "number"},
    "minItems": 3,
    "maxItems": 3,
}

BOUNDS_SCHEMA = {
    "type": "object",
    "properties": {
        "min": VECTOR3_SCHEMA,
        "max": VECTOR3_SCHEMA,
        "center": VECTOR3_SCHEMA,
    },
    "required": ["min", "max", "center"],
}

OBJECT_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "uuid": {"type": "string"},
        "type": {"type": "string"},
        "location": VECTOR3_SCHEMA,
        "rotation_euler": VECTOR3_SCHEMA,
        "scale": VECTOR3_SCHEMA,
        "dimensions": VECTOR3_SCHEMA,
        "bounds": BOUNDS_SCHEMA,
        "rotation_mode": {"type": "string"},
        "visible": {"type": "boolean"},
        "parent": {"type": ["string", "null"]},
        "collections": {"type": "array", "items": {"type": "string"}},
        "materials": {"type": "array", "items": {"type": ["string", "null"]}},
    },
    "required": [
        "name",
        "uuid",
        "type",
        "location",
        "rotation_euler",
        "scale",
        "dimensions",
        "bounds",
    ],
}

ERROR_SCHEMA = {
    "type": "object",
    "properties": {
        "code": {"type": "string"},
        "message": {"type": "string"},
    },
    "required": ["code", "message"],
}
