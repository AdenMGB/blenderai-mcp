# BlenderAI MCP

Hybrid MCP integration for **Blender 5.0+**: a Blender addon exposes a localhost TCP JSON bridge, and an external stdio MCP server connects Cursor (or any MCP client) to your live scene.

## Architecture

```
Cursor  ←stdio→  blenderai-mcp (Python)  ←TCP/JSON→  Blender Addon  →  bpy (main thread)
```

See [docs/architecture.md](docs/architecture.md) for protocol and threading details.

## Prerequisites

- **Blender 5.0+**
- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** (recommended) or pip

## 1. Install the Blender addon

1. Copy or symlink the addon folder into Blender's addons directory:
   - **Windows:** `%APPDATA%\Blender Foundation\Blender\5.0\scripts\addons\`
   - **macOS:** `~/Library/Application Support/Blender/5.0/scripts/addons/`
   - **Linux:** `~/.config/blender/5.0/scripts/addons/`

   Copy `blender_addon/blenderai_mcp` → `addons/blenderai_mcp`

2. Open Blender → **Edit → Preferences → Add-ons**
3. Search **BlenderAI MCP Bridge** and enable it
4. Expand addon preferences:
   - Set **Port** (default `9876`)
   - Set **Auth Token** (choose a secret string)

## 2. Start the bridge in Blender

1. Open the **3D Viewport** sidebar (`N` key) → **BlenderAI** tab
2. Click **Start Server**
3. Confirm status shows `Listening on 127.0.0.1:9876`

## 3. Install the MCP server

### Option A: Local development (this repo)

```bash
cd blenderai
pip install -e .
```

### Option B: uvx (after publishing to PyPI)

```bash
uvx blenderai-mcp
```

## 4. Configure Cursor

The repo includes `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "blenderai": {
      "command": "cmd",
      "args": ["/c", "uvx", "blenderai-mcp"],
      "env": {
        "BLENDERAI_HOST": "127.0.0.1",
        "BLENDERAI_PORT": "9876",
        "BLENDERAI_AUTH_TOKEN": "your-secret-token"
      }
    }
  }
}
```

For local dev, replace the command with:

```json
"command": "python",
"args": ["-m", "blenderai_mcp.server"]
```

Set `BLENDERAI_AUTH_TOKEN` to the same value configured in Blender addon preferences.

Restart Cursor after changing MCP config.

## Available MCP tools

| Category | Tools |
|----------|-------|
| **Connectivity** | `ping` |
| **Scene** | `scene_get_summary`, `scene_list_objects`, `scene_list_collections`, `object_get`, `selection_get` |
| **Objects** | `object_create_primitive`, `object_delete`, `object_rename`, `object_set_transform`, `object_duplicate`, `collection_create`, `collection_link_object` |
| **Materials** | `material_create`, `material_assign`, `material_set_principled` |
| **Render** | `viewport_capture`, `render_still`, `render_set_engine`, `render_set_resolution` |
| **Power** | `execute_python`, `batch_execute` |

### `execute_python` safety

Arbitrary code execution requires `confirm_destructive: true`. Example:

```python
# Via batch_execute or execute_python tool
code = "result = len(bpy.data.objects)"
```

## JSON protocol (addon bridge)

**Request:**
```json
{"id": "1", "method": "scene_get_summary", "params": {"auth_token": "secret"}}
```

**Response:**
```json
{"id": "1", "ok": true, "data": {"name": "Scene", "object_count": 3}}
```

**Error codes:** `AUTH_FAILED`, `INVALID_PARAMS`, `OBJECT_NOT_FOUND`, `TIMEOUT`, `METHOD_NOT_FOUND`, `EXECUTION_ERROR`, `DESTRUCTIVE_NOT_CONFIRMED`

## Development

```bash
# Syntax check
python -m compileall mcp_server blender_addon

# Run MCP server locally
python -m blenderai_mcp.server
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `TIMEOUT` / cannot connect | Start the bridge in Blender N-panel first |
| `AUTH_FAILED` | Match token in addon prefs and `BLENDERAI_AUTH_TOKEN` |
| Tools hang | Ensure Blender is open and not blocked by a modal dialog |
| Viewport capture fails | Keep a 3D viewport visible |

## License

MIT
