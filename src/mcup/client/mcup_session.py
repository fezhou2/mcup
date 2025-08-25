import logging
from typing import Any, Optional, Set
from aioconsole import ainput  # For async CLI input

from .session import ClientSession, ProgressFnT
from mcup.types import CallToolResult

logger = logging.getLogger("client")

class MCUPSession(ClientSession):
    def __init__(
        self,
        read_stream,
        write_stream,
        read_timeout_seconds=None,
        sampling_callback=None,
        elicitation_callback=None,
        list_roots_callback=None,
        logging_callback=None,
        message_handler=None,
        client_info=None,
        approval_mode: Optional[str] = None,
        mutating_tool_keywords: Set[str] = {"write", "delete", "update", "create", "modify"},
    ) -> None:
        """Initialize an MCUP session with optional CLI approval for mutating tool calls."""
        super().__init__(
            read_stream,
            write_stream,
            read_timeout_seconds=read_timeout_seconds,
            sampling_callback=sampling_callback,
            elicitation_callback=elicitation_callback,
            list_roots_callback=list_roots_callback,
            logging_callback=logging_callback,
            message_handler=message_handler,
            client_info=client_info or types.Implementation(name="mcup", version="0.1.0"),
        )
        self.approval_mode = approval_mode
        self._mutating_tool_keywords = mutating_tool_keywords

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
        read_timeout_seconds=None,
        progress_callback: Optional[ProgressFnT] = None,
    ) -> CallToolResult:
        """Send a tools/call request, prompting for approval if the tool is mutating."""
        is_mutating = any(keyword in name.lower() for keyword in self._mutating_tool_keywords)
        if is_mutating and self.approval_mode == "cli":
            logger.debug(f"Requesting approval for tool call: {name}")
            details = {"tool_name": name, "arguments": arguments or {}}
            prompt = f"Approve MCUP tool call?\nDetails: {details}\n(y/n): "
            try:
                user_input = await ainput(prompt)
                approved = user_input.strip().lower() == 'y'
                logger.info(f"[tool call] {'Approved' if approved else 'Denied'}: {details}")
                if not approved:
                    raise ValueError(f"User denied tool call: {name}")
            except Exception as e:
                logger.error(f"Approval error: {e}")
                raise
        return await super().call_tool(name, arguments, read_timeout_seconds, progress_callback)