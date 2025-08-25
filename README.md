# MCUP: Model Context Protocol with User Control

MCUP is a fork of the [Model Context Protocol SDK](https://github.com/modelcontextprotocol/python-sdk) that adds CLI-based user confirmation for mutating tool call actions (e.g., tools with names containing 'write', 'delete', 'update', 'create', 'modify'). Other actions like initialization, resource reads, and tool listing proceed without prompts.

## Installation

```bash
pip install mcup
```

## Usage

Use `MCUPSession` with `approval_mode='cli'` to enable CLI prompts for mutating tool calls:

```python
import asyncio
from mcup.client import sse_client, stdio_client
from mcup.shared.stdio import StdioServerParameters

async def main():
    # SSE client
    async with sse_client(url="http://localhost:8000", approval_mode='cli') as session:
        # Prompts for approval (mutating tool, replace with actual tool from list_tools)
        result = await session.call_tool("write_data", {"data": "example"})
        print(f"Result: {result}")
        # No prompt (non-mutating tool, replace with actual tool from list_tools)
        result = await session.call_tool("get_data", {"id": "123"})
        print(f"Get result: {result}")

    # Stdio client
    server_params = StdioServerParameters(command="uv", args=["run", "server", "fastmcp_quickstart", "stdio"])
    async with stdio_client(server_params, approval_mode='cli') as session:
        # Prompts for approval (mutating tool, replace with actual tool from list_tools)
        result = await session.call_tool("write_data", {"data": "example"})
        print(f"Result: {result}")
        # No prompt (non-mutating tool, replace with actual tool from list_tools)
        result = await session.call_tool("get_data", {"id": "123"})
        print(f"Get result: {result}")

asyncio.run(main())
```

## Credits

Based on the Model Context Protocol SDK by Anthropic, originally maintained by:
- David Soria Parra (davidsp@anthropic.com)
- Justin Spahr-Summers (justin@anthropic.com)

## License

MIT License (see LICENSE file).