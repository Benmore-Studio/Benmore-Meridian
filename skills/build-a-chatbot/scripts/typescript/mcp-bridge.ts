// mcp-bridge.ts — MCP client → Anthropic tools bridge.
//
// Connects to one or more MCP servers, lists their tools, and exposes them
// as Anthropic tool schemas (1:1 mapping). Drop the bridged tools into your
// existing tool list before calling `client.messages.create`.
//
// SCAFFOLD: The MCP SDK is required for this file to type-check. Install
// with `npm install @modelcontextprotocol/sdk`. Adapt imports for your build
// system (ESM vs CommonJS).

// @ts-nocheck — disabled because this is a SCAFFOLD.

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

export interface ServerConfig {
  name: string;                       // logical name; used as prefix
  transport: "stdio" | "http";
  // stdio:
  command?: string;
  args?: string[];
  env?: Record<string, string>;
  // http:
  url?: string;
  headers?: Record<string, string>;
}

export interface AnthropicTool {
  name: string;
  description: string;
  input_schema: Record<string, unknown>;
}

export class MCPBridge {
  private clients = new Map<string, Client>();
  private toolToServer = new Map<string, string>();   // mcp:srv:tool → srv
  private toolMeta = new Map<string, AnthropicTool>(); // mcp:srv:tool → schema

  constructor(private configs: ServerConfig[]) {}

  async connectAll(): Promise<void> {
    for (const cfg of this.configs) {
      try {
        const client = new Client({ name: "my-chatbot-bridge", version: "1.0.0" });
        const transport =
          cfg.transport === "stdio"
            ? new StdioClientTransport({
                command: cfg.command!,
                args: cfg.args,
                env: cfg.env,
              })
            : new StreamableHTTPClientTransport(new URL(cfg.url!), {
                requestInit: cfg.headers ? { headers: cfg.headers } : undefined,
              });
        await client.connect(transport);
        this.clients.set(cfg.name, client);

        const { tools } = await client.listTools();
        for (const t of tools) {
          const fullName = `mcp:${cfg.name}:${t.name}`;
          this.toolToServer.set(fullName, cfg.name);
          this.toolMeta.set(fullName, {
            name: fullName,
            description: t.description ?? "",
            input_schema: (t.inputSchema as Record<string, unknown>) ?? { type: "object" },
          });
        }
      } catch (err) {
        console.error(`Failed to connect MCP server ${cfg.name}:`, err);
      }
    }
  }

  /** All bridged MCP tools in Anthropic format. Concat with your native tools. */
  listAnthropicTools(): AnthropicTool[] {
    return Array.from(this.toolMeta.values());
  }

  /** Call an MCP tool. `fullName` is `mcp:<server>:<tool>`. */
  async dispatch(fullName: string, args: Record<string, unknown>): Promise<unknown> {
    const serverName = this.toolToServer.get(fullName);
    if (!serverName) return { error: `Unknown MCP tool: ${fullName}` };
    const client = this.clients.get(serverName);
    if (!client) return { error: `MCP server '${serverName}' not connected.` };

    const toolName = fullName.split(":").slice(2).join(":");
    try {
      const result = await client.callTool({ name: toolName, arguments: args });
      return {
        is_error: result.isError ?? false,
        content: result.content,
      };
    } catch (err: any) {
      return { error: `MCP tool failed: ${err?.message ?? err}` };
    }
  }

  async closeAll(): Promise<void> {
    for (const client of this.clients.values()) {
      try {
        await client.close();
      } catch (err) {
        console.error("Error closing MCP client:", err);
      }
    }
    this.clients.clear();
  }
}
