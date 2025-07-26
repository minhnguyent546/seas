from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings

mcp = FastMCP(name="seas-mcp-server")


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


@mcp.tool()
async def hello_world():
    return {
        'message': "Hello, world!",
        'port': settings.FASTMCP_PORT,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
