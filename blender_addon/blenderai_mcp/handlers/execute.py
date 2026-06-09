"""Execute and batch handlers."""



from __future__ import annotations



import io

import traceback

from contextlib import redirect_stderr, redirect_stdout

from typing import Any



from .registry import register_handler



DESTRUCTIVE_NOT_CONFIRMED = "DESTRUCTIVE_NOT_CONFIRMED"





def _json_safe(value: Any) -> Any:

    if value is None or isinstance(value, (bool, int, float, str)):

        return value

    if isinstance(value, (list, tuple)):

        return [_json_safe(v) for v in value]

    if isinstance(value, dict):

        return {str(k): _json_safe(v) for k, v in value.items()}

    return str(value)





def execute_python(params: dict[str, Any]) -> dict[str, Any]:

    code = params.get("code")

    if not isinstance(code, str) or not code.strip():

        raise ValueError("code is required")



    if not params.get("confirm_destructive"):

        raise PermissionError(

            DESTRUCTIVE_NOT_CONFIRMED,

            "execute_python requires confirm_destructive=true",

        )



    import bpy



    stdout_buf = io.StringIO()

    stderr_buf = io.StringIO()

    global_ns: dict[str, Any] = {"__builtins__": __builtins__, "bpy": bpy}

    local_ns: dict[str, Any] = {}

    error: dict[str, str] | None = None

    result: Any = None



    try:

        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):

            exec(compile(code, "<blenderai>", "exec"), global_ns, local_ns)

        result = local_ns.get("result", local_ns.get("RESULT"))

    except Exception as exc:

        error = {

            "type": type(exc).__name__,

            "message": str(exc),

            "traceback": traceback.format_exc(),

        }



    return {

        "executed": error is None,

        "stdout": stdout_buf.getvalue(),

        "stderr": stderr_buf.getvalue(),

        "error": error,

        "result": _json_safe(result) if error is None else None,

    }





def batch_execute(params: dict[str, Any]) -> dict[str, Any]:
    calls = params.get("calls")
    if not isinstance(calls, list) or not calls:
        raise ValueError("calls must be a non-empty list")

    from .registry import get_handler

    results: list[dict[str, Any]] = []
    for index, call in enumerate(calls):
        if not isinstance(call, dict):
            results.append({"index": index, "ok": False, "error": "call must be an object"})
            continue

        method = call.get("method") or call.get("name")
        call_params = dict(call.get("params") or call.get("arguments") or {})
        if not method:
            results.append({"index": index, "ok": False, "error": "method is required"})
            continue

        handler = get_handler(str(method))
        if handler is None:
            results.append(
                {
                    "index": index,
                    "method": method,
                    "ok": False,
                    "error": f"Unknown method: {method}",
                }
            )
            continue

        try:
            data = handler.fn(call_params)
            results.append({"index": index, "method": method, "ok": True, "data": data})
        except Exception as exc:
            results.append(
                {
                    "index": index,
                    "method": method,
                    "ok": False,
                    "error": str(exc),
                }
            )

    return {"count": len(results), "results": results}


def register() -> None:
    register_handler(
        "execute_python",
        execute_python,
        mutating=True,
        description="Run Python code on Blender main thread (requires confirm_destructive)",
    )
    register_handler(
        "batch_execute",
        batch_execute,
        mutating=True,
        description="Execute multiple bridge methods in one main-thread tick",
    )


