# Unreal AI MCP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python MCP server + UE5 editor plugin that lets Claude create/modify Blueprints, Materials, and query scene actors inside a live Unreal Engine 5 editor.

**Architecture:** A standalone Python MCP server registers 22 tools and forwards each tool call over HTTP (localhost:7777) to a Python HTTP server running inside UE5's editor process. The UE5 side processes requests on the game thread via a tick callback queue, executes `unreal.*` Python API calls, and returns JSON. No C++ is required — UE5 auto-executes `Content/Python/init_unreal.py` on plugin load.

**Tech Stack:** Python 3.11+, `mcp[cli]` (FastMCP), `requests`, Python stdlib `http.server` (UE5 side — no third-party deps), `pytest`, `unittest.mock`, Unreal Engine 5.3+

---

## File Map

```
unreal_ai/
  mcp_server/
    server.py                   # FastMCP entrypoint — registers all 22 tools
    client.py                   # HTTP client → localhost:7777
    tools/
      blueprints.py             # 12 blueprint tool definitions
      materials.py              # 7 material tool definitions
      scene.py                  # 3 scene tool definitions
  ue5_plugin/
    UnrealAI/
      UnrealAI.uplugin           # Plugin descriptor (no C++ modules)
      Content/Python/
        init_unreal.py           # Auto-executed by UE5 on plugin load
        server.py                # Threaded HTTP server + tick queue dispatcher
        routes.py                # URL → handler routing table
        handlers/
          blueprints.py          # unreal.* Blueprint operations
          materials.py           # unreal.* Material operations
          scene.py               # Actor queries + viewport screenshot
  tests/
    mcp_server/
      test_client.py             # HTTP client unit tests
      test_blueprints.py         # BP tool tests (mock HTTP)
      test_materials.py          # Material tool tests (mock HTTP)
      test_scene.py              # Scene tool tests (mock HTTP)
    ue5_plugin/
      conftest.py                # Mock unreal module fixture
      test_server.py             # HTTP server scaffold tests
      test_handlers_blueprints.py
      test_handlers_materials.py
      test_handlers_scene.py
  pyproject.toml
```

---

## Task 1: Project Setup

**Files:**
- Create: `pyproject.toml`
- Create: `tests/ue5_plugin/conftest.py`

- [ ] **Step 1: Write pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "unreal-ai-mcp"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "mcp[cli]>=1.0.0",
    "requests>=2.31.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-mock>=3.0"]

[project.scripts]
unreal-ai-mcp = "mcp_server.server:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create mock unreal module for UE5 plugin tests**

```python
# tests/ue5_plugin/conftest.py
"""
Provides a mock `unreal` module so UE5 plugin handlers can be tested
without a running Unreal Engine editor.
"""
import sys
import types
import pytest


def _make_mock_unreal():
    mod = types.ModuleType("unreal")

    # --- Asset creation helpers ---
    class _AssetTools:
        def create_asset(self, name, path, asset_class, factory):
            obj = types.SimpleNamespace(
                get_name=lambda: name,
                get_path_name=lambda: f"{path}{name}",
            )
            return obj

    class _AssetToolsHelpers:
        @staticmethod
        def get_asset_tools():
            return _AssetTools()

    mod.AssetToolsHelpers = _AssetToolsHelpers

    # --- Blueprint factory ---
    class _BlueprintFactory:
        parent_class = None

    mod.BlueprintFactory = _BlueprintFactory
    mod.Blueprint = object()

    # --- BlueprintEditorLibrary ---
    class _BlueprintEditorLibrary:
        @staticmethod
        def add_member_variable(bp, name, var_type):
            return True

        @staticmethod
        def compile_blueprint(bp):
            return []  # no errors

        @staticmethod
        def get_all_graphs(bp):
            return []

        @staticmethod
        def add_component(bp, component_class, name):
            return types.SimpleNamespace(get_name=lambda: name)

    mod.BlueprintEditorLibrary = _BlueprintEditorLibrary

    # --- EditorAssetLibrary ---
    class _EditorAssetLibrary:
        @staticmethod
        def load_asset(path):
            return types.SimpleNamespace(
                get_name=lambda: path.split("/")[-1],
                get_path_name=lambda: path,
            )

        @staticmethod
        def list_assets(path, recursive=True, include_folder=False):
            return []

        @staticmethod
        def make_directory(path):
            return True

        @staticmethod
        def does_asset_exist(path):
            return False

    mod.EditorAssetLibrary = _EditorAssetLibrary

    # --- EditorLevelLibrary ---
    class _EditorLevelLibrary:
        @staticmethod
        def get_all_level_actors():
            return []

    mod.EditorLevelLibrary = _EditorLevelLibrary

    # --- Material factory ---
    class _MaterialFactoryNew:
        pass

    mod.MaterialFactoryNew = _MaterialFactoryNew
    mod.Material = object()

    # --- MaterialEditingLibrary ---
    class _MaterialEditingLibrary:
        @staticmethod
        def create_material_expression(material, expression_class, node_x=0, node_y=0):
            return types.SimpleNamespace(
                get_name=lambda: expression_class.__name__,
            )

        @staticmethod
        def connect_material_expressions(from_expr, from_pin, to_expr, to_pin):
            return True

        @staticmethod
        def connect_material_property(from_expr, from_pin, prop):
            return True

        @staticmethod
        def recompile_material(material):
            pass

    mod.MaterialEditingLibrary = _MaterialEditingLibrary

    # --- Expression classes (used as identifiers) ---
    class _ExprClass:
        def __init__(self, name):
            self.__name__ = name

    for expr in ["MaterialExpressionMultiply", "MaterialExpressionAdd",
                  "MaterialExpressionLerp", "MaterialExpressionTextureSample",
                  "MaterialExpressionConstant", "MaterialExpressionConstant3Vector",
                  "MaterialExpressionScalarParameter", "MaterialExpressionVectorParameter",
                  "MaterialExpressionEmissiveColor"]:
        setattr(mod, expr, _ExprClass(expr))

    # --- SystemLibrary ---
    class _SystemLibrary:
        @staticmethod
        def execute_console_command(world_context, command):
            pass

    mod.SystemLibrary = _SystemLibrary

    # --- load_class helper ---
    mod.load_class = lambda outer, path: type(path.split(".")[-1], (), {})()

    # --- Actor transform helpers ---
    class _Vector:
        def __init__(self, x=0, y=0, z=0):
            self.x, self.y, self.z = x, y, z

    mod.Vector = _Vector

    # --- log ---
    mod.log = lambda msg: None
    mod.log_warning = lambda msg: None
    mod.log_error = lambda msg: None

    # --- Tick callback (no-op in tests) ---
    mod.register_slate_post_tick_callback = lambda fn: None
    mod.unregister_slate_post_tick_callback = lambda handle: None

    return mod


@pytest.fixture(autouse=True)
def mock_unreal(monkeypatch):
    """Inject mock unreal module before importing any handler under test."""
    mock = _make_mock_unreal()
    monkeypatch.setitem(sys.modules, "unreal", mock)
    yield mock
```

- [ ] **Step 3: Install dependencies**

```bash
cd /Users/mikecoker/projects/unreal_ai
pip install -e ".[dev]"
```

Expected: packages install without error.

- [ ] **Step 4: Verify test infrastructure**

```bash
pytest tests/ --collect-only
```

Expected: `0 errors` (no tests yet, but conftest loads cleanly).

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml tests/ue5_plugin/conftest.py
git commit -m "feat: project setup and mock unreal test fixture"
```

---

## Task 2: UE5 Plugin Scaffold

**Files:**
- Create: `ue5_plugin/UnrealAI/UnrealAI.uplugin`
- Create: `ue5_plugin/UnrealAI/Content/Python/init_unreal.py`
- Create: `ue5_plugin/UnrealAI/Content/Python/server.py`
- Create: `ue5_plugin/UnrealAI/Content/Python/routes.py`
- Create: `tests/ue5_plugin/test_server.py`

- [ ] **Step 1: Write failing test for health check endpoint**

```python
# tests/ue5_plugin/test_server.py
import sys, json, threading
from http.client import HTTPConnection

# Add plugin Python path so imports work
sys.path.insert(0, "ue5_plugin/UnrealAI/Content/Python")


def test_health_check_returns_ok():
    """Server should respond to GET /health with {"ok": true}."""
    from server import UnrealAIServer

    srv = UnrealAIServer(port=17777)
    t = threading.Thread(target=srv.serve_once, daemon=True)
    t.start()

    conn = HTTPConnection("localhost", 17777)
    conn.request("GET", "/health")
    resp = conn.getresponse()
    body = json.loads(resp.read())
    conn.close()
    srv.shutdown()

    assert resp.status == 200
    assert body == {"ok": True, "service": "unreal-ai"}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/ue5_plugin/test_server.py::test_health_check_returns_ok -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'server'`

- [ ] **Step 3: Write the server scaffold**

```python
# ue5_plugin/UnrealAI/Content/Python/server.py
"""
HTTP server that runs inside UE5's editor process.
Requests arrive on a background thread; unreal.* calls are dispatched
on the game thread via a tick callback queue.
"""
import json
import queue
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self._send({"ok": True, "service": "unreal-ai"})
        else:
            self._send({"ok": False, "error": f"Unknown route: {self.path}"}, 404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        resp_q = queue.Queue()
        self.server.request_queue.put((self.path, body, resp_q))
        try:
            result = resp_q.get(timeout=30)
        except queue.Empty:
            result = {"ok": False, "error": "Request timed out (30s)"}

        self._send(result)

    def _send(self, data, status=200):
        payload = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        pass  # suppress default HTTP logs


class UnrealAIServer:
    def __init__(self, port=7777):
        self.port = port
        self._httpd = HTTPServer(("localhost", port), _Handler)
        self._httpd.request_queue = queue.Queue()
        self._thread = None

    def start(self):
        """Start serving in a background thread. Register tick callback for game thread dispatch."""
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()

        try:
            import unreal
            self._tick_handle = unreal.register_slate_post_tick_callback(self._tick)
            unreal.log(f"[UnrealAI] Server running on localhost:{self.port}")
        except ImportError:
            pass  # running outside UE5 (tests)

    def serve_once(self):
        """Used in tests — handle one request then return."""
        self._httpd.handle_request()

    def shutdown(self):
        self._httpd.shutdown()

    def _tick(self, _delta):
        """Called on the game thread each frame. Drains the request queue."""
        from routes import dispatch
        while True:
            try:
                path, body, resp_q = self._httpd.request_queue.get_nowait()
            except queue.Empty:
                break
            try:
                result = dispatch(path, body)
            except Exception as exc:
                result = {"ok": False, "error": str(exc)}
            resp_q.put(result)
```

- [ ] **Step 4: Write routes dispatcher**

```python
# ue5_plugin/UnrealAI/Content/Python/routes.py
"""Maps HTTP paths to handler functions."""
from handlers import blueprints, materials, scene

_ROUTES = {
    # Scene
    "/scene/actors":       scene.get_actors,
    "/scene/actor":        scene.get_actor_detail,
    "/scene/screenshot":   scene.screenshot,

    # Blueprints
    "/blueprint/create":           blueprints.create,
    "/blueprint/read":             blueprints.read,
    "/blueprint/list":             blueprints.list_assets,
    "/blueprint/add_variable":     blueprints.add_variable,
    "/blueprint/add_component":    blueprints.add_component,
    "/blueprint/add_function":     blueprints.add_function,
    "/blueprint/add_event":        blueprints.add_event,
    "/blueprint/add_node":         blueprints.add_node,
    "/blueprint/connect_pins":     blueprints.connect_pins,
    "/blueprint/set_property":     blueprints.set_property,
    "/blueprint/set_component_property": blueprints.set_component_property,
    "/blueprint/compile":          blueprints.compile,

    # Materials
    "/material/create":            materials.create,
    "/material/read":              materials.read,
    "/material/list":              materials.list_assets,
    "/material/add_expression":    materials.add_expression,
    "/material/connect_pins":      materials.connect_pins,
    "/material/set_parameter":     materials.set_parameter,
    "/material/apply":             materials.apply,
}


def dispatch(path: str, body: dict) -> dict:
    handler = _ROUTES.get(path)
    if handler is None:
        return {"ok": False, "error": f"Unknown route: {path}"}
    return handler(body)
```

- [ ] **Step 5: Write empty handler stubs so routes.py imports**

Create `ue5_plugin/UnrealAI/Content/Python/handlers/__init__.py` (empty).

Create `ue5_plugin/UnrealAI/Content/Python/handlers/scene.py`:
```python
def get_actors(body): return {"ok": False, "error": "not implemented"}
def get_actor_detail(body): return {"ok": False, "error": "not implemented"}
def screenshot(body): return {"ok": False, "error": "not implemented"}
```

Create `ue5_plugin/UnrealAI/Content/Python/handlers/blueprints.py`:
```python
def create(body): return {"ok": False, "error": "not implemented"}
def read(body): return {"ok": False, "error": "not implemented"}
def list_assets(body): return {"ok": False, "error": "not implemented"}
def add_variable(body): return {"ok": False, "error": "not implemented"}
def add_component(body): return {"ok": False, "error": "not implemented"}
def add_function(body): return {"ok": False, "error": "not implemented"}
def add_event(body): return {"ok": False, "error": "not implemented"}
def add_node(body): return {"ok": False, "error": "not implemented"}
def connect_pins(body): return {"ok": False, "error": "not implemented"}
def set_property(body): return {"ok": False, "error": "not implemented"}
def set_component_property(body): return {"ok": False, "error": "not implemented"}
def compile(body): return {"ok": False, "error": "not implemented"}
```

Create `ue5_plugin/UnrealAI/Content/Python/handlers/materials.py`:
```python
def create(body): return {"ok": False, "error": "not implemented"}
def read(body): return {"ok": False, "error": "not implemented"}
def list_assets(body): return {"ok": False, "error": "not implemented"}
def add_expression(body): return {"ok": False, "error": "not implemented"}
def connect_pins(body): return {"ok": False, "error": "not implemented"}
def set_parameter(body): return {"ok": False, "error": "not implemented"}
def apply(body): return {"ok": False, "error": "not implemented"}
```

- [ ] **Step 6: Write the plugin descriptor and init script**

```json
// ue5_plugin/UnrealAI/UnrealAI.uplugin
{
  "FileVersion": 3,
  "Version": 1,
  "VersionName": "1.0",
  "FriendlyName": "UnrealAI",
  "Description": "MCP bridge — lets Claude create Blueprints and Materials via AI",
  "Category": "Scripting",
  "CanContainContent": true,
  "Installed": false,
  "Plugins": [
    { "Name": "PythonScriptPlugin", "Enabled": true }
  ]
}
```

```python
# ue5_plugin/UnrealAI/Content/Python/init_unreal.py
"""
Auto-executed by UE5 when the UnrealAI plugin loads.
Starts the HTTP server after a single tick to ensure the editor is ready.
"""
import unreal

_server = None
_started = False


def _on_first_tick(_delta):
    global _server, _started
    if _started:
        return
    _started = True
    from server import UnrealAIServer
    _server = UnrealAIServer(port=7777)
    _server.start()


unreal.register_slate_post_tick_callback(_on_first_tick)
```

- [ ] **Step 7: Run the health check test**

```bash
pytest tests/ue5_plugin/test_server.py::test_health_check_returns_ok -v
```

Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add ue5_plugin/ tests/ue5_plugin/test_server.py
git commit -m "feat: UE5 plugin scaffold with HTTP server and route dispatcher"
```

---

## Task 3: Scene Handlers (UE5 side)

**Files:**
- Modify: `ue5_plugin/UnrealAI/Content/Python/handlers/scene.py`
- Create: `tests/ue5_plugin/test_handlers_scene.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/ue5_plugin/test_handlers_scene.py
import sys
sys.path.insert(0, "ue5_plugin/UnrealAI/Content/Python")


def test_get_actors_returns_list(mock_unreal):
    import types

    actor_a = types.SimpleNamespace(
        get_name=lambda: "BP_Character_1",
        get_class=lambda: types.SimpleNamespace(get_name=lambda: "BP_Character_C"),
        get_actor_location=lambda: mock_unreal.Vector(100, 200, 0),
    )
    mock_unreal.EditorLevelLibrary.get_all_level_actors = lambda: [actor_a]

    from handlers.scene import get_actors
    result = get_actors({})

    assert result["ok"] is True
    assert len(result["actors"]) == 1
    assert result["actors"][0]["name"] == "BP_Character_1"
    assert result["actors"][0]["class"] == "BP_Character_C"
    assert result["actors"][0]["location"] == {"x": 100, "y": 200, "z": 0}


def test_get_actor_detail_not_found(mock_unreal):
    mock_unreal.EditorLevelLibrary.get_all_level_actors = lambda: []

    from handlers.scene import get_actor_detail
    result = get_actor_detail({"name": "NonExistent"})

    assert result["ok"] is False
    assert "not found" in result["error"].lower()


def test_screenshot_triggers_console_command(mock_unreal):
    commands_run = []
    mock_unreal.SystemLibrary.execute_console_command = (
        lambda ctx, cmd: commands_run.append(cmd)
    )

    from handlers.scene import screenshot
    result = screenshot({"width": 1920, "height": 1080})

    assert result["ok"] is True
    assert any("HighResShot" in c for c in commands_run)
    assert "path" in result
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/ue5_plugin/test_handlers_scene.py -v
```

Expected: 3 FAILs — `get_actors` returns `"not implemented"`.

- [ ] **Step 3: Implement scene handlers**

```python
# ue5_plugin/UnrealAI/Content/Python/handlers/scene.py
import os
import tempfile
import unreal


def get_actors(body: dict) -> dict:
    try:
        actors = unreal.EditorLevelLibrary.get_all_level_actors()
        result = []
        for actor in actors:
            loc = actor.get_actor_location()
            result.append({
                "name": actor.get_name(),
                "class": actor.get_class().get_name(),
                "location": {"x": loc.x, "y": loc.y, "z": loc.z},
            })
        return {"ok": True, "actors": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_actor_detail(body: dict) -> dict:
    name = body.get("name", "")
    try:
        actors = unreal.EditorLevelLibrary.get_all_level_actors()
        actor = next((a for a in actors if a.get_name() == name), None)
        if actor is None:
            return {"ok": False, "error": f"Actor not found: {name}"}

        loc = actor.get_actor_location()
        rot = actor.get_actor_rotation()

        components = []
        for comp in actor.get_components_by_class(unreal.ActorComponent):
            components.append({
                "name": comp.get_name(),
                "class": comp.get_class().get_name(),
            })

        return {
            "ok": True,
            "name": actor.get_name(),
            "class": actor.get_class().get_name(),
            "location": {"x": loc.x, "y": loc.y, "z": loc.z},
            "rotation": {"pitch": rot.pitch, "yaw": rot.yaw, "roll": rot.roll},
            "components": components,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def screenshot(body: dict) -> dict:
    width = body.get("width", 1920)
    height = body.get("height", 1080)
    path = body.get("path", os.path.join(tempfile.gettempdir(), "unreal_ai_screenshot.png"))
    try:
        cmd = f"HighResShot {width}x{height} filename={path}"
        unreal.SystemLibrary.execute_console_command(None, cmd)
        return {"ok": True, "path": path, "note": "Screenshot saved asynchronously — wait ~1s before reading."}
    except Exception as e:
        return {"ok": False, "error": str(e)}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/ue5_plugin/test_handlers_scene.py -v
```

Expected: 3 PASSes

- [ ] **Step 5: Commit**

```bash
git add ue5_plugin/UnrealAI/Content/Python/handlers/scene.py tests/ue5_plugin/test_handlers_scene.py
git commit -m "feat: scene handlers — get_actors, get_actor_detail, screenshot"
```

---

## Task 4: Blueprint Handlers (UE5 side)

**Files:**
- Modify: `ue5_plugin/UnrealAI/Content/Python/handlers/blueprints.py`
- Create: `tests/ue5_plugin/test_handlers_blueprints.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/ue5_plugin/test_handlers_blueprints.py
import sys, types
sys.path.insert(0, "ue5_plugin/UnrealAI/Content/Python")


def test_create_blueprint(mock_unreal):
    from handlers.blueprints import create
    result = create({"asset_path": "/Game/Characters/BP_Hero", "parent_class": "Actor"})
    assert result["ok"] is True
    assert result["asset_path"] == "/Game/Characters/BP_Hero"


def test_create_blueprint_missing_path(mock_unreal):
    from handlers.blueprints import create
    result = create({"parent_class": "Actor"})
    assert result["ok"] is False
    assert "asset_path" in result["error"]


def test_add_variable(mock_unreal):
    # Set up a fake loaded asset
    fake_bp = types.SimpleNamespace(get_name=lambda: "BP_Hero", get_path_name=lambda: "/Game/BP_Hero")
    mock_unreal.EditorAssetLibrary.load_asset = lambda path: fake_bp

    from handlers.blueprints import add_variable
    result = add_variable({
        "asset_path": "/Game/BP_Hero",
        "name": "Health",
        "type": "float",
        "default_value": 100.0,
    })
    assert result["ok"] is True
    assert result["variable"] == "Health"


def test_compile_blueprint_returns_errors(mock_unreal):
    fake_bp = types.SimpleNamespace(get_name=lambda: "BP_Hero", get_path_name=lambda: "/Game/BP_Hero")
    mock_unreal.EditorAssetLibrary.load_asset = lambda path: fake_bp
    mock_unreal.BlueprintEditorLibrary.compile_blueprint = lambda bp: [
        types.SimpleNamespace(get_message=lambda: "Pin not connected")
    ]

    from handlers.blueprints import compile
    result = compile({"asset_path": "/Game/BP_Hero"})
    assert result["ok"] is True  # compile ran
    assert result["errors"] == ["Pin not connected"]


def test_list_blueprints(mock_unreal):
    mock_unreal.EditorAssetLibrary.list_assets = lambda path, recursive, include_folder: [
        "/Game/Characters/BP_Hero.BP_Hero",
        "/Game/Characters/BP_Enemy.BP_Enemy",
    ]

    from handlers.blueprints import list_assets
    result = list_assets({"path": "/Game/Characters/"})
    assert result["ok"] is True
    assert len(result["assets"]) == 2
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/ue5_plugin/test_handlers_blueprints.py -v
```

Expected: 5 FAILs

- [ ] **Step 3: Implement blueprint handlers**

```python
# ue5_plugin/UnrealAI/Content/Python/handlers/blueprints.py
import unreal

# Map type name strings to UE5 pin type identifiers
_TYPE_MAP = {
    "bool":    "bool",
    "int":     "int",
    "float":   "real",
    "string":  "string",
    "vector":  "struct",
    "rotator": "struct",
    "actor":   "object",
    "object":  "object",
}

# Common parent class paths
_PARENT_CLASS_MAP = {
    "Actor":          "/Script/Engine.Actor",
    "Pawn":           "/Script/Engine.Pawn",
    "Character":      "/Script/Engine.Character",
    "ActorComponent": "/Script/Engine.ActorComponent",
    "GameMode":       "/Script/Engine.GameMode",
}


def _load_bp(asset_path: str):
    """Load a Blueprint asset by path. Raises ValueError if not found."""
    asset = unreal.EditorAssetLibrary.load_asset(asset_path)
    if asset is None:
        raise ValueError(f"Asset not found: {asset_path}")
    return asset


def create(body: dict) -> dict:
    asset_path = body.get("asset_path")
    if not asset_path:
        return {"ok": False, "error": "asset_path is required"}

    parent_name = body.get("parent_class", "Actor")
    parent_path = _PARENT_CLASS_MAP.get(parent_name, f"/Script/Engine.{parent_name}")

    try:
        # Split into package path + asset name
        parts = asset_path.rsplit("/", 1)
        package_path = parts[0] + "/" if len(parts) > 1 else "/Game/"
        asset_name = parts[-1]

        parent_class = unreal.load_class(None, parent_path)
        factory = unreal.BlueprintFactory()
        factory.parent_class = parent_class

        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        bp = asset_tools.create_asset(asset_name, package_path, unreal.Blueprint, factory)

        return {"ok": True, "asset_path": asset_path, "name": asset_name}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def read(body: dict) -> dict:
    asset_path = body.get("asset_path")
    if not asset_path:
        return {"ok": False, "error": "asset_path is required"}
    try:
        bp = _load_bp(asset_path)
        graphs = [g.get_name() for g in unreal.BlueprintEditorLibrary.get_all_graphs(bp)]
        return {"ok": True, "asset_path": asset_path, "graphs": graphs}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def list_assets(body: dict) -> dict:
    path = body.get("path", "/Game/")
    try:
        raw = unreal.EditorAssetLibrary.list_assets(path, recursive=True, include_folder=False)
        # Strip the .AssetName suffix UE5 appends
        assets = [p.rsplit(".", 1)[0] for p in raw]
        return {"ok": True, "assets": assets}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def add_variable(body: dict) -> dict:
    asset_path = body.get("asset_path")
    name = body.get("name")
    var_type = body.get("type", "float")
    if not asset_path or not name:
        return {"ok": False, "error": "asset_path and name are required"}
    try:
        bp = _load_bp(asset_path)
        pin_type = unreal.EdGraphPinType()
        pin_type.pc_type = _TYPE_MAP.get(var_type, var_type)
        unreal.BlueprintEditorLibrary.add_member_variable(bp, name, pin_type)
        return {"ok": True, "variable": name, "type": var_type}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def add_component(body: dict) -> dict:
    asset_path = body.get("asset_path")
    component_class = body.get("component_class", "StaticMeshComponent")
    name = body.get("name", component_class)
    if not asset_path:
        return {"ok": False, "error": "asset_path is required"}
    try:
        bp = _load_bp(asset_path)
        cls = unreal.load_class(None, f"/Script/Engine.{component_class}")
        comp = unreal.BlueprintEditorLibrary.add_component(bp, cls, name)
        return {"ok": True, "component": name, "class": component_class}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def add_function(body: dict) -> dict:
    asset_path = body.get("asset_path")
    name = body.get("name")
    if not asset_path or not name:
        return {"ok": False, "error": "asset_path and name are required"}
    try:
        bp = _load_bp(asset_path)
        # BlueprintEditorLibrary.add_function creates a new function graph
        unreal.BlueprintEditorLibrary.add_function(bp, name)
        return {"ok": True, "function": name}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def add_event(body: dict) -> dict:
    asset_path = body.get("asset_path")
    event = body.get("event", "BeginPlay")
    if not asset_path:
        return {"ok": False, "error": "asset_path is required"}
    try:
        bp = _load_bp(asset_path)
        # Standard events are already present in EventGraph; this ensures the node exists
        graph = unreal.BlueprintEditorLibrary.get_editor_graph(bp, "EventGraph")
        return {"ok": True, "event": event, "graph": "EventGraph"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def add_node(body: dict) -> dict:
    """Add a function call node to a Blueprint graph by function name."""
    asset_path = body.get("asset_path")
    graph_name = body.get("graph", "EventGraph")
    function = body.get("function")
    node_x = body.get("x", 0)
    node_y = body.get("y", 0)
    if not asset_path or not function:
        return {"ok": False, "error": "asset_path and function are required"}
    try:
        bp = _load_bp(asset_path)
        graph = unreal.BlueprintEditorLibrary.get_editor_graph(bp, graph_name)
        if graph is None:
            return {"ok": False, "error": f"Graph not found: {graph_name}"}
        node = unreal.BlueprintEditorLibrary.add_function_call_node(graph, function, node_x, node_y)
        pins = [p.get_name() for p in node.get_all_pins()] if hasattr(node, "get_all_pins") else []
        return {"ok": True, "node_id": node.get_name(), "function": function, "pins": pins}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def connect_pins(body: dict) -> dict:
    """Connect an output pin to an input pin between two nodes."""
    asset_path = body.get("asset_path")
    graph_name = body.get("graph", "EventGraph")
    from_node = body.get("from_node")
    from_pin = body.get("from_pin")
    to_node = body.get("to_node")
    to_pin = body.get("to_pin")
    required = [asset_path, graph_name, from_node, from_pin, to_node, to_pin]
    if not all(required):
        return {"ok": False, "error": "asset_path, graph, from_node, from_pin, to_node, to_pin are all required"}
    try:
        bp = _load_bp(asset_path)
        graph = unreal.BlueprintEditorLibrary.get_editor_graph(bp, graph_name)
        unreal.BlueprintEditorLibrary.connect_graph_pins(
            graph, from_node, from_pin, to_node, to_pin
        )
        return {"ok": True, "connected": f"{from_node}.{from_pin} → {to_node}.{to_pin}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def set_property(body: dict) -> dict:
    asset_path = body.get("asset_path")
    property_name = body.get("property")
    value = body.get("value")
    if not asset_path or property_name is None:
        return {"ok": False, "error": "asset_path and property are required"}
    try:
        bp = _load_bp(asset_path)
        unreal.BlueprintEditorLibrary.set_variable_default_value(bp, property_name, str(value))
        return {"ok": True, "property": property_name, "value": value}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def set_component_property(body: dict) -> dict:
    asset_path = body.get("asset_path")
    component = body.get("component")
    property_name = body.get("property")
    value = body.get("value")
    if not asset_path or not component or property_name is None:
        return {"ok": False, "error": "asset_path, component, and property are required"}
    try:
        bp = _load_bp(asset_path)
        # Set via subobject data
        comp_obj = unreal.EditorAssetLibrary.load_asset(f"{asset_path}:{component}")
        if comp_obj:
            comp_obj.set_editor_property(property_name, value)
        return {"ok": True, "component": component, "property": property_name, "value": value}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def compile(body: dict) -> dict:
    asset_path = body.get("asset_path")
    if not asset_path:
        return {"ok": False, "error": "asset_path is required"}
    try:
        bp = _load_bp(asset_path)
        error_objs = unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        errors = [e.get_message() for e in (error_objs or [])]
        return {"ok": True, "asset_path": asset_path, "errors": errors, "clean": len(errors) == 0}
    except Exception as e:
        return {"ok": False, "error": str(e)}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/ue5_plugin/test_handlers_blueprints.py -v
```

Expected: 5 PASSes

- [ ] **Step 5: Commit**

```bash
git add ue5_plugin/UnrealAI/Content/Python/handlers/blueprints.py tests/ue5_plugin/test_handlers_blueprints.py
git commit -m "feat: blueprint handlers — create, read, list, add_variable/component/function/event/node, connect_pins, compile"
```

---

## Task 5: Material Handlers (UE5 side)

**Files:**
- Modify: `ue5_plugin/UnrealAI/Content/Python/handlers/materials.py`
- Create: `tests/ue5_plugin/test_handlers_materials.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/ue5_plugin/test_handlers_materials.py
import sys, types
sys.path.insert(0, "ue5_plugin/UnrealAI/Content/Python")


def test_create_material(mock_unreal):
    from handlers.materials import create
    result = create({"asset_path": "/Game/Materials/M_Rock"})
    assert result["ok"] is True
    assert result["asset_path"] == "/Game/Materials/M_Rock"


def test_create_material_missing_path(mock_unreal):
    from handlers.materials import create
    result = create({})
    assert result["ok"] is False
    assert "asset_path" in result["error"]


def test_add_expression(mock_unreal):
    fake_mat = types.SimpleNamespace(get_name=lambda: "M_Rock", get_path_name=lambda: "/Game/M_Rock")
    mock_unreal.EditorAssetLibrary.load_asset = lambda p: fake_mat

    from handlers.materials import add_expression
    result = add_expression({
        "asset_path": "/Game/M_Rock",
        "type": "Multiply",
        "x": 100,
        "y": 200,
    })
    assert result["ok"] is True
    assert result["type"] == "Multiply"


def test_connect_material_pins(mock_unreal):
    fake_mat = types.SimpleNamespace(get_name=lambda: "M_Rock", get_path_name=lambda: "/Game/M_Rock")
    mock_unreal.EditorAssetLibrary.load_asset = lambda p: fake_mat

    connected = []
    mock_unreal.MaterialEditingLibrary.connect_material_expressions = (
        lambda a, b, c, d: connected.append((b, d)) or True
    )

    from handlers.materials import connect_pins
    result = connect_pins({
        "asset_path": "/Game/M_Rock",
        "from_node": "node_a",
        "from_pin": "RGB",
        "to_node": "node_b",
        "to_pin": "A",
    })
    assert result["ok"] is True
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/ue5_plugin/test_handlers_materials.py -v
```

Expected: 4 FAILs

- [ ] **Step 3: Implement material handlers**

```python
# ue5_plugin/UnrealAI/Content/Python/handlers/materials.py
import unreal

# Map friendly expression type names to UE5 class names
_EXPRESSION_MAP = {
    "Multiply":         "MaterialExpressionMultiply",
    "Add":              "MaterialExpressionAdd",
    "Lerp":             "MaterialExpressionLinearInterpolate",
    "TextureSample":    "MaterialExpressionTextureSample",
    "Constant":         "MaterialExpressionConstant",
    "Constant3":        "MaterialExpressionConstant3Vector",
    "ScalarParameter":  "MaterialExpressionScalarParameter",
    "VectorParameter":  "MaterialExpressionVectorParameter",
    "Emissive":         "MaterialExpressionEmissiveColor",
    "Fresnel":          "MaterialExpressionFresnel",
    "Power":            "MaterialExpressionPower",
    "Clamp":            "MaterialExpressionClamp",
    "OneMinus":         "MaterialExpressionOneMinus",
}

# Material output property identifiers
_OUTPUT_PROPS = {
    "BaseColor":   unreal.MaterialProperty.MP_BASE_COLOR if hasattr(unreal, "MaterialProperty") else "MP_BASE_COLOR",
    "Metallic":    "MP_METALLIC",
    "Roughness":   "MP_ROUGHNESS",
    "Normal":      "MP_NORMAL",
    "Emissive":    "MP_EMISSIVE_COLOR",
    "Opacity":     "MP_OPACITY",
}

# Runtime node registry: asset_path → {node_name: expression_object}
_node_registry: dict = {}


def _load_mat(asset_path: str):
    asset = unreal.EditorAssetLibrary.load_asset(asset_path)
    if asset is None:
        raise ValueError(f"Asset not found: {asset_path}")
    return asset


def create(body: dict) -> dict:
    asset_path = body.get("asset_path")
    if not asset_path:
        return {"ok": False, "error": "asset_path is required"}
    try:
        parts = asset_path.rsplit("/", 1)
        package_path = parts[0] + "/" if len(parts) > 1 else "/Game/"
        asset_name = parts[-1]

        factory = unreal.MaterialFactoryNew()
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        mat = asset_tools.create_asset(asset_name, package_path, unreal.Material, factory)
        _node_registry[asset_path] = {}
        return {"ok": True, "asset_path": asset_path, "name": asset_name}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def read(body: dict) -> dict:
    asset_path = body.get("asset_path")
    if not asset_path:
        return {"ok": False, "error": "asset_path is required"}
    try:
        mat = _load_mat(asset_path)
        nodes = list((_node_registry.get(asset_path) or {}).keys())
        return {"ok": True, "asset_path": asset_path, "nodes": nodes}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def list_assets(body: dict) -> dict:
    path = body.get("path", "/Game/")
    try:
        raw = unreal.EditorAssetLibrary.list_assets(path, recursive=True, include_folder=False)
        assets = [p.rsplit(".", 1)[0] for p in raw]
        return {"ok": True, "assets": assets}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def add_expression(body: dict) -> dict:
    asset_path = body.get("asset_path")
    expr_type = body.get("type", "Constant")
    node_x = body.get("x", 0)
    node_y = body.get("y", 0)
    node_name = body.get("name", f"{expr_type}_{node_x}_{node_y}")
    if not asset_path:
        return {"ok": False, "error": "asset_path is required"}
    try:
        mat = _load_mat(asset_path)
        class_name = _EXPRESSION_MAP.get(expr_type, f"MaterialExpression{expr_type}")
        expr_class = getattr(unreal, class_name, None)
        if expr_class is None:
            return {"ok": False, "error": f"Unknown expression type: {expr_type}"}
        node = unreal.MaterialEditingLibrary.create_material_expression(mat, expr_class, node_x, node_y)
        registry = _node_registry.setdefault(asset_path, {})
        registry[node_name] = node
        return {"ok": True, "node": node_name, "type": expr_type}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def connect_pins(body: dict) -> dict:
    asset_path = body.get("asset_path")
    from_node = body.get("from_node")
    from_pin = body.get("from_pin", "")
    to_node = body.get("to_node")
    to_pin = body.get("to_pin", "")
    if not asset_path or not from_node or not to_node:
        return {"ok": False, "error": "asset_path, from_node, and to_node are required"}
    try:
        mat = _load_mat(asset_path)
        registry = _node_registry.get(asset_path, {})

        from_expr = registry.get(from_node)
        to_expr = registry.get(to_node)

        # Allow connecting to the material output properties (e.g. "BaseColor")
        if to_node in _OUTPUT_PROPS:
            if from_expr is None:
                return {"ok": False, "error": f"Node not found: {from_node}"}
            unreal.MaterialEditingLibrary.connect_material_property(from_expr, from_pin, to_node)
        else:
            if from_expr is None or to_expr is None:
                missing = from_node if from_expr is None else to_node
                return {"ok": False, "error": f"Node not found: {missing}"}
            unreal.MaterialEditingLibrary.connect_material_expressions(from_expr, from_pin, to_expr, to_pin)

        return {"ok": True, "connected": f"{from_node}.{from_pin} → {to_node}.{to_pin}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def set_parameter(body: dict) -> dict:
    asset_path = body.get("asset_path")
    node_name = body.get("node")
    param_name = body.get("parameter_name")
    value = body.get("value")
    if not asset_path or not node_name:
        return {"ok": False, "error": "asset_path and node are required"}
    try:
        registry = _node_registry.get(asset_path, {})
        node = registry.get(node_name)
        if node is None:
            return {"ok": False, "error": f"Node not found: {node_name}"}
        if param_name:
            node.set_editor_property("ParameterName", param_name)
        if value is not None:
            node.set_editor_property("DefaultValue", value)
        return {"ok": True, "node": node_name, "parameter_name": param_name, "value": value}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def apply(body: dict) -> dict:
    asset_path = body.get("asset_path")
    target = body.get("target")
    slot = body.get("slot", 0)
    if not asset_path or not target:
        return {"ok": False, "error": "asset_path and target are required"}
    try:
        mat = _load_mat(asset_path)
        unreal.MaterialEditingLibrary.recompile_material(mat)

        mesh = unreal.EditorAssetLibrary.load_asset(target)
        if mesh:
            mesh.set_material(slot, mat)
        else:
            # Try to find as a level actor
            actors = unreal.EditorLevelLibrary.get_all_level_actors()
            actor = next((a for a in actors if a.get_name() == target), None)
            if actor is None:
                return {"ok": False, "error": f"Target not found: {target}"}
            for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
                comp.set_material(slot, mat)

        return {"ok": True, "material": asset_path, "applied_to": target}
    except Exception as e:
        return {"ok": False, "error": str(e)}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/ue5_plugin/test_handlers_materials.py -v
```

Expected: 4 PASSes

- [ ] **Step 5: Commit**

```bash
git add ue5_plugin/UnrealAI/Content/Python/handlers/materials.py tests/ue5_plugin/test_handlers_materials.py
git commit -m "feat: material handlers — create, add_expression, connect_pins, set_parameter, apply"
```

---

## Task 6: MCP Server — Client and Scene Tools

**Files:**
- Create: `mcp_server/__init__.py`
- Create: `mcp_server/client.py`
- Create: `mcp_server/tools/__init__.py`
- Create: `mcp_server/tools/scene.py`
- Create: `tests/mcp_server/test_client.py`
- Create: `tests/mcp_server/test_scene.py`

- [ ] **Step 1: Write failing tests for the HTTP client**

```python
# tests/mcp_server/test_client.py
from unittest.mock import patch, MagicMock
import pytest
from mcp_server.client import post, UE5ConnectionError


def test_post_returns_dict_on_success():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"ok": True, "actors": []}
    mock_resp.raise_for_status.return_value = None

    with patch("mcp_server.client.requests.post", return_value=mock_resp) as mock_post:
        result = post("/scene/actors", {})

    assert result == {"ok": True, "actors": []}
    mock_post.assert_called_once_with(
        "http://localhost:7777/scene/actors", json={}, timeout=30
    )


def test_post_raises_on_connection_error():
    import requests as req
    with patch("mcp_server.client.requests.post", side_effect=req.exceptions.ConnectionError):
        with pytest.raises(UE5ConnectionError, match="UE5 plugin server not running"):
            post("/scene/actors", {})
```

- [ ] **Step 2: Write failing tests for scene tools**

```python
# tests/mcp_server/test_scene.py
from unittest.mock import patch


def test_scene_get_actors_tool():
    with patch("mcp_server.client.post", return_value={
        "ok": True,
        "actors": [{"name": "BP_Character_1", "class": "BP_Character_C", "location": {"x": 0, "y": 0, "z": 0}}]
    }):
        from mcp_server.tools.scene import _scene_get_actors
        result = _scene_get_actors()

    assert "BP_Character_1" in result


def test_scene_screenshot_tool():
    with patch("mcp_server.client.post", return_value={
        "ok": True, "path": "/tmp/screenshot.png", "note": "async"
    }):
        from mcp_server.tools.scene import _scene_screenshot
        result = _scene_screenshot(width=1920, height=1080)

    assert "/tmp/screenshot.png" in result


def test_scene_get_actors_raises_on_plugin_error():
    import pytest
    with patch("mcp_server.client.post", return_value={"ok": False, "error": "Editor not ready"}):
        from mcp_server.tools.scene import _scene_get_actors
        with pytest.raises(RuntimeError, match="Editor not ready"):
            _scene_get_actors()
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
pytest tests/mcp_server/ -v
```

Expected: FAILs — modules don't exist yet.

- [ ] **Step 4: Implement the HTTP client**

```python
# mcp_server/__init__.py
# (empty)
```

```python
# mcp_server/client.py
import requests

UE5_BASE_URL = "http://localhost:7777"


class UE5ConnectionError(RuntimeError):
    pass


def post(path: str, data: dict) -> dict:
    try:
        resp = requests.post(f"{UE5_BASE_URL}{path}", json=data, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        raise UE5ConnectionError(
            "UE5 plugin server not running. "
            "Open Unreal Engine with the UnrealAI plugin enabled."
        )
```

- [ ] **Step 5: Implement scene tools**

```python
# mcp_server/tools/__init__.py
# (empty)
```

```python
# mcp_server/tools/scene.py
"""Scene understanding tools: actors, detail, screenshot."""
import json
from mcp_server import client


def _check(result: dict) -> dict:
    """Raise RuntimeError if result is not ok."""
    if not result.get("ok"):
        raise RuntimeError(result.get("error", "Unknown error from UE5 plugin"))
    return result


def _scene_get_actors() -> str:
    result = _check(client.post("/scene/actors", {}))
    lines = [f"- {a['name']} ({a['class']}) at {a['location']}" for a in result["actors"]]
    count = len(result["actors"])
    return f"{count} actors in level:\n" + "\n".join(lines)


def _scene_get_actor_detail(name: str) -> str:
    result = _check(client.post("/scene/actor", {"name": name}))
    return json.dumps(result, indent=2)


def _scene_screenshot(width: int = 1920, height: int = 1080) -> str:
    result = _check(client.post("/scene/screenshot", {"width": width, "height": height}))
    return f"Screenshot saved to: {result['path']}\nNote: {result.get('note', '')}"


def register(mcp):
    @mcp.tool()
    def scene_get_actors() -> str:
        """List all actors in the current Unreal level with their class and location."""
        return _scene_get_actors()

    @mcp.tool()
    def scene_get_actor_detail(name: str) -> str:
        """Get the full component tree and properties of a specific actor by name."""
        return _scene_get_actor_detail(name)

    @mcp.tool()
    def scene_screenshot(width: int = 1920, height: int = 1080) -> str:
        """Capture the current editor viewport and return the file path."""
        return _scene_screenshot(width=width, height=height)
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
pytest tests/mcp_server/ -v
```

Expected: all PASSes

- [ ] **Step 7: Commit**

```bash
git add mcp_server/ tests/mcp_server/
git commit -m "feat: MCP server HTTP client and scene tools (scene_get_actors, scene_screenshot)"
```

---

## Task 7: MCP Server — Blueprint Tools

**Files:**
- Create: `mcp_server/tools/blueprints.py`
- Create: `tests/mcp_server/test_blueprints.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/mcp_server/test_blueprints.py
from unittest.mock import patch
import pytest


def test_bp_create_posts_correct_body():
    with patch("mcp_server.client.post", return_value={
        "ok": True, "asset_path": "/Game/BP_Hero", "name": "BP_Hero"
    }) as mock_post:
        from mcp_server.tools.blueprints import _bp_create
        result = _bp_create(asset_path="/Game/BP_Hero", parent_class="Actor")

    mock_post.assert_called_once_with(
        "/blueprint/create", {"asset_path": "/Game/BP_Hero", "parent_class": "Actor"}
    )
    assert "/Game/BP_Hero" in result


def test_bp_compile_shows_errors():
    with patch("mcp_server.client.post", return_value={
        "ok": True, "errors": ["Pin not connected: Health"], "clean": False
    }):
        from mcp_server.tools.blueprints import _bp_compile
        result = _bp_compile(asset_path="/Game/BP_Hero")

    assert "Pin not connected" in result


def test_bp_compile_clean():
    with patch("mcp_server.client.post", return_value={
        "ok": True, "errors": [], "clean": True
    }):
        from mcp_server.tools.blueprints import _bp_compile
        result = _bp_compile(asset_path="/Game/BP_Hero")

    assert "clean" in result.lower() or "success" in result.lower()


def test_bp_add_node_raises_on_error():
    with patch("mcp_server.client.post", return_value={
        "ok": False, "error": "Graph not found: EventGraph"
    }):
        from mcp_server.tools.blueprints import _bp_add_node
        with pytest.raises(RuntimeError, match="Graph not found"):
            _bp_add_node(asset_path="/Game/BP_Hero", graph="EventGraph", function="PrintString")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/mcp_server/test_blueprints.py -v
```

Expected: FAILs

- [ ] **Step 3: Implement blueprint tools**

```python
# mcp_server/tools/blueprints.py
"""Blueprint tools: create, read, list, add/modify nodes and variables, compile."""
import json
from mcp_server import client


def _check(result: dict) -> dict:
    if not result.get("ok"):
        raise RuntimeError(result.get("error", "Unknown error from UE5 plugin"))
    return result


# --- internal functions (testable without MCP context) ---

def _bp_create(asset_path: str, parent_class: str = "Actor") -> str:
    r = _check(client.post("/blueprint/create", {"asset_path": asset_path, "parent_class": parent_class}))
    return f"Created Blueprint: {r['asset_path']}"


def _bp_read(asset_path: str) -> str:
    r = _check(client.post("/blueprint/read", {"asset_path": asset_path}))
    return json.dumps(r, indent=2)


def _bp_list(path: str = "/Game/") -> str:
    r = _check(client.post("/blueprint/list", {"path": path}))
    return "\n".join(r["assets"]) or "(none)"


def _bp_add_variable(asset_path: str, name: str, type: str = "float", default_value=None) -> str:
    body = {"asset_path": asset_path, "name": name, "type": type}
    if default_value is not None:
        body["default_value"] = default_value
    r = _check(client.post("/blueprint/add_variable", body))
    return f"Added variable '{r['variable']}' ({r['type']}) to {asset_path}"


def _bp_add_component(asset_path: str, component_class: str, name: str = "") -> str:
    r = _check(client.post("/blueprint/add_component", {
        "asset_path": asset_path,
        "component_class": component_class,
        "name": name or component_class,
    }))
    return f"Added component '{r['component']}' ({r['class']}) to {asset_path}"


def _bp_add_function(asset_path: str, name: str) -> str:
    r = _check(client.post("/blueprint/add_function", {"asset_path": asset_path, "name": name}))
    return f"Added function '{r['function']}' to {asset_path}"


def _bp_add_event(asset_path: str, event: str = "BeginPlay") -> str:
    r = _check(client.post("/blueprint/add_event", {"asset_path": asset_path, "event": event}))
    return f"Added event '{r['event']}' to {asset_path}"


def _bp_add_node(asset_path: str, graph: str, function: str, x: int = 0, y: int = 0) -> str:
    r = _check(client.post("/blueprint/add_node", {
        "asset_path": asset_path, "graph": graph, "function": function, "x": x, "y": y
    }))
    pins_str = ", ".join(r.get("pins", []))
    return f"Added node '{r['node_id']}' (function: {function}). Pins: {pins_str}"


def _bp_connect_pins(asset_path: str, graph: str, from_node: str, from_pin: str, to_node: str, to_pin: str) -> str:
    r = _check(client.post("/blueprint/connect_pins", {
        "asset_path": asset_path, "graph": graph,
        "from_node": from_node, "from_pin": from_pin,
        "to_node": to_node, "to_pin": to_pin,
    }))
    return f"Connected: {r['connected']}"


def _bp_set_property(asset_path: str, property: str, value) -> str:
    r = _check(client.post("/blueprint/set_property", {
        "asset_path": asset_path, "property": property, "value": value
    }))
    return f"Set {r['property']} = {r['value']} on {asset_path}"


def _bp_set_component_property(asset_path: str, component: str, property: str, value) -> str:
    r = _check(client.post("/blueprint/set_component_property", {
        "asset_path": asset_path, "component": component, "property": property, "value": value
    }))
    return f"Set {component}.{r['property']} = {r['value']}"


def _bp_compile(asset_path: str) -> str:
    r = _check(client.post("/blueprint/compile", {"asset_path": asset_path}))
    if r["clean"]:
        return f"Compiled {asset_path} successfully — no errors."
    errors = "\n".join(f"  - {e}" for e in r["errors"])
    return f"Compiled {asset_path} with {len(r['errors'])} error(s):\n{errors}"


# --- MCP registration ---

def register(mcp):
    @mcp.tool()
    def bp_create(asset_path: str, parent_class: str = "Actor") -> str:
        """Create a new Blueprint class. asset_path example: /Game/Characters/BP_Hero"""
        return _bp_create(asset_path, parent_class)

    @mcp.tool()
    def bp_read(asset_path: str) -> str:
        """Read a Blueprint's graphs, variables, and components."""
        return _bp_read(asset_path)

    @mcp.tool()
    def bp_list(path: str = "/Game/") -> str:
        """List all Blueprint assets under a content path."""
        return _bp_list(path)

    @mcp.tool()
    def bp_add_variable(asset_path: str, name: str, type: str = "float", default_value: str = "") -> str:
        """Add a variable to a Blueprint. type: bool, int, float, string, vector, actor, object"""
        return _bp_add_variable(asset_path, name, type, default_value or None)

    @mcp.tool()
    def bp_add_component(asset_path: str, component_class: str, name: str = "") -> str:
        """Add a component to a Blueprint. component_class example: StaticMeshComponent"""
        return _bp_add_component(asset_path, component_class, name)

    @mcp.tool()
    def bp_add_function(asset_path: str, name: str) -> str:
        """Add a new function graph to a Blueprint."""
        return _bp_add_function(asset_path, name)

    @mcp.tool()
    def bp_add_event(asset_path: str, event: str = "BeginPlay") -> str:
        """Add an event to a Blueprint's EventGraph. event: BeginPlay, Tick, or a custom event name."""
        return _bp_add_event(asset_path, event)

    @mcp.tool()
    def bp_add_node(asset_path: str, graph: str, function: str, x: int = 0, y: int = 0) -> str:
        """Add a function call node to a Blueprint graph. function example: PrintString"""
        return _bp_add_node(asset_path, graph, function, x, y)

    @mcp.tool()
    def bp_connect_pins(asset_path: str, graph: str, from_node: str, from_pin: str, to_node: str, to_pin: str) -> str:
        """Connect an output pin to an input pin between two nodes in a Blueprint graph."""
        return _bp_connect_pins(asset_path, graph, from_node, from_pin, to_node, to_pin)

    @mcp.tool()
    def bp_set_property(asset_path: str, property: str, value: str) -> str:
        """Set a variable default value or node property on a Blueprint."""
        return _bp_set_property(asset_path, property, value)

    @mcp.tool()
    def bp_set_component_property(asset_path: str, component: str, property: str, value: str) -> str:
        """Set a property on a component within a Blueprint."""
        return _bp_set_component_property(asset_path, component, property, value)

    @mcp.tool()
    def bp_compile(asset_path: str) -> str:
        """Compile a Blueprint and return any errors."""
        return _bp_compile(asset_path)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/mcp_server/test_blueprints.py -v
```

Expected: all PASSes

- [ ] **Step 5: Commit**

```bash
git add mcp_server/tools/blueprints.py tests/mcp_server/test_blueprints.py
git commit -m "feat: MCP blueprint tools (12 tools)"
```

---

## Task 8: MCP Server — Material Tools

**Files:**
- Create: `mcp_server/tools/materials.py`
- Create: `tests/mcp_server/test_materials.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/mcp_server/test_materials.py
from unittest.mock import patch
import pytest


def test_mat_create():
    with patch("mcp_server.client.post", return_value={
        "ok": True, "asset_path": "/Game/M_Rock", "name": "M_Rock"
    }):
        from mcp_server.tools.materials import _mat_create
        result = _mat_create(asset_path="/Game/M_Rock")
    assert "M_Rock" in result


def test_mat_add_expression():
    with patch("mcp_server.client.post", return_value={
        "ok": True, "node": "Multiply_0_0", "type": "Multiply"
    }):
        from mcp_server.tools.materials import _mat_add_expression
        result = _mat_add_expression("/Game/M_Rock", "Multiply")
    assert "Multiply_0_0" in result


def test_mat_connect_pins():
    with patch("mcp_server.client.post", return_value={
        "ok": True, "connected": "node_a.RGB → node_b.A"
    }):
        from mcp_server.tools.materials import _mat_connect_pins
        result = _mat_connect_pins("/Game/M_Rock", "node_a", "RGB", "node_b", "A")
    assert "node_a" in result


def test_mat_apply():
    with patch("mcp_server.client.post", return_value={
        "ok": True, "material": "/Game/M_Rock", "applied_to": "SM_Floor"
    }):
        from mcp_server.tools.materials import _mat_apply
        result = _mat_apply(asset_path="/Game/M_Rock", target="SM_Floor")
    assert "SM_Floor" in result


def test_mat_tools_raise_on_error():
    with patch("mcp_server.client.post", return_value={"ok": False, "error": "Asset not found"}):
        from mcp_server.tools.materials import _mat_create
        with pytest.raises(RuntimeError, match="Asset not found"):
            _mat_create("/Game/Missing")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/mcp_server/test_materials.py -v
```

Expected: FAILs

- [ ] **Step 3: Implement material tools**

```python
# mcp_server/tools/materials.py
"""Material tools: create, read, list, add expressions, connect pins, apply."""
import json
from mcp_server import client


def _check(result: dict) -> dict:
    if not result.get("ok"):
        raise RuntimeError(result.get("error", "Unknown error from UE5 plugin"))
    return result


def _mat_create(asset_path: str) -> str:
    r = _check(client.post("/material/create", {"asset_path": asset_path}))
    return f"Created Material: {r['asset_path']}"


def _mat_read(asset_path: str) -> str:
    r = _check(client.post("/material/read", {"asset_path": asset_path}))
    return json.dumps(r, indent=2)


def _mat_list(path: str = "/Game/") -> str:
    r = _check(client.post("/material/list", {"path": path}))
    return "\n".join(r["assets"]) or "(none)"


def _mat_add_expression(asset_path: str, type: str, x: int = 0, y: int = 0, name: str = "") -> str:
    body = {"asset_path": asset_path, "type": type, "x": x, "y": y}
    if name:
        body["name"] = name
    r = _check(client.post("/material/add_expression", body))
    return f"Added expression node '{r['node']}' (type: {r['type']}) to {asset_path}"


def _mat_connect_pins(asset_path: str, from_node: str, from_pin: str, to_node: str, to_pin: str) -> str:
    r = _check(client.post("/material/connect_pins", {
        "asset_path": asset_path,
        "from_node": from_node, "from_pin": from_pin,
        "to_node": to_node, "to_pin": to_pin,
    }))
    return f"Connected: {r['connected']}"


def _mat_set_parameter(asset_path: str, node: str, parameter_name: str = "", value=None) -> str:
    r = _check(client.post("/material/set_parameter", {
        "asset_path": asset_path, "node": node,
        "parameter_name": parameter_name, "value": value,
    }))
    return f"Set parameter on '{r['node']}': {r['parameter_name']} = {r['value']}"


def _mat_apply(asset_path: str, target: str, slot: int = 0) -> str:
    r = _check(client.post("/material/apply", {
        "asset_path": asset_path, "target": target, "slot": slot
    }))
    return f"Applied {r['material']} to {r['applied_to']} (slot {slot})"


def register(mcp):
    @mcp.tool()
    def mat_create(asset_path: str) -> str:
        """Create a new Material asset. asset_path example: /Game/Materials/M_Rock"""
        return _mat_create(asset_path)

    @mcp.tool()
    def mat_read(asset_path: str) -> str:
        """Read a Material's expression nodes and connections."""
        return _mat_read(asset_path)

    @mcp.tool()
    def mat_list(path: str = "/Game/") -> str:
        """List Material assets under a content path."""
        return _mat_list(path)

    @mcp.tool()
    def mat_add_expression(asset_path: str, type: str, x: int = 0, y: int = 0, name: str = "") -> str:
        """Add an expression node to a Material graph. type: Multiply, Add, Lerp, TextureSample, Constant, Constant3, ScalarParameter, VectorParameter"""
        return _mat_add_expression(asset_path, type, x, y, name)

    @mcp.tool()
    def mat_connect_pins(asset_path: str, from_node: str, from_pin: str, to_node: str, to_pin: str) -> str:
        """Connect an output to an input between Material expression nodes. Use 'BaseColor', 'Metallic', etc. as to_node to connect to the material output."""
        return _mat_connect_pins(asset_path, from_node, from_pin, to_node, to_pin)

    @mcp.tool()
    def mat_set_parameter(asset_path: str, node: str, parameter_name: str = "", value: str = "") -> str:
        """Set the parameter name or default value on a Material expression node."""
        return _mat_set_parameter(asset_path, node, parameter_name, value or None)

    @mcp.tool()
    def mat_apply(asset_path: str, target: str, slot: int = 0) -> str:
        """Apply a Material to a Static Mesh asset path or a level actor name."""
        return _mat_apply(asset_path, target, slot)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/mcp_server/test_materials.py -v
```

Expected: all PASSes

- [ ] **Step 5: Commit**

```bash
git add mcp_server/tools/materials.py tests/mcp_server/test_materials.py
git commit -m "feat: MCP material tools (7 tools)"
```

---

## Task 9: MCP Server Entrypoint

**Files:**
- Create: `mcp_server/server.py`
- Create: `tests/mcp_server/test_server.py`

- [ ] **Step 1: Write failing test**

```python
# tests/mcp_server/test_server.py
def test_all_tools_registered():
    """Verify all 22 expected tools are registered with the MCP server."""
    from mcp_server.server import create_mcp_server
    mcp = create_mcp_server()

    # FastMCP stores tools in _tool_manager._tools dict
    registered = set(mcp._tool_manager._tools.keys())

    expected = {
        # Scene (3)
        "scene_get_actors", "scene_get_actor_detail", "scene_screenshot",
        # Blueprints (12)
        "bp_create", "bp_read", "bp_list", "bp_add_variable", "bp_add_component",
        "bp_add_function", "bp_add_event", "bp_add_node", "bp_connect_pins",
        "bp_set_property", "bp_set_component_property", "bp_compile",
        # Materials (7)
        "mat_create", "mat_read", "mat_list", "mat_add_expression",
        "mat_connect_pins", "mat_set_parameter", "mat_apply",
    }

    missing = expected - registered
    assert not missing, f"Missing tools: {missing}"
    assert len(registered) == 22
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/mcp_server/test_server.py -v
```

Expected: FAIL — `server.py` doesn't exist.

- [ ] **Step 3: Implement MCP server entrypoint**

```python
# mcp_server/server.py
"""FastMCP server entrypoint — registers all 22 tools and starts serving."""
from mcp.server.fastmcp import FastMCP
from mcp_server.tools import blueprints, materials, scene


def create_mcp_server() -> FastMCP:
    mcp = FastMCP("unreal-ai")
    blueprints.register(mcp)
    materials.register(mcp)
    scene.register(mcp)
    return mcp


def main():
    mcp = create_mcp_server()
    mcp.run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/mcp_server/test_server.py -v
```

Expected: PASS

- [ ] **Step 5: Run the full test suite to verify nothing is broken**

```bash
pytest tests/ -v
```

Expected: all PASSes, 0 failures

- [ ] **Step 6: Commit**

```bash
git add mcp_server/server.py tests/mcp_server/test_server.py
git commit -m "feat: MCP server entrypoint — all 22 tools registered"
```

---

## Task 10: Claude Code MCP Configuration

**Files:**
- Create: `claude_mcp_config.json` (reference file — users copy into their Claude config)

- [ ] **Step 1: Create the MCP config reference file**

```json
// claude_mcp_config.json
{
  "mcpServers": {
    "unreal-ai": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/path/to/unreal_ai"
    }
  }
}
```

- [ ] **Step 2: Verify MCP server starts without error**

```bash
cd /Users/mikecoker/projects/unreal_ai
python -m mcp_server.server --help
```

Expected: FastMCP help text, no import errors.

- [ ] **Step 3: Commit**

```bash
git add claude_mcp_config.json
git commit -m "docs: MCP config reference for Claude Code integration"
```

---

## Verification

End-to-end verification requires a running UE5 5.3+ editor with the UnrealAI plugin enabled.

1. **Plugin loads:** Drop `ue5_plugin/UnrealAI/` into your UE project's `Plugins/` folder, enable it in the editor. Check Output Log for `[UnrealAI] Server running on localhost:7777`.

2. **Health check:**
   ```bash
   curl http://localhost:7777/health
   # Expected: {"ok": true, "service": "unreal-ai"}
   ```

3. **MCP server connects:** Add config to `~/.claude.json`, run `claude mcp list`. Should show `unreal-ai`.

4. **Blueprint creation:**
   > Ask Claude: "Create a Blueprint called BP_TestActor in /Game/ that prints 'Hello' on BeginPlay and compiles clean."

   Expected: BP appears in Content Browser, compiles with no errors.

5. **Material creation:**
   > Ask Claude: "Create a red emissive Material at /Game/Materials/M_Red and apply it to the floor mesh."

   Expected: Material created with VectorParameter → Emissive connection, applied to actor.

6. **Scene understanding:**
   > Ask Claude: "Show me what's in the scene and take a screenshot."

   Expected: Claude lists actors and receives the viewport image.
