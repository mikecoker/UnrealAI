import os
import tempfile


def get_actors(body: dict) -> dict:
    import unreal
    try:
        actors = unreal.EditorLevelLibrary.get_all_level_actors()
        result = []
        for actor in actors:
            loc = actor.get_actor_location()
            result.append({
                "name": actor.get_name(),
                "class": actor.get_class().get_name(),
                "location": {"x": loc.x, "y": loc.y, "z": loc.z},
            })
        return {"ok": True, "actors": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_actor_detail(body: dict) -> dict:
    import unreal
    name = body.get("name", "")
    try:
        actors = unreal.EditorLevelLibrary.get_all_level_actors()
        actor = next((a for a in actors if a.get_name() == name), None)
        if actor is None:
            return {"ok": False, "error": f"Actor not found: {name}"}

        loc = actor.get_actor_location()
        rot = actor.get_actor_rotation()

        components = []
        for comp in actor.get_components_by_class(unreal.ActorComponent):
            components.append({
                "name": comp.get_name(),
                "class": comp.get_class().get_name(),
            })

        return {
            "ok": True,
            "name": actor.get_name(),
            "class": actor.get_class().get_name(),
            "location": {"x": loc.x, "y": loc.y, "z": loc.z},
            "rotation": {"pitch": rot.pitch, "yaw": rot.yaw, "roll": rot.roll},
            "components": components,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def screenshot(body: dict) -> dict:
    import unreal
    width = body.get("width", 1920)
    height = body.get("height", 1080)
    path = body.get("path", os.path.join(tempfile.gettempdir(), "unreal_ai_screenshot.png"))
    try:
        cmd = f"HighResShot {width}x{height} filename={path}"
        unreal.SystemLibrary.execute_console_command(None, cmd)
        return {"ok": True, "path": path, "note": "Screenshot saved asynchronously — wait ~1s before reading."}
    except Exception as e:
        return {"ok": False, "error": str(e)}
