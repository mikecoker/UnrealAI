import sys, types
sys.path.insert(0, "ue5_plugin/UnrealAI/Content/Python")


def test_create_material(mock_unreal):
    from handlers.materials import create
    result = create({"asset_path": "/Game/Materials/M_Rock"})
    assert result["ok"] is True
    assert result["asset_path"] == "/Game/Materials/M_Rock"


def test_create_material_missing_path(mock_unreal):
    from handlers.materials import create
    result = create({})
    assert result["ok"] is False
    assert "asset_path" in result["error"]


def test_add_expression(mock_unreal):
    fake_mat = types.SimpleNamespace(get_name=lambda: "M_Rock", get_path_name=lambda: "/Game/M_Rock")
    mock_unreal.EditorAssetLibrary.load_asset = lambda p: fake_mat

    from handlers.materials import add_expression
    result = add_expression({
        "asset_path": "/Game/M_Rock",
        "type": "Multiply",
        "x": 100,
        "y": 200,
    })
    assert result["ok"] is True
    assert result["type"] == "Multiply"


def test_connect_material_pins(mock_unreal):
    fake_mat = types.SimpleNamespace(get_name=lambda: "M_Rock", get_path_name=lambda: "/Game/M_Rock")
    mock_unreal.EditorAssetLibrary.load_asset = lambda p: fake_mat

    connected = []
    mock_unreal.MaterialEditingLibrary.connect_material_expressions = (
        lambda a, b, c, d: connected.append((b, d)) or True
    )

    from handlers.materials import connect_pins
    result = connect_pins({
        "asset_path": "/Game/M_Rock",
        "from_node": "node_a",
        "from_pin": "RGB",
        "to_node": "node_b",
        "to_pin": "A",
    })
    assert result["ok"] is True
