import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal, TextIO, Optional
from collections.abc import AsyncGenerator

import anyio
import anyio.lowlevel
from anyio.abc import Process
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from anyio.streams.text import TextReceiveStream
from pydantic import BaseModel, Field

import mcup.types as types
from mcup.os.posix.utilities import terminate_posix_process_tree
from mcup.os.win32.utilities import (
    FallbackProcess,
    create_windows_process,
    get_windows_executable_command,
    terminate_windows_process_tree,
)
from mcup.shared.message import SessionMessage
from ..session import ClientSession
from ..mcup_session import MCUPSession

logger = logging.getLogger(__name__)

# Environment variables to inherit by default
DEFAULT_INHERITED_ENV_VARS = (
    [
        "APPDATA",
        "HOMEDRIVE",
        "HOMEPATH",
        "LOCALAPPDATA",
        "PATH",
        "PATHEXT",
        "PROCESSOR_ARCHITECTURE",
        "SYSTEMDRIVE",
        "SYSTEMROOT",
        "TEMP",
        "USERNAME",
        "USERPROFILE",
    ]
    if sys.platform == "win32"
    else ["HOME", "LOGNAME", "PATH", "SHELL", "TERM", "USER"]
)

# Timeout for process termination before falling back to force kill
PROCESS_TERMINATION_TIMEOUT = 2.0

def get_default_environment() -> dict[str, str]:
    """
    Returns a default environment object including only environment variables deemed
    safe to inherit.
    """
    env: dict[str, str] = {}
    for key in DEFAULT_INHERITED_ENV_VARS:
        value = os.environ.get(key)
        if value is None:
            continue
        if value.startswith("()"):
            continue
        env[key] = value
    return env

class StdioServerParameters(BaseModel):
    command: str
    """The executable to run to start the server."""
    args: list[str] = Field(default_factory=list)
    """Command line arguments to pass to the executable."""
    env: dict[str, str] | None = None
    """
    The environment to use when spawning the process.
    If not specified, the result of get_default_environment() will be used.
    """
    cwd: str | Path | None = None
    """The working directory to use when spawning the process."""
    encoding: str = "utf-8"
    """The text encoding used when sending/receiving messages to the server."""
    encoding_error_handler: Literal["strict", "ignore", "replace"] = "strict"
    """The text encoding error handler."""

@asynccontextmanager
async def stdio_client(
    server: StdioServerParameters,
    errlog: TextIO = sys.stderr,
    approval_mode: Optional[str] = None,
) -> AsyncGenerator[ClientSession, None]:
    """
    Stdio client transport for MCP.

    Args:
        server: Parameters for the stdio server (command, args, env).
        errlog: Stream for stderr output (defaults to sys.stderr).
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

    try:
        command = _get_executable_command(server.command)
        process = await _create_platform_compatible_process(
            command=command,
            args=server.args,
            env=({**get_default_environment(), **server.env} if server.env is not None else get_default_environment()),
            errlog=errlog,
            cwd=server.cwd,
        )
    except OSError:
        await read_stream.aclose()
        await write_stream.aclose()
        await read_stream_writer.aclose()
        await write_stream_reader.aclose()
        raise

    async def stdout_reader():
        assert process.stdout, "Opened process is missing stdout"
        try:
            async with read_stream_writer:
                buffer = ""
                async for chunk in TextReceiveStream(
                    process.stdout,
                    encoding=server.encoding,
                    errors=server.encoding_error_handler,
                ):
                    lines = (buffer + chunk).split("\n")
                    buffer = lines.pop()
                    for line in lines:
                        try:
                            message = types.JSONRPCMessage.model_validate_json(line)
                            session_message = SessionMessage(message)
                            await read_stream_writer.send(session_message)
                        except Exception as exc:
                            await read_stream_writer.send(exc)
        except anyio.ClosedResourceError:
            await anyio.lowlevel.checkpoint()

    async def stdin_writer():
        assert process.stdin, "Opened process is missing stdin"
        try:
            async with write_stream_reader:
                async for session_message in write_stream_reader:
                    json = session_message.message.model_dump_json(by_alias=True, exclude_none=True)
                    await process.stdin.send(
                        (json + "\n").encode(
                            encoding=server.encoding,
                            errors=server.encoding_error_handler,
                        )
                    )
        except anyio.ClosedResourceError:
            await anyio.lowlevel.checkpoint()

    async with anyio.create_task_group() as tg, process:
        tg.start_soon(stdout_reader)
        tg.start_soon(stdin_writer)
        try:
            session_class = MCUPSession if approval_mode == "cli" else ClientSession
            async with session_class(
                read_stream,
                write_stream,
                approval_mode=approval_mode,
            ) as session:
                yield session
        finally:
            if process.stdin:
                try:
                    await process.stdin.aclose()
                except Exception:
                    pass
            try:
                with anyio.fail_after(PROCESS_TERMINATION_TIMEOUT):
                    await process.wait()
            except TimeoutError:
                await _terminate_process_tree(process)
            except ProcessLookupError:
                pass
            await read_stream.aclose()
            await write_stream.aclose()
            await read_stream_writer.aclose()
            await write_stream_reader.aclose()

def _get_executable_command(command: str) -> str:
    """Get the correct executable command normalized for the current platform."""
    if sys.platform == "win32":
        return get_windows_executable_command(command)
    else:
        return command

async def _create_platform_compatible_process(
    command: str,
    args: list[str],
    env: dict[str, str] | None = None,
    errlog: TextIO = sys.stderr,
    cwd: Path | str | None = None,
):
    """Creates a subprocess in a platform-compatible way."""
    if sys.platform == "win32":
        process = await create_windows_process(command, args, env, errlog, cwd)
    else:
        process = await anyio.open_process(
            [command, *args],
            env=env,
            stderr=errlog,
            cwd=cwd,
            start_new_session=True,
        )
    return process

async def _terminate_process_tree(process: Process | FallbackProcess, timeout_seconds: float = 2.0) -> None:
    """Terminate a process and all its children using platform-specific methods."""
    if sys.platform == "win32":
        await terminate_windows_process_tree(process, timeout_seconds)
    else:
        assert isinstance(process, Process)
        await terminate_posix_process_tree(process, timeout_seconds)