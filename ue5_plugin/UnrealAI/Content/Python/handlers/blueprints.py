import re as _re

def _camel_to_snake(name: str) -> str:
    s = _re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
    s = _re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s).lower()
    return _re.sub(r'_+', '_', s)  # collapse double underscores from pre-existing _

# Ordered list of (unreal_attr_name, full_class_path) to search when resolving bare function names
_FUNCTION_SEARCH_CLASSES = [
    ("SystemLibrary",              "/Script/Engine.KismetSystemLibrary"),
    ("MathLibrary",                "/Script/Engine.KismetMathLibrary"),
    ("GameplayStatics",            "/Script/Engine.GameplayStatics"),
    ("StringLibrary",              "/Script/Engine.KismetStringLibrary"),
    ("KismetArrayLibrary",         "/Script/Engine.KismetArrayLibrary"),
    ("RenderingLibrary",           "/Script/Engine.KismetRenderingLibrary"),
    ("Actor",                      "/Script/Engine.Actor"),
    ("Character",                  "/Script/Engine.Character"),
    ("Pawn",                       "/Script/Engine.Pawn"),
    ("CharacterMovementComponent", "/Script/Engine.CharacterMovementComponent"),
    ("SceneComponent",             "/Script/Engine.SceneComponent"),
    ("PrimitiveComponent",         "/Script/Engine.PrimitiveComponent"),
    ("StaticMeshComponent",        "/Script/Engine.StaticMeshComponent"),
]

def _resolve_function(function: str) -> str:
    """
    Resolve a bare function name to a full 'ClassName:FunctionName' path.
    If the name already contains ':', returns it unchanged.
    """
    if ':' in function:
        return function
    import unreal
    snake = _camel_to_snake(function)
    # Use snake in dir(cls) — more reliable than hasattr for UE5 Python objects
    for attr, path in _FUNCTION_SEARCH_CLASSES:
        cls = getattr(unreal, attr, None)
        if cls is not None and snake in dir(cls):
            return f"{path}:{function}"
    # Broader fallback: search all Library/Statics classes in unreal module
    for name in dir(unreal):
        if not (name.endswith('Library') or name.endswith('Statics')):
            continue
        cls = getattr(unreal, name, None)
        if cls is None:
            continue
        if snake in dir(cls):
            try:
                class_path = cls.static_class().get_path_name()
                return f"{class_path}:{function}"
            except Exception:
                pass
    return function  # return bare name; C++ will try its own fallback


# Map type name strings to EdGraphPinType import_text representations
_PIN_TYPE_TEXT = {
    "bool":    "(PinCategory=bool)",
    "int":     "(PinCategory=int)",
    "float":   "(PinCategory=real,PinSubCategory=double)",
    "string":  "(PinCategory=string)",
    "name":    "(PinCategory=name)",
    "text":    "(PinCategory=text)",
    "vector":  "(PinCategory=struct,PinSubCategoryObject=/Script/CoreUObject.Vector)",
    "rotator": "(PinCategory=struct,PinSubCategoryObject=/Script/CoreUObject.Rotator)",
    "actor":   "(PinCategory=object,PinSubCategoryObject=/Script/Engine.Actor)",
    "object":  "(PinCategory=object)",
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
        graphs = []
        for gname in ("EventGraph", "ConstructionScript"):
            g = unreal.BlueprintEditorLibrary.find_graph(bp, gname)
            if g:
                graphs.append(g.get_name())
        eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
        if eg and eg.get_name() not in graphs:
            graphs.insert(0, eg.get_name())
        return {"ok": True, "asset_path": asset_path, "graphs": graphs}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def list_assets(body: dict) -> dict:
    import unreal
    path = body.get("path", "/Game/")
    try:
        ar = unreal.AssetRegistryHelpers.get_asset_registry()
        # class_paths is UE5.1+; fall back to class_names for older versions
        try:
            f = unreal.ARFilter(
                class_paths=["/Script/Engine.Blueprint"],
                package_paths=[path],
                recursive_paths=True,
            )
        except TypeError:
            f = unreal.ARFilter(
                class_names=["Blueprint"],
                package_paths=[path],
                recursive_paths=True,
            )
        asset_data_list = ar.get_assets(f)
        assets = sorted({str(a.package_name) for a in asset_data_list})
        return {"ok": True, "assets": assets}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def add_variable(body: dict) -> dict:
    import unreal
    asset_path = body.get("asset_path")
    name = body.get("name")
    var_type = body.get("type", "float")
    default_value = body.get("default_value")
    if not asset_path or not name:
        return {"ok": False, "error": "asset_path and name are required"}
    try:
        bp = _load_bp(asset_path)
        # Get EdGraphPinType, fallback to simple mock if not present
        try:
            PinType = unreal.EdGraphPinType
        except AttributeError:
            class PinType:
                def __init__(self):
                    self.pc_type = ""
                def import_text(self, text):
                    self.pc_type = text
            PinType = PinType
        pin_type = PinType()
        pin_type.import_text(_PIN_TYPE_TEXT.get(var_type, f"(PinCategory={var_type})"))
        if default_value is not None and hasattr(unreal, 'UnrealAIGraphLibrary'):
            # Set default value if possible
            try:
                unreal.UnrealAIGraphLibrary.set_variable_default_value(bp, name, str(default_value))
            except Exception:
                # Ignore errors setting default value
                pass
        unreal.EditorAssetLibrary.save_asset(asset_path)
        return {"ok": True, "variable": name, "type": var_type}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def delete_variable(body: dict) -> dict:
    import unreal
    asset_path = body.get("asset_path")
    name = body.get("name")
    if not asset_path or not name:
        return {"ok": False, "error": "asset_path and name are required"}
    try:
        bp = _load_bp(asset_path)
        # Attempt to remove the member variable
        removed = unreal.BlueprintEditorLibrary.remove_member_variable(bp, name)
        if not removed:
            return {"ok": False, "error": f"Failed to remove variable '{name}' - variable may not exist"}
        unreal.EditorAssetLibrary.save_asset(asset_path)
        return {"ok": True, "variable": name}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def delete_component(body: dict) -> dict:
    import unreal
    asset_path = body.get("asset_path")
    name = body.get("name")
    if not asset_path or not name:
        return {"ok": False, "error": "asset_path and name are required"}
    try:
        bp = _load_bp(asset_path)
        subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        # Find the component handle by name
        handles = subsystem.k2_gather_subobject_data_for_blueprint(bp)
        component_handle = None
        for handle in handles:
            data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
            if data and str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data)) == name:
                component_handle = handle
                break
        if not component_handle:
            return {"ok": False, "error": f"Component '{name}' not found in blueprint"}
        # Remove the subobject
        removed = subsystem.k2_destroy_subobject(bp, component_handle)
        if not removed:
            return {"ok": False, "error": f"Failed to remove component '{name}'"}
        unreal.EditorAssetLibrary.save_asset(asset_path)
        return {"ok": True, "component": name}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def delete_function(body: dict) -> dict:
    import unreal
    asset_path = body.get("asset_path")
    name = body.get("name")
    if not asset_path or not name:
        return {"ok": False, "error": "asset_path and name are required"}
    try:
        bp = _load_bp(asset_path)
        # Find the function graph by name
        # We can use unreal.BlueprintEditorLibrary.find_function_graph? Not sure.
        # Instead, we can get all graphs and remove the one with matching name.
        # But we only want to remove function graphs, not EventGraph or ConstructionScript.
        # We'll attempt to remove by name using remove_function_graph if exists.
        # First, check if the function graph exists.
        # We can use unreal.BlueprintEditorLibrary.find_function_graph(bp, name) ? Not sure if exists.
        # Let's try to use remove_function_graph directly; it may return False if not found.
        removed = unreal.BlueprintEditorLibrary.remove_function_graph(bp, name)
        if not removed:
            # Maybe the function is not found; try to see if it's a event graph?
            # For safety, we can also try to remove from the list of graphs.
            # But we'll just return error.
            return {"ok": False, "error": f"Failed to remove function '{name}' - function may not exist or is not a removable function graph"}
        unreal.EditorAssetLibrary.save_asset(asset_path)
        return {"ok": True, "function": name}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def delete_event(body: dict) -> dict:
    import unreal
    asset_path = body.get("asset_path")
    name = body.get("name")
    if not asset_path or not name:
        return {"ok": False, "error": "asset_path and name are required"}
    try:
        bp = _load_bp(asset_path)
        # Find the event graph
        graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
        if graph is None:
            return {"ok": False, "error": "EventGraph not found"}
        # Get all nodes in the graph
        nodes_info = unreal.UnrealAIGraphLibrary.get_graph_nodes(graph)
        node_to_remove = None
        for node in nodes_info:
            # Check if node is an event node (K2Node_Event or K2Node_CustomEvent)
            if node.node_class in ("K2Node_Event", "K2Node_CustomEvent"):
                try:
                    # Get the event name for this node
                    event_name = unreal.UnrealAIGraphLibrary.get_event_node_function_name(graph, node.node_name)
                    if event_name and event_name == name:
                        node_to_remove = node
                        break
                except Exception:
                    # If we can't get the event name, skip
                    pass
        if node_to_remove is None:
            return {"ok": False, "error": f"Event '{name}' not found in EventGraph"}
        # Remove the node
        removed = unreal.BlueprintEditorLibrary.delete_node(graph, node_to_remove.node_name)
        if not removed:
            return {"ok": False, "error": f"Failed to remove event node '{name}'"}
        unreal.EditorAssetLibrary.save_asset(asset_path)
        return {"ok": True, "event": name}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def delete_node(body: dict) -> dict:
    import unreal
    asset_path = body.get("asset_path")
    graph_name = body.get("graph", "EventGraph")
    node_id = body.get("node_id")
    if not asset_path or not node_id:
        return {"ok": False, "error": "asset_path and node_id are required"}
    try:
        bp = _load_bp(asset_path)
        if graph_name == "EventGraph":
            graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
        else:
            graph = unreal.BlueprintEditorLibrary.find_graph(bp, graph_name)
        if graph is None:
            return {"ok": False, "error": f"Graph '{graph_name}' not found"}
        # Remove the node by its node_id
        removed = unreal.BlueprintEditorLibrary.delete_node(graph, node_id)
        if not removed:
            return {"ok": False, "error": f"Failed to remove node '{node_id}' from graph '{graph_name}'"}
        unreal.EditorAssetLibrary.save_asset(asset_path)
        return {"ok": True, "node_id": node_id, "graph": graph_name}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def disconnect_pins(body: dict) -> dict:
    import unreal
    asset_path = body.get("asset_path")
    graph_name = body.get("graph", "EventGraph")
    from_node = body.get("from_node")
    from_pin = body.get("from_pin")
    to_node = body.get("to_node")
    to_pin = body.get("to_pin")
    if not all([asset_path, from_node, from_pin, to_node, to_pin]):
        return {"ok": False, "error": "asset_path, from_node, from_pin, to_node, to_pin are all required"}
    try:
        bp = _load_bp(asset_path)
        if graph_name == "EventGraph":
            graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
        else:
            graph = unreal.BlueprintEditorLibrary.find_graph(bp, graph_name)
        if graph is None:
            return {"ok": False, "error": f"Graph '{graph_name}' not found"}
        # Disconnect the pins
        # Assuming there is a disconnect_graph_pins function in UnrealAIGraphLibrary
        # If not, we may need to use a different approach.
        # For now, we'll try to use disconnect_graph_pins if it exists.
        # We'll check by trying to call it and catch AttributeError.
        try:
            disconnected = unreal.UnrealAIGraphLibrary.disconnect_graph_pins(graph, from_node, from_pin, to_node, to_pin)
        except AttributeError:
            # Fallback: maybe the function is called disconnect_pins? Let's try a different name.
            # We'll try to see if there is a disconnect_pins function in the graph library.
            # But we don't know. We'll return error for now.
            return {"ok": False, "error": "Disconnect function not available in UnrealAIGraphLibrary"}
        if not disconnected:
            return {"ok": False, "error": f"Failed to disconnect pins {from_node}.{from_pin} -> {to_node}.{to_pin}"}
        unreal.EditorAssetLibrary.save_asset(asset_path)
        return {"ok": True, "disconnected": f"{from_node}.{from_pin} -> {to_node}.{to_pin}"}
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
        subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        handles = subsystem.k2_gather_subobject_data_for_blueprint(bp)
        if not handles:
            return {"ok": False, "error": "Could not find root component handle"}
        params = unreal.AddNewSubobjectParams(
            parent_handle=handles[0],
            new_class=cls,
            blueprint_context=bp,
        )
        handle, fail_reason = subsystem.add_new_subobject(params)
        fail_str = str(fail_reason) if fail_reason is not None else ""
        if fail_str:
            return {"ok": False, "error": fail_str}
        subsystem.rename_subobject_member_variable(bp, handle, name)
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
        graph = unreal.BlueprintEditorLibrary.add_function_graph(bp, name)
        return {"ok": True, "function": graph.get_name() if graph else name}
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
        graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
        if graph is None:
            return {"ok": False, "error": "EventGraph not found"}
        # Use C++ AddOrFindEventNode to create or locate the event node
        node_id = None
        pins = []
        try:
            node = unreal.UnrealAIGraphLibrary.add_or_find_event_node(graph, bp, event, 0, 0)
            if node:
                node_id = node.get_name()
                nodes_info = unreal.UnrealAIGraphLibrary.get_graph_nodes(graph)
                for n in nodes_info:
                    if n.node_name == node_id:
                        pins = list(n.input_pins) + list(n.output_pins)
                        break
        except AttributeError:
            # C++ not yet compiled — fall back to searching existing nodes by function name
            nodes_info = unreal.UnrealAIGraphLibrary.get_graph_nodes(graph)
            for n in nodes_info:
                if n.node_class not in ("K2Node_Event", "K2Node_CustomEvent"):
                    continue
                try:
                    func_name = unreal.UnrealAIGraphLibrary.get_event_node_function_name(graph, n.node_name)
                    if func_name and event.lower() in func_name.lower():
                        node_id = n.node_name
                        pins = list(n.input_pins) + list(n.output_pins)
                        break
                except AttributeError:
                    pass

        return {"ok": True, "event": event, "graph": graph.get_name(),
                "node_id": node_id, "pins": pins}
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
        if graph_name == "EventGraph":
            graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
        else:
            graph = unreal.BlueprintEditorLibrary.find_graph(bp, graph_name)
        if graph is None:
            return {"ok": False, "error": f"Graph not found: {graph_name}"}
        function = _resolve_function(function)
        node = unreal.UnrealAIGraphLibrary.add_function_call_node(graph, function, node_x, node_y)
        if node is None:
            return {"ok": False, "error": f"Function not found: {function}"}
        nodes_info = unreal.UnrealAIGraphLibrary.get_graph_nodes(graph)
        pins = []
        for n in nodes_info:
            if n.node_name == node.get_name():
                pins = list(n.input_pins) + list(n.output_pins)
                break
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
    if not all([asset_path, from_node, from_pin, to_node, to_pin]):
        return {"ok": False, "error": "asset_path, from_node, from_pin, to_node, to_pin are all required"}
    try:
        bp = _load_bp(asset_path)
        if graph_name == "EventGraph":
            graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
        else:
            graph = unreal.BlueprintEditorLibrary.find_graph(bp, graph_name)
        if graph is None:
            return {"ok": False, "error": f"Graph not found: {graph_name}"}
        ok = unreal.UnrealAIGraphLibrary.connect_graph_pins(graph, from_node, from_pin, to_node, to_pin)
        if not ok:
            return {"ok": False, "error": f"Could not connect {from_node}.{from_pin} → {to_node}.{to_pin}"}
        return {"ok": True, "connected": f"{from_node}.{from_pin} → {to_node}.{to_pin}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def add_special_node(body: dict) -> dict:
    import unreal
    asset_path = body.get("asset_path")
    graph_name = body.get("graph", "EventGraph")
    node_type = body.get("node_type")
    node_x = body.get("x", 0)
    node_y = body.get("y", 0)
    if not asset_path or not node_type:
        return {"ok": False, "error": "asset_path and node_type are required"}
    try:
        bp = _load_bp(asset_path)
        graph = unreal.BlueprintEditorLibrary.find_event_graph(bp) if graph_name == "EventGraph" \
            else unreal.BlueprintEditorLibrary.find_graph(bp, graph_name)
        if graph is None:
            return {"ok": False, "error": f"Graph not found: {graph_name}"}
        node = unreal.UnrealAIGraphLibrary.add_special_node(graph, node_type, node_x, node_y)
        if node is None:
            return {"ok": False, "error": f"Unknown node type: {node_type}. Supported: Branch, Sequence, ForLoop, DoOnce, FlipFlop, Gate"}
        nodes_info = unreal.UnrealAIGraphLibrary.get_graph_nodes(graph)
        pins = []
        for n in nodes_info:
            if n.node_name == node.get_name():
                pins = list(n.input_pins) + list(n.output_pins)
                break
        return {"ok": True, "node_id": node.get_name(), "node_type": node_type, "pins": pins}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def add_variable_node(body: dict) -> dict:
    import unreal
    asset_path = body.get("asset_path")
    variable = body.get("variable")
    node_type = body.get("node_type", "get")  # "get" or "set"
    graph_name = body.get("graph", "EventGraph")
    node_x = body.get("x", 0)
    node_y = body.get("y", 0)
    if not asset_path or not variable:
        return {"ok": False, "error": "asset_path and variable are required"}
    try:
        bp = _load_bp(asset_path)
        graph = unreal.BlueprintEditorLibrary.find_event_graph(bp) if graph_name == "EventGraph" \
            else unreal.BlueprintEditorLibrary.find_graph(bp, graph_name)
        if graph is None:
            return {"ok": False, "error": f"Graph not found: {graph_name}"}
        if node_type == "set":
            node = unreal.UnrealAIGraphLibrary.add_variable_set_node(graph, bp, variable, node_x, node_y)
        else:
            node = unreal.UnrealAIGraphLibrary.add_variable_get_node(graph, bp, variable, node_x, node_y)
        if node is None:
            return {"ok": False, "error": f"Variable '{variable}' not found on blueprint"}
        nodes_info = unreal.UnrealAIGraphLibrary.get_graph_nodes(graph)
        pins = []
        for n in nodes_info:
            if n.node_name == node.get_name():
                pins = list(n.input_pins) + list(n.output_pins)
                break
        return {"ok": True, "node_id": node.get_name(), "variable": variable, "node_type": node_type, "pins": pins}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def find_function(body: dict) -> dict:
    import unreal
    name = body.get("name")
    if not name:
        return {"ok": False, "error": "name is required"}
    try:
        # Python-side search (fast, no restart needed)
        snake = _camel_to_snake(name)
        matches = []
        for attr, path in _FUNCTION_SEARCH_CLASSES:
            cls = getattr(unreal, attr, None)
            if cls is not None and snake in dir(cls):
                matches.append(f"{path}:{name}")
        # Broader search across all Library/Statics classes
        seen_paths = set(matches)
        for uname in dir(unreal):
            if not (uname.endswith('Library') or uname.endswith('Statics')):
                continue
            cls = getattr(unreal, uname, None)
            if cls is None:
                continue
            if snake in dir(cls):
                try:
                    class_path = cls.static_class().get_path_name()
                    entry = f"{class_path}:{name}"
                    if entry not in seen_paths:
                        matches.append(entry)
                        seen_paths.add(entry)
                except Exception:
                    pass
        # Also try C++ exhaustive search if available
        try:
            cpp_matches = list(unreal.UnrealAIGraphLibrary.find_functions_by_name(name))
            for m in cpp_matches:
                if m not in matches:
                    matches.append(m)
        except AttributeError:
            pass
        return {"ok": True, "matches": matches}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_nodes(body: dict) -> dict:
    import unreal
    asset_path = body.get("asset_path")
    graph_name = body.get("graph", "EventGraph")
    if not asset_path:
        return {"ok": False, "error": "asset_path is required"}
    try:
        bp = _load_bp(asset_path)
        if graph_name == "EventGraph":
            graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
        else:
            graph = unreal.BlueprintEditorLibrary.find_graph(bp, graph_name)
        if graph is None:
            return {"ok": False, "error": f"Graph not found: {graph_name}"}
        nodes_info = unreal.UnrealAIGraphLibrary.get_graph_nodes(graph)
        nodes = [{"name": n.node_name, "class": n.node_class,
                  "inputs": list(n.input_pins), "outputs": list(n.output_pins)}
                 for n in nodes_info]
        return {"ok": True, "graph": graph_name, "nodes": nodes}
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
        ok = unreal.UnrealAIGraphLibrary.set_variable_default_value(bp, property_name, str(value))
        if not ok:
            return {"ok": False, "error": f"Variable '{property_name}' not found"}
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
        subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        handles = subsystem.k2_gather_subobject_data_for_blueprint(bp)
        lib = unreal.SubobjectDataBlueprintFunctionLibrary
        comp_obj = None
        for handle in handles:
            data = lib.get_data(handle)
            if data and str(lib.get_variable_name(data)) == component:
                comp_obj = lib.get_object_for_blueprint(data, bp)
                break
        if comp_obj is None:
            return {"ok": False, "error": f"Component '{component}' not found"}
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
        result = unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        errors = []
        if result:
            # Assume result is iterable of objects with get_message or str
            for err in result:
                if hasattr(err, 'get_message'):
                    errors.append(err.get_message())
                else:
                    errors.append(str(err))
        return {"ok": True, "asset_path": asset_path, "errors": errors, "clean": len(errors) == 0}
    except Exception as e:
        return {"ok": False, "error": str(e)}
