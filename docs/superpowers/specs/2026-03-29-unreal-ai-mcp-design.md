# Unreal AI MCP — Design Spec
*Date: 2026-03-29*

## Context

This tool enables AI (Claude) to create and modify Unreal Engine 5 assets live inside the editor. The motivation is to let developers and artists describe what they want in natural language and have Claude execute it directly — creating Blueprints, wiring graph nodes, building Material expressions, and reading the scene.

The MVP covers: **Blueprints, Materials, and Scene understanding** (actors + viewport screenshots).

---

## Architecture

```
Claude (Claude Code or API)
    │ MCP protocol (stdio/SSE)
MCP Server  (Python — unreal_ai/mcp_server/)
    │ HTTP  localhost:7777
UE5 Plugin  (C++ bootstrap + Python Flask server — UE project Plugins/UnrealAI/)
    │ unreal.* Python module
Unreal Engine 5 Editor
```

### Repo structure

```
unreal_ai/
  mcp_server/
    server.py              # MCP entrypoint, tool registration
    client.py              # HTTP client → UE5 plugin
    tools/
      blueprints.py        # BP tool handlers
      materials.py         # Material tool handlers
      scene.py             # Scene query + screenshot tools
  ue5_plugin/
    UnrealAI/
      Source/UnrealAI/     # C++ module (bootstrap Python server on startup)
      Content/Python/
        server.py          # Flask HTTP server entry
        handlers/
          blueprints.py    # unreal.* BP operations
          materials.py     # unreal.* Material operations
          scene.py         # Actor queries + viewport screenshot
```

---

## Components

### 1. UE5 Plugin (C++ + Python)

**C++ module** (~50 lines): Registers a startup callback that runs `unreal.py_execute_file("UnrealAI/server.py")` when the editor finishes loading. That's it — all real logic is in Python.

**Python Flask server** (localhost:7777): Handles POST requests from the MCP server. Every handler wraps its `unreal.*` calls in try/except and returns `{"ok": true, ...}` or `{"ok": false, "error": "..."}`. Server never crashes — errors are returned as JSON.

### 2. MCP Server (Python)

Standalone Python process. Registers tools via the MCP SDK, each tool:
1. Validates arguments
2. POSTs to localhost:7777 with a JSON body
3. If `ok: false`, raises an MCP tool error (Claude sees the message directly)
4. If `ok: true`, returns the result as an MCP content block

Screenshot tool returns the image as a base64 content block so Claude can see the viewport.

---

## MVP Tool List (22 tools)

### Blueprint (12)

| Tool | Description |
|------|-------------|
| `bp_create` | Create a Blueprint class with a given parent |
| `bp_read` | Read variables, components, functions, graphs |
| `bp_list` | List BPs under a content path |
| `bp_add_variable` | Add a typed variable |
| `bp_add_component` | Add a component (StaticMesh, Camera, etc.) |
| `bp_add_function` | Create a function graph |
| `bp_add_event` | Add an event (BeginPlay, Tick, custom) |
| `bp_add_node` | Add a function call node to a graph |
| `bp_connect_pins` | Wire output pin → input pin between nodes |
| `bp_set_property` | Set a node property or variable default |
| `bp_set_component_property` | Set a component property |
| `bp_compile` | Compile; returns errors if any |

### Material (7)

| Tool | Description |
|------|-------------|
| `mat_create` | Create a Material asset |
| `mat_read` | Read nodes and connections |
| `mat_list` | List Materials under a content path |
| `mat_add_expression` | Add an expression node (Multiply, Lerp, TextureSample, etc.) |
| `mat_connect_pins` | Connect expression output → input |
| `mat_set_parameter` | Set parameter name/value on a node |
| `mat_apply` | Apply Material to a mesh asset or actor |

### Scene (3)

| Tool | Description |
|------|-------------|
| `scene_get_actors` | List all actors: name, class, location |
| `scene_get_actor_detail` | Full component tree + properties for one actor |
| `scene_screenshot` | Capture viewport, return as image Claude can see |

---

## Data Flow

**Request (MCP Server → UE5 Plugin):**
```json
POST localhost:7777/blueprint/add_node
{
  "asset_path": "/Game/Characters/BP_Character",
  "graph": "EventGraph",
  "function": "SetActorLocation",
  "position": [200, 300]
}
```

**Success response:**
```json
{ "ok": true, "node_id": "K2Node_CallFunction_42", "pins": ["NewLocation", "Sweep", "ReturnValue"] }
```

**Error response:**
```json
{ "ok": false, "error": "Asset not found: /Game/Characters/BP_Character" }
```

---

## Error Handling

1. **UE5 Plugin** — every handler wrapped in try/except; returns `ok: false` with Python error message. HTTP server stays up.
2. **MCP Server** — `ok: false` raises an MCP tool error; Claude sees the message and can adapt.
3. **Blueprint compile errors** — `bp_compile` always returns the full error list. Claude can fix-and-recompile in a loop.

---

## Out of Scope (MVP)

- Animation Blueprints, Niagara, Sequencer, IK Rigs, Behavior Trees, Widget BPs, DataTables, PCG, MetaSounds
- AI generation (text-to-image, text-to-3D)
- In-editor chat panel UI (MCP / Claude Code first)
- C++ code generation (filesystem write + Live Coding trigger)
- WebSocket push events from UE5 back to MCP

These are natural next phases after the MVP ships.

## Future Extensions (Post-MVP)

Beyond the MVP, the following enhancements are planned to enable full iterative AI-driven development:

### Blueprint Editing Tools
- Deletion: `bp_delete_variable`, `bp_delete_component`, `bp_delete_function`, `bp_delete_event`, `bp_delete_node`, `bp_disconnect_pins`
- Editing: `bp_move_node`, `bp_rename_variable`, `bp_change_variable_type`, `bp_set_node_position`
- Advanced: Custom event handling, timeline editing, timeline replication

### Material Editing Tools
- Deletion: `mat_delete_expression`
- Editing: `mat_move_expression`, `mat_rename_expression`
- Advanced: Material function creation, parameter group management

### Scene Editing Tools
- Actor spawning/destruction
- Component addition/removal at runtime
- Transform editing
- Level editing (visibility, locking)

### Advanced Integration Features
- C++ code generation with Live Coding trigger
- WebSocket push events from UE5 to MCP for real-time updates
- In-editor chat panel UI
- AI generation (text-to-image textures, text-to-3D models)

These features will build upon the same MCP → HTTP → unreal.* Python API pattern established in the MVP.

---

## Verification Plan

1. Enable plugin in a UE5 project → confirm Flask server starts on port 7777
2. `curl localhost:7777/scene/actors` → returns actor list JSON
3. Add MCP server to Claude Code config → `claude mcp list` shows `unreal-ai`
4. Ask Claude: *"Create a Blueprint called BP_TestActor that prints Hello on BeginPlay"* → BP appears in Content Browser, compiles clean
5. Ask Claude: *"Create a simple red emissive Material and apply it to the floor mesh"* → Material created and applied in editor
6. Ask Claude: *"Show me the current viewport"* → Claude receives and describes the screenshot
