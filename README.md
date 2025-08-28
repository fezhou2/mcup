# MCUP: Model Context Protocol with User Control

MCUP is a fork of the [Model Context Protocol SDK](https://github.com/modelcontextprotocol/python-sdk) that adds CLI-based user confirmation for mutating tool call actions (e.g., tools with names containing 'write', 'delete', 'update', 'create', 'modify'). Other actions like initialization and tool listing proceed without prompts.

## Installation

```bash
pip install mcup
```

Alternatively, clone the repository and install in editable mode:

```bash
git clone https://github.com/fezhou2/mcup
cd mcup
pip install -e .
```

## Usage

Use `MCUPSession` with `approval_mode='cli'` to enable CLI prompts for mutating tool calls. The example below uses a simple server provided in the repository, which supports `fetch` (non-mutating, fetches website content) and `write_data` (mutating, simulates writing data).

### Server Setup
Start the server in a separate terminal:

```bash
cd examples/servers/simple-tool
export UV_INDEX=""
python3 -m mcp_simple_tool --transport stdio
```

### Example Client
Run the client to interact with the server:

```python
import asyncio
from mcup.client.stdio import stdio_client
from mcup.shared.stdio import StdioServerParameters
from mcup import types

async def main():
    server_params = StdioServerParameters(
        command="python3",
        args=["-m", "examples.servers.simple-tool.mcp_simple_tool", "--transport", "stdio"],
        env={"UV_INDEX": ""},
    )
    async with stdio_client(server_params, approval_mode='cli') as session:
        # List available tools
        tools = await session.list_tools()
        print(f"Available tools: {[t.name for t in tools.tools]}")

        # Call fetch tool (non-mutating, no prompt)
        result = await session.call_tool("fetch", {"url": "https://example.com"})
        result_unstructured = result.content[0]
        if isinstance(result_unstructured, types.TextContent):
            print(f"Tool result (fetch): {result_unstructured.text[:100]}...")
        print(f"Structured tool result (fetch): {result.structuredContent}")

        # Call write_data tool (mutating, requires CLI approval)
        result = await session.call_tool("write_data", {"data": "example"})
        result_unstructured = result.content[0]
        if isinstance(result_unstructured, types.TextContent):
            print(f"Tool result (write_data): {result_unstructured.text}")
        print(f"Structured tool result (write_data): {result.structuredContent}")

asyncio.run(main())
```

**Expected Output**:
```
Session initialized successfully
Available tools: ['fetch', 'write_data']
Tool result (fetch): <!doctype html><html><head>    <title>Example Domain</title>...
Structured tool result (fetch): {'url': 'https://example.com'}
Approve MCUP tool call?
Details: {'tool_name': 'write_data', 'arguments': {'data': 'example'}}
(y/n): y
Tool result (write_data): Data written: example
Structured tool result (write_data): {'status': 'success', 'data': 'example'}
```

## Testing

To verify the `mcup` package’s functionality, including CLI approval for mutating tools, you can run the provided test suite.

### Setup
1. Install dependencies and the `mcup` package:
   ```bash
   cd /path/to/mcup
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -e .
   ```

2. Start the server in a separate terminal:
   ```bash
   cd /path/to/mcup/examples/servers/simple-tool
   export UV_INDEX=""
   python3 -m mcp_simple_tool --transport stdio
   ```

3. Run the tests:
   ```bash
   cd /path/to/mcup
   pytest tests/client/test_stdio_client.py -v
   ```
   - When prompted (`Approve action for write_data? [y/n]:`), type `y` and press Enter.

### Example Test Script
The test suite (`tests/client/test_stdio_client.py`) verifies session initialization, tool listing, and the `fetch` and `write_data` tools. Below is an excerpt:

```python
import asyncio
import pytest
from mcup.client.stdio import stdio_client
from mcup.shared.stdio import StdioServerParameters
from mcup import types

@pytest.fixture(scope="session")
def server_params():
    """Provide Stdio server parameters for all tests."""
    return StdioServerParameters(
        command="python3",
        args=["-m", "examples.servers.simple-tool.mcp_simple_tool", "--transport", "stdio"],
        env={"UV_INDEX": ""},
    )

@pytest.mark.asyncio
async def test_list_tools(server_params):
    """Verify list_tools includes fetch and write_data."""
    async with stdio_client(server_params, approval_mode="cli") as session:
        tools = await session.list_tools()
        assert isinstance(tools.tools, list), "list_tools should return a list"
        assert "fetch" in [t.name for t in tools.tools], "fetch tool should be available"
        assert "write_data" in [t.name for t in tools.tools], "write_data tool should be available"
        print("Available tools:", [t.name for t in tools.tools])

@pytest.mark.asyncio
async def test_write_data_tool(server_params):
    """Test the write_data tool (mutating, with CLI prompt)."""
    async with stdio_client(server_params, approval_mode="cli") as session:
        # Enter 'y' at the CLI prompt when running
        result = await session.call_tool("write_data", arguments={"data": "example"})
        assert result.content, "Tool call should return content"
        result_unstructured = result.content[0]
        assert isinstance(result_unstructured, types.TextContent), "Result should be TextContent"
        assert "Data written" in result_unstructured.text, "Write_data result should include Data written"
        assert result.structuredContent == {"status": "success", "data": "example"}, "Structured result should match"
        print(f"Tool result (write_data): {result_unstructured.text}")
```

**Expected Test Output**:
```
============================= test session starts =============================
collected 4 items

tests/client/test_stdio_client.py::test_initialize_session PASSED        [ 25%]
tests/client/test_stdio_client.py::test_list_tools PASSED                [ 50%]
Available tools: ['fetch', 'write_data']
tests/client/test_stdio_client.py::test_fetch_tool PASSED                [ 75%]
Tool result (fetch): <!doctype html><html><head>    <title>Example Domain</title>...
tests/client/test_stdio_client.py::test_write_data_tool PASSED           [100%]
Approve action for write_data? [y/n]: y
Tool result (write_data): Data written: example

============================= 4 passed in 0.XXs =============================
```

## Credits

Based on the Model Context Protocol SDK by Anthropic, originally maintained by:
- David Soria Parra (davidsp@anthropic.com)
- Justin Spahr-Summers (justin@anthropic.com)

## License

MIT License (see LICENSE file).

## About

MCP protocol with user confirmation before action.

## Releases

No releases published

## Packages

No packages published

## Languages

* Python 100.0%

## Footer

© 2025 GitHub, Inc.
