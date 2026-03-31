"""FastMCP server entrypoint — registers all tools and starts serving."""
from mcp.server.fastmcp import FastMCP
from mcp_server.tools import blueprints, materials, scene, behavior_trees, animation


def create_mcp_server() -> FastMCP:
    mcp = FastMCP("unreal-ai")
    blueprints.register(mcp)
    materials.register(mcp)
    scene.register(mcp)
    behavior_trees.register(mcp)
    animation.register(mcp)
    return mcp


def main():
    mcp = create_mcp_server()
    mcp.run()


if __name__ == "__main__":
    main()
