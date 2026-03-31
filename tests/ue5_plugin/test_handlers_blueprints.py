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


def test_delete_node(mock_unreal):
    fake_bp = types.SimpleNamespace(get_name=lambda: "BP_Hero", get_path_name=lambda: "/Game/BP_Hero")
    mock_unreal.EditorAssetLibrary.load_asset = lambda path: fake_bp
    mock_unreal.EditorAssetLibrary.save_asset = lambda path: None
    mock_unreal.BlueprintEditorLibrary.find_event_graph = lambda bp: types.SimpleNamespace()
    mock_unreal.BlueprintEditorLibrary.delete_node = lambda graph, node_id: True

    from handlers.blueprints import delete_node
    result = delete_node({
        "asset_path": "/Game/BP_Hero",
        "graph": "EventGraph",
        "node_id": "Node_1"
    })
    assert result["ok"] is True
    assert result["node_id"] == "Node_1"
    assert result["graph"] == "EventGraph"


def test_disconnect_pins(mock_unreal):
    fake_bp = types.SimpleNamespace(get_name=lambda: "BP_Hero", get_path_name=lambda: "/Game/BP_Hero")
    mock_unreal.EditorAssetLibrary.load_asset = lambda path: fake_bp
    mock_unreal.EditorAssetLibrary.save_asset = lambda path: None
    mock_unreal.BlueprintEditorLibrary.find_event_graph = lambda bp: types.SimpleNamespace()
    mock_unreal.UnrealAIGraphLibrary = types.SimpleNamespace()
    mock_unreal.UnrealAIGraphLibrary.disconnect_graph_pins = lambda graph, from_node, from_pin, to_node, to_pin: True

    from handlers.blueprints import disconnect_pins
    result = disconnect_pins({
        "asset_path": "/Game/BP_Hero",
        "graph": "EventGraph",
        "from_node": "Node_A",
        "from_pin": "Output",
        "to_node": "Node_B",
        "to_pin": "Input"
    })
    assert result["ok"] is True
    assert result["disconnected"] == "Node_A.Output -> Node_B.Input"
