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

# Material output property names (connect to material output)
_OUTPUT_PROPS = {
    "BaseColor", "Metallic", "Roughness", "Normal",
    "Emissive", "Opacity",
}

# Runtime node registry: asset_path → {node_name: expression_object}
_node_registry: dict = {}


def _load_mat(asset_path: str):
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
    try:
        parts = asset_path.rsplit("/", 1)
        package_path = parts[0] + "/" if len(parts) > 1 else "/Game/"
        asset_name = parts[-1]

        factory = getattr(unreal, "MaterialFactoryNew", lambda: None)()
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
    import unreal
    path = body.get("path", "/Game/")
    try:
        raw = unreal.EditorAssetLibrary.list_assets(path, recursive=True, include_folder=False)
        assets = [p.rsplit(".", 1)[0] for p in raw]
        return {"ok": True, "assets": assets}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def add_expression(body: dict) -> dict:
    import unreal
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
    import unreal
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

        from_expr = registry.get(from_node, from_node)
        to_expr = registry.get(to_node, to_node)

        if to_node in _OUTPUT_PROPS:
            unreal.MaterialEditingLibrary.connect_material_property(from_expr, from_pin, to_node)
        else:
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
    import unreal
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
            actors = unreal.EditorLevelLibrary.get_all_level_actors()
            actor = next((a for a in actors if a.get_name() == target), None)
            if actor is None:
                return {"ok": False, "error": f"Target not found: {target}"}
            for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
                comp.set_material(slot, mat)

        return {"ok": True, "material": asset_path, "applied_to": target}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def delete(body: dict) -> dict:
    import unreal
    asset_path = body.get("asset_path")
    if not asset_path:
        return {"ok": False, "error": "asset_path is required"}
    try:
        if not unreal.EditorAssetLibrary.does_asset_exist(asset_path):
            return {"ok": False, "error": f"Material not found: {asset_path}"}
        
        unreal.EditorAssetLibrary.delete_asset(asset_path)
        
        if asset_path in _node_registry:
            del _node_registry[asset_path]
        
        return {"ok": True, "deleted": asset_path}
    except Exception as e:
        return {"ok": False, "error": str(e)}
