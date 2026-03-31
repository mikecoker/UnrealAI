"""Tests for the animation handler."""
import importlib
from unittest import mock


def test_create():
    mu = mock.MagicMock()
    mock_skeleton = mock.MagicMock()
    mock_anim_bp = mock.MagicMock()
    mu.EditorAssetLibrary.load_asset.return_value = mock_skeleton
    mu.AssetToolsHelpers.get_asset_tools.return_value.create_asset.return_value = mock_anim_bp
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.animation as mod
        importlib.reload(mod)
        result = mod.create({"asset_path": "/Game/ABP_Test", "skeleton_path": "/Game/SK_Test"})
    assert result["ok"] is True
    assert result["asset_path"] == "/Game/ABP_Test"
    assert result["name"] == "ABP_Test"


def test_create_missing_params():
    mu = mock.MagicMock()
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.animation as mod
        importlib.reload(mod)
        result = mod.create({"asset_path": "/Game/ABP_Test"})
    assert result["ok"] is False
    assert "skeleton_path" in result["error"]


def test_create_skeleton_not_found():
    mu = mock.MagicMock()
    mu.EditorAssetLibrary.load_asset.return_value = None
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.animation as mod
        importlib.reload(mod)
        result = mod.create({"asset_path": "/Game/ABP_Test", "skeleton_path": "/Game/SK_Missing"})
    assert result["ok"] is False
    assert "Skeleton not found" in result["error"]


def test_read():
    mu = mock.MagicMock()
    mock_anim_bp = mock.MagicMock()
    mock_graph = mock.MagicMock()
    mock_graph.get_name.return_value = "AnimGraph"
    mock_skeleton = mock.MagicMock()
    mock_skeleton.get_path_name.return_value = "/Game/SK_Test"
    mu.EditorAssetLibrary.load_asset.return_value = mock_anim_bp
    mu.BlueprintEditorLibrary.find_graph.return_value = mock_graph
    mock_anim_bp.get_editor_property.return_value = mock_skeleton
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.animation as mod
        importlib.reload(mod)
        result = mod.read({"asset_path": "/Game/ABP_Test"})
    assert result["ok"] is True
    assert result["skeleton"] == "/Game/SK_Test"
    assert "AnimGraph" in result["graphs"]


def test_read_asset_not_found():
    mu = mock.MagicMock()
    mu.EditorAssetLibrary.load_asset.return_value = None
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.animation as mod
        importlib.reload(mod)
        result = mod.read({"asset_path": "/Game/ABP_Test"})
    assert result["ok"] is False
    assert "not found" in result["error"]


def test_add_node():
    mu = mock.MagicMock()
    mock_anim_bp = mock.MagicMock()
    mock_graph = mock.MagicMock()
    mock_node = mock.MagicMock()
    mock_node.get_name.return_value = "AnimGraphNode_SequencePlayer_0"
    mu.EditorAssetLibrary.load_asset.return_value = mock_anim_bp
    mu.BlueprintEditorLibrary.find_graph.return_value = mock_graph
    mu.UnrealAIGraphLibrary.add_animation_node.return_value = mock_node
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.animation as mod
        importlib.reload(mod)
        result = mod.add_node({
            "asset_path": "/Game/ABP_Test",
            "node_type": "SequencePlayer",
            "x": 200, "y": 100,
        })
    assert result["ok"] is True
    assert result["node_id"] == "AnimGraphNode_SequencePlayer_0"
    assert result["node_type"] == "SequencePlayer"
    mu.UnrealAIGraphLibrary.add_animation_node.assert_called_once_with(
        mock_graph, "SequencePlayer", 200, 100
    )


def test_add_node_not_found():
    mu = mock.MagicMock()
    mock_anim_bp = mock.MagicMock()
    mock_graph = mock.MagicMock()
    mu.EditorAssetLibrary.load_asset.return_value = mock_anim_bp
    mu.BlueprintEditorLibrary.find_graph.return_value = mock_graph
    mu.UnrealAIGraphLibrary.add_animation_node.return_value = None
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.animation as mod
        importlib.reload(mod)
        result = mod.add_node({"asset_path": "/Game/ABP_Test", "node_type": "Unknown"})
    assert result["ok"] is False
    assert "Failed to add node" in result["error"]


def test_get_nodes():
    mu = mock.MagicMock()
    mock_anim_bp = mock.MagicMock()
    mock_graph = mock.MagicMock()
    mock_info = mock.MagicMock()
    mock_info.node_name = "AnimGraphNode_Result_0"
    mock_info.node_class = "AnimGraphNode_Result"
    mock_info.input_pins = ["Result"]
    mock_info.output_pins = []
    mu.EditorAssetLibrary.load_asset.return_value = mock_anim_bp
    mu.BlueprintEditorLibrary.find_graph.return_value = mock_graph
    mu.UnrealAIGraphLibrary.get_graph_nodes.return_value = [mock_info]
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.animation as mod
        importlib.reload(mod)
        result = mod.get_nodes({"asset_path": "/Game/ABP_Test"})
    assert result["ok"] is True
    assert len(result["nodes"]) == 1
    assert result["nodes"][0]["name"] == "AnimGraphNode_Result_0"


def test_delete_node():
    mu = mock.MagicMock()
    mock_anim_bp = mock.MagicMock()
    mock_graph = mock.MagicMock()
    mu.EditorAssetLibrary.load_asset.return_value = mock_anim_bp
    mu.BlueprintEditorLibrary.find_graph.return_value = mock_graph
    mu.UnrealAIGraphLibrary.delete_animation_node.return_value = True
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.animation as mod
        importlib.reload(mod)
        result = mod.delete_node({"asset_path": "/Game/ABP_Test", "node_name": "Node_0"})
    assert result["ok"] is True
    assert result["node_name"] == "Node_0"
    mu.UnrealAIGraphLibrary.delete_animation_node.assert_called_once_with(mock_graph, "Node_0")


def test_delete_node_protected():
    mu = mock.MagicMock()
    mock_anim_bp = mock.MagicMock()
    mock_graph = mock.MagicMock()
    mu.EditorAssetLibrary.load_asset.return_value = mock_anim_bp
    mu.BlueprintEditorLibrary.find_graph.return_value = mock_graph
    mu.UnrealAIGraphLibrary.delete_animation_node.return_value = False
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.animation as mod
        importlib.reload(mod)
        result = mod.delete_node({"asset_path": "/Game/ABP_Test", "node_name": "Result_0"})
    assert result["ok"] is False
    assert "not found or cannot be deleted" in result["error"]


def test_connect_nodes():
    mu = mock.MagicMock()
    mock_anim_bp = mock.MagicMock()
    mock_graph = mock.MagicMock()
    mu.EditorAssetLibrary.load_asset.return_value = mock_anim_bp
    mu.BlueprintEditorLibrary.find_graph.return_value = mock_graph
    mu.UnrealAIGraphLibrary.connect_animation_nodes.return_value = True
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.animation as mod
        importlib.reload(mod)
        result = mod.connect_nodes({
            "asset_path": "/Game/ABP_Test",
            "from_node": "SeqPlayer_0",
            "to_node": "Result_0",
        })
    assert result["ok"] is True
    assert result["connected"] == "SeqPlayer_0 -> Result_0"
    mu.UnrealAIGraphLibrary.connect_animation_nodes.assert_called_once_with(
        mock_graph, "SeqPlayer_0", "Result_0"
    )


def test_connect_nodes_failed():
    mu = mock.MagicMock()
    mock_anim_bp = mock.MagicMock()
    mock_graph = mock.MagicMock()
    mu.EditorAssetLibrary.load_asset.return_value = mock_anim_bp
    mu.BlueprintEditorLibrary.find_graph.return_value = mock_graph
    mu.UnrealAIGraphLibrary.connect_animation_nodes.return_value = False
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.animation as mod
        importlib.reload(mod)
        result = mod.connect_nodes({
            "asset_path": "/Game/ABP_Test", "from_node": "A", "to_node": "B"
        })
    assert result["ok"] is False
    assert "Could not connect" in result["error"]


def test_disconnect_nodes():
    mu = mock.MagicMock()
    mock_anim_bp = mock.MagicMock()
    mock_graph = mock.MagicMock()
    mu.EditorAssetLibrary.load_asset.return_value = mock_anim_bp
    mu.BlueprintEditorLibrary.find_graph.return_value = mock_graph
    mu.UnrealAIGraphLibrary.disconnect_animation_nodes.return_value = True
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.animation as mod
        importlib.reload(mod)
        result = mod.disconnect_nodes({
            "asset_path": "/Game/ABP_Test", "from_node": "A", "to_node": "B"
        })
    assert result["ok"] is True
    assert result["disconnected"] == "A -> B"


def test_disconnect_nodes_no_connection():
    mu = mock.MagicMock()
    mock_anim_bp = mock.MagicMock()
    mock_graph = mock.MagicMock()
    mu.EditorAssetLibrary.load_asset.return_value = mock_anim_bp
    mu.BlueprintEditorLibrary.find_graph.return_value = mock_graph
    mu.UnrealAIGraphLibrary.disconnect_animation_nodes.return_value = False
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.animation as mod
        importlib.reload(mod)
        result = mod.disconnect_nodes({
            "asset_path": "/Game/ABP_Test", "from_node": "A", "to_node": "B"
        })
    assert result["ok"] is False
    assert "No connection" in result["error"]


def test_compile():
    mu = mock.MagicMock()
    mock_anim_bp = mock.MagicMock()
    mu.EditorAssetLibrary.load_asset.return_value = mock_anim_bp
    mu.BlueprintEditorLibrary.compile_blueprint.return_value = []
    with mock.patch.dict('sys.modules', {'unreal': mu}):
        import ue5_plugin.UnrealAI.Content.Python.handlers.animation as mod
        importlib.reload(mod)
        result = mod.compile({"asset_path": "/Game/ABP_Test"})
    assert result["ok"] is True
    assert result["clean"] is True
    assert result["errors"] == []
