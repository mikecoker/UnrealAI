"""Console command handler: execute UE console commands from within the editor."""

_history: list = []


def execute(body: dict) -> dict:
    import unreal
    command = body.get("command")
    target = body.get("target", "editor")
    if not command:
        return {"ok": False, "error": "command is required"}
    try:
        if target == "game":
            world = unreal.GameplayStatics.get_game_world()
        else:
            world = unreal.EditorLevelLibrary.get_editor_world()
        if world is None:
            return {"ok": False, "error": f"No {target} world available"}
        unreal.SystemLibrary.execute_console_command(world, command)
        _history.append(command)
        return {"ok": True, "message": f"Executed: {command}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_history(body: dict) -> dict:
    return {"ok": True, "history": list(_history)}


def clear_history(body: dict) -> dict:
    _history.clear()
    return {"ok": True}
