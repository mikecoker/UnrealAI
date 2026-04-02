def test_all_tools_registered():
    """Verify all expected tools are registered with the MCP server."""
    from mcp_server.server import create_mcp_server
    mcp = create_mcp_server()
    
    # FastMCP stores tools in _tool_manager._tools dict
    registered = set(mcp._tool_manager._tools.keys())
    
    expected = {
        # Scene (3)
        "scene_get_actors", "scene_get_actor_detail", "scene_screenshot",
        # Blueprints (22)
        "bp_create", "bp_read", "bp_list", "bp_add_variable", "bp_add_component", "bp_add_function", "bp_add_event",
        "bp_get_nodes", "bp_find_function", "bp_add_node", "bp_connect_pins", "bp_set_property", "bp_set_component_property",
        "bp_add_variable_node", "bp_add_special_node", "bp_delete_variable", "bp_delete_component", "bp_delete_function",
        "bp_delete_event", "bp_delete_node", "bp_disconnect_pins", "bp_compile",
        # Materials (8)
        "mat_create", "mat_read", "mat_list", "mat_add_expression", "mat_connect_pins",
        "mat_set_parameter", "mat_apply", "mat_delete",
        # Behavior Trees (15)
        "bt_create", "bt_read", "bt_add_node", "bt_delete_node", "bt_connect_nodes", "bt_disconnect_nodes",
        "bt_set_blackboard", "bt_get_blackboard", "bt_get_nodes", "bt_compile", "bt_delete",
        "bb_create", "bb_read", "bb_add_variable", "bb_delete_variable", "bb_delete",
        # Animation (8)
        "anim_create", "anim_read", "anim_add_node", "anim_get_nodes", "anim_delete_node",
        "anim_connect_nodes", "anim_disconnect_nodes", "anim_compile",
        # Console / Python execution (5)
        "console_clear_history", "console_execute", "console_get_history",
        "execute_python_file", "execute_python_script",
        # UMG Widgets (12)
        "uw_create", "uw_read", "uw_list", "uw_compile",
        "uw_add_widget", "uw_delete_widget",
        "uw_add_slot", "uw_delete_slot", "uw_set_slot_property",
        "uw_add_property", "uw_delete_property", "uw_set_property",
    }

    missing = expected - registered
    assert not missing, f"Missing tools: {missing}"
    assert len(registered) == 74
