# BlenderAI Agent Playbook

Recipes and practices for reliable scene authoring through the MCP bridge.

## Build a room

Use primitives and mesh tools instead of dumping full geometry in one call.

1. **Floor and walls** — `object_create_primitive` with `plane` / `cube`, then `object_set_transform` for size and position.
2. **Door cutout** — `mesh_extrude_region` on wall face indices with a small offset, or boolean via `execute_python` only when `confirm_destructive=true`.
3. **Mirror symmetry** — `modifier_add_mirror` on repeated props (windows, trim).
4. **Arrays** — `modifier_add_array` for repeating beams, tiles, or fence posts.
5. **Materials** — `material_create` + `material_assign` + `material_set_principled` for walls/floor/ceiling.
6. **Lighting** — `light_create` (AREA for soft indoor light) and `camera_create` + `camera_frame_objects`.

Example sequence:

```
object_create_primitive → plane (floor)
object_create_primitive → cube (walls, scaled)
modifier_add_mirror → symmetry on props
material_assign → room surfaces
light_create → ceiling area light
viewport_capture → verify layout
```

Keep wall meshes low-poly until layout is approved; use `modifier_add_subdivision` only on hero surfaces.

## Vision feedback loop

1. **Capture** — `viewport_capture` or `render_still` after meaningful changes.
2. **Compare** — Describe what you see vs. the goal (proportions, alignment, materials).
3. **Adjust** — Small, targeted tool calls (`object_set_transform`, `mesh_set_vertices`, material params).
4. **Re-capture** — Same camera angle when possible for before/after.

Tips:

- Set `viewport_set_shading` to `material` or `rendered` before capture when checking materials.
- Use `scene_get_summary` + `object_get` for numeric checks; use images for composition and lighting.
- Batch related edits, then one capture — avoid a screenshot after every single vertex move.

## Token budget tips

### Geometry

- Prefer **`mesh_get_geometry`** with `max_verts` / `max_faces` and offsets — never pull an entire dense mesh unless necessary.
- Return payloads always include **`vertex_count`**, **`face_count`**, and **`bounds`** — use those for decisions without re-fetching all verts.
- Use **`mesh_create_from_verts_faces`** for coarse blocks; refine with extrude/subdivide only where needed.

### Scene introspection

- Start with **`scene_get_summary`** and **`selection_get`** instead of listing every object property.
- Use **`object_get`** on one object at a time when debugging.

### Execution

- Avoid **`execute_python`** for operations that have dedicated tools (modifiers, transforms, materials).
- When using `execute_python`, keep scripts short; set `result` to a small summary dict, not mesh data.
- Read `stdout` / `error.traceback` in the response instead of re-running failed code blindly.

### Batching

- Group independent creates/links in logical steps; use bridge `batch_execute` when available to cut round-trips.
- After destructive edits, rely on Blender undo (each mutating handler pushes undo) rather than re-building from scratch.

## bmesh mode handling

Handlers use a shared session pattern:

| Object mode | bmesh flow |
|-------------|------------|
| **OBJECT** | `bmesh.new()` → `from_mesh` → edit → `to_mesh` → `mesh.update()` → `bm.free()` |
| **EDIT** | `bmesh.from_edit_mesh` → edit → `bmesh.update_edit_mesh` (no `free`) |

Agents should prefer **OBJECT mode** when calling mesh tools unless the user is actively modeling in Edit mode. Mixed-mode scenes work, but Edit-mode targets must be the active object in the viewport for consistent `from_edit_mesh` behavior.
