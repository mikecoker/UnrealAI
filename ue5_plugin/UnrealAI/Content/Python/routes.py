"""Maps HTTP paths to handler functions."""
from handlers import blueprints, materials, scene

_ROUTES = {
    # Scene
    "/scene/actors":       scene.get_actors,
    "/scene/actor":        scene.get_actor_detail,
    "/scene/screenshot":   scene.screenshot,

    # Blueprints
    "/blueprint/create":           blueprints.create,
    "/blueprint/read":             blueprints.read,
    "/blueprint/list":             blueprints.list_assets,
    "/blueprint/add_variable":     blueprints.add_variable,
    "/blueprint/add_component":    blueprints.add_component,
    "/blueprint/add_function":     blueprints.add_function,
    "/blueprint/add_event":        blueprints.add_event,
    "/blueprint/add_node":         blueprints.add_node,
    "/blueprint/connect_pins":     blueprints.connect_pins,
    "/blueprint/set_property":     blueprints.set_property,
    "/blueprint/set_component_property": blueprints.set_component_property,
    "/blueprint/compile":          blueprints.compile,

    # Materials
    "/material/create":            materials.create,
    "/material/read":              materials.read,
    "/material/list":              materials.list_assets,
    "/material/add_expression":    materials.add_expression,
    "/material/connect_pins":      materials.connect_pins,
    "/material/set_parameter":     materials.set_parameter,
    "/material/apply":             materials.apply,
}


def dispatch(path: str, body: dict) -> dict:
    handler = _ROUTES.get(path)
    if handler is None:
        return {"ok": False, "error": f"Unknown route: {path}"}
    return handler(body)
