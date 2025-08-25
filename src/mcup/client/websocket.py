import json
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Optional

import anyio
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from pydantic import ValidationError
from websockets.asyncio.client import connect as ws_connect
from websockets.typing import Subprotocol

import mcup.types as types
from mcup.shared.message import SessionMessage
from .session import ClientSession
from .mcup_session import MCUPSession

logger = logging.getLogger(__name__)

@asynccontextmanager
async def websocket_client(
    url: str,
    approval_mode: Optional[str] = None,
) -> AsyncGenerator[ClientSession, None]:
    """
    WebSocket client transport for MCP, symmetrical to the server version.

    Connects to 'url' using the 'mcp' subprotocol, yielding a ClientSession or MCUPSession instance.

    Args:
        url: The WebSocket endpoint URL (e.g., ws://localhost:8000).
        approval_mode: Optional mode for approving mutating tool calls ('cli' for CLI prompts, None to disable).

    Yields:
        ClientSession or MCUPSession instance for interacting with the server.
    """
    read_stream: MemoryObjectReceiveStream[SessionMessage | Exception]
    read_stream_writer: MemoryObjectSendStream[SessionMessage | Exception]
    write_stream: MemoryObjectSendStream[SessionMessage]
    write_stream_reader: MemoryObjectReceiveStream[SessionMessage]

    read_stream_writer, read_stream = anyio.create_memory_object_stream(0)
    write_stream, write_stream_reader = anyio.create_memory_object_stream(0)

    async with ws_connect(url, subprotocols=[Subprotocol("mcp")]) as ws:
        async def ws_reader():
            """
            Reads text messages from the WebSocket, parses them as JSON-RPC messages,
            and sends them into read_stream_writer.
            """
            async with read_stream_writer:
                async for raw_text in ws:
                    try:
                        message = types.JSONRPCMessage.model_validate_json(raw_text)
                        session_message = SessionMessage(message)
                        await read_stream_writer.send(session_message)
                    except ValidationError as exc:
                        await read_stream_writer.send(exc)

        async def ws_writer():
            """
            Reads JSON-RPC messages from write_stream_reader and
            sends them to the server.
            """
            async with write_stream_reader:
                async for session_message in write_stream_reader:
                    msg_dict = session_message.message.model_dump(by_alias=True, mode="json", exclude_none=True)
                    await ws.send(json.dumps(msg_dict))

        async with anyio.create_task_group() as tg:
            tg.start_soon(ws_reader)
            tg.start_soon(ws_writer)
            session_class = MCUPSession if approval_mode == "cli" else ClientSession
            async with session_class(
                read_stream,
                write_stream,
                approval_mode=approval_mode,
            ) as session:
                yield session
            tg.cancel_scope.cancel()