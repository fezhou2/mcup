# Changelog

All notable changes to the MCUP library will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2025-08-25

### Added
- Forked from [Model Context Protocol SDK](https://github.com/modelcontextprotocol/python-sdk).
- Added `MCUPSession` in `src/mcup/client/mcup_session.py` with CLI-based user confirmation for mutating tool calls (e.g., tools with names containing 'write', 'delete', 'update', 'create', 'modify') using `approval_mode='cli'`.
- Updated client transports (`sse.py`, `streamable_http.py`, `websocket.py`) to support `MCUPSession` with `approval_mode`.
- Updated `examples/snippets/clients/stdio_client.py` to demonstrate CLI approval for mutating tools.
- Added `examples/mcup/cli_approval.py` for a minimal CLI approval example.
- Added `aioconsole>=0.7.1` dependency for async CLI input.
- Added test suite in `tests/` with `test_mcup_session.py` to verify CLI approval logic.
- Added `examples/servers/fastmcp_quickstart.py` for testing with stdio transport.
- Added `CHANGELOG.md` to document changes.

### Changed
- Renamed package from `mcp` to `mcup` in `pyproject.toml` and imports.
- Updated `README.md` to document MCUP’s CLI approval feature and usage.

## [Unreleased]

- No unreleased changes.

[1.0.0]: https://github.com/fezhou2/mcup/releases/tag/v1.0.0