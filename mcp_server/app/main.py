from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

mcp = FastMCP(name="seas-mcp-server")


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


@mcp.tool()
async def hello_world() -> str:
    return "Hello, world!"


if __name__ == "__main__":
    mcp.run(transport="stdio")
