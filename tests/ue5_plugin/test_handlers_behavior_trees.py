"""Tests for the behavior_trees handler."""
from unittest import mock
import sys


def test_create():
    # Setup mock unreal
    mock_unreal = mock.MagicMock()
    mock_unreal.AssetToolsHelpers.get_asset_tools.return_value.create_asset.return_value = mock.MagicMock()
    mock_unreal.EditorAssetLibrary.save_asset.return_value = True
    mock_unreal.BehaviorTreeFactory.return_value = mock.MagicMock()
    mock_unreal.BehaviorTree = mock.MagicMock()

    with mock.patch.dict('sys.modules', {'unreal': mock_unreal}):
        from ue5_plugin.UnrealAI.Content.Python.handlers import behavior_trees

        # Execute
        result = behavior_trees.create({"asset_path": "/Game/TestBT"})

        # Verify
        assert result["ok"] is True
        assert result["asset_path"] == "/Game/TestBT"
        assert result["name"] == "TestBT"


def test_create_missing_asset_path():
    with mock.patch.dict('sys.modules', {'unreal': mock.MagicMock()}):
        from ue5_plugin.UnrealAI.Content.Python.handlers import behavior_trees
        result = behavior_trees.create({})
        assert result["ok"] is False
        assert "asset_path is required" in result["error"]


def test_read():
    # Setup mock unreal
    mock_unreal = mock.MagicMock()
    mock_bt = mock.MagicMock()
    mock_root = mock.MagicMock()
    mock_root.get_name.return_value = "RootNode"
    mock_bt.get_root_node.return_value = mock_root
    mock_bb = mock.MagicMock()
    mock_bb.get_path_name.return_value = "/Game/Blackboard.BB_Test"
    mock_bt.blackboard_asset = mock_bb
    mock_unreal.EditorAssetLibrary.load_asset.return_value = mock_bt

    with mock.patch.dict('sys.modules', {'unreal': mock_unreal}):
        from ue5_plugin.UnrealAI.Content.Python.handlers import behavior_trees

        # Execute
        result = behavior_trees.read({"asset_path": "/Game/TestBT"})

        # Verify
        assert result["ok"] is True
        assert result["asset_path"] == "/Game/TestBT"
        assert result["root_node"] == "RootNode"
        assert result["blackboard"] == "/Game/Blackboard.BB_Test"


def test_read_asset_not_found():
    mock_unreal = mock.MagicMock()
    mock_unreal.EditorAssetLibrary.load_asset.return_value = None
    with mock.patch.dict('sys.modules', {'unreal': mock_unreal}):
        from ue5_plugin.UnrealAI.Content.Python.handlers import behavior_trees
        result = behavior_trees.read({"asset_path": "/Game/TestBT"})
        assert result["ok"] is False
        assert "Behavior Tree not found" in result["error"]


def test_add_node():
    mock_unreal = mock.MagicMock()
    mock_bt = mock.MagicMock()
    mock_unreal.EditorAssetLibrary.load_asset.return_value = mock_bt
    with mock.patch.dict('sys.modules', {'unreal': mock_unreal}):
        from ue5_plugin.UnrealAI.Content.Python.handlers import behavior_trees
        result = behavior_trees.add_node({
            "asset_path": "/Game/TestBT",
            "node_type": "Sequence"
        })
        assert result["ok"] is True
        assert "Node type 'Sequence' addition not fully implemented" in result["message"]


def test_delete_node():
    mock_unreal = mock.MagicMock()
    mock_bt = mock.MagicMock()
    mock_unreal.EditorAssetLibrary.load_asset.return_value = mock_bt
    with mock.patch.dict('sys.modules', {'unreal': mock_unreal}):
        from ue5_plugin.UnrealAI.Content.Python.handlers import behavior_trees
        result = behavior_trees.delete_node({
            "asset_path": "/Game/TestBT",
            "node_name": "SomeNode"
        })
        assert result["ok"] is True
        assert "Node 'SomeNode' deletion not fully implemented" in result["message"]


def test_connect_nodes():
    mock_unreal = mock.MagicMock()
    mock_bt = mock.MagicMock()
    mock_unreal.EditorAssetLibrary.load_asset.return_value = mock_bt
    with mock.patch.dict('sys.modules', {'unreal': mock_unreal}):
        from ue5_plugin.UnrealAI.Content.Python.handlers import behavior_trees
        result = behavior_trees.connect_nodes({
            "asset_path": "/Game/TestBT",
            "from_node": "NodeA",
            "to_node": "NodeB"
        })
        assert result["ok"] is True
        assert "Connection from 'NodeA' to 'NodeB' not fully implemented" in result["message"]


def test_disconnect_nodes():
    mock_unreal = mock.MagicMock()
    mock_bt = mock.MagicMock()
    mock_unreal.EditorAssetLibrary.load_asset.return_value = mock_bt
    with mock.patch.dict('sys.modules', {'unreal': mock_unreal}):
        from ue5_plugin.UnrealAI.Content.Python.handlers import behavior_trees
        result = behavior_trees.disconnect_nodes({
            "asset_path": "/Game/TestBT",
            "from_node": "NodeA",
            "to_node": "NodeB"
        })
        assert result["ok"] is True
        assert "Disconnection from 'NodeA' to 'NodeB' not fully implemented" in result["message"]


def test_set_blackboard():
    mock_unreal = mock.MagicMock()
    mock_bt = mock.MagicMock()
    mock_bb = mock.MagicMock()
    mock_bb.get_path_name.return_value = "/Game/Blackboard.BB_Test"
    mock_unreal.EditorAssetLibrary.load_asset.side_effect = [mock_bt, mock_bb]
    mock_unreal.EditorAssetLibrary.save_asset.return_value = True
    with mock.patch.dict('sys.modules', {'unreal': mock_unreal}):
        from ue5_plugin.UnrealAI.Content.Python.handlers import behavior_trees
        result = behavior_trees.set_blackboard({
            "asset_path": "/Game/TestBT",
            "blackboard_path": "/Game/Blackboard.BB_Test"
        })
        assert result["ok"] is True
        assert result["blackboard"] == "/Game/Blackboard.BB_Test"


def test_set_blackboard_missing_asset():
    with mock.patch.dict('sys.modules', {'unreal': mock.MagicMock()}):
        from ue5_plugin.UnrealAI.Content.Python.handlers import behavior_trees
        result = behavior_trees.set_blackboard({})
        assert result["ok"] is False
        assert "asset_path and blackboard_path are required" in result["error"]


def test_get_blackboard():
    mock_unreal = mock.MagicMock()
    mock_bt = mock.MagicMock()
    mock_bb = mock.MagicMock()
    mock_bb.get_path_name.return_value = "/Game/Blackboard.BB_Test"
    mock_bt.blackboard_asset = mock_bb
    mock_unreal.EditorAssetLibrary.load_asset.return_value = mock_bt
    with mock.patch.dict('sys.modules', {'unreal': mock_unreal}):
        from ue5_plugin.UnrealAI.Content.Python.handlers import behavior_trees
        result = behavior_trees.get_blackboard({"asset_path": "/Game/TestBT"})
        assert result["ok"] is True
        assert result["blackboard_path"] == "/Game/Blackboard.BB_Test"


def test_get_blackboard_none():
    mock_unreal = mock.MagicMock()
    mock_bt = mock.MagicMock()
    mock_bt.blackboard_asset = None
    mock_unreal.EditorAssetLibrary.load_asset.return_value = mock_bt
    with mock.patch.dict('sys.modules', {'unreal': mock_unreal}):
        from ue5_plugin.UnrealAI.Content.Python.handlers import behavior_trees
        result = behavior_trees.get_blackboard({"asset_path": "/Game/TestBT"})
        assert result["ok"] is True
        assert result["blackboard_path"] is None


def test_compile():
    mock_unreal = mock.MagicMock()
    mock_bt = mock.MagicMock()
    mock_unreal.EditorAssetLibrary.load_asset.return_value = mock_bt
    mock_unreal.EditorAssetLibrary.save_asset.return_value = True
    with mock.patch.dict('sys.modules', {'unreal': mock_unreal}):
        from ue5_plugin.UnrealAI.Content.Python.handlers import behavior_trees
        result = behavior_trees.compile({"asset_path": "/Game/TestBT"})
        assert result["ok"] is True
        assert result["asset_path"] == "/Game/TestBT"
        assert result["message"] == "Behavior Tree saved"


# Blackboard tests
def test_bb_create():
    mock_unreal = mock.MagicMock()
    mock_unreal.AssetToolsHelpers.get_asset_tools.return_value.create_asset.return_value = mock.MagicMock()
    mock_unreal.EditorAssetLibrary.save_asset.return_value = True
    mock_unreal.BlackboardFactory.return_value = mock.MagicMock()
    with mock.patch.dict('sys.modules', {'unreal': mock_unreal}):
        from ue5_plugin.UnrealAI.Content.Python.handlers import behavior_trees
        result = behavior_trees.bb_create({"asset_path": "/Game/TestBB"})
        assert result["ok"] is True
        assert result["asset_path"] == "/Game/TestBB"
        assert result["name"] == "TestBB"


def test_bb_create_missing_asset_path():
    with mock.patch.dict('sys.modules', {'unreal': mock.MagicMock()}):
        from ue5_plugin.UnrealAI.Content.Python.handlers import behavior_trees
        result = behavior_trees.bb_create({})
        assert result["ok"] is False
        assert "asset_path is required" in result["error"]


def test_bb_read():
    mock_unreal = mock.MagicMock()
    mock_bb = mock.MagicMock()
    mock_bb.get_all_variable_names.return_value = ["Health", "Ammo"]
    mock_unreal.EditorAssetLibrary.load_asset.return_value = mock_bb
    with mock.patch.dict('sys.modules', {'unreal': mock_unreal}):
        from ue5_plugin.UnrealAI.Content.Python.handlers import behavior_trees
        result = behavior_trees.bb_read({"asset_path": "/Game/TestBB"})
        assert result["ok"] is True
        assert result["asset_path"] == "/Game/TestBB"
        assert set(result["variable_names"]) == {"Health", "Ammo"}


def test_bb_read_asset_not_found():
    mock_unreal = mock.MagicMock()
    mock_unreal.EditorAssetLibrary.load_asset.return_value = None
    with mock.patch.dict('sys.modules', {'unreal': mock_unreal}):
        from ue5_plugin.UnrealAI.Content.Python.handlers import behavior_trees
        result = behavior_trees.bb_read({"asset_path": "/Game/TestBB"})
        assert result["ok"] is False
        assert "Blackboard not found" in result["error"]


def test_bb_add_variable():
    mock_unreal = mock.MagicMock()
    mock_bb = mock.MagicMock()
    mock_unreal.EditorAssetLibrary.load_asset.return_value = mock_bb
    with mock.patch.dict('sys.modules', {'unreal': mock_unreal}):
        from ue5_plugin.UnrealAI.Content.Python.handlers import behavior_trees
        result = behavior_trees.bb_add_variable({
            "asset_path": "/Game/TestBB",
            "var_name": "Health",
            "var_type": "float"
        })
        assert result["ok"] is True
        assert result["variable"] == "Health"
        assert result["type"] == "float"


def test_bb_add_variable_missing_params():
    with mock.patch.dict('sys.modules', {'unreal': mock.MagicMock()}):
        from ue5_plugin.UnrealAI.Content.Python.handlers import behavior_trees
        result = behavior_trees.bb_add_variable({})
        assert result["ok"] is False
        assert "asset_path and var_name are required" in result["error"]


def test_bb_delete_variable():
    mock_unreal = mock.MagicMock()
    mock_bb = mock.MagicMock()
    mock_unreal.EditorAssetLibrary.load_asset.return_value = mock_bb
    with mock.patch.dict('sys.modules', {'unreal': mock_unreal}):
        from ue5_plugin.UnrealAI.Content.Python.handlers import behavior_trees
        result = behavior_trees.bb_delete_variable({
            "asset_path": "/Game/TestBB",
            "var_name": "Health"
        })
        assert result["ok"] is True
        assert result["variable"] == "Health"


def test_bb_delete_variable_missing_params():
    with mock.patch.dict('sys.modules', {'unreal': mock.MagicMock()}):
        from ue5_plugin.UnrealAI.Content.Python.handlers import behavior_trees
        result = behavior_trees.bb_delete_variable({})
        assert result["ok"] is False
        assert "asset_path and var_name are required" in result["error"]


def test_bb_delete():
    mock_unreal = mock.MagicMock()
    mock_unreal.EditorAssetLibrary.delete_asset.return_value = True
    with mock.patch.dict('sys.modules', {'unreal': mock_unreal}):
        from ue5_plugin.UnrealAI.Content.Python.handlers import behavior_trees
        result = behavior_trees.bb_delete({"asset_path": "/Game/TestBB"})
        assert result["ok"] is True
        assert result["asset_path"] == "/Game/TestBB"


def test_bb_delete_missing_asset_path():
    with mock.patch.dict('sys.modules', {'unreal': mock.MagicMock()}):
        from ue5_plugin.UnrealAI.Content.Python.handlers import behavior_trees
        result = behavior_trees.bb_delete({})
        assert result["ok"] is False
        assert "asset_path is required" in result["error"]