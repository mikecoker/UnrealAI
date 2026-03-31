"""Blueprint tools: create, read, list, add/modify nodes and variables, compile."""
import json
from mcp_server import client


def _check(result: dict) -> dict:
    if not result.get("ok"):
        raise RuntimeError(result.get("error", "Unknown error from UE5 plugin"))
    return result


def _bp_create(asset_path: str, parent_class: str = "Actor") -> str:
    r = _check(client.post("/blueprint/create", {"asset_path": asset_path, "parent_class": parent_class}))
    return f"Created Blueprint: {r['asset_path']}"


def _bp_read(asset_path: str) -> str:
    r = _check(client.post("/blueprint/read", {"asset_path": asset_path}))
    return json.dumps(r, indent=2)


def _bp_list(path: str = "/Game/") -> str:
    r = _check(client.post("/blueprint/list", {"path": path}))
    return "\n".join(r["assets"]) or "(none)"


def _bp_add_variable(asset_path: str, name: str, type: str = "float", default_value=None) -> str:
    body = {"asset_path": asset_path, "name": name, "type": type}
    if default_value is not None:
        body["default_value"] = default_value
    r = _check(client.post("/blueprint/add_variable", body))
    return f"Added variable '{r['variable']}' ({r['type']}) to {asset_path}"


def _bp_add_component(asset_path: str, component_class: str, name: str = "") -> str:
    r = _check(client.post("/blueprint/add_component", {
        "asset_path": asset_path,
        "component_class": component_class,
        "name": name or component_class,
    }))
    return f"Added component '{r['component']}' ({r['class']}) to {asset_path}"


def _bp_add_function(asset_path: str, name: str) -> str:
    r = _check(client.post("/blueprint/add_function", {"asset_path": asset_path, "name": name}))
    return f"Added function '{r['function']}' to {asset_path}"


def _bp_add_event(asset_path: str, event: str = "BeginPlay") -> str:
    r = _check(client.post("/blueprint/add_event", {"asset_path": asset_path, "event": event}))
    return json.dumps(r, indent=2)


def _bp_get_nodes(asset_path: str, graph: str = "EventGraph") -> str:
    r = _check(client.post("/blueprint/get_nodes", {"asset_path": asset_path, "graph": graph}))
    return json.dumps(r, indent=2)


def _bp_add_variable_node(asset_path: str, graph: str, variable: str, node_type: str = "get", x: int = 0, y: int = 0) -> str:
    r = _check(client.post("/blueprint/add_variable_node", {
        "asset_path": asset_path, "graph": graph, "variable": variable,
        "node_type": node_type, "x": x, "y": y
    }))
    pins_str = ", ".join(r.get("pins", []))
    return f"Added variable {node_type} node '{r['node_id']}' for '{variable}'. Pins: {pins_str}"


def _bp_add_special_node(asset_path: str, graph: str, node_type: str, x: int = 0, y: int = 0) -> str:
    r = _check(client.post("/blueprint/add_special_node", {
        "asset_path": asset_path, "graph": graph, "node_type": node_type, "x": x, "y": y
    }))
    pins_str = ", ".join(r.get("pins", []))
    return f"Added '{node_type}' node '{r['node_id']}'. Pins: {pins_str}"


def _bp_find_function(name: str) -> str:
    r = _check(client.post("/blueprint/find_function", {"name": name}))
    matches = r.get("matches", [])
    if not matches:
        return f"No functions found matching '{name}'"
    return "\n".join(matches)


def _bp_add_node(asset_path: str, graph: str, function: str, x: int = 0, y: int = 0) -> str:
    r = _check(client.post("/blueprint/add_node", {
        "asset_path": asset_path, "graph": graph, "function": function, "x": x, "y": y
    }))
    pins_str = ", ".join(r.get("pins", []))
    return f"Added node '{r['node_id']}' (function: {function}). Pins: {pins_str}"


def _bp_connect_pins(asset_path: str, graph: str, from_node: str, from_pin: str, to_node: str, to_pin: str) -> str:
    r = _check(client.post("/blueprint/connect_pins", {
        "asset_path": asset_path, "graph": graph,
        "from_node": from_node, "from_pin": from_pin,
        "to_node": to_node, "to_pin": to_pin,
    }))
    return f"Connected: {r['connected']}"


def _bp_set_property(asset_path: str, property: str, value) -> str:
    r = _check(client.post("/blueprint/set_property", {
        "asset_path": asset_path, "property": property, "value": value
    }))
    return f"Set {r['property']} = {r['value']} on {asset_path}"


def _bp_set_component_property(asset_path: str, component: str, property: str, value) -> str:
    r = _check(client.post("/blueprint/set_component_property", {
        "asset_path": asset_path, "component": component, "property": property, "value": value
    }))
    return f"Set {component}.{r['property']} = {r['value']}"


def _bp_compile(asset_path: str) -> str:
    r = _check(client.post("/blueprint/compile", {"asset_path": asset_path}))
    if r["clean"]:
        return f"Compiled {asset_path} successfully — no errors."
    errors = "\n".join(f"  - {e}" for e in r["errors"])
    return f"Compiled {asset_path} with {len(r['errors'])} error(s):\n{errors}"


def register(mcp):
    @mcp.tool()
    def bp_create(asset_path: str, parent_class: str = "Actor") -> str:
        """Create a new Blueprint class. asset_path example: /Game/Characters/BP_Hero"""
        return _bp_create(asset_path, parent_class)

    @mcp.tool()
    def bp_read(asset_path: str) -> str:
        """Read a Blueprint's graphs, variables, and components."""
        return _bp_read(asset_path)

    @mcp.tool()
    def bp_list(path: str = "/Game/") -> str:
        """List all Blueprint assets under a content path."""
        return _bp_list(path)

    @mcp.tool()
    def bp_add_variable(asset_path: str, name: str, type: str = "float", default_value: str = "") -> str:
        """Add a variable to a Blueprint. type: bool, int, float, string, vector, actor, object"""
        return _bp_add_variable(asset_path, name, type, default_value or None)

    @mcp.tool()
    def bp_add_component(asset_path: str, component_class: str, name: str = "") -> str:
        """Add a component to a Blueprint. component_class example: StaticMeshComponent"""
        return _bp_add_component(asset_path, component_class, name)

    @mcp.tool()
    def bp_add_function(asset_path: str, name: str) -> str:
        """Add a new function graph to a Blueprint."""
        return _bp_add_function(asset_path, name)

    @mcp.tool()
    def bp_add_event(asset_path: str, event: str = "BeginPlay") -> str:
        """Add an event to a Blueprint's EventGraph and return its node_id and pins. event: BeginPlay, Tick, or a custom event name. Use the returned node_id for bp_connect_pins."""
        return _bp_add_event(asset_path, event)

    @mcp.tool()
    def bp_get_nodes(asset_path: str, graph: str = "EventGraph") -> str:
        """List all nodes in a Blueprint graph with their IDs, classes, and pin names. Use this to find node IDs for bp_connect_pins."""
        return _bp_get_nodes(asset_path, graph)

    @mcp.tool()
    def bp_add_variable_node(asset_path: str, graph: str, variable: str, node_type: str = "get", x: int = 0, y: int = 0) -> str:
        """Add a variable getter or setter node to a Blueprint graph. node_type: 'get' (default) or 'set'. variable must be the exact variable name as defined on the Blueprint."""
        return _bp_add_variable_node(asset_path, graph, variable, node_type, x, y)

    @mcp.tool()
    def bp_add_special_node(asset_path: str, graph: str, node_type: str, x: int = 0, y: int = 0) -> str:
        """Add a special node to a Blueprint graph. node_type: Branch, Sequence, ForLoop, DoOnce, FlipFlop, Gate, Self"""
        return _bp_add_special_node(asset_path, graph, node_type, x, y)

    @mcp.tool()
    def bp_find_function(name: str) -> str:
        """Search for a UE5 function by name. Returns full paths like '/Script/Engine.KismetSystemLibrary:PrintString' needed by bp_add_node. Use this before bp_add_node if you don't know the exact path."""
        return _bp_find_function(name)

    @mcp.tool()
    def bp_add_node(asset_path: str, graph: str, function: str, x: int = 0, y: int = 0) -> str:
        """Add a function call node to a Blueprint graph. Use bp_find_function to discover the correct name first. UE5.5+ uses double precision: comparison operators are 'Greater_DoubleDouble' not 'Greater_FloatFloat'; vector length is 'VSize' not 'VectorLength'. For Branch/ForLoop/Sequence use bp_add_special_node instead."""
        return _bp_add_node(asset_path, graph, function, x, y)

    @mcp.tool()
    def bp_connect_pins(asset_path: str, graph: str, from_node: str, from_pin: str, to_node: str, to_pin: str) -> str:
        """Connect an output pin to an input pin between two nodes in a Blueprint graph."""
        return _bp_connect_pins(asset_path, graph, from_node, from_pin, to_node, to_pin)

    @mcp.tool()
    def bp_set_property(asset_path: str, property: str, value: str) -> str:
        """Set a variable default value or node property on a Blueprint."""
        return _bp_set_property(asset_path, property, value)

    @mcp.tool()
    def bp_set_component_property(asset_path: str, component: str, property: str, value: str) -> str:
        """Set a property on a component within a Blueprint."""
        return _bp_set_component_property(asset_path, component, property, value)

    @mcp.tool()
    def bp_compile(asset_path: str) -> str:
        """Compile a Blueprint and return any errors."""
        return _bp_compile(asset_path)
