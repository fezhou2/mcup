"""
cd to the `examples/snippets/clients` directory and run:
    uv run client
"""

import asyncio
import os
from typing import Optional

from pydantic import AnyUrl

from mcup import ClientSession, StdioServerParameters, types
from mcup.client.stdio import stdio_client
# MCUPSession used via session_class when approval_mode="cli"
from mcup.client.mcup_session import MCUPSession
from mcup.shared.context import RequestContext

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="uv",
    args=["run", "server", "fastmcp_quickstart", "stdio"],
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
    async with stdio_client(server_params, approval_mode=approval_mode) as session:
        # Initialize the connection
        await session.initialize()

        # List available prompts
        prompts = await session.list_prompts()
        print(f"Available prompts: {[p.name for p in prompts.prompts]}")

        # Get a prompt (greet_user prompt from fastmcp_quickstart)
        if prompts.prompts:
            prompt = await session.get_prompt("greet_user", arguments={"name": "Alice", "style": "friendly"})
            print(f"Prompt result: {prompt.messages[0].content}")

        # List available resources
        resources = await session.list_resources()
        print(f"Available resources: {[r.uri for r in resources.resources]}")

        # List available tools
        tools = await session.list_tools()
        print(f"Available tools: {[t.name for t in tools.tools]}")

        # Read a resource (greeting resource from fastmcp_quickstart)
        resource_content = await session.read_resource(AnyUrl("greeting://World"))
        content_block = resource_content.contents[0]
        if isinstance(content_block, types.TextContent):
            print(f"Resource content: {content_block.text}")

        # Call a non-mutating tool (add tool from fastmcp_quickstart)
        result = await session.call_tool("add", arguments={"a": 5, "b": 3})
        result_unstructured = result.content[0]
        if isinstance(result_unstructured, types.TextContent):
            print(f"Tool result (add): {result_unstructured.text}")
        result_structured = result.structuredContent
        print(f"Structured tool result (add): {result_structured}")

        # Call a mutating tool (example, adjust based on server tools)
        try:
            result = await session.call_tool("write_data", arguments={"data": "example"})
            result_unstructured = result.content[0]
            if isinstance(result_unstructured, types.TextContent):
                print(f"Tool result (write_data): {result_unstructured.text}")
            result_structured = result.structuredContent
            print(f"Structured tool result (write_data): {result_structured}")
        except Exception as e:
            print(f"Error calling write_data: {e}")

def main():
    """Entry point for the client script."""
    asyncio.run(run(approval_mode="cli"))

if __name__ == "__main__":
    main()