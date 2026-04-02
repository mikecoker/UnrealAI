"""Tests for the behavior_trees handler."""
import importlib
from unittest import mock


def _bt_mock():
    """Return a MagicMock that passes _load_bt type check."""
    m = mock.MagicMock()
    m.get_class.return_value.get_name.return_value = "BehaviorTree"
    return m


def _bb_mock():
    """Return a MagicMock that passes _load_bb type check."""
    m = mock.MagicMock()
    m.get_class.return_value.get_name.return_value = "BlackboardData"
    return m


def test_create():
    mu = mock.MagicMock()
    mu.AssetToolsHelpers.get_asset_tools.return_value.create_asset.return_value = mock.MagicMock()
    mu.BehaviorTreeFactory.return_value = mock.MagicMock()
    mu.BehaviorTree = mock.MagicMock()
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.create({"asset_path": "/Game/TestBT"})
    assert result["ok"] is True
    assert result["asset_path"] == "/Game/TestBT"
    assert result["name"] == "TestBT"


def test_create_missing_asset_path():
    with mock.patch.dict('sys.modules', {'unreal': mock.MagicMock()}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.create({})
    assert result["ok"] is False
    assert "asset_path is required" in result["error"]


def test_read():
    mu = mock.MagicMock()
    mock_bt = _bt_mock()
    mock_root = mock.MagicMock()
    mock_root.get_name.return_value = "RootNode"
    mock_bt.get_root_node.return_value = mock_root
    mock_bb = mock.MagicMock()
    mock_bb.get_path_name.return_value = "/Game/Blackboard.BB_Test"
    mock_bt.blackboard_asset = mock_bb
    mu.EditorAssetLibrary.load_asset.return_value = mock_bt
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.read({"asset_path": "/Game/TestBT"})
    assert result["ok"] is True
    assert result["root_node"] == "RootNode"
    assert result["blackboard"] == "/Game/Blackboard.BB_Test"


def test_read_asset_not_found():
    mu = mock.MagicMock()
    mu.EditorAssetLibrary.load_asset.return_value = None
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.read({"asset_path": "/Game/TestBT"})
    assert result["ok"] is False
    assert "Asset not found" in result["error"]


def test_read_wrong_asset_type():
    mu = mock.MagicMock()
    wrong_asset = mock.MagicMock()
    wrong_asset.get_class.return_value.get_name.return_value = "StateTree"
    mu.EditorAssetLibrary.load_asset.return_value = wrong_asset
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.read({"asset_path": "/Game/ST_CombatEnemy"})
    assert result["ok"] is False
    assert "Expected BehaviorTree" in result["error"]
    assert "StateTree" in result["error"]


def test_add_node_composite():
    mu = mock.MagicMock()
    mock_bt = _bt_mock()
    mock_node = mock.MagicMock()
    mock_node.get_name.return_value = "BehaviorTreeGraphNode_Composite_0"
    mu.EditorAssetLibrary.load_asset.return_value = mock_bt
    mu.UnrealAIGraphLibrary.add_bt_composite_node.return_value = mock_node
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.add_node({"asset_path": "/Game/TestBT", "node_type": "Sequence", "x": 100, "y": 200})
    assert result["ok"] is True
    assert result["node_id"] == "BehaviorTreeGraphNode_Composite_0"
    assert result["node_type"] == "Sequence"
    mu.UnrealAIGraphLibrary.add_bt_composite_node.assert_called_once_with(mock_bt, "Sequence", 100, 200)


def test_add_node_task():
    mu = mock.MagicMock()
    mock_bt = _bt_mock()
    mock_node = mock.MagicMock()
    mock_node.get_name.return_value = "BehaviorTreeGraphNode_Task_0"
    mu.EditorAssetLibrary.load_asset.return_value = mock_bt
    mu.UnrealAIGraphLibrary.add_bt_task_node.return_value = mock_node
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.add_node({"asset_path": "/Game/TestBT", "node_type": "Wait"})
    assert result["ok"] is True
    assert result["node_id"] == "BehaviorTreeGraphNode_Task_0"
    mu.UnrealAIGraphLibrary.add_bt_task_node.assert_called_once_with(mock_bt, "Wait", 0, 0)


def test_add_node_not_found():
    mu = mock.MagicMock()
    mock_bt = _bt_mock()
    mu.EditorAssetLibrary.load_asset.return_value = mock_bt
    mu.UnrealAIGraphLibrary.add_bt_composite_node.return_value = None
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.add_node({"asset_path": "/Game/TestBT", "node_type": "Sequence"})
    assert result["ok"] is False
    assert "Failed to add node" in result["error"]


def test_delete_node():
    mu = mock.MagicMock()
    mock_bt = _bt_mock()
    mu.EditorAssetLibrary.load_asset.return_value = mock_bt
    mu.UnrealAIGraphLibrary.delete_bt_node.return_value = True
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.delete_node({"asset_path": "/Game/TestBT", "node_name": "BehaviorTreeGraphNode_Composite_0"})
    assert result["ok"] is True
    assert result["node_name"] == "BehaviorTreeGraphNode_Composite_0"
    mu.UnrealAIGraphLibrary.delete_bt_node.assert_called_once_with(mock_bt, "BehaviorTreeGraphNode_Composite_0")


def test_delete_node_not_found():
    mu = mock.MagicMock()
    mock_bt = _bt_mock()
    mu.EditorAssetLibrary.load_asset.return_value = mock_bt
    mu.UnrealAIGraphLibrary.delete_bt_node.return_value = False
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.delete_node({"asset_path": "/Game/TestBT", "node_name": "Ghost"})
    assert result["ok"] is False
    assert "not found" in result["error"]


def test_connect_nodes():
    mu = mock.MagicMock()
    mock_bt = _bt_mock()
    mu.EditorAssetLibrary.load_asset.return_value = mock_bt
    mu.UnrealAIGraphLibrary.connect_bt_nodes.return_value = True
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.connect_nodes({
            "asset_path": "/Game/TestBT",
            "from_node": "BehaviorTreeGraphNode_Root_0",
            "to_node": "BehaviorTreeGraphNode_Composite_0",
        })
    assert result["ok"] is True
    assert result["connected"] == "BehaviorTreeGraphNode_Root_0 -> BehaviorTreeGraphNode_Composite_0"
    mu.UnrealAIGraphLibrary.connect_bt_nodes.assert_called_once_with(
        mock_bt, "BehaviorTreeGraphNode_Root_0", "BehaviorTreeGraphNode_Composite_0"
    )


def test_connect_nodes_failed():
    mu = mock.MagicMock()
    mock_bt = _bt_mock()
    mu.EditorAssetLibrary.load_asset.return_value = mock_bt
    mu.UnrealAIGraphLibrary.connect_bt_nodes.return_value = False
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.connect_nodes({"asset_path": "/Game/TestBT", "from_node": "NodeA", "to_node": "NodeB"})
    assert result["ok"] is False
    assert "Could not connect" in result["error"]


def test_disconnect_nodes():
    mu = mock.MagicMock()
    mock_bt = _bt_mock()
    mu.EditorAssetLibrary.load_asset.return_value = mock_bt
    mu.UnrealAIGraphLibrary.disconnect_bt_nodes.return_value = True
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.disconnect_nodes({"asset_path": "/Game/TestBT", "from_node": "NodeA", "to_node": "NodeB"})
    assert result["ok"] is True
    assert result["disconnected"] == "NodeA -> NodeB"


def test_disconnect_nodes_no_connection():
    mu = mock.MagicMock()
    mock_bt = _bt_mock()
    mu.EditorAssetLibrary.load_asset.return_value = mock_bt
    mu.UnrealAIGraphLibrary.disconnect_bt_nodes.return_value = False
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.disconnect_nodes({"asset_path": "/Game/TestBT", "from_node": "NodeA", "to_node": "NodeB"})
    assert result["ok"] is False
    assert "No connection" in result["error"]


def test_get_nodes():
    mu = mock.MagicMock()
    mock_bt = _bt_mock()
    mock_node_info = mock.MagicMock()
    mock_node_info.node_name = "BehaviorTreeGraphNode_Root_0"
    mock_node_info.node_class = "BehaviorTreeGraphNode_Root"
    mock_node_info.input_pins = []
    mock_node_info.output_pins = ["Out"]
    mu.EditorAssetLibrary.load_asset.return_value = mock_bt
    mu.UnrealAIGraphLibrary.get_bt_nodes.return_value = [mock_node_info]
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.get_nodes({"asset_path": "/Game/TestBT"})
    assert result["ok"] is True
    assert len(result["nodes"]) == 1
    assert result["nodes"][0]["name"] == "BehaviorTreeGraphNode_Root_0"
    assert result["nodes"][0]["class"] == "BehaviorTreeGraphNode_Root"


def test_get_nodes_asset_not_found():
    mu = mock.MagicMock()
    mu.EditorAssetLibrary.load_asset.return_value = None
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.get_nodes({"asset_path": "/Game/TestBT"})
    assert result["ok"] is False
    assert "Asset not found" in result["error"]


def test_set_blackboard():
    mu = mock.MagicMock()
    mock_bt = _bt_mock()
    mock_bb = _bb_mock()
    mu.EditorAssetLibrary.load_asset.side_effect = [mock_bt, mock_bb]
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.set_blackboard({"asset_path": "/Game/TestBT", "blackboard_path": "/Game/TestBB"})
    assert result["ok"] is True
    assert result["blackboard"] == "/Game/TestBB"


def test_set_blackboard_missing_params():
    with mock.patch.dict('sys.modules', {'unreal': mock.MagicMock()}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.set_blackboard({})
    assert result["ok"] is False
    assert "asset_path and blackboard_path are required" in result["error"]


def test_get_blackboard():
    mu = mock.MagicMock()
    mock_bt = _bt_mock()
    mock_bb_asset = mock.MagicMock()
    mock_bb_asset.get_path_name.return_value = "/Game/TestBB"
    mock_bt.blackboard_asset = mock_bb_asset
    mu.EditorAssetLibrary.load_asset.return_value = mock_bt
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.get_blackboard({"asset_path": "/Game/TestBT"})
    assert result["ok"] is True
    assert result["blackboard_path"] == "/Game/TestBB"


def test_get_blackboard_none():
    mu = mock.MagicMock()
    mock_bt = _bt_mock()
    mock_bt.blackboard_asset = None
    mu.EditorAssetLibrary.load_asset.return_value = mock_bt
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.get_blackboard({"asset_path": "/Game/TestBT"})
    assert result["ok"] is True
    assert result["blackboard_path"] is None


def test_compile():
    mu = mock.MagicMock()
    mock_bt = _bt_mock()
    mu.EditorAssetLibrary.load_asset.return_value = mock_bt
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.compile({"asset_path": "/Game/TestBT"})
    assert result["ok"] is True
    assert result["asset_path"] == "/Game/TestBT"


# Blackboard tests

def test_bb_create():
    mu = mock.MagicMock()
    mu.AssetToolsHelpers.get_asset_tools.return_value.create_asset.return_value = mock.MagicMock()
    mu.BlackboardFactory.return_value = mock.MagicMock()
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.bb_create({"asset_path": "/Game/TestBB"})
    assert result["ok"] is True
    assert result["asset_path"] == "/Game/TestBB"
    assert result["name"] == "TestBB"


def test_bb_create_missing_asset_path():
    with mock.patch.dict('sys.modules', {'unreal': mock.MagicMock()}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.bb_create({})
    assert result["ok"] is False
    assert "asset_path is required" in result["error"]


def test_bb_read():
    mu = mock.MagicMock()
    mock_bb = _bb_mock()
    # keys array: two entries whose entry_name property returns a name string
    entry_health = mock.MagicMock()
    entry_health.get_editor_property.return_value = "Health"
    entry_ammo = mock.MagicMock()
    entry_ammo.get_editor_property.return_value = "Ammo"
    mock_bb.get_editor_property.return_value = [entry_health, entry_ammo]
    mu.EditorAssetLibrary.load_asset.return_value = mock_bb
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.bb_read({"asset_path": "/Game/TestBB"})
    assert result["ok"] is True
    assert set(result["variable_names"]) == {"Health", "Ammo"}


def test_bb_read_asset_not_found():
    mu = mock.MagicMock()
    mu.EditorAssetLibrary.load_asset.return_value = None
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.bb_read({"asset_path": "/Game/TestBB"})
    assert result["ok"] is False
    assert "Asset not found" in result["error"]


def test_bb_read_wrong_asset_type():
    mu = mock.MagicMock()
    wrong_asset = mock.MagicMock()
    wrong_asset.get_class.return_value.get_name.return_value = "Blueprint"
    mu.EditorAssetLibrary.load_asset.return_value = wrong_asset
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.bb_read({"asset_path": "/Game/BP_CombatEnemy"})
    assert result["ok"] is False
    assert "Expected BlackboardData" in result["error"]
    assert "Blueprint" in result["error"]


def test_bb_add_variable():
    mu = mock.MagicMock()
    mock_bb = _bb_mock()
    mu.EditorAssetLibrary.load_asset.return_value = mock_bb
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.bb_add_variable({"asset_path": "/Game/TestBB", "var_name": "Health", "var_type": "float"})
    assert result["ok"] is True
    assert result["variable"] == "Health"
    assert result["type"] == "float"


def test_bb_add_variable_missing_params():
    with mock.patch.dict('sys.modules', {'unreal': mock.MagicMock()}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.bb_add_variable({})
    assert result["ok"] is False
    assert "asset_path and var_name are required" in result["error"]


def test_bb_delete_variable():
    mu = mock.MagicMock()
    mock_bb = _bb_mock()
    entry_health = mock.MagicMock()
    entry_health.get_editor_property.return_value = "Health"
    entry_ammo = mock.MagicMock()
    entry_ammo.get_editor_property.return_value = "Ammo"
    mock_bb.get_editor_property.return_value = [entry_health, entry_ammo]
    mu.EditorAssetLibrary.load_asset.return_value = mock_bb
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.bb_delete_variable({"asset_path": "/Game/TestBB", "var_name": "Health"})
    assert result["ok"] is True
    assert result["variable"] == "Health"
    # Verify the remaining keys were written back (only Ammo)
    written_keys = mock_bb.set_editor_property.call_args[0][1]
    assert len(written_keys) == 1
    assert written_keys[0] is entry_ammo


def test_bb_delete_variable_missing_params():
    with mock.patch.dict('sys.modules', {'unreal': mock.MagicMock()}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.bb_delete_variable({})
    assert result["ok"] is False
    assert "asset_path and var_name are required" in result["error"]


def test_bb_delete():
    mu = mock.MagicMock()
    mu.EditorAssetLibrary.delete_asset.return_value = True
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.bb_delete({"asset_path": "/Game/TestBB"})
    assert result["ok"] is True
    assert result["asset_path"] == "/Game/TestBB"


def test_bb_delete_missing_asset_path():
    with mock.patch.dict('sys.modules', {'unreal': mock.MagicMock()}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.behavior_trees as mod
        importlib.reload(mod)
        result = mod.bb_delete({})
    assert result["ok"] is False
    assert "asset_path is required" in result["error"]
