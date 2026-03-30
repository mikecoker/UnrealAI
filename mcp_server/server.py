"""FastMCP server entrypoint — registers all 22 tools and starts serving."""
from mcp.server.fastmcp import FastMCP
from mcp_server.tools import blueprints, materials, scene


def create_mcp_server() -> FastMCP:
    mcp = FastMCP("unreal-ai")
    blueprints.register(mcp)
    materials.register(mcp)
    scene.register(mcp)
    return mcp


def main():
    mcp = create_mcp_server()
    mcp.run()


if __name__ == "__main__":
    main()
