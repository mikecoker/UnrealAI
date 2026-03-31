"""Behavior Tree tools: create, read, add/delete nodes, connect, set blackboard."""
import json
from mcp_server import client


def _check(result: dict) -> dict:
    if not result.get("ok"):
        raise RuntimeError(result.get("error", "Unknown error from UE5 plugin"))
    return result


def _bt_create(asset_path: str) -> str:
    r = _check(client.post("/behavior_tree/create", {"asset_path": asset_path}))
    return f"Created Behavior Tree: {r['asset_path']}"


def _bt_read(asset_path: str) -> str:
    r = _check(client.post("/behavior_tree/read", {"asset_path": asset_path}))
    return json.dumps(r, indent=2)


def _bt_add_node(asset_path: str, node_type: str) -> str:
    r = _check(client.post("/behavior_tree/add_node", {
        "asset_path": asset_path,
        "node_type": node_type
    }))
    return f"Added node type '{node_type}' to {asset_path}"


def _bt_delete_node(asset_path: str, node_name: str) -> str:
    r = _check(client.post("/behavior_tree/delete_node", {
        "asset_path": asset_path,
        "node_name": node_name
    }))
    return f"Deleted node '{node_name}' from {asset_path}"


def _bt_connect_nodes(asset_path: str, from_node: str, to_node: str) -> str:
    r = _check(client.post("/behavior_tree/connect_nodes", {
        "asset_path": asset_path,
        "from_node": from_node,
        "to_node": to_node
    }))
    return f"Connected nodes: {from_node} -> {to_node}"


def _bt_disconnect_nodes(asset_path: str, from_node: str, to_node: str) -> str:
    r = _check(client.post("/behavior_tree/disconnect_nodes", {
        "asset_path": asset_path,
        "from_node": from_node,
        "to_node": to_node
    }))
    return f"Disconnected nodes: {from_node} -> {to_node}"


def _bt_set_blackboard(asset_path: str, blackboard_path: str) -> str:
    r = _check(client.post("/behavior_tree/set_blackboard", {
        "asset_path": asset_path,
        "blackboard_path": blackboard_path
    }))
    return f"Set blackboard for {asset_path} to {blackboard_path}"


def _bt_get_blackboard(asset_path: str) -> str:
    r = _check(client.post("/behavior_tree/get_blackboard", {"asset_path": asset_path}))
    bb = r.get("blackboard_path")
    return f"Blackboard for {asset_path}: {bb if bb else '(none)'}"


def _bt_compile(asset_path: str) -> str:
    r = _check(client.post("/behavior_tree/compile", {"asset_path": asset_path}))
    return f"Compiled Behavior Tree: {asset_path}"


# Blackboard tools
def _bb_create(asset_path: str) -> str:
    r = _check(client.post("/blackboard/create", {"asset_path": asset_path}))
    return f"Created Blackboard: {r['asset_path']}"


def _bb_read(asset_path: str) -> str:
    r = _check(client.post("/blackboard/read", {"asset_path": asset_path}))
    vars = ", ".join(r.get("variable_names", [])) or "(none)"
    return f"Blackboard {asset_path} variables: {vars}"


def _bb_add_variable(asset_path: str, var_name: str, var_type: str = "bool") -> str:
    r = _check(client.post("/blackboard/add_variable", {
        "asset_path": asset_path,
        "var_name": var_name,
        "var_type": var_type
    }))
    return f"Added variable '{var_name}' ({var_type}) to {asset_path}"


def _bb_delete_variable(asset_path: str, var_name: str) -> str:
    r = _check(client.post("/blackboard/delete_variable", {
        "asset_path": asset_path,
        "var_name": var_name
    }))
    return f"Deleted variable '{var_name}' from {asset_path}"


def _bb_delete(asset_path: str) -> str:
    r = _check(client.post("/blackboard/delete", {"asset_path": asset_path}))
    return f"Deleted Blackboard: {asset_path}"


def register(mcp):
    @mcp.tool()
    def bt_create(asset_path: str) -> str:
        """Create a new Behavior Tree asset. asset_path example: /Game/AI/BT_Enemy"""
        return _bt_create(asset_path)

    @mcp.tool()
    def bt_read(asset_path: str) -> str:
        """Read a Behavior Tree's root node and blackboard asset."""
        return _bt_read(asset_path)

    @mcp.tool()
    def bt_add_node(asset_path: str, node_type: str) -> str:
        """Add a node to the Behavior Tree. node_type examples: Sequence, Selector, Task, Decorator"""
        return _bt_add_node(asset_path, node_type)

    @mcp.tool()
    def bt_delete_node(asset_path: str, node_name: str) -> str:
        """Delete a node from the Behavior Tree by name."""
        return _bt_delete_node(asset_path, node_name)

    @mcp.tool()
    def bt_connect_nodes(asset_path: str, from_node: str, to_node: str) -> str:
        """Connect two nodes in the Behavior Tree (from_node -> to_node)."""
        return _bt_connect_nodes(asset_path, from_node, to_node)

    @mcp.tool()
    def bt_disconnect_nodes(asset_path: str, from_node: str, to_node: str) -> str:
        """Disconnect two nodes in the Behavior Tree."""
        return _bt_disconnect_nodes(asset_path, from_node, to_node)

    @mcp.tool()
    def bt_set_blackboard(asset_path: str, blackboard_path: str) -> str:
        """Set the blackboard asset for the Behavior Tree."""
        return _bt_set_blackboard(asset_path, blackboard_path)

    @mcp.tool()
    def bt_get_blackboard(asset_path: str) -> str:
        """Get the blackboard asset assigned to the Behavior Tree."""
        return _bt_get_blackboard(asset_path)

    @mcp.tool()
    def bt_compile(asset_path: str) -> str:
        """Save (compile) the Behavior Tree."""
        return _bt_compile(asset_path)

    # Blackboard tools
    @mcp.tool()
    def bb_create(asset_path: str) -> str:
        """Create a new Blackboard asset. asset_path example: /Game/AI/BB_Enemy"""
        return _bb_create(asset_path)

    @mcp.tool()
    def bb_read(asset_path: str) -> str:
        """Read a Blackboard's variable names."""
        return _bb_read(asset_path)

    @mcp.tool()
    def bb_add_variable(asset_path: str, var_name: str, var_type: str = "bool") -> str:
        """Add a variable to the Blackboard. var_type: bool, int, float, string, vector, object"""
        return _bb_add_variable(asset_path, var_name, var_type)

    @mcp.tool()
    def bb_delete_variable(asset_path: str, var_name: str) -> str:
        """Delete a variable from the Blackboard."""
        return _bb_delete_variable(asset_path, var_name)

    @mcp.tool()
    def bb_delete(asset_path: str) -> str:
        """Delete a Blackboard asset."""
        return _bb_delete(asset_path)