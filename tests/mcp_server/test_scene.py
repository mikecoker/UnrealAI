from unittest.mock import patch


def test_scene_get_actors_tool():
    with patch("mcp_server.client.post", return_value={
        "ok": True,
        "actors": [{"name": "BP_Character_1", "class": "BP_Character_C", "location": {"x": 0, "y": 0, "z": 0}}]
    }):
        from mcp_server.tools.scene import _scene_get_actors
        result = _scene_get_actors()

    assert "BP_Character_1" in result


def test_scene_screenshot_tool():
    with patch("mcp_server.client.post", return_value={
        "ok": True, "path": "/tmp/screenshot.png", "note": "async"
    }):
        from mcp_server.tools.scene import _scene_screenshot
        result = _scene_screenshot(width=1920, height=1080)

    assert "/tmp/screenshot.png" in result


def test_scene_get_actors_raises_on_plugin_error():
    import pytest
    with patch("mcp_server.client.post", return_value={"ok": False, "error": "Editor not ready"}):
        from mcp_server.tools.scene import _scene_get_actors
        with pytest.raises(RuntimeError, match="Editor not ready"):
            _scene_get_actors()
