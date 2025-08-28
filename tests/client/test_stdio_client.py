import asyncio
import pytest
from mcup.client.stdio import stdio_client
try:
    from mcup.shared.stdio import StdioServerParameters
except ImportError:
    from mcup.client.stdio import StdioServerParameters  # Fallback import
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
async def test_initialize_session(server_params):
    """Test session initialization."""
    async with stdio_client(server_params, approval_mode="cli") as session:
        await session.initialize()
        assert session is not None, "Session should initialize successfully"

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
async def test_fetch_tool(server_params):
    """Test the fetch tool (non-mutating, no prompt)."""
    async with stdio_client(server_params, approval_mode="cli") as session:
        result = await session.call_tool("fetch", arguments={"url": "https://example.com"})
        assert result.content, "Tool call should return content"
        result_unstructured = result.content[0]
        assert isinstance(result_unstructured, types.TextContent), "Result should be TextContent"
        assert "Example Domain" in result_unstructured.text, "Fetch result should include website content"
        assert result.structuredContent == {"url": "https://example.com"}, "Structured result should match"
        print(f"Tool result (fetch): {result_unstructured.text[:100]}...")

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