// chat-service.ts — Multi-turn Anthropic tool-calling loop.
//
// Companion to scripts/python/chat_service.py. Same architecture, Anthropic
// wire format. Uses `claude-opus-4-7` by default; swap for `claude-haiku-4-5`
// for cost-sensitive paths.
//
// SCAFFOLD: imports for `./dispatch-tool` and `./tools` won't resolve until
// you copy this into a real codebase and create those files.

// @ts-nocheck — disabled because this is a SCAFFOLD; remove after adapting.

import Anthropic from "@anthropic-ai/sdk";

import { dispatchTool } from "./dispatch-tool";
import { ALL_TOOLS } from "./tools";   // [{ name, description, input_schema }, ...]

const SYSTEM_PROMPT = `\
You are an AI assistant for [YOUR APP].

When the user asks you to do something, CALL THE APPROPRIATE TOOL. Do NOT
say "I'll do that for you" — those phrases are wasted tokens. Just call
the tool. Only respond in plain text after a tool has returned.

When a tool returns {"error": "requires_pro", ...}, write a brief upsell
linking to /settings/subscription. Do not retry the tool.
`;

const MAX_TURNS = 5;
const MODEL = "claude-opus-4-7";   // or claude-haiku-4-5 for cheaper paths

const client = new Anthropic();

export interface ChatHistoryMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatAction {
  tool: string;
  args: Record<string, unknown>;
  result: unknown;
}

export interface ChatResult {
  response: string;
  actions: ChatAction[];
}

export async function processMessage(
  user: { id: string; role?: string },
  message: string,
  history: ChatHistoryMessage[] = [],
): Promise<ChatResult> {
  // Trim history to last 20 to stay within context budgets.
  const trimmed = history.slice(-20);
  const messages: Anthropic.MessageParam[] = [
    ...trimmed.map((m) => ({ role: m.role, content: m.content })),
    { role: "user", content: message },
  ];

  const actions: ChatAction[] = [];

  for (let turn = 0; turn < MAX_TURNS; turn++) {
    // ### CONDITIONAL TOOLS (Anthropic version) ###
    // On the final turn, omit `tools` to force a text summary.
    const params: Anthropic.MessageCreateParams = {
      model: MODEL,
      max_tokens: 1024,
      system: [
        {
          type: "text",
          text: SYSTEM_PROMPT,
          cache_control: { type: "ephemeral", ttl: "1h" },   // cache the prefix
        },
      ],
      messages,
    };

    if (turn < MAX_TURNS - 1) {
      params.tools = ALL_TOOLS;
      params.tool_choice = { type: "auto" };
    }

    const resp = await client.messages.create(params);

    // Append the assistant content (text + tool_use blocks) BEFORE results.
    messages.push({ role: "assistant", content: resp.content });

    if (resp.stop_reason !== "tool_use") {
      // Done — collect the text and return.
      const textBlocks = resp.content.filter((b) => b.type === "text");
      const text = textBlocks.map((b) => (b as { text: string }).text).join("\n");
      return { response: text, actions };
    }

    // Execute every tool_use block in this assistant message.
    const toolResults: Anthropic.ToolResultBlockParam[] = [];
    for (const block of resp.content) {
      if (block.type !== "tool_use") continue;
      let result: unknown;
      try {
        result = await dispatchTool(user, block.name, block.input as Record<string, unknown>);
      } catch (err: any) {
        result = { error: err?.message ?? String(err), is_error: true };
      }
      actions.push({ tool: block.name, args: block.input as Record<string, unknown>, result });
      toolResults.push({
        type: "tool_result",
        tool_use_id: block.id,
        content: JSON.stringify(result),
      });
    }

    // Reply with all tool results in one user-role message.
    messages.push({ role: "user", content: toolResults });
  }

  return {
    response: "I tried several steps but didn't reach a clean stopping point.",
    actions,
  };
}
