"""User Widget handler: create, read, list, add/modify widgets inside User Widget Blueprints."""

_node_registry: dict = {}


def _load_uw(asset_path: str):
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

        parent_name = body.get("parent_class", "UserWidget")
        parent_class = unreal.load_class(None, f"/Script/UMG.{parent_name}")

        factory = unreal.WidgetBlueprintFactory()
        factory.parent_class = parent_class

        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        uw = asset_tools.create_asset(asset_name, package_path, unreal.WidgetBlueprint, factory)
        _node_registry[asset_path] = {}
        return {"ok": True, "asset_path": asset_path, "name": asset_name}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def read(body: dict) -> dict:
    import unreal
    asset_path = body.get("asset_path")
    if not asset_path:
        return {"ok": False, "error": "asset_path is required"}
    try:
        uw = _load_uw(asset_path)
        widget_tree = getattr(uw, "WidgetTree", None) or getattr(uw, "widget_tree", None)
        if widget_tree is None:
            return {"ok": True, "asset_path": asset_path, "root": None, "widgets": [], "variables": []}

        root = widget_tree.root_widget if hasattr(widget_tree, "root_widget") else None
        children = []
        if hasattr(widget_tree, "get_all_widgets"):
            for child in widget_tree.get_all_widgets():
                children.append({
                    "name": str(child.get_name()),
                    "class": str(child.get_class().get_name()),
                })
        variables = [{"name": str(v.variable_name), "type": str(v.var_type)}
                     for v in uw.new_variables]
        return {"ok": True, "asset_path": asset_path,
                "root": str(root.get_name()) if root else None,
                "widgets": children, "variables": variables}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def list_assets(body: dict) -> dict:
    import unreal
    path = body.get("path", "/Game/")
    try:
        ar = unreal.AssetRegistryHelpers.get_asset_registry()
        try:
            f = unreal.ARFilter(
                class_paths=["/Script/UMGEditor.WidgetBlueprint"],
                package_paths=[path],
                recursive_paths=True,
            )
        except TypeError:
            f = unreal.ARFilter(
                class_names=["WidgetBlueprint"],
                package_paths=[path],
                recursive_paths=True,
            )
        asset_data_list = ar.get_assets(f)
        assets = sorted({str(a.package_name) for a in asset_data_list})
        return {"ok": True, "assets": assets}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def add_widget(body: dict) -> dict:
    import unreal
    asset_path = body.get("asset_path")
    widget_class = body.get("widget_class", "TextBlock")
    name = body.get("name", widget_class)
    if not asset_path:
        return {"ok": False, "error": "asset_path is required"}
    try:
        uw = _load_uw(asset_path)
        widget_tree = uw.widget_tree
        if widget_tree is None:
            return {"ok": False, "error": "WidgetTree not found on blueprint"}

        cls = unreal.load_class(None, f"/Script/UMG.{widget_class}")
        widget = widget_tree.add_widget(cls, name)

        registry = _node_registry.setdefault(asset_path, {})
        registry[name] = widget

        unreal.EditorAssetLibrary.save_asset(asset_path)
        return {"ok": True, "widget": name, "class": widget_class}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def delete_widget(body: dict) -> dict:
    import unreal
    asset_path = body.get("asset_path")
    name = body.get("name")
    if not asset_path or not name:
        return {"ok": False, "error": "asset_path and name are required"}
    try:
        uw = _load_uw(asset_path)
        widget_tree = uw.widget_tree
        if widget_tree is None:
            return {"ok": False, "error": "WidgetTree not found"}

        widget = widget_tree.find_widget(name)
        if widget is None:
            return {"ok": False, "error": f"Widget '{name}' not found"}

        widget_tree.remove_widget(widget)
        registry = _node_registry.get(asset_path, {})
        registry.pop(name, None)

        unreal.EditorAssetLibrary.save_asset(asset_path)
        return {"ok": True, "widget": name}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def add_slot(body: dict) -> dict:
    import unreal
    asset_path = body.get("asset_path")
    slot_name = body.get("slot_name", "Slot")
    if not asset_path:
        return {"ok": False, "error": "asset_path is required"}
    try:
        uw = _load_uw(asset_path)
        widget_tree = getattr(uw, "WidgetTree", None) or getattr(uw, "widget_tree", None)
        if widget_tree is None:
            return {"ok": False, "error": "WidgetTree not found"}

        canvas = widget_tree.find_widget("CanvasPanel")
        if canvas is None:
            canvas = widget_tree.add_widget(unreal.CanvasPanel, "CanvasPanel")

        slot = unreal.CanvasPanelSlot()
        slot.set_editor_property("slot_name", slot_name)
        unreal.PanelWidget.add_child(canvas, slot)

        registry = _node_registry.setdefault(asset_path, {})
        registry[slot_name] = slot

        unreal.EditorAssetLibrary.save_asset(asset_path)
        return {"ok": True, "slot": slot_name}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def delete_slot(body: dict) -> dict:
    import unreal
    asset_path = body.get("asset_path")
    slot_name = body.get("slot_name")
    if not asset_path or not slot_name:
        return {"ok": False, "error": "asset_path and slot_name are required"}
    try:
        uw = _load_uw(asset_path)
        widget_tree = getattr(uw, "WidgetTree", None) or getattr(uw, "widget_tree", None)
        if widget_tree is None:
            return {"ok": False, "error": "WidgetTree not found"}

        canvas = widget_tree.find_widget("CanvasPanel")
        if canvas is None:
            return {"ok": False, "error": "CanvasPanel not found"}

        for child in canvas.get_slots():
            if str(child.slot_name) == slot_name:
                unreal.PanelWidget.remove_child(canvas, child.content)
                registry = _node_registry.get(asset_path, {})
                registry.pop(slot_name, None)
                unreal.EditorAssetLibrary.save_asset(asset_path)
                return {"ok": True, "slot": slot_name}

        return {"ok": False, "error": f"Slot '{slot_name}' not found"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def add_property(body: dict) -> dict:
    import unreal
    asset_path = body.get("asset_path")
    name = body.get("name")
    var_type = body.get("type", "float")
    default_value = body.get("default_value")
    if not asset_path or not name:
        return {"ok": False, "error": "asset_path and name are required"}
    try:
        uw = _load_uw(asset_path)

        type_map = {
            "bool": unreal.EdGraphPinTypeCategory.BOOLEAN,
            "int": unreal.EdGraphPinTypeCategory.INTEGER,
            "float": unreal.EdGraphPinTypeCategory.REAL,
            "string": unreal.EdGraphPinTypeCategory.STRING,
        }
        pin_category = type_map.get(var_type, unreal.EdGraphPinTypeCategory.OBJECT)

        new_var = unreal.WidgetBlueprintEditorLibrary.add_variable(
            uw, name, pin_category
        )
        if default_value is not None:
            new_var.set_editor_property("default_value", default_value)

        unreal.EditorAssetLibrary.save_asset(asset_path)
        return {"ok": True, "property": name, "type": var_type}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def delete_property(body: dict) -> dict:
    import unreal
    asset_path = body.get("asset_path")
    name = body.get("name")
    if not asset_path or not name:
        return {"ok": False, "error": "asset_path and name are required"}
    try:
        uw = _load_uw(asset_path)
        removed = unreal.WidgetBlueprintEditorLibrary.remove_variable(uw, name)
        if not removed:
            return {"ok": False, "error": f"Property '{name}' not found"}
        unreal.EditorAssetLibrary.save_asset(asset_path)
        return {"ok": True, "property": name}
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
        uw = _load_uw(asset_path)
        for var in uw.new_variables:
            if str(var.variable_name) == property_name:
                var.set_editor_property("default_value", value)
                unreal.EditorAssetLibrary.save_asset(asset_path)
                return {"ok": True, "property": property_name, "value": value}
        return {"ok": False, "error": f"Property '{property_name}' not found"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def set_slot_property(body: dict) -> dict:
    import unreal
    asset_path = body.get("asset_path")
    slot_name = body.get("slot")
    property_name = body.get("property")
    value = body.get("value")
    if not asset_path or not slot_name or property_name is None:
        return {"ok": False, "error": "asset_path, slot, and property are required"}
    try:
        uw = _load_uw(asset_path)
        widget_tree = getattr(uw, "WidgetTree", None) or getattr(uw, "widget_tree", None)
        if widget_tree is None:
            return {"ok": False, "error": "WidgetTree not found"}

        canvas = widget_tree.find_widget("CanvasPanel")
        if canvas is None:
            return {"ok": False, "error": "CanvasPanel not found"}

        for child in canvas.get_slots():
            if str(child.slot_name) == slot_name:
                child.set_editor_property(property_name, value)
                unreal.EditorAssetLibrary.save_asset(asset_path)
                return {"ok": True, "slot": slot_name, "property": property_name, "value": value}

        return {"ok": False, "error": f"Slot '{slot_name}' not found"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def compile(body: dict) -> dict:
    import unreal
    asset_path = body.get("asset_path")
    if not asset_path:
        return {"ok": False, "error": "asset_path is required"}
    try:
        uw = _load_uw(asset_path)
        result = unreal.BlueprintEditorLibrary.compile_blueprint(uw)
        errors = []
        if result:
            for err in result:
                if hasattr(err, 'get_message'):
                    errors.append(str(err.get_message()))
                else:
                    errors.append(str(err))
        unreal.EditorAssetLibrary.save_asset(asset_path)
        return {"ok": True, "asset_path": asset_path, "errors": errors, "clean": len(errors) == 0}
    except Exception as e:
        return {"ok": False, "error": str(e)}
