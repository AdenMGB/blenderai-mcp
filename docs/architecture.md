# BlenderAI MCP Architecture

## Overview

BlenderAI uses a **hybrid architecture** that separates MCP protocol handling from Blender's main-thread execution requirements.

```
┌─────────────────┐     stdio      ┌──────────────────┐     TCP/JSON     ┌─────────────────────┐
│  Cursor / MCP   │ ◄────────────► │  blenderai-mcp   │ ◄──────────────► │  Blender Addon      │
│  Client         │                │  (external proc) │   127.0.0.1      │  (in Blender proc)  │
└─────────────────┘                └──────────────────┘                  └─────────────────────┘
                                                                              │
                                                                              ▼
                                                                    bpy.app.timers (main thread)
                                                                    queue.Queue dispatcher
```

## Components

### Blender Addon (`blender_addon/blenderai_mcp/`)

- **TCP server** binds to `127.0.0.1` only (configurable port, default `9876`).
- A **background socket thread** accepts connections and reads newline-delimited JSON.
- Requests are placed on a **thread-safe `queue.Queue`**.
- **`bpy.app.timers`** polls the queue every ~8ms and runs handlers on Blender's main thread.
- All mutating operations call `bpy.ops.ed.undo_push` before changes.
- Handlers return structured JSON via serializers.

### External MCP Server (`mcp_server/blenderai_mcp/`)

- Runs as a **stdio MCP server** (invoked via `uvx blenderai-mcp`).
- Translates MCP tool calls into JSON RPC requests over TCP.
- Reads connection settings from environment variables:
  - `BLENDERAI_HOST` (default `127.0.0.1`)
  - `BLENDERAI_PORT` (default `9876`)
  - `BLENDERAI_AUTH_TOKEN` (must match addon preference)

### JSON Protocol

**Request:**

```json
{
  "id": "unique-request-id",
  "method": "scene_get_summary",
  "params": {
    "auth_token": "your-token"
  }
}
```

**Success response:**

```json
{
  "id": "unique-request-id",
  "ok": true,
  "data": { }
}
```

**Error response:**

```json
{
  "id": "unique-request-id",
  "ok": false,
  "error": {
    "code": "OBJECT_NOT_FOUND",
    "message": "Object 'Cube' not found"
  }
}
```

### Error Codes

| Code | Description |
|------|-------------|
| `AUTH_FAILED` | Invalid or missing auth token |
| `INVALID_PARAMS` | Missing or invalid parameters |
| `OBJECT_NOT_FOUND` | Referenced Blender data-block not found |
| `TIMEOUT` | Request timed out waiting for Blender |
| `METHOD_NOT_FOUND` | Unknown method name |
| `EXECUTION_ERROR` | Handler raised an exception |
| `DESTRUCTIVE_NOT_CONFIRMED` | `execute_python` without `confirm_destructive` |

## Thread Safety

Blender's Python API is **not thread-safe**. Only the timer callback touches `bpy`. The socket thread never calls `bpy` directly.

## Security

- Localhost-only binding prevents remote access.
- Auth token required on every request.
- `execute_python` requires explicit `confirm_destructive: true`.
- Destructive ops are logged in the addon UI status.

## Phase Roadmap

- **Phase 0**: Bridge, auth, ping, scene summary, guarded Python execution.
- **Phase 1**: Scene introspection, object lifecycle, materials, rendering, batch execute.
