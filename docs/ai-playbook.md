# BlenderAI Agent Playbook

How to build scenes reliably through MCP — lessons from real tests (e.g. the tree fix).

## Golden workflow

```
ping → scene_get_summary → batch_execute (build) → viewport_set_shading MATERIAL
     → viewport_capture (LOOK) → adjust from bounds + image → repeat
```

Every tool response includes **`agent_feedback`**:

| Field | Use |
|-------|-----|
| `summary` | What just happened |
| `next_steps` | Suggested follow-up tools |
| `verify_with` | Best tool to confirm result |
| `warnings` | Floating parts, gaps, failures |
| `capabilities_hint` | Shader nodes, modifiers, advanced bpy |

**Read `agent_feedback` after every call** — don't guess the next step.

---

## Vision feedback loop (critical)

1. **Build** — `batch_execute` with creates, transforms, materials
2. **Shade** — `viewport_set_shading` → `MATERIAL` or `RENDERED`
3. **Capture** — `viewport_capture` (fast) or `render_still` (quality)
4. **Analyze** — Compare image to goal: gaps, float, scale, color
5. **Fix numerically** — `object_get` → check `bounds.min[2]` / `bounds.max[2]`
6. **Fix visually** — `object_set_transform`, materials, lights
7. **Re-capture** — Same camera angle when possible

### Tree lesson (multi-part models)

- **Problem:** Trunk `bounds.max.z = 2` but foliage `bounds.min.z = 3` → 1m air gap
- **Fix:** Lower foliage or raise trunk until ranges **overlap**
- **Don't:** Rely on `object_set_parent` for layout — use world `object_set_transform`
- **Do:** Delete default **Cube** so props sit on the grid (`bounds.min[2] ≈ 0`)

---

## Bounds cheat sheet

| Check | Rule |
|-------|------|
| On ground | `bounds.min[2]` ≈ 0 |
| Stacked parts | Child `bounds.min.z` ≤ parent `bounds.max.z` |
| Floating | `bounds.min[2] > 0.1` → lower `location.z` |
| Too small gap | Compare `object_get` on both parts |

---

## batch_execute patterns

### Stylized tree

```json
{
  "calls": [
    {"method": "object_delete", "params": {"name": "Cube"}},
    {"method": "object_create_primitive", "params": {"primitive": "cylinder", "name": "Trunk", "location": [0,0,1.5], "scale": [0.4,0.4,3]}},
    {"method": "object_create_primitive", "params": {"primitive": "uv_sphere", "name": "Crown", "location": [0,0,3.2], "scale": [2.2,2.2,1.6]}},
    {"method": "material_create", "params": {"name": "Bark", "base_color": [0.35,0.2,0.08]}},
    {"method": "material_create", "params": {"name": "Leaves", "base_color": [0.12,0.42,0.1]}},
    {"method": "material_assign", "params": {"object": "Trunk", "material": "Bark"}},
    {"method": "material_assign", "params": {"object": "Crown", "material": "Leaves"}}
  ]
}
```

Then: `viewport_set_shading` → `viewport_capture` → read `agent_feedback.warnings`

---

## Materials & shader nodes

### Typed tools (preferred)

- `material_create` — Principled BSDF + base_color
- `material_set_principled` — metallic, roughness, emission
- `material_assign` — slot 0
- `material_get` — node tree summary

### Advanced (execute_python)

When you need procedural or PBR detail:

- `ShaderNodeTexNoise` + `ShaderNodeTexVoronoi` — wood, dirt, variation
- `ShaderNodeMix` — blend colors
- `ShaderNodeBump` / `ShaderNodeNormalMap` — surface detail
- `ShaderNodeTexImage` — image textures
- `ShaderNodeMapping` + `ShaderNodeTexCoord` — UV/world mapping
- World HDRI via world shader nodes

Always `viewport_set_shading MATERIAL` before judging colors.

---

## Modifiers & mesh

| Tool | Use |
|------|-----|
| `modifier_add_mirror` | Symmetry |
| `modifier_add_array` | Repeats |
| `modifier_add_subdivision` | Smooth forms |
| `mesh_extrude_region` | Branches, walls |
| `mesh_smooth_shade` | Organic vs hard edge |

Geometry Nodes: use `execute_python` to build `GeometryNodeTree` + assign via `modifiers.new(type='NODES')`.

---

## Lighting & camera

- **SUN** — outdoor key (rotate for direction)
- **AREA** — soft fill (large size = softer)
- **SPOT** — dramatic accent
- `camera_frame_objects` before capture
- `render_set_engine` CYCLES for finals, EEVEE_NEXT for speed

---

## Token budget

- `scene_get_summary` before listing everything
- `object_get` one at a time when debugging
- `mesh_get_geometry` with `max_verts` / pagination
- One `viewport_capture` per iteration, not per vertex
- `batch_execute` over many single calls
- `execute_python` only when no typed tool exists

---

## When things fail

| Error | Action |
|-------|--------|
| `TIMEOUT` | Start Blender bridge (N-panel) |
| `AUTH_FAILED` | Match token in prefs + mcp.json |
| Grey viewport | `viewport_set_shading MATERIAL` |
| Output validation | Restart Cursor after `pip install -e .` |
| Parenting weirdness | Clear parent, use world transforms |
