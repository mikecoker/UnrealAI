"""Console command tools: execute UE console commands within editor context."""
import json
from mcp_server import client


def _check(result: dict) -> dict:
    """Raise RuntimeError if result is not ok."""
    if not result.get("ok"):
        raise RuntimeError(result.get("error", "Unknown error from UE5 plugin"))
    return result


def _console_execute(command: str, target: str = "editor") -> str:
    """Execute a console command in the Unreal Engine editor context."""
    result = _check(client.post("/console/execute", {
        "command": command,
        "target": target
    }))
    return f"Console command executed: {result.get('output', 'No output')}"


def _console_get_history() -> str:
    """Get the console command history."""
    result = _check(client.post("/console/history", {}))
    commands = result.get("commands", [])
    if not commands:
        return "No console command history."
    lines = [f"{i+1}. {cmd}" for i, cmd in enumerate(commands)]
    return f"Console command history:\n" + "\n".join(lines)


def _console_clear_history() -> str:
    """Clear the console command history."""
    result = _check(client.post("/console/clear", {}))
    return "Console command history cleared."


def register(mcp):
    @mcp.tool()
    def console_execute(command: str, target: str = "editor") -> str:
        """Execute a console command in Unreal Engine. 
        command: The console command to execute (e.g., 'stat fps', 'r.ScreenPercentage 100')
        target: Target context - either 'editor' or 'game'"""
        return _console_execute(command, target)

    @mcp.tool()
    def console_get_history() -> str:
        """Get the history of previously executed console commands."""
        return _console_get_history()

    @mcp.tool()
    def console_clear_history() -> str:
        """Clear the console command history."""
        return _console_clear_history()