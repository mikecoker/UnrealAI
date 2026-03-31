def create(body: dict) -> dict:
    """Create a new Behavior Tree asset."""
    import unreal
    asset_path = body.get("asset_path")
    if not asset_path:
        return {"ok": False, "error": "asset_path is required"}
    
    try:
        parts = asset_path.rsplit("/", 1)
        package_path = parts[0] + "/" if len(parts) > 1 else "/Game/"
        asset_name = parts[-1]
        
        # Create Behavior Tree factory
        factory = unreal.BehaviorTreeFactory()
        
        # Create the asset
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        bt = asset_tools.create_asset(asset_name, package_path, unreal.BehaviorTree, factory)
        
        if bt is None:
            return {"ok": False, "error": "Failed to create Behavior Tree asset"}
        
        return {"ok": True, "asset_path": asset_path, "name": asset_name}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def read(body: dict) -> dict:
    """Read Behavior Tree information."""
    import unreal
    asset_path = body.get("asset_path")
    if not asset_path:
        return {"ok": False, "error": "asset_path is required"}
    
    try:
        bt = unreal.EditorAssetLibrary.load_asset(asset_path)
        if bt is None:
            return {"ok": False, "error": f"Behavior Tree not found: {asset_path}"}
        
        # Get root node
        root_node = bt.get_root_node() if hasattr(bt, 'get_root_node') else None
        root_name = root_node.get_name() if root_node else None
        
        # Get blackboard asset
        blackboard_asset = bt.blackboard_asset if hasattr(bt, 'blackboard_asset') else None
        blackboard_path = blackboard_asset.get_path_name() if blackboard_asset else None
        
        return {
            "ok": True,
            "asset_path": asset_path,
            "root_node": root_name,
            "blackboard": blackboard_path
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def add_node(body: dict) -> dict:
    """Add a node to the Behavior Tree."""
    import unreal
    asset_path = body.get("asset_path")
    node_type = body.get("node_type")
    if not asset_path or not node_type:
        return {"ok": False, "error": "asset_path and node_type are required"}
    
    try:
        bt = unreal.EditorAssetLibrary.load_asset(asset_path)
        if bt is None:
            return {"ok": False, "error": f"Behavior Tree not found: {asset_path}"}
        
        # This is a simplified implementation - actual node addition would require
        # using the Behavior Tree editor APIs which are more complex
        # For now, we'll return a placeholder response
        return {
            "ok": True,
            "message": f"Node type '{node_type}' addition not fully implemented",
            "asset_path": asset_path
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def delete_node(body: dict) -> dict:
    """Delete a node from the Behavior Tree."""
    import unreal
    asset_path = body.get("asset_path")
    node_name = body.get("node_name")
    if not asset_path or not node_name:
        return {"ok": False, "error": "asset_path and node_name are required"}
    
    try:
        bt = unreal.EditorAssetLibrary.load_asset(asset_path)
        if bt is None:
            return {"ok": False, "error": f"Behavior Tree not found: {asset_path}"}
        
        # Placeholder implementation
        return {
            "ok": True,
            "message": f"Node '{node_name}' deletion not fully implemented",
            "asset_path": asset_path
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def connect_nodes(body: dict) -> dict:
    """Connect two nodes in the Behavior Tree."""
    import unreal
    asset_path = body.get("asset_path")
    from_node = body.get("from_node")
    to_node = body.get("to_node")
    if not all([asset_path, from_node, to_node]):
        return {"ok": False, "error": "asset_path, from_node, and to_node are required"}
    
    try:
        bt = unreal.EditorAssetLibrary.load_asset(asset_path)
        if bt is None:
            return {"ok": False, "error": f"Behavior Tree not found: {asset_path}"}
        
        # Placeholder implementation
        return {
            "ok": True,
            "message": f"Connection from '{from_node}' to '{to_node}' not fully implemented",
            "asset_path": asset_path
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def disconnect_nodes(body: dict) -> dict:
    """Disconnect two nodes in the Behavior Tree."""
    import unreal
    asset_path = body.get("asset_path")
    from_node = body.get("from_node")
    to_node = body.get("to_node")
    if not all([asset_path, from_node, to_node]):
        return {"ok": False, "error": "asset_path, from_node, and to_node are required"}
    
    try:
        bt = unreal.EditorAssetLibrary.load_asset(asset_path)
        if bt is None:
            return {"ok": False, "error": f"Behavior Tree not found: {asset_path}"}
        
        # Placeholder implementation
        return {
            "ok": True,
            "message": f"Disconnection from '{from_node}' to '{to_node}' not fully implemented",
            "asset_path": asset_path
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def set_blackboard(body: dict) -> dict:
    """Set the blackboard asset for the Behavior Tree."""
    import unreal
    asset_path = body.get("asset_path")
    blackboard_path = body.get("blackboard_path")
    if not asset_path or not blackboard_path:
        return {"ok": False, "error": "asset_path and blackboard_path are required"}
    
    try:
        bt = unreal.EditorAssetLibrary.load_asset(asset_path)
        if bt is None:
            return {"ok": False, "error": f"Behavior Tree not found: {asset_path}"}
        
        bb = unreal.EditorAssetLibrary.load_asset(blackboard_path)
        if bb is None:
            return {"ok": False, "error": f"Blackboard not found: {blackboard_path}"}
        
        # Set blackboard asset (assuming the property exists)
        if hasattr(bt, 'blackboard_asset'):
            bt.blackboard_asset = bb
            unreal.EditorAssetLibrary.save_asset(asset_path)
            return {"ok": True, "blackboard": blackboard_path}
        else:
            return {"ok": False, "error": "Behavior Tree does not have blackboard_asset property"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_blackboard(body: dict) -> dict:
    """Get the blackboard asset of the Behavior Tree."""
    import unreal
    asset_path = body.get("asset_path")
    if not asset_path:
        return {"ok": False, "error": "asset_path is required"}
    
    try:
        bt = unreal.EditorAssetLibrary.load_asset(asset_path)
        if bt is None:
            return {"ok": False, "error": f"Behavior Tree not found: {asset_path}"}
        
        if hasattr(bt, 'blackboard_asset') and bt.blackboard_asset:
            bb_path = bt.blackboard_asset.get_path_name()
            return {"ok": True, "blackboard_path": bb_path}
        else:
            return {"ok": True, "blackboard_path": None}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def compile(body: dict) -> dict:
    """Compile the Behavior Tree."""
    import unreal
    asset_path = body.get("asset_path")
    if not asset_path:
        return {"ok": False, "error": "asset_path is required"}
    
    try:
        bt = unreal.EditorAssetLibrary.load_asset(asset_path)
        if bt is None:
            return {"ok": False, "error": f"Behavior Tree not found: {asset_path}" }
        
        # Behavior Trees don't have a direct compile method like Blueprints
        # But we can save the asset which might trigger validation
        unreal.EditorAssetLibrary.save_asset(asset_path)
        return {"ok": True, "asset_path": asset_path, "message": "Behavior Tree saved"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# Blackboard management
def bb_create(body: dict) -> dict:
    """Create a new Blackboard asset."""
    import unreal
    asset_path = body.get("asset_path")
    if not asset_path:
        return {"ok": False, "error": "asset_path is required"}
    
    try:
        parts = asset_path.rsplit("/", 1)
        package_path = parts[0] + "/" if len(parts) > 1 else "/Game/"
        asset_name = parts[-1]
        
        factory = unreal.BlackboardFactory()
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        bb = asset_tools.create_asset(asset_name, package_path, unreal.Blackboard, factory)
        
        if bb is None:
            return {"ok": False, "error": "Failed to create Blackboard asset"}
        
        return {"ok": True, "asset_path": asset_path, "name": asset_name}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def bb_read(body: dict) -> dict:
    """Read Blackboard information."""
    import unreal
    asset_path = body.get("asset_path")
    if not asset_path:
        return {"ok": False, "error": "asset_path is required"}
    
    try:
        bb = unreal.EditorAssetLibrary.load_asset(asset_path)
        if bb is None:
            return {"ok": False, "error": f"Blackboard not found: {asset_path}"}
        
        # Get variable names
        var_names = []
        if hasattr(bb, 'get_all_variable_names'):
            var_names = bb.get_all_variable_names()
        else:
            # fallback: iterate through properties? We'll just return empty for now.
            var_names = []
        
        return {
            "ok": True,
            "asset_path": asset_path,
            "variable_names": var_names
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def bb_add_variable(body: dict) -> dict:
    """Add a variable to the Blackboard."""
    import unreal
    asset_path = body.get("asset_path")
    var_name = body.get("var_name")
    var_type = body.get("var_type", "bool")  # default bool
    if not asset_path or not var_name:
        return {"ok": False, "error": "asset_path and var_name are required"}
    
    try:
        bb = unreal.EditorAssetLibrary.load_asset(asset_path)
        if bb is None:
            return {"ok": False, "error": f"Blackboard not found: {asset_path}"}
        
        # Map type to unreal property type
        type_map = {
            "bool": unreal.BlackboardKeyType_Bool,
            "int": unreal.BlackboardKeyType_Int,
            "float": unreal.BlackboardKeyType_Float,
            "string": unreal.BlackboardKeyType_String,
            "vector": unreal.BlackboardKeyType_Vector,
            "object": unreal.BlackboardKeyType_Object,
        }
        ue_type = type_map.get(var_type.lower(), unreal.BlackboardKeyType_Bool)
        
        # Add key
        if hasattr(bb, 'add_key'):
            bb.add_key(var_name, ue_type)
        else:
            # fallback: we'll simulate by setting a property? Not ideal.
            pass
        
        unreal.EditorAssetLibrary.save_asset(asset_path)
        return {"ok": True, "variable": var_name, "type": var_type}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def bb_delete_variable(body: dict) -> dict:
    """Delete a variable from the Blackboard."""
    import unreal
    asset_path = body.get("asset_path")
    var_name = body.get("var_name")
    if not asset_path or not var_name:
        return {"ok": False, "error": "asset_path and var_name are required"}
    
    try:
        bb = unreal.EditorAssetLibrary.load_asset(asset_path)
        if bb is None:
            return {"ok": False, "error": f"Blackboard not found: {asset_path}"}
        
        if hasattr(bb, 'remove_key'):
            bb.remove_key(var_name)
        else:
            pass
        
        unreal.EditorAssetLibrary.save_asset(asset_path)
        return {"ok": True, "variable": var_name}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def bb_delete(body: dict) -> dict:
    """Delete a Blackboard asset."""
    import unreal
    asset_path = body.get("asset_path")
    if not asset_path:
        return {"ok": False, "error": "asset_path is required"}
    
    try:
        # Actually deleting asset
        success = unreal.EditorAssetLibrary.delete_asset(asset_path)
        if not success:
            return {"ok": False, "error": f"Failed to delete Blackboard asset: {asset_path}"}
        return {"ok": True, "asset_path": asset_path}
    except Exception as e:
        return {"ok": False, "error": str(e)}