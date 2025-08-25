import asyncio
import pytest
from anyio.streams.memory import MemoryObjectSendStream, MemoryObjectReceiveStream
from mcup.client.mcup_session import MCUPSession
from mcup.types import CallToolResult
import aioconsole

@pytest.mark.asyncio
async def test_mcup_session_mutating_tool_approval(monkeypatch):
    """Test CLI approval for mutating tool calls."""
    read_stream_writer, read_stream = anyio.create_memory_object_stream(0)
    write_stream, write_stream_reader = anyio.create_memory_object_stream(0)

    async def mock_ainput(prompt):
        print(prompt)  # Simulate CLI prompt
        return "y"  # Approve action

    monkeypatch.setattr(aioconsole, "ainput", mock_ainput)

    session = MCUPSession(read_stream, write_stream, approval_mode="cli")
    result = await session.call_tool("write_data", {"data": "example"})
    assert isinstance(result, CallToolResult), "Expected CallToolResult"

@pytest.mark.asyncio
async def test_mcup_session_mutating_tool_denial(monkeypatch):
    """Test CLI denial for mutating tool calls."""
    read_stream_writer, read_stream = anyio.create_memory_object_stream(0)
    write_stream, write_stream_reader = anyio.create_memory_object_stream(0)

    async def mock_ainput(prompt):
        print(prompt)  # Simulate CLI prompt
        return "n"  # Deny action

    monkeypatch.setattr(aioconsole, "ainput", mock_ainput)

    session = MCUPSession(read_stream, write_stream, approval_mode="cli")
    with pytest.raises(ValueError, match="User denied tool call: write_data"):
        await session.call_tool("write_data", {"data": "example"})

@pytest.mark.asyncio
async def test_mcup_session_non_mutating_tool_no_prompt():
    """Test non-mutating tool calls bypass approval."""
    read_stream_writer, read_stream = anyio.create_memory_object_stream(0)
    write_stream, write_stream_reader = anyio.create_memory_object_stream(0)

    session = MCUPSession(read_stream, write_stream, approval_mode="cli")
    result = await session.call_tool("get_data", {"id": "123"})
    assert isinstance(result, CallToolResult), "Expected CallToolResult"

@pytest.mark.asyncio
async def test_mcup_session_no_approval_mode():
    """Test no prompts when approval_mode is None."""
    read_stream_writer, read_stream = anyio.create_memory_object_stream(0)
    write_stream, write_stream_reader = anyio.create_memory_object_stream(0)

    session = MCUPSession(read_stream, write_stream, approval_mode=None)
    result = await session.call_tool("write_data", {"data": "example"})
    assert isinstance(result, CallToolResult), "Expected CallToolResult"