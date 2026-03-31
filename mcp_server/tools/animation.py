"""Animation Graph tools: create, read, add/delete nodes, connect, set properties."""
import json
from mcp_server import client


def _check(result: dict) -> dict:
    if not result.get("ok"):
        raise RuntimeError(result.get("error", "Unknown error from UE5 plugin"))
    return result


def _anim_create(asset_path: str) -> str:
    r = _check(client.post("/animation/create", {"asset_path": asset_path}))
    return f"Created Animation Graph: {r['asset_path']}"


def _anim_read(asset_path: str) -> str:
    r = _check(client.post("/animation/read", {"asset_path": asset_path}))
    return json.dumps(r, indent=2)


def _anim_add_node(asset_path: str, node_type: str, x: int = 0, y: int = 0) -> str:
    r = _check(client.post("/animation/add_node", {
        "asset_path": asset_path,
        "node_type": node_type,
        "x": x,
        "y": y,
    }))
    node_id = r.get("node_id", "")
    return f"Added {node_type} node '{node_id}' to {asset_path}"


def _anim_get_nodes(asset_path: str) -> str:
    r = _check(client.post("/animation/get_nodes", {"asset_path": asset_path}))
    return json.dumps(r, indent=2)


def _anim_delete_node(asset_path: str, node_name: str) -> str:
    r = _check(client.post("/animation/delete_node", {
        "asset_path": asset_path,
        "node_name": node_name
    }))
    return f"Deleted node '{node_name}' from {asset_path}"


def _anim_connect_nodes(asset_path: str, from_node: str, to_node: str) -> str:
    r = _check(client.post("/animation/connect_nodes", {
        "asset_path": asset_path,
        "from_node": from_node,
        "to_node": to_node
    }))
    return f"Connected nodes: {from_node} -> {to_node}"


def _anim_disconnect_nodes(asset_path: str, from_node: str, to_node: str) -> str:
    r = _check(client.post("/animation/disconnect_nodes", {
        "asset_path": asset_path,
        "from_node": from_node,
        "to_node": to_node
    }))
    return f"Disconnected nodes: {from_node} -> {to_node}"


def _anim_compile(asset_path: str) -> str:
    r = _check(client.post("/animation/compile", {"asset_path": asset_path}))
    return f"Compiled Animation Graph: {asset_path}"


def register(mcp):
    @mcp.tool()
    def anim_create(asset_path: str) -> str:
        """Create a new Animation Graph asset. asset_path example: /Game/Characters/AnimGraph_Character"""
        return _anim_create(asset_path)

    @mcp.tool()
    def anim_read(asset_path: str) -> str:
        """Read an Animation Graph's nodes and connections."""
        return _anim_read(asset_path)

    @mcp.tool()
    def anim_add_node(asset_path: str, node_type: str, x: int = 0, y: int = 0) -> str:
        """Add a node to the Animation Graph. node_type: BlendSpace1D, BlendSpace2D, Sequence, etc."""
        return _anim_add_node(asset_path, node_type, x, y)

    @mcp.tool()
    def anim_get_nodes(asset_path: str) -> str:
        """List all nodes in an Animation Graph with their names and types."""
        return _anim_get_nodes(asset_path)

    @mcp.tool()
    def anim_delete_node(asset_path: str, node_name: str) -> str:
        """Delete a node from the Animation Graph by name."""
        return _anim_delete_node(asset_path, node_name)

    @mcp.tool()
    def anim_connect_nodes(asset_path: str, from_node: str, to_node: str) -> str:
        """Connect two nodes in the Animation Graph (from_node -> to_node)."""
        return _anim_connect_nodes(asset_path, from_node, to_node)

    @mcp.tool()
    def anim_disconnect_nodes(asset_path: str, from_node: str, to_node: str) -> str:
        """Disconnect two nodes in the Animation Graph."""
        return _anim_disconnect_nodes(asset_path, from_node, to_node)

    @mcp.tool()
    def anim_compile(asset_path: str) -> str:
        """Save (compile) the Animation Graph."""
        return _anim_compile(asset_path)