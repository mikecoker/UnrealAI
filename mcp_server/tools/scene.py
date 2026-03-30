"""Scene understanding tools: actors, detail, screenshot."""
import json
from mcp_server import client


def _check(result: dict) -> dict:
    """Raise RuntimeError if result is not ok."""
    if not result.get("ok"):
        raise RuntimeError(result.get("error", "Unknown error from UE5 plugin"))
    return result


def _scene_get_actors() -> str:
    result = _check(client.post("/scene/actors", {}))
    lines = [f"- {a['name']} ({a['class']}) at {a['location']}" for a in result["actors"]]
    count = len(result["actors"])
    return f"{count} actors in level:\n" + "\n".join(lines)


def _scene_get_actor_detail(name: str) -> str:
    result = _check(client.post("/scene/actor", {"name": name}))
    return json.dumps(result, indent=2)


def _scene_screenshot(width: int = 1920, height: int = 1080) -> str:
    result = _check(client.post("/scene/screenshot", {"width": width, "height": height}))
    return f"Screenshot saved to: {result['path']}\nNote: {result.get('note', '')}"


def register(mcp):
    @mcp.tool()
    def scene_get_actors() -> str:
        """List all actors in the current Unreal level with their class and location."""
        return _scene_get_actors()

    @mcp.tool()
    def scene_get_actor_detail(name: str) -> str:
        """Get the full component tree and properties of a specific actor by name."""
        return _scene_get_actor_detail(name)

    @mcp.tool()
    def scene_screenshot(width: int = 1920, height: int = 1080) -> str:
        """Capture the current editor viewport and return the file path."""
        return _scene_screenshot(width=width, height=height)
