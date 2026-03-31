"""User Widget tools: create, read, list, add/modify widgets."""
import json
from mcp_server import client


def _check(result: dict) -> dict:
    if not result.get("ok"):
        raise RuntimeError(result.get("error", "Unknown error from UE5 plugin"))
    return result


def _uw_create(asset_path: str, parent_class: str = "UserWidget") -> str:
    r = _check(client.post("/userwidget/create", {"asset_path": asset_path, "parent_class": parent_class}))
    return f"Created User Widget: {r['asset_path']}"


def _uw_read(asset_path: str) -> str:
    r = _check(client.post("/userwidget/read", {"asset_path": asset_path}))
    return json.dumps(r, indent=2)


def _uw_list(path: str = "/Game/") -> str:
    r = _check(client.post("/userwidget/list", {"path": path}))
    return "\n".join(r["assets"]) or "(none)"


def _uw_add_widget(asset_path: str, widget_class: str, name: str = "") -> str:
    r = _check(client.post("/userwidget/add_widget", {
        "asset_path": asset_path,
        "widget_class": widget_class,
        "name": name or widget_class,
    }))
    return f"Added widget '{r['widget']}' ({r['class']}) to {asset_path}"


def _uw_add_slot(asset_path: str, slot_name: str) -> str:
    r = _check(client.post("/userwidget/add_slot", {
        "asset_path": asset_path,
        "slot_name": slot_name,
    }))
    return f"Added slot '{r['slot']}' to {asset_path}"


def _uw_add_property(asset_path: str, name: str, type: str = "float", default_value=None) -> str:
    body = {"asset_path": asset_path, "name": name, "type": type}
    if default_value is not None:
        body["default_value"] = default_value
    r = _check(client.post("/userwidget/add_property", body))
    return f"Added property '{r['property']}' ({r['type']}) to {asset_path}"


def _uw_set_property(asset_path: str, property: str, value) -> str:
    r = _check(client.post("/userwidget/set_property", {
        "asset_path": asset_path, "property": property, "value": value
    }))
    return f"Set {r['property']} = {r['value']} on {asset_path}"


def _uw_set_slot_property(asset_path: str, slot: str, property: str, value) -> str:
    r = _check(client.post("/userwidget/set_slot_property", {
        "asset_path": asset_path, "slot": slot, "property": property, "value": value
    }))
    return f"Set {slot}.{r['property']} = {r['value']}"


def _uw_compile(asset_path: str) -> str:
    r = _check(client.post("/userwidget/compile", {"asset_path": asset_path}))
    errors = r.get("errors", [])
    clean = r.get("clean", False)
    if errors:
        return f"Compiled User Widget: {asset_path} with errors: {', '.join(errors)}"
    else:
        return f"Compiled User Widget: {asset_path} (clean)"


def _uw_delete_widget(asset_path: str, name: str) -> str:
    r = _check(client.post("/userwidget/delete_widget", {"asset_path": asset_path, "name": name}))
    return f"Deleted widget '{name}' from {asset_path}"


def _uw_delete_slot(asset_path: str, slot_name: str) -> str:
    r = _check(client.post("/userwidget/delete_slot", {"asset_path": asset_path, "slot_name": slot_name}))
    return f"Deleted slot '{slot_name}' from {asset_path}"


def _uw_delete_property(asset_path: str, name: str) -> str:
    r = _check(client.post("/userwidget/delete_property", {"asset_path": asset_path, "name": name}))
    return f"Deleted property '{name}' from {asset_path}"


def register(mcp):
    @mcp.tool()
    def uw_create(asset_path: str, parent_class: str = "UserWidget") -> str:
        """Create a new User Widget class. asset_path example: /Game/UI/BP_MainMenu"""
        return _uw_create(asset_path, parent_class)

    @mcp.tool()
    def uw_read(asset_path: str) -> str:
        """Read a User Widget's structure, widgets, and properties."""
        return _uw_read(asset_path)

    @mcp.tool()
    def uw_list(path: str = "/Game/") -> str:
        """List all User Widget assets under a content path."""
        return _uw_list(path)

    @mcp.tool()
    def uw_add_widget(asset_path: str, widget_class: str, name: str = "") -> str:
        """Add a widget to a User Widget. widget_class example: Button, TextBlock"""
        return _uw_add_widget(asset_path, widget_class, name)

    @mcp.tool()
    def uw_delete_widget(asset_path: str, name: str) -> str:
        """Delete a widget from a User Widget."""
        return _uw_delete_widget(asset_path, name)

    @mcp.tool()
    def uw_add_slot(asset_path: str, slot_name: str) -> str:
        """Add a slot to a User Widget."""
        return _uw_add_slot(asset_path, slot_name)

    @mcp.tool()
    def uw_delete_slot(asset_path: str, slot_name: str) -> str:
        """Delete a slot from a User Widget."""
        return _uw_delete_slot(asset_path, slot_name)

    @mcp.tool()
    def uw_add_property(asset_path: str, name: str, type: str = "float", default_value: str = "") -> str:
        """Add a property to a User Widget. type: bool, int, float, string, vector, widget"""
        return _uw_add_property(asset_path, name, type, default_value or None)

    @mcp.tool()
    def uw_delete_property(asset_path: str, name: str) -> str:
        """Delete a property from a User Widget."""
        return _uw_delete_property(asset_path, name)

    @mcp.tool()
    def uw_set_property(asset_path: str, property: str, value: str) -> str:
        """Set a property default value on a User Widget."""
        return _uw_set_property(asset_path, property, value)

    @mcp.tool()
    def uw_set_slot_property(asset_path: str, slot: str, property: str, value: str) -> str:
        """Set a property on a slot within a User Widget."""
        return _uw_set_slot_property(asset_path, slot, property, value)

    @mcp.tool()
    def uw_compile(asset_path: str) -> str:
        """Compile a User Widget and return any errors."""
        return _uw_compile(asset_path)