"""MCP tool for guarded Python execution in Blender."""



from __future__ import annotations



from typing import Any



import mcp.types as types



EXECUTE_PYTHON_INPUT = {

    "type": "object",

    "properties": {

        "code": {

            "type": "string",

            "description": "Python source to execute in Blender. Set `result` in locals to return a value.",

        },

        "confirm_destructive": {

            "type": "boolean",

            "description": "Must be true to run arbitrary Python on the scene.",

        },

        "auth_token": {

            "type": "string",

            "description": "Optional; bridge client injects BLENDERAI_AUTH_TOKEN if omitted.",

        },

    },

    "required": ["code", "confirm_destructive"],

}



EXECUTE_PYTHON_OUTPUT = {

    "type": "object",

    "properties": {

        "ok": {"type": "boolean"},

        "executed": {"type": "boolean"},

        "stdout": {"type": "string"},

        "stderr": {"type": "string"},

        "result": {},

        "error": {

            "type": "object",

            "properties": {

                "type": {"type": "string"},

                "message": {"type": "string"},

                "traceback": {"type": "string"},

            },

        },

    },

    "required": ["ok"],

}



BATCH_EXECUTE_INPUT = {
    "type": "object",
    "properties": {
        "calls": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "method": {"type": "string"},
                    "params": {"type": "object"},
                },
                "required": ["method"],
            },
        },
        "auth_token": {
            "type": "string",
            "description": "Optional; bridge client injects BLENDERAI_AUTH_TOKEN if omitted.",
        },
    },
    "required": ["calls"],
}

BATCH_EXECUTE_OUTPUT = {
    "type": "object",
    "properties": {
        "ok": {"type": "boolean"},
        "count": {"type": "integer"},
        "results": {"type": "array", "items": {"type": "object"}},
    },
    "required": ["ok", "count", "results"],
}

TOOLS = [
    types.Tool(
        name="execute_python",
        description=(
            "Run Python code on Blender's main thread. Requires confirm_destructive=true. "
            "Captures stdout/stderr; assign to `result` to return a JSON-safe value."
        ),
        inputSchema=EXECUTE_PYTHON_INPUT,
        outputSchema=EXECUTE_PYTHON_OUTPUT,
    ),
    types.Tool(
        name="batch_execute",
        description="Execute multiple bridge methods in one request to reduce round-trips.",
        inputSchema=BATCH_EXECUTE_INPUT,
        outputSchema=BATCH_EXECUTE_OUTPUT,
    ),
]

TOOL_HANDLERS = {
    "execute_python": "execute_python",
    "batch_execute": "batch_execute",
}





def format_result(data: dict[str, Any]) -> dict[str, Any]:

    return {"ok": True, **data}


