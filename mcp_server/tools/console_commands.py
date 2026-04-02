"""Console command tools: execute UE console commands and Python scripts in-editor."""
from mcp_server import client


def _check(result: dict) -> dict:
    if not result.get("ok"):
        raise RuntimeError(result.get("error", "Unknown error from UE5 plugin"))
    return result


def _console_execute(command: str, target: str = "editor") -> str:
    r = _check(client.post("/console/execute", {"command": command, "target": target}))
    return r.get("message", f"Executed: {command}")


def _console_get_history() -> str:
    r = _check(client.post("/console/history", {}))
    history = r.get("history", [])
    return "\n".join(history) if history else "(no history)"


def _console_clear_history() -> str:
    _check(client.post("/console/clear_history", {}))
    return "Console history cleared"


def register(mcp):
    @mcp.tool()
    def console_execute(command: str, target: str = "editor") -> str:
        """Execute a UE5 console command in-editor. Examples: 'stat fps', 'r.ScreenPercentage 100'. target: 'editor' or 'game'"""
        return _console_execute(command, target)

    @mcp.tool()
    def console_get_history() -> str:
        """Get the history of previously executed console commands."""
        return _console_get_history()

    @mcp.tool()
    def console_clear_history() -> str:
        """Clear the console command history."""
        return _console_clear_history()
