"""Maps HTTP paths to handler functions."""
from handlers import blueprints, materials, scene, debug, behavior_trees, animation

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
    "/blueprint/delete_variable":  blueprints.delete_variable,
    "/blueprint/delete_component": blueprints.delete_component,
    "/blueprint/delete_function":  blueprints.delete_function,
    "/blueprint/delete_event":     blueprints.delete_event,
    "/blueprint/delete_node":      blueprints.delete_node,
    "/blueprint/disconnect_pins":  blueprints.disconnect_pins,
    "/blueprint/add_component":    blueprints.add_component,
    "/blueprint/add_function":     blueprints.add_function,
    "/blueprint/add_event":        blueprints.add_event,
    "/blueprint/add_node":         blueprints.add_node,
    "/blueprint/connect_pins":     blueprints.connect_pins,
    "/blueprint/get_nodes":        blueprints.get_nodes,
    "/blueprint/find_function":    blueprints.find_function,
    "/blueprint/add_special_node":  blueprints.add_special_node,
    "/blueprint/add_variable_node": blueprints.add_variable_node,
    "/blueprint/set_property":     blueprints.set_property,
    "/blueprint/set_component_property": blueprints.set_component_property,
    "/blueprint/compile":          blueprints.compile,

    # Debug
    "/debug/pintype":                debug.pintype,
    "/debug/bp_api":                 debug.bp_api,
    "/debug/ue_classes":             debug.ue_classes,
    "/debug/obj_api":                debug.obj_api,
    "/debug/graph_nodes":            debug.graph_nodes,
    "/debug/browse_class":           debug.browse_class,
    "/debug/bp_variables":           debug.bp_variables,
    "/debug/cdo_props":              debug.cdo_props,

    # Materials
    "/material/create":            materials.create,
    "/material/read":              materials.read,
    "/material/list":              materials.list_assets,
    "/material/add_expression":    materials.add_expression,
    "/material/connect_pins":      materials.connect_pins,
    "/material/set_parameter":     materials.set_parameter,
    "/material/apply":             materials.apply,
    "/material/delete":            materials.delete,

    # Behavior Trees
    "/behavior_tree/create":       behavior_trees.create,
    "/behavior_tree/read":         behavior_trees.read,
    "/behavior_tree/add_node":     behavior_trees.add_node,
    "/behavior_tree/delete_node":  behavior_trees.delete_node,
    "/behavior_tree/connect_nodes": behavior_trees.connect_nodes,
    "/behavior_tree/disconnect_nodes": behavior_trees.disconnect_nodes,
    "/behavior_tree/set_blackboard": behavior_trees.set_blackboard,
    "/behavior_tree/get_blackboard": behavior_trees.get_blackboard,
    "/behavior_tree/get_nodes":    behavior_trees.get_nodes,
    "/behavior_tree/compile":      behavior_trees.compile,
    # Blackboard
    "/blackboard/create":          behavior_trees.bb_create,
    "/blackboard/read":            behavior_trees.bb_read,
    "/blackboard/add_variable":    behavior_trees.bb_add_variable,
    "/blackboard/delete_variable": behavior_trees.bb_delete_variable,
    "/blackboard/delete":          behavior_trees.bb_delete,

    # Animation Graphs
    "/animation/create":           animation.create,
    "/animation/read":             animation.read,
    "/animation/add_node":         animation.add_node,
    "/animation/get_nodes":        animation.get_nodes,
    "/animation/delete_node":      animation.delete_node,
    "/animation/connect_nodes":    animation.connect_nodes,
    "/animation/disconnect_nodes": animation.disconnect_nodes,
    "/animation/compile":          animation.compile,
}


def dispatch(path: str, body: dict) -> dict:
    handler = _ROUTES.get(path)
    if handler is None:
        return {"ok": False, "error": f"Unknown route: {path}"}
    return handler(body)
