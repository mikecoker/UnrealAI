def _load_anim_bp(asset_path: str):
    import unreal
    asset = unreal.EditorAssetLibrary.load_asset(asset_path)
    if asset is None:
        raise ValueError(f"Animation Blueprint not found: {asset_path}")
    return asset


def _get_graph(anim_bp, graph_name: str):
    import unreal
    graph = unreal.BlueprintEditorLibrary.find_graph(anim_bp, graph_name)
    if graph is None:
        raise ValueError(f"Graph '{graph_name}' not found")
    return graph


def create(body: dict) -> dict:
    """Create a new Animation Blueprint asset."""
    import unreal
    asset_path = body.get("asset_path")
    skeleton_path = body.get("skeleton_path")
    if not asset_path or not skeleton_path:
        return {"ok": False, "error": "asset_path and skeleton_path are required"}

    try:
        parts = asset_path.rsplit("/", 1)
        package_path = parts[0] + "/" if len(parts) > 1 else "/Game/"
        asset_name = parts[-1]

        skeleton = unreal.EditorAssetLibrary.load_asset(skeleton_path)
        if skeleton is None:
            return {"ok": False, "error": f"Skeleton not found: {skeleton_path}"}

        factory = unreal.AnimBlueprintFactory()
        factory.target_skeleton = skeleton
        factory.parent_class = unreal.AnimInstance

        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        anim_bp = asset_tools.create_asset(
            asset_name, package_path, unreal.AnimBlueprint, factory
        )
        if anim_bp is None:
            return {"ok": False, "error": "Failed to create Animation Blueprint"}

        return {"ok": True, "asset_path": asset_path, "name": asset_name}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def read(body: dict) -> dict:
    """Read Animation Blueprint info: graphs and bound skeleton."""
    import unreal
    asset_path = body.get("asset_path")
    if not asset_path:
        return {"ok": False, "error": "asset_path is required"}

    try:
        anim_bp = _load_anim_bp(asset_path)

        graphs = []
        for name in ("AnimGraph", "EventGraph"):
            g = unreal.BlueprintEditorLibrary.find_graph(anim_bp, name)
            if g:
                graphs.append(g.get_name())

        skeleton = anim_bp.get_editor_property("target_skeleton")
        skeleton_path = skeleton.get_path_name() if skeleton else None

        return {
            "ok": True,
            "asset_path": asset_path,
            "graphs": graphs,
            "skeleton": skeleton_path,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def add_node(body: dict) -> dict:
    """Add a node to an animation graph."""
    import unreal
    asset_path = body.get("asset_path")
    node_type = body.get("node_type")
    graph_name = body.get("graph", "AnimGraph")
    x = body.get("x", 0)
    y = body.get("y", 0)
    if not asset_path or not node_type:
        return {"ok": False, "error": "asset_path and node_type are required"}

    try:
        anim_bp = _load_anim_bp(asset_path)
        graph = _get_graph(anim_bp, graph_name)

        node = unreal.UnrealAIGraphLibrary.add_animation_node(graph, node_type, x, y)
        if node is None:
            return {"ok": False, "error": f"Failed to add node of type '{node_type}'"}

        unreal.EditorAssetLibrary.save_asset(asset_path)
        return {"ok": True, "node_id": node.get_name(), "node_type": node_type,
                "asset_path": asset_path}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_nodes(body: dict) -> dict:
    """Get all nodes in an animation graph."""
    import unreal
    asset_path = body.get("asset_path")
    graph_name = body.get("graph", "AnimGraph")
    if not asset_path:
        return {"ok": False, "error": "asset_path is required"}

    try:
        anim_bp = _load_anim_bp(asset_path)
        graph = _get_graph(anim_bp, graph_name)

        nodes_info = unreal.UnrealAIGraphLibrary.get_graph_nodes(graph)
        nodes = [{"name": n.node_name, "class": n.node_class,
                  "inputs": list(n.input_pins), "outputs": list(n.output_pins)}
                 for n in nodes_info]
        return {"ok": True, "asset_path": asset_path, "graph": graph_name, "nodes": nodes}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def delete_node(body: dict) -> dict:
    """Delete a node from an animation graph by its node_id."""
    import unreal
    asset_path = body.get("asset_path")
    node_name = body.get("node_name")
    graph_name = body.get("graph", "AnimGraph")
    if not asset_path or not node_name:
        return {"ok": False, "error": "asset_path and node_name are required"}

    try:
        anim_bp = _load_anim_bp(asset_path)
        graph = _get_graph(anim_bp, graph_name)

        removed = unreal.UnrealAIGraphLibrary.delete_animation_node(graph, node_name)
        if not removed:
            return {"ok": False,
                    "error": f"Node '{node_name}' not found or cannot be deleted (result node is protected)"}

        unreal.EditorAssetLibrary.save_asset(asset_path)
        return {"ok": True, "node_name": node_name, "asset_path": asset_path}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def connect_nodes(body: dict) -> dict:
    """Connect two animation nodes (from_node output → to_node input)."""
    import unreal
    asset_path = body.get("asset_path")
    from_node = body.get("from_node")
    to_node = body.get("to_node")
    graph_name = body.get("graph", "AnimGraph")
    if not all([asset_path, from_node, to_node]):
        return {"ok": False, "error": "asset_path, from_node, and to_node are required"}

    try:
        anim_bp = _load_anim_bp(asset_path)
        graph = _get_graph(anim_bp, graph_name)

        ok = unreal.UnrealAIGraphLibrary.connect_animation_nodes(graph, from_node, to_node)
        if not ok:
            return {"ok": False, "error": f"Could not connect '{from_node}' to '{to_node}'"}

        unreal.EditorAssetLibrary.save_asset(asset_path)
        return {"ok": True, "connected": f"{from_node} -> {to_node}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def disconnect_nodes(body: dict) -> dict:
    """Disconnect two animation nodes."""
    import unreal
    asset_path = body.get("asset_path")
    from_node = body.get("from_node")
    to_node = body.get("to_node")
    graph_name = body.get("graph", "AnimGraph")
    if not all([asset_path, from_node, to_node]):
        return {"ok": False, "error": "asset_path, from_node, and to_node are required"}

    try:
        anim_bp = _load_anim_bp(asset_path)
        graph = _get_graph(anim_bp, graph_name)

        ok = unreal.UnrealAIGraphLibrary.disconnect_animation_nodes(graph, from_node, to_node)
        if not ok:
            return {"ok": False,
                    "error": f"No connection found between '{from_node}' and '{to_node}'"}

        unreal.EditorAssetLibrary.save_asset(asset_path)
        return {"ok": True, "disconnected": f"{from_node} -> {to_node}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def compile(body: dict) -> dict:
    """Compile the Animation Blueprint."""
    import unreal
    asset_path = body.get("asset_path")
    if not asset_path:
        return {"ok": False, "error": "asset_path is required"}

    try:
        anim_bp = _load_anim_bp(asset_path)
        result = unreal.BlueprintEditorLibrary.compile_blueprint(anim_bp)
        errors = []
        if result:
            for err in result:
                errors.append(err.get_message() if hasattr(err, "get_message") else str(err))
        return {"ok": True, "asset_path": asset_path, "errors": errors,
                "clean": len(errors) == 0}
    except Exception as e:
        return {"ok": False, "error": str(e)}
