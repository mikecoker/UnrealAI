import sys, types
sys.path.insert(0, "ue5_plugin/UnrealAI/Content/Python")


def test_create_user_widget(mock_unreal):
    from handlers.user_widgets import create
    result = create({"asset_path": "/Game/UI/BP_MainMenu", "parent_class": "UserWidget"})
    assert result["ok"] is True
    assert result["asset_path"] == "/Game/UI/BP_MainMenu"


def test_create_user_widget_missing_path(mock_unreal):
    from handlers.user_widgets import create
    result = create({"parent_class": "UserWidget"})
    assert result["ok"] is False
    assert "asset_path" in result["error"]


def test_read_user_widget(mock_unreal):
    fake_uw = types.SimpleNamespace(
        get_name=lambda: "BP_MainMenu",
        get_path_name=lambda: "/Game/UI/BP_MainMenu",
        widget_tree=types.SimpleNamespace(
            root_widget=types.SimpleNamespace(get_name=lambda: "CanvasPanel_0"),
            get_all_widgets=lambda: [
                types.SimpleNamespace(get_name=lambda: "Button_0", get_class=lambda: types.SimpleNamespace(get_name=lambda: "Button")),
                types.SimpleNamespace(get_name=lambda: "TextBlock_0", get_class=lambda: types.SimpleNamespace(get_name=lambda: "TextBlock")),
            ],
        ),
        new_variables=[
            types.SimpleNamespace(variable_name="Score", var_type="int"),
        ],
    )
    mock_unreal.EditorAssetLibrary.load_asset = lambda path: fake_uw

    from handlers.user_widgets import read
    result = read({"asset_path": "/Game/UI/BP_MainMenu"})
    assert result["ok"] is True
    assert result["root"] == "CanvasPanel_0"
    assert len(result["widgets"]) == 2
    assert len(result["variables"]) == 1


def test_list_user_widgets(mock_unreal):
    asset1 = types.SimpleNamespace(package_name="/Game/UI/BP_MainMenu")
    asset2 = types.SimpleNamespace(package_name="/Game/UI/BP_Settings")
    mock_ar = types.SimpleNamespace(get_assets=lambda f: [asset1, asset2])
    mock_unreal.AssetRegistryHelpers.get_asset_registry = lambda: mock_ar
    mock_unreal.ARFilter = lambda **kwargs: types.SimpleNamespace()

    from handlers.user_widgets import list_assets
    result = list_assets({"path": "/Game/UI/"})
    assert result["ok"] is True
    assert len(result["assets"]) == 2


def test_add_widget(mock_unreal):
    fake_uw = types.SimpleNamespace(
        get_name=lambda: "BP_MainMenu",
        widget_tree=types.SimpleNamespace(
            add_widget=lambda cls, name: types.SimpleNamespace(get_name=lambda: name),
        ),
    )
    mock_unreal.EditorAssetLibrary.load_asset = lambda path: fake_uw
    mock_unreal.EditorAssetLibrary.save_asset = lambda path: None

    from handlers.user_widgets import add_widget
    result = add_widget({
        "asset_path": "/Game/UI/BP_MainMenu",
        "widget_class": "Button",
        "name": "StartButton",
    })
    assert result["ok"] is True
    assert result["widget"] == "StartButton"
    assert result["class"] == "Button"


def test_delete_widget(mock_unreal):
    fake_uw = types.SimpleNamespace(
        get_name=lambda: "BP_MainMenu",
        widget_tree=types.SimpleNamespace(
            find_widget=lambda name: types.SimpleNamespace() if name == "StartButton" else None,
            remove_widget=lambda widget: None,
        ),
    )
    mock_unreal.EditorAssetLibrary.load_asset = lambda path: fake_uw
    mock_unreal.EditorAssetLibrary.save_asset = lambda path: None

    from handlers.user_widgets import delete_widget
    result = delete_widget({
        "asset_path": "/Game/UI/BP_MainMenu",
        "name": "StartButton",
    })
    assert result["ok"] is True
    assert result["widget"] == "StartButton"


def test_add_slot(mock_unreal):
    fake_uw = types.SimpleNamespace(
        get_name=lambda: "BP_MainMenu",
        widget_tree=types.SimpleNamespace(
            find_widget=lambda name: types.SimpleNamespace(
                get_slots=lambda: [],
            ) if name == "CanvasPanel" else None,
            add_widget=lambda cls, name: types.SimpleNamespace(
                get_slots=lambda: [],
            ),
        ),
    )
    mock_unreal.EditorAssetLibrary.load_asset = lambda path: fake_uw
    mock_unreal.EditorAssetLibrary.save_asset = lambda path: None
    mock_unreal.CanvasPanel = object
    mock_unreal.CanvasPanelSlot = lambda: types.SimpleNamespace(set_editor_property=lambda p, v: None)
    mock_unreal.PanelWidget = types.SimpleNamespace(add_child=lambda panel, slot: None)

    from handlers.user_widgets import add_slot
    result = add_slot({
        "asset_path": "/Game/UI/BP_MainMenu",
        "slot_name": "ContentSlot",
    })
    assert result["ok"] is True
    assert result["slot"] == "ContentSlot"


def test_set_property(mock_unreal):
    fake_uw = types.SimpleNamespace(
        get_name=lambda: "BP_MainMenu",
        new_variables=[
            types.SimpleNamespace(
                variable_name="Score",
                set_editor_property=lambda p, v: None,
            ),
        ],
    )
    mock_unreal.EditorAssetLibrary.load_asset = lambda path: fake_uw
    mock_unreal.EditorAssetLibrary.save_asset = lambda path: None

    from handlers.user_widgets import set_property
    result = set_property({
        "asset_path": "/Game/UI/BP_MainMenu",
        "property": "Score",
        "value": 42,
    })
    assert result["ok"] is True
    assert result["property"] == "Score"
    assert result["value"] == 42


def test_set_property_not_found(mock_unreal):
    fake_uw = types.SimpleNamespace(
        get_name=lambda: "BP_MainMenu",
        new_variables=[],
    )
    mock_unreal.EditorAssetLibrary.load_asset = lambda path: fake_uw

    from handlers.user_widgets import set_property
    result = set_property({
        "asset_path": "/Game/UI/BP_MainMenu",
        "property": "MissingVar",
        "value": 42,
    })
    assert result["ok"] is False
    assert "not found" in result["error"]


def test_compile_user_widget(mock_unreal):
    fake_uw = types.SimpleNamespace(
        get_name=lambda: "BP_MainMenu",
    )
    mock_unreal.EditorAssetLibrary.load_asset = lambda path: fake_uw
    mock_unreal.EditorAssetLibrary.save_asset = lambda path: None
    mock_unreal.BlueprintEditorLibrary.compile_blueprint = lambda bp: []

    from handlers.user_widgets import compile
    result = compile({"asset_path": "/Game/UI/BP_MainMenu"})
    assert result["ok"] is True
    assert result["clean"] is True
    assert result["errors"] == []


def test_compile_user_widget_with_errors(mock_unreal):
    fake_uw = types.SimpleNamespace(
        get_name=lambda: "BP_MainMenu",
    )
    mock_unreal.EditorAssetLibrary.load_asset = lambda path: fake_uw
    mock_unreal.EditorAssetLibrary.save_asset = lambda path: None
    mock_unreal.BlueprintEditorLibrary.compile_blueprint = lambda bp: [
        types.SimpleNamespace(get_message=lambda: "Widget not bound")
    ]

    from handlers.user_widgets import compile
    result = compile({"asset_path": "/Game/UI/BP_MainMenu"})
    assert result["ok"] is True
    assert result["clean"] is False
    assert "Widget not bound" in result["errors"]
