def test_all_tools_registered():
    """Verify all 22 expected tools are registered with the MCP server."""
    from mcp_server.server import create_mcp_server
    mcp = create_mcp_server()

    # FastMCP stores tools in _tool_manager._tools dict
    registered = set(mcp._tool_manager._tools.keys())

    expected = {
        # Scene (3)
        "scene_get_actors", "scene_get_actor_detail", "scene_screenshot",
        # Blueprints (12)
        "bp_create", "bp_read", "bp_list", "bp_add_variable", "bp_add_component",
        "bp_add_function", "bp_add_event", "bp_add_node", "bp_connect_pins",
        "bp_set_property", "bp_set_component_property", "bp_compile",
        # Materials (7)
        "mat_create", "mat_read", "mat_list", "mat_add_expression",
        "mat_connect_pins", "mat_set_parameter", "mat_apply",
    }

    missing = expected - registered
    assert not missing, f"Missing tools: {missing}"
    assert len(registered) == 22
