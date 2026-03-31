"""FastMCP server entrypoint — registers all tools and starts serving."""
from mcp.server.fastmcp import FastMCP
from mcp_server.tools import blueprints, materials, scene, behavior_trees, animation, python_execution, console_commands, user_widgets


def create_mcp_server() -> FastMCP:
    mcp = FastMCP("unreal-ai")
    blueprints.register(mcp)
    materials.register(mcp)
    scene.register(mcp)
    behavior_trees.register(mcp)
    animation.register(mcp)
    python_execution.register(mcp)
    console_commands.register(mcp)
    user_widgets.register(mcp)
    return mcp


def main():
    mcp = create_mcp_server()
    mcp.run()


if __name__ == "__main__":
    main()
