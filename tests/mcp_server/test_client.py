from unittest.mock import patch, MagicMock
import pytest
from mcp_server.client import post, UE5ConnectionError


def test_post_returns_dict_on_success():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"ok": True, "actors": []}
    mock_resp.raise_for_status.return_value = None

    with patch("mcp_server.client.requests.post", return_value=mock_resp) as mock_post:
        result = post("/scene/actors", {})

    assert result == {"ok": True, "actors": []}
    mock_post.assert_called_once_with(
        "http://localhost:7777/scene/actors", json={}, timeout=30
    )


def test_post_raises_on_connection_error():
    import requests as req
    with patch("mcp_server.client.requests.post", side_effect=req.exceptions.ConnectionError):
        with pytest.raises(UE5ConnectionError, match="UE5 plugin server not running"):
            post("/scene/actors", {})
