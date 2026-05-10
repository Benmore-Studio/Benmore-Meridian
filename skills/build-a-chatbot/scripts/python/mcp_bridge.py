# pyright: reportPossiblyUnboundVariable=false, reportCallIssue=false, reportMissingImports=false
# Note: This is a SCAFFOLD. The MCP SDK is optional; imports are wrapped in
# try/except so the rest of the chatbot still works without it. Type-checker
# warnings about possibly-unbound names are expected — at runtime the code
# is gated behind `_MCP_AVAILABLE`.
"""
mcp_bridge.py — MCP client → OpenAI/Anthropic tool adapter.

Connects to one or more MCP servers, lists their tools, converts schemas
to OpenAI function-calling format, and exposes a `dispatch()` method that
your `dispatch_tool` can route to.

Usage:

    bridge = MCPBridge([
        {"name": "stripe",     "transport": "http", "url": "https://mcp.stripe.com/mcp",
         "headers": {"Authorization": f"Bearer {STRIPE_MCP_TOKEN}"}},
        {"name": "filesystem", "transport": "stdio", "command": "mcp-server-filesystem",
         "args": ["/var/data"]},
    ])
    await bridge.connect_all()

    # Add MCP tools to your existing ALL_TOOLS:
    ALL_TOOLS_WITH_MCP = ALL_TOOLS + bridge.list_openai_tools()

    # In dispatch_tool:
    if name.startswith("mcp:"):
        return await bridge.dispatch(name, args)

Names are prefixed: "mcp:<server_name>:<tool_name>" to avoid collisions.

NOTE: This file uses async because the MCP Python SDK is async-first. If
your codebase is sync (Django sync views), wrap calls in `asgiref.sync.async_to_sync`
or run the bridge in a separate event loop.

References:
  - https://modelcontextprotocol.io
  - pip install mcp  (Python SDK 1.x)
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


# These imports require `pip install mcp`.
# Wrapped in try/except so the rest of the chatbot still works without MCP.
# Note: the SDK has shipped two streamable-http symbol names; the current
# stable name is `streamable_http_client`. Fall back to the older name for
# compatibility with older SDK pins.
try:
    from mcp import ClientSession
    from mcp.client.stdio import stdio_client, StdioServerParameters
    try:
        from mcp.client.streamable_http import streamable_http_client as streamable_http
    except ImportError:  # older SDK
        from mcp.client.streamable_http import streamablehttp_client as streamable_http
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False
    logger.warning("mcp package not installed; MCPBridge disabled.")


class MCPBridge:
    """Connects to MCP servers and exposes their tools to the chatbot."""

    def __init__(self, server_configs: list[dict]) -> None:
        if not _MCP_AVAILABLE:
            raise RuntimeError("Install `mcp` package to use MCPBridge.")
        self.server_configs = server_configs
        self.sessions: dict[str, ClientSession] = {}    # name → session
        self.tools_by_name: dict[str, dict] = {}        # mcp:<srv>:<tool> → schema
        self._tool_to_server: dict[str, str] = {}       # mcp:<srv>:<tool> → server_name

    # ---------- lifecycle --------------------------------------------------

    async def connect_all(self) -> None:
        """Connect to every configured server and cache its tool list."""
        for cfg in self.server_configs:
            name = cfg["name"]
            try:
                session = await self._connect_one(cfg)
                self.sessions[name] = session
                tools_resp = await session.list_tools()
                for t in tools_resp.tools:
                    full_name = f"mcp:{name}:{t.name}"
                    self.tools_by_name[full_name] = {
                        "name": t.name,
                        "description": t.description or "",
                        "input_schema": t.inputSchema or {"type": "object"},
                    }
                    self._tool_to_server[full_name] = name
                logger.info("MCP %s connected, %d tools", name, len(tools_resp.tools))
            except Exception:
                logger.exception("Failed to connect MCP server %s", name)

    async def _connect_one(self, cfg: dict) -> ClientSession:
        transport = cfg.get("transport", "stdio")
        if transport == "stdio":
            params = StdioServerParameters(
                command=cfg["command"],
                args=cfg.get("args", []),
                env=cfg.get("env"),
            )
            ctx = stdio_client(params)
        elif transport == "http":
            ctx = streamable_http(
                cfg["url"],
                headers=cfg.get("headers"),
            )
        else:
            raise ValueError(f"Unknown MCP transport: {transport}")

        # NOTE: Production code should manage lifetimes via async context.
        # This simplified version assumes long-lived sessions for the
        # duration of the process.
        read, write, *_ = await ctx.__aenter__()
        session = ClientSession(read, write)
        await session.initialize()
        return session

    async def close_all(self) -> None:
        # ClientSession lifetime is normally managed by the transport's
        # async context manager. If you used __aenter__ above, you should
        # call __aexit__ on the same context. This simplified shim assumes
        # process-lifetime sessions; for production use, manage lifetimes
        # explicitly with `async with`.
        self.sessions.clear()

    # ---------- schema conversion ------------------------------------------

    def list_openai_tools(self) -> list[dict]:
        """Return all bridged MCP tools in OpenAI function-calling format.

        Add these to your existing ALL_TOOLS before sending to the LLM.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": full_name,
                    "description": meta["description"],
                    "parameters": meta["input_schema"],
                },
            }
            for full_name, meta in self.tools_by_name.items()
        ]

    def list_anthropic_tools(self) -> list[dict]:
        """Same in Anthropic format (input_schema instead of parameters)."""
        return [
            {
                "name": full_name,
                "description": meta["description"],
                "input_schema": meta["input_schema"],
            }
            for full_name, meta in self.tools_by_name.items()
        ]

    # ---------- dispatch ---------------------------------------------------

    async def dispatch(self, full_name: str, args: dict) -> Any:
        """Call an MCP tool. `full_name` is `mcp:<server>:<tool>`."""
        if full_name not in self._tool_to_server:
            return {"error": f"Unknown MCP tool: {full_name}"}

        server_name = self._tool_to_server[full_name]
        session = self.sessions.get(server_name)
        if session is None:
            return {"error": f"MCP server '{server_name}' is not connected."}

        # Strip the "mcp:<server>:" prefix; the server expects the bare tool name.
        tool_name = full_name.split(":", 2)[2]

        try:
            result = await session.call_tool(tool_name, arguments=args)
            # MCP returns content blocks; flatten to a JSON-able dict.
            return {
                "is_error": result.isError,
                "content": [
                    {"type": c.type, "text": getattr(c, "text", None)}
                    for c in result.content
                ],
            }
        except Exception as exc:
            logger.exception("MCP tool %s failed", full_name)
            return {"error": f"MCP tool failed: {exc}"}
