"""Material tools: create, read, list, add expressions, connect pins, apply."""
import json
from mcp_server import client


def _check(result: dict) -> dict:
    if not result.get("ok"):
        raise RuntimeError(result.get("error", "Unknown error from UE5 plugin"))
    return result


def _mat_create(asset_path: str) -> str:
    r = _check(client.post("/material/create", {"asset_path": asset_path}))
    return f"Created Material: {r['asset_path']}"


def _mat_read(asset_path: str) -> str:
    r = _check(client.post("/material/read", {"asset_path": asset_path}))
    return json.dumps(r, indent=2)


def _mat_list(path: str = "/Game/") -> str:
    r = _check(client.post("/material/list", {"path": path}))
    return "\n".join(r["assets"]) or "(none)"


def _mat_add_expression(asset_path: str, type: str, x: int = 0, y: int = 0, name: str = "") -> str:
    body = {"asset_path": asset_path, "type": type, "x": x, "y": y}
    if name:
        body["name"] = name
    r = _check(client.post("/material/add_expression", body))
    return f"Added expression node '{r['node']}' (type: {r['type']}) to {asset_path}"


def _mat_connect_pins(asset_path: str, from_node: str, from_pin: str, to_node: str, to_pin: str) -> str:
    r = _check(client.post("/material/connect_pins", {
        "asset_path": asset_path,
        "from_node": from_node, "from_pin": from_pin,
        "to_node": to_node, "to_pin": to_pin,
    }))
    return f"Connected: {r['connected']}"


def _mat_set_parameter(asset_path: str, node: str, parameter_name: str = "", value=None) -> str:
    r = _check(client.post("/material/set_parameter", {
        "asset_path": asset_path, "node": node,
        "parameter_name": parameter_name, "value": value,
    }))
    return f"Set parameter on '{r['node']}': {r['parameter_name']} = {r['value']}"


def _mat_apply(asset_path: str, target: str, slot: int = 0) -> str:
    r = _check(client.post("/material/apply", {
        "asset_path": asset_path, "target": target, "slot": slot
    }))
    return f"Applied {r['material']} to {r['applied_to']} (slot {slot})"


def _mat_delete(asset_path: str) -> str:
    r = _check(client.post("/material/delete", {"asset_path": asset_path}))
    return f"Deleted Material: {r['deleted']}"


def register(mcp):
    @mcp.tool()
    def mat_create(asset_path: str) -> str:
        """Create a new Material asset. asset_path example: /Game/Materials/M_Rock"""
        return _mat_create(asset_path)

    @mcp.tool()
    def mat_read(asset_path: str) -> str:
        """Read a Material's expression nodes and connections."""
        return _mat_read(asset_path)

    @mcp.tool()
    def mat_list(path: str = "/Game/") -> str:
        """List Material assets under a content path."""
        return _mat_list(path)

    @mcp.tool()
    def mat_add_expression(asset_path: str, type: str, x: int = 0, y: int = 0, name: str = "") -> str:
        """Add an expression node to a Material graph. type: Multiply, Add, Lerp, TextureSample, Constant, Constant3, ScalarParameter, VectorParameter"""
        return _mat_add_expression(asset_path, type, x, y, name)

    @mcp.tool()
    def mat_connect_pins(asset_path: str, from_node: str, from_pin: str, to_node: str, to_pin: str) -> str:
        """Connect an output to an input between Material expression nodes. Use 'BaseColor', 'Metallic', etc. as to_node to connect to the material output."""
        return _mat_connect_pins(asset_path, from_node, from_pin, to_node, to_pin)

    @mcp.tool()
    def mat_set_parameter(asset_path: str, node: str, parameter_name: str = "", value: str = "") -> str:
        """Set the parameter name or default value on a Material expression node."""
        return _mat_set_parameter(asset_path, node, parameter_name, value or None)

    @mcp.tool()
    def mat_apply(asset_path: str, target: str, slot: int = 0) -> str:
        """Apply a Material to a Static Mesh asset path or a level actor name."""
        return _mat_apply(asset_path, target, slot)

    @mcp.tool()
    def mat_delete(asset_path: str) -> str:
        """Delete a Material asset."""
        return _mat_delete(asset_path)
