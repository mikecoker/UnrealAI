from unittest.mock import patch
import pytest


def test_mat_create():
    with patch("mcp_server.client.post", return_value={
        "ok": True, "asset_path": "/Game/M_Rock", "name": "M_Rock"
    }):
        from mcp_server.tools.materials import _mat_create
        result = _mat_create(asset_path="/Game/M_Rock")
    assert "M_Rock" in result


def test_mat_add_expression():
    with patch("mcp_server.client.post", return_value={
        "ok": True, "node": "Multiply_0_0", "type": "Multiply"
    }):
        from mcp_server.tools.materials import _mat_add_expression
        result = _mat_add_expression("/Game/M_Rock", "Multiply")
    assert "Multiply_0_0" in result


def test_mat_connect_pins():
    with patch("mcp_server.client.post", return_value={
        "ok": True, "connected": "node_a.RGB → node_b.A"
    }):
        from mcp_server.tools.materials import _mat_connect_pins
        result = _mat_connect_pins("/Game/M_Rock", "node_a", "RGB", "node_b", "A")
    assert "node_a" in result


def test_mat_apply():
    with patch("mcp_server.client.post", return_value={
        "ok": True, "material": "/Game/M_Rock", "applied_to": "SM_Floor"
    }):
        from mcp_server.tools.materials import _mat_apply
        result = _mat_apply(asset_path="/Game/M_Rock", target="SM_Floor")
    assert "SM_Floor" in result


def test_mat_tools_raise_on_error():
    with patch("mcp_server.client.post", return_value={"ok": False, "error": "Asset not found"}):
        from mcp_server.tools.materials import _mat_create
        with pytest.raises(RuntimeError, match="Asset not found"):
            _mat_create("/Game/Missing")
