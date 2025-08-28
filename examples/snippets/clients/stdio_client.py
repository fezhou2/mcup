"""
cd to the `examples/snippets/clients` directory and run:
    python stdio_client.py
"""

import asyncio
import os
from typing import Optional

from mcup import ClientSession, StdioServerParameters, types
from mcup.client.stdio import stdio_client
from mcup.client.mcup_session import MCUPSession
from mcup.shared.context import RequestContext

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="python3",
    args=["-m", "examples.servers.simple-tool.mcp_simple_tool", "--transport", "stdio"],
    env={"UV_INDEX": os.environ.get("UV_INDEX", "")},
)

# Optional: create a sampling callback
async def handle_sampling_message(
    context: RequestContext[ClientSession, None], params: types.CreateMessageRequestParams
) -> types.CreateMessageResult:
    print(f"Sampling request: {params.messages}")
    return types.CreateMessageResult(
        role="assistant",
        content=types.TextContent(
            type="text",
            text="Hello, world! from model",
        ),
        model="gpt-3.5-turbo",
        stopReason="endTurn",
    )

async def run(approval_mode: Optional[str] = None):
    try:
        async with stdio_client(server_params, approval_mode=approval_mode) as session:
            # Initialize the connection
            try:
                await session.initialize()
                print("Session initialized successfully")
            except Exception as e:
                print(f"Error initializing session: {e}")
                return

            # List available tools
            try:
                tools = await session.list_tools()
                print(f"Available tools: {[t.name for t in tools.tools]}")
            except Exception as e:
                print(f"Error listing tools: {e}")

            # Call the fetch tool (non-mutating)
            try:
                result = await session.call_tool("fetch", arguments={"url": "https://example.com"})
                result_unstructured = result.content[0]
                if isinstance(result_unstructured, types.TextContent):
                    print(f"Tool result (fetch): {result_unstructured.text[:100]}...")  # Truncate for brevity
                result_structured = result.structuredContent
                print(f"Structured tool result (fetch): {result_structured}")
            except Exception as e:
                print(f"Error calling fetch: {e}")

            # Call the write_data tool (mutating)
            try:
                result = await session.call_tool("write_data", arguments={"data": "example"})
                result_unstructured = result.content[0]
                if isinstance(result_unstructured, types.TextContent):
                    print(f"Tool result (write_data): {result_unstructured.text}")
                result_structured = result.structuredContent
                print(f"Structured tool result (write_data): {result_structured}")
            except Exception as e:
                print(f"Error calling write_data: {e}")
    except Exception as e:
        print(f"Stdio client error: {e}")
        import traceback
        traceback.print_exc()
        raise

def main():
    """Entry point for the client script."""
    asyncio.run(run(approval_mode="cli"))

if __name__ == "__main__":
    main()