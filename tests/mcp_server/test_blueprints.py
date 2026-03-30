from unittest.mock import patch
import pytest


def test_bp_create_posts_correct_body():
    with patch("mcp_server.client.post", return_value={
        "ok": True, "asset_path": "/Game/BP_Hero", "name": "BP_Hero"
    }) as mock_post:
        from mcp_server.tools.blueprints import _bp_create
        result = _bp_create(asset_path="/Game/BP_Hero", parent_class="Actor")

    mock_post.assert_called_once_with(
        "/blueprint/create", {"asset_path": "/Game/BP_Hero", "parent_class": "Actor"}
    )
    assert "/Game/BP_Hero" in result


def test_bp_compile_shows_errors():
    with patch("mcp_server.client.post", return_value={
        "ok": True, "errors": ["Pin not connected: Health"], "clean": False
    }):
        from mcp_server.tools.blueprints import _bp_compile
        result = _bp_compile(asset_path="/Game/BP_Hero")

    assert "Pin not connected" in result


def test_bp_compile_clean():
    with patch("mcp_server.client.post", return_value={
        "ok": True, "errors": [], "clean": True
    }):
        from mcp_server.tools.blueprints import _bp_compile
        result = _bp_compile(asset_path="/Game/BP_Hero")

    assert "clean" in result.lower() or "success" in result.lower()


def test_bp_add_node_raises_on_error():
    with patch("mcp_server.client.post", return_value={
        "ok": False, "error": "Graph not found: EventGraph"
    }):
        from mcp_server.tools.blueprints import _bp_add_node
        with pytest.raises(RuntimeError, match="Graph not found"):
            _bp_add_node(asset_path="/Game/BP_Hero", graph="EventGraph", function="PrintString")
