def bp_api(body: dict) -> dict:
    import unreal
    prefix = body.get("prefix", "")
    methods = [m for m in dir(unreal.BlueprintEditorLibrary) if prefix.lower() in m.lower()]
    return {"ok": True, "methods": sorted(methods)}


def ue_classes(body: dict) -> dict:
    import unreal
    prefix = body.get("prefix", "")
    names = [n for n in dir(unreal) if prefix.lower() in n.lower()]
    return {"ok": True, "names": sorted(names)}


def browse_class(body: dict) -> dict:
    import unreal
    cls_name = body.get("class", "MathLibrary")
    prefix = body.get("prefix", "")
    cls = getattr(unreal, cls_name, None)
    if cls is None:
        return {"ok": False, "error": f"Class not found: {cls_name}"}
    methods = sorted(m for m in dir(cls) if not m.startswith("_") and prefix.lower() in m.lower())
    return {"ok": True, "class": cls_name, "methods": methods}


def bp_variables(body: dict) -> dict:
    import unreal
    bp_path = body.get("asset_path", "/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter")
    bp = unreal.EditorAssetLibrary.load_asset(bp_path)
    try:
        # Try C++ helper first
        names = list(unreal.UnrealAIGraphLibrary.get_variable_names(bp))
        return {"ok": True, "source": "cpp", "variables": names}
    except AttributeError:
        pass
    # Fall back: try reading new_variables directly from Python
    try:
        vars_raw = bp.get_editor_property("new_variables")
        names = [v.get_editor_property("var_name") for v in (vars_raw or [])]
        return {"ok": True, "source": "python", "variables": names}
    except Exception as e2:
        return {"ok": False, "error": str(e2)}


def cdo_props(body: dict) -> dict:
    import unreal
    bp_path = body.get("asset_path", "/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter")
    bp = unreal.EditorAssetLibrary.load_asset(bp_path)
    gen_cls = unreal.BlueprintEditorLibrary.generated_class(bp)
    try:
        cdo = gen_cls.get_default_object()
        props = [p for p in dir(cdo) if not p.startswith("_")][:30]
        return {"ok": True, "cdo_type": type(cdo).__name__, "props": props}
    except Exception as e:
        return {"ok": False, "gen_cls_type": type(gen_cls).__name__, "error": str(e)}


def graph_nodes(body: dict) -> dict:
    import unreal
    bp_path = body.get("asset_path", "/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter")
    bp = unreal.EditorAssetLibrary.load_asset(bp_path)
    graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    if graph is None:
        return {"ok": False, "error": "no event graph"}
    try:
        nodes = graph.get_editor_property("nodes")
        node_info = []
        for n in (nodes or []):
            node_info.append({
                "name": n.get_name(),
                "class": n.get_class().get_name(),
                "methods": [m for m in dir(n) if not m.startswith("_")][:20]
            })
        return {"ok": True, "node_count": len(node_info), "nodes": node_info[:5]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def obj_api(body: dict) -> dict:
    import unreal
    cls_name = body.get("class", "SubobjectDataSubsystem")
    prefix = body.get("prefix", "")
    cls = getattr(unreal, cls_name, None)
    if cls is None:
        return {"ok": False, "error": f"Class not found: {cls_name}"}
    methods = [m for m in dir(cls) if prefix.lower() in m.lower() and not m.startswith("__")]
    return {"ok": True, "class": cls_name, "methods": sorted(methods)}


def pintype(body: dict) -> dict:
    import unreal
    bp_path = body.get("asset_path", "/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter")
    bp = unreal.EditorAssetLibrary.load_asset(bp_path)
    results = {}

    # Try 1: import_text
    try:
        pt = unreal.EdGraphPinType()
        pt.import_text("(PinCategory=real)")
        unreal.BlueprintEditorLibrary.add_member_variable(bp, "_test1", pt)
        results["import_text"] = "ok"
    except Exception as e:
        results["import_text"] = str(e)

    # Try 2: set_editor_properties
    try:
        pt = unreal.EdGraphPinType()
        pt.set_editor_properties({"PinCategory": "real"})
        unreal.BlueprintEditorLibrary.add_member_variable(bp, "_test2", pt)
        results["set_editor_properties"] = "ok"
    except Exception as e:
        results["set_editor_properties"] = str(e)

    # Try 3: no pin type setup at all (pass empty EdGraphPinType)
    try:
        pt = unreal.EdGraphPinType()
        unreal.BlueprintEditorLibrary.add_member_variable(bp, "_test3", pt)
        results["empty_pin_type"] = "ok"
    except Exception as e:
        results["empty_pin_type"] = str(e)

    return {"ok": True, "results": results}
