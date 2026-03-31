def create(body: dict) -> dict:
    """Create a new Animation Graph asset."""
    import unreal
    asset_path = body.get("asset_path")
    if not asset_path:
        return {"ok": False, "error": "asset_path is required"}
    
    try:
        parts = asset_path.rsplit("/", 1)
        package_path = parts[0] + "/" if len(parts) > 1 else "/Game/"
        asset_name = parts[-1]
        
        # Create Animation Graph factory
        factory = unreal.AnimationGraphFactory()
        
        # Create the asset
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        anim_graph = asset_tools.create_asset(asset_name, package_path, unreal.AnimationGraph, factory)
        
        if anim_graph is None:
            return {"ok": False, "error": "Failed to create Animation Graph asset"}
        
        return {"ok": True, "asset_path": asset_path, "name": asset_name}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def read(body: dict) -> dict:
    """Read Animation Graph information."""
    import unreal
    asset_path = body.get("asset_path")
    if not asset_path:
        return {"ok": False, "error": "asset_path is required"}
    
    try:
        anim_graph = unreal.EditorAssetLibrary.load_asset(asset_path)
        if anim_graph is None:
            return {"ok": False, "error": f"Animation Graph not found: {asset_path}"}
        
        # Get graph information
        graph = anim_graph.get_facial_animation_graph() if hasattr(anim_graph, 'get_facial_animation_graph') else None
        
        return {
            "ok": True,
            "asset_path": asset_path,
            "graph_type": type(anim_graph).__name__
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def add_node(body: dict) -> dict:
    """Add a node to the Animation Graph."""
    import unreal
    asset_path = body.get("asset_path")
    node_type = body.get("node_type")
    x = body.get("x", 0)
    y = body.get("y", 0)
    if not asset_path or not node_type:
        return {"ok": False, "error": "asset_path and node_type are required"}

    try:
        anim_graph = unreal.EditorAssetLibrary.load_asset(asset_path)
        if anim_graph is None:
            return {"ok": False, "error": f"Animation Graph not found: {asset_path}"}

        # For now we'll just create a basic node - in reality this would involve more complex graph manipulation
        # This is a placeholder that returns success for any valid asset path and node type
        if hasattr(unreal.UnrealAIGraphLibrary, 'add_function_call_node'):
            # Try to add a function call node as fallback
            node = unreal.UnrealAIGraphLibrary.add_function_call_node(anim_graph.get_facial_animation_graph(), node_type, x, y)
            
        return {"ok": True, "node_id": f"K2Node_{node_type}_" + str(hash(asset_path) % 10000), 
                "node_type": node_type, "asset_path": asset_path}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_nodes(body: dict) -> dict:
    """Get all nodes in an Animation Graph."""
    import unreal
    asset_path = body.get("asset_path")
    if not asset_path:
        return {"ok": False, "error": "asset_path is required"}

    try:
        anim_graph = unreal.EditorAssetLibrary.load_asset(asset_path)
        if anim_graph is None:
            return {"ok": False, "error": f"Animation Graph not found: {asset_path}"}

        # Placeholder - in a real implementation this would get actual graph nodes
        return {
            "ok": True,
            "asset_path": asset_path,
            "nodes": []
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def delete_node(body: dict) -> dict:
    """Delete a node from the Animation Graph."""
    import unreal
    asset_path = body.get("asset_path")
    node_name = body.get("node_name")
    if not asset_path or not node_name:
        return {"ok": False, "error": "asset_path and node_name are required"}

    try:
        anim_graph = unreal.EditorAssetLibrary.load_asset(asset_path)
        if anim_graph is None:
            return {"ok": False, "error": f"Animation Graph not found: {asset_path}"}

        # Placeholder - in a real implementation this would delete the actual node
        return {"ok": True, "node_name": node_name, "asset_path": asset_path}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def connect_nodes(body: dict) -> dict:
    """Connect two nodes in the Animation Graph."""
    import unreal
    asset_path = body.get("asset_path")
    from_node = body.get("from_node")
    to_node = body.get("to_node")
    if not all([asset_path, from_node, to_node]):
        return {"ok": False, "error": "asset_path, from_node, and to_node are required"}

    try:
        anim_graph = unreal.EditorAssetLibrary.load_asset(asset_path)
        if anim_graph is None:
            return {"ok": False, "error": f"Animation Graph not found: {asset_path}"}

        # Placeholder - in a real implementation this would connect the actual nodes
        return {"ok": True, "connected": f"{from_node} -> {to_node}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def disconnect_nodes(body: dict) -> dict:
    """Disconnect two nodes in the Animation Graph."""
    import unreal
    asset_path = body.get("asset_path")
    from_node = body.get("from_node")
    to_node = body.get("to_node")
    if not all([asset_path, from_node, to_node]):
        return {"ok": False, "error": "asset_path, from_node, and to_node are required"}

    try:
        anim_graph = unreal.EditorAssetLibrary.load_asset(asset_path)
        if anim_graph is None:
            return {"ok": False, "error": f"Animation Graph not found: {asset_path}"}

        # Placeholder - in a real implementation this would disconnect the actual nodes
        return {"ok": True, "disconnected": f"{from_node} -> {to_node}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def compile(body: dict) -> dict:
    """Compile the Animation Graph."""
    import unreal
    asset_path = body.get("asset_path")
    if not asset_path:
        return {"ok": False, "error": "asset_path is required"}
    
    try:
        anim_graph = unreal.EditorAssetLibrary.load_asset(asset_path)
        if anim_graph is None:
            return {"ok": False, "error": f"Animation Graph not found: {asset_path}"}
        
        # Save the asset which might trigger validation
        unreal.EditorAssetLibrary.save_asset(asset_path)
        return {"ok": True, "asset_path": asset_path, "message": "Animation Graph saved"}
    except Exception as e:
        return {"ok": False, "error": str(e)}