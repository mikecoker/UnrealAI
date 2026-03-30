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
    import unreal
    asset = unreal.EditorAssetLibrary.load_asset(asset_path)
    if asset is None:
        raise ValueError(f"Asset not found: {asset_path}")
    return asset


def create(body: dict) -> dict:
    import unreal
    asset_path = body.get("asset_path")
    if not asset_path:
        return {"ok": False, "error": "asset_path is required"}

    parent_name = body.get("parent_class", "Actor")
    parent_path = _PARENT_CLASS_MAP.get(parent_name, f"/Script/Engine.{parent_name}")

    try:
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
    import unreal
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
    import unreal
    path = body.get("path", "/Game/")
    try:
        raw = unreal.EditorAssetLibrary.list_assets(path, recursive=True, include_folder=False)
        assets = [p.rsplit(".", 1)[0] for p in raw]
        return {"ok": True, "assets": assets}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def add_variable(body: dict) -> dict:
    import unreal
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
    import unreal
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
    import unreal
    asset_path = body.get("asset_path")
    name = body.get("name")
    if not asset_path or not name:
        return {"ok": False, "error": "asset_path and name are required"}
    try:
        bp = _load_bp(asset_path)
        unreal.BlueprintEditorLibrary.add_function(bp, name)
        return {"ok": True, "function": name}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def add_event(body: dict) -> dict:
    import unreal
    asset_path = body.get("asset_path")
    event = body.get("event", "BeginPlay")
    if not asset_path:
        return {"ok": False, "error": "asset_path is required"}
    try:
        bp = _load_bp(asset_path)
        graph = unreal.BlueprintEditorLibrary.get_editor_graph(bp, "EventGraph")
        return {"ok": True, "event": event, "graph": "EventGraph"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def add_node(body: dict) -> dict:
    import unreal
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
    import unreal
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
    import unreal
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
    import unreal
    asset_path = body.get("asset_path")
    component = body.get("component")
    property_name = body.get("property")
    value = body.get("value")
    if not asset_path or not component or property_name is None:
        return {"ok": False, "error": "asset_path, component, and property are required"}
    try:
        bp = _load_bp(asset_path)
        comp_obj = unreal.EditorAssetLibrary.load_asset(f"{asset_path}:{component}")
        if comp_obj:
            comp_obj.set_editor_property(property_name, value)
        return {"ok": True, "component": component, "property": property_name, "value": value}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def compile(body: dict) -> dict:
    import unreal
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
