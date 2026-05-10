# MCP Integration Reference

Model Context Protocol (MCP) is Anthropic's open standard (Nov 2024) for
giving LLM hosts a uniform plug-in surface. As of 2026 it's stable enough
to use in production for third-party data integrations.

## TL;DR

- An MCP **server** exposes tools/resources/prompts over JSON-RPC (stdio
  for local, Streamable HTTP for remote).
- Your chatbot is an MCP **host**; you instantiate one **client** per
  server.
- MCP tools map ~1:1 to OpenAI/Anthropic tools — wrap them in a small
  bridge and they look identical to native handlers.
- Use MCP for third-party data (Stripe, GitHub, Slack, internal warehouses).
- Keep tightly coupled domain ops (your DB writes) as native handlers — the
  ORM transaction story is cleaner.

## Three primitives

| Primitive | Shape | Equivalent in raw LLM API |
|---|---|---|
| **Tool** | name + description + JSON-Schema input | OpenAI `function` / Anthropic `tool` |
| **Resource** | URI + content (`stripe://customers/123`) | *no equivalent* — host inlines into context |
| **Prompt** | server-supplied template | *no equivalent* — host renders as slash-command |

For a chatbot you mostly care about tools. Resources are useful for showing
the user "@mention" pickers (a file list, a customer list). Prompts are
useful for slash-menu shortcuts.

## Three transports

| Transport | Use case |
|---|---|
| **stdio** | Local subprocess. Zero network surface. Default for Claude Desktop. |
| **Streamable HTTP** | Remote servers. Single endpoint, POST + GET, optional SSE upgrade, `Mcp-Session-Id` header. |
| **HTTP+SSE** | Legacy (pre-2025-03-26). Deprecated. |

For a chatbot, you'll almost always use Streamable HTTP for remote third-
party servers and stdio for any local-only tools.

## Authorization (remote servers, 2026 spec)

Public remote MCP servers must implement:

- **OAuth 2.1 + PKCE** — no static API keys.
- **RFC 8707 Resource Indicators** — audience-bind the access token to the
  specific server URL.
- **RFC 9728 Protected Resource Metadata** — expose
  `/.well-known/oauth-protected-resource`.

For your own first-party MCP servers (running inside your VPC), bearer
tokens or mTLS are fine — the spec only mandates OAuth for *public* servers.

## When to add MCP to a chatbot

Add MCP when:

- You're integrating a third party that has an official MCP server (Stripe,
  GitHub, Slack, Linear, Postgres, filesystem).
- You want the same tools to work in Claude Desktop / Cursor for ops staff
  *and* in your in-app chatbot. MCP is the only layer that achieves this.
- You're building internal data-warehouse access where the tool contract
  changes outside your release cycle.

Skip MCP when:

- All your tools are CRUD on your own DB. Native handlers are simpler,
  faster, and have transactional safety.
- The third party doesn't have an MCP server and you don't want to build
  one. A direct REST call from a native handler is fine.

## The bridge pattern

The cleanest way to integrate MCP without disturbing your existing dispatch
layer: at boot, list all MCP tools, convert their schemas to your LLM's tool
format, and register them in `ALL_TOOLS` and `ALL_HANDLERS` with an `mcp:`
prefix in the name.

```python
# scripts/python/mcp_bridge.py (already provided)

class MCPBridge:
    def __init__(self, server_configs: list[dict]):
        self.clients = {}            # server_name → Client
        self.tools_by_name = {}      # mcp:server:tool → server_name
        # connect to each server, list tools, register
        ...

    def list_openai_tools(self) -> list[dict]:
        """Return MCP tools in OpenAI function-calling format."""
        return [...]

    def dispatch(self, name: str, args: dict) -> dict:
        """name = 'mcp:stripe:get_customer' → routes to Stripe MCP client."""
        ...
```

In your `dispatch_tool`:

```python
def dispatch_tool(user, name, args):
    if name.startswith("mcp:"):
        return mcp_bridge.dispatch(name, args)   # MCP path
    # ... native path
```

Result: to `chat_service.py`, MCP tools look identical to native tools.
Same logging, same gating, same retry policy.

## MCP server hosting options

For first-party MCP servers (your data, your tools):

1. **Inline in your monolith** — same Python/Node process as your API. Fast
   to deploy, no extra infra. Run `python -m my_mcp_server` as a sidecar.
2. **Standalone microservice** — separate service, separate scaling. Better
   if traffic patterns differ from your main API.
3. **Cloudflare Workers / Vercel Edge** — serverless, low ops. Good for
   stateless data lookups.

For third-party servers, use the official ones from
`github.com/modelcontextprotocol/servers` (filesystem, git, postgres,
sqlite, GitHub, Slack, Brave Search, Puppeteer). Note: those are labeled
educational, not production-ready — review the code before deploying.

## Building a minimal server (Python FastMCP)

`scripts/python/fastmcp_server.py` has a complete example. The shape:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-pricing")

@mcp.tool()
def lookup_price(item_name: str, province: str = "ON") -> dict:
    """Look up a Home Depot Canada price for a construction material."""
    return {"item": item_name, "province": province, "price_cad": 4.97}

@mcp.resource("pricing://catalog")
def catalog() -> str:
    """The full pricing catalog as CSV."""
    return "name,unit,price\n..."

if __name__ == "__main__":
    mcp.run()                              # stdio
    # mcp.run(transport="streamable-http") # remote
```

`FastMCP` auto-generates JSON Schema from the type hints + docstring.

## Building a minimal client (TypeScript)

`scripts/typescript/mcp-bridge.ts` has the canonical bridge.
The shape:

```typescript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

const transport = new StreamableHTTPClientTransport(new URL("https://mcp.example.com/mcp"));
const mcp = new Client({ name: "my-bridge", version: "1.0.0" });
await mcp.connect(transport);

const { tools } = await mcp.listTools();
// tools is [{name, description, inputSchema}, ...] — convert to your LLM's tool format
```

## Production gotchas

1. **Latency.** Each MCP tool call is a network round trip. For frequently-
   called tools, consider caching the result for 30–60s.
2. **Schema drift.** MCP servers can update their tool list at runtime via
   `tools/list_changed` notifications. Either subscribe and re-register, or
   reconnect on startup only and accept the limitation.
3. **Auth scopes.** OAuth scopes you grant to the MCP token become the
   model's authority. Be conservative — read-only by default.
4. **Don't expose your DB through MCP.** That's what your native handlers
   are for. MCP is for third-party / cross-host scenarios.
5. **Rate limits.** Many third-party MCP servers rate-limit aggressively.
   Wrap calls in retry-with-jitter; surface the rate-limit error to the
   model so it can apologize gracefully.
6. **Connection pooling.** Streamable HTTP supports session reuse via
   `Mcp-Session-Id`. Reuse one session per server per process.

## Claude Desktop / Claude Code integration

If you also want the same MCP servers to work in Claude Desktop or
Claude Code, configure them in:

- **Claude Desktop**:
  `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Claude Code**:
  `.mcp.json` at the project root (per-project config).

Format:

```json
{
  "mcpServers": {
    "my-pricing": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "my_pricing_mcp_server"]
    },
    "remote-stripe": {
      "type": "http",
      "url": "https://mcp.stripe.com/mcp",
      "headers": {"Authorization": "Bearer ${STRIPE_MCP_TOKEN}"}
    }
  }
}
```

Same servers can power your in-app chatbot via the bridge — that's the
point of MCP.

## Observability

Log MCP tool calls just like native ones, but tag `source: "mcp"` and
include `server: "stripe"` in the structured log. This lets you slice the
metrics dashboard by source and quickly spot when a third party is the
bottleneck or the source of errors.
