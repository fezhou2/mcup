from typing import Any

import anyio
import click
import mcup.types as types
from mcup.server.lowlevel import Server
from mcup.shared._httpx_utils import create_mcp_http_client
from starlette.requests import Request

async def fetch_website(
    url: str,
) -> tuple[list[types.ContentBlock], dict[str, Any]]:
    headers = {"User-Agent": "MCP Test Server (github.com/modelcontextprotocol/python-sdk)"}
    async with create_mcp_http_client(headers=headers) as client:
        response = await client.get(url)
        response.raise_for_status()
        return [types.TextContent(type="text", text=response.text)], {"url": url}

async def write_data(
    data: str,
) -> tuple[list[types.ContentBlock], dict[str, Any]]:
    # Simulate writing data (e.g., to a file or store)
    return [types.TextContent(type="text", text=f"Data written: {data}")], {"status": "success", "data": data}

@click.command()
@click.option("--port", default=8000, help="Port to listen on for SSE")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport type",
)
def main(port: int, transport: str) -> int:
    app = Server("mcp-website-fetcher")

    @app.call_tool()
    async def fetch_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "fetch":
            if "url" not in arguments:
                raise ValueError("Missing required argument 'url'")
            content, structured = await fetch_website(arguments["url"])
            return {
                "content": [{"type": "text", "text": content[0].text}],
                "structuredContent": structured,
                "isMutating": False
            }
        elif name == "write_data":
            if "data" not in arguments:
                raise ValueError("Missing required argument 'data'")
            content, structured = await write_data(arguments["data"])
            return {
                "content": [{"type": "text", "text": content[0].text}],
                "structuredContent": structured,
                "isMutating": True
            }
        else:
            raise ValueError(f"Unknown tool: {name}")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="fetch",
                title="Website Fetcher",
                description="Fetches a website and returns its content",
                inputSchema={
                    "type": "object",
                    "required": ["url"],
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to fetch",
                        }
                    },
                },
                isMutating=False
            ),
            types.Tool(
                name="write_data",
                title="Data Writer",
                description="Writes data to a store",
                inputSchema={
                    "type": "object",
                    "required": ["data"],
                    "properties": {
                        "data": {
                            "type": "string",
                            "description": "Data to write",
                        }
                    },
                },
                isMutating=True
            )
        ]

    if transport == "sse":
        from mcup.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.responses import Response
        from starlette.routing import Mount, Route

        sse = SseServerTransport("/messages/")

        async def handle_sse(request: Request):
            async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
                await app.run(streams[0], streams[1], app.create_initialization_options())
            return Response()

        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse, methods=["GET"]),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        import uvicorn

        uvicorn.run(starlette_app, host="127.0.0.1", port=port)
    else:
        from mcup.server.stdio import stdio_server

        async def arun():
            async with stdio_server() as streams:
                await app.run(streams[0], streams[1], app.create_initialization_options())

        anyio.run(arun)

    return 0

if __name__ == "__main__":
    main()