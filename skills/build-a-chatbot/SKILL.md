---
name: build-a-chatbot
description: Use when the user wants to build, add, or wire up a chatbot, AI assistant, conversational interface, or LLM tool-calling layer in any codebase — including phrases like "build a chatbot", "add a chatbot to this app", "wire up an AI assistant", "add LLM tool calling", "let users chat with our app", "make an AI helper", "add a Cmd+K assistant", "integrate MCP into the chat", "build an AI assistant for this codebase". Trigger this skill whenever the user is starting from zero or extending an existing chatbot — it walks through codebase survey, vendor selection (OpenAI/Anthropic), architecture choice (native tools / MCP / hybrid), the multi-turn tool-calling loop, dispatch layer with feature gating, optional embedding-based intent routing, optional MCP integration, frontend wiring, and verification. Works in any backend (Django, FastAPI, Express, Rails, Next.js API routes, Spring Boot, etc.) and any frontend (React, Vue, Svelte, mobile). Copy this skill's bundled scaffolds rather than writing from scratch. Use even when the user describes the work in domain terms ("let users ask questions about their orders", "add a support bot", "AI search for our app") — those are all chatbot tasks.
---

# Build a Chatbot

This skill walks you through standing up a production-grade chatbot in any
codebase. It distills the architecture of a working production chatbot
(39 tools, multi-turn GPT-4o, cosine-similarity intent routing, per-org RBAC)
into a vendor-neutral, framework-neutral playbook plus copy-paste scaffolds.

**Before you start coding, read this whole file.** Then jump into references/
and scripts/ as the workflow directs.

---

## When this skill applies

You're being asked to add conversational AI to an app — anything from a Cmd+K
palette to a support bot to "let users ask questions about their data." The
user has APIs (their own), and possibly MCP servers (third-party). Your job is
to wire a chat UI to an LLM that can call those APIs/MCP tools on behalf of
the user.

If the user only wants pure RAG (search over docs, no actions), this skill is
overkill — point them at a vector-store recipe instead. This skill is for
**chatbots that take actions**.

---

## The five-part architecture (always)

```
┌─────────────────────────────────────────────────────────────┐
│  1. CHAT UI               (frontend or terminal)            │
│     ↓ HTTP + auth                                           │
│  2. CHAT ENDPOINT         (validate + rate limit + RBAC)    │
│     ↓                                                       │
│  3. (optional) INTENT ROUTER  (embedding centroids)         │
│     ↓                                                       │
│  4. MULTI-TURN LOOP       (LLM ↔ tool_calls ↔ results)      │
│     ↓                                                       │
│  5. TOOL DISPATCH         (single entry point, feature gate)│
│     ├─ NATIVE handlers (your DB, Celery, etc.)              │
│     └─ MCP-bridged tools (third-party data)                 │
└─────────────────────────────────────────────────────────────┘
```

Three of these — the multi-turn loop, the dispatch layer, and the tool
handlers — are mandatory. Intent router and MCP bridge are optional but
recommended for nontrivial chatbots.

---

## Workflow

Follow these steps in order. Each step has a "verify" checkpoint — don't move
on until it passes. The whole flow takes a senior engineer ~1–2 days for a
basic chatbot, ~1 week including intent router + MCP.

### Step 1 — Survey the codebase

Before writing anything, find out what you're building inside of. Use
`Explore` (or read directly) to determine:

- **Backend framework** — Django, FastAPI, Flask, Express, Rails, Spring,
  Next.js API routes? This tells you where the chat endpoint lives and how
  request lifecycle / auth / RBAC work.
- **Auth model** — JWT? Session cookies? OAuth? Per-user, per-org, per-tenant?
  The dispatch layer needs to know "who is calling" to scope queries.
- **Existing AI usage** — is there already an OpenAI/Anthropic client? A
  chatbot? A vector store? Reuse before reinventing.
- **API surface** — what are the highest-value 5–10 endpoints? Those are
  your first chat tools. Don't try to expose everything on day one.
- **Frontend stack** — React / Vue / Svelte / mobile / Electron / terminal?
  The UI scaffold differs but the request shape is identical.
- **Secrets management** — `.env`, AWS Secrets Manager, Doppler, Vault? You
  need this for the LLM API key and any MCP server credentials.

Write a short summary of what you found before proceeding. It should fit in
~10 lines and answer: *Where does the chat endpoint go? Who can call it?
What 5 tools do I expose first? Which LLM vendor and why?*

### Step 2 — Pick the architecture

Three patterns. Default to **Pattern C (Hybrid)** for any nontrivial app.

- **Pattern A — Native tools only.** Tools live in your repo, dispatch
  in-process. Best when all tools touch your own DB and you don't share
  with other LLM hosts. Lowest latency.
- **Pattern B — MCP only.** All tools come from MCP servers. Best when the
  same tools need to work in Claude Desktop, Cursor, *and* your app. Higher
  latency.
- **Pattern C — Hybrid (recommended).** Native handlers for tightly coupled
  domain ops (create/update/delete on your DB, transactional safety
  matters). MCP servers for third-party data (Stripe, GitHub, Slack,
  QuickBooks, internal data warehouses).

For more nuance see `references/architecture.md`.

### Step 3 — Pick the vendor and scaffold the LLM client

Both OpenAI and Anthropic work. The scaffolds support both. Pick based on:

- **OpenAI** — broader ecosystem, automatic prompt caching, strict mode for
  guaranteed JSON. Default to GPT-4o for quality, GPT-4o-mini for cost.
- **Anthropic** — better citation API, explicit `cache_control` for fine
  control, often stronger long-context reasoning. Default to Claude Opus
  4.7 (1M ctx) for quality, Claude Haiku 4.5 for cost.

The wire formats differ; see `references/vendor-cheatsheet.md` for a side-by-
side. The scaffold in `scripts/python/chat_service.py` is OpenAI-shaped;
`scripts/typescript/chat-service.ts` is Anthropic-shaped. Mix and match.

Initialize the client in a singleton (`@lru_cache`d in Python, module-scoped
in TS) so you reuse the HTTP connection pool. Read the API key from your
existing secrets pipeline, never hardcode.

### Step 4 — Copy the dispatch layer

This is the centralized entry point for every tool call. **Copy
`scripts/python/dispatch_tool.py`** (or the TS equivalent) into your codebase
and adapt the imports. It does three things:

1. Looks up the handler by name.
2. Checks feature gating (Pro-only, role-based, etc.) **before** the handler
   runs. Returns a structured `{"error": "requires_pro", "feature": ...,
   "message": ...}` envelope on denial.
3. Calls the handler with `(user, args)`.

**Why centralized:** the model sees the full tool catalog; the dispatcher
enforces RBAC server-side. Never gate tools by hiding them from the model —
that's bypassable. Gate at dispatch.

### Step 5 — Define first-party tools

Group tools by domain (e.g. `customer_tools.py`, `order_tools.py`,
`billing_tools.py`). Each module exports:

```python
HANDLERS = {
    "tool_name": handler_function,  # signature: (user, args: dict) -> dict
}
```

Each handler:

- Takes `(user, args: dict)` and returns a JSON-serializable dict.
- Scopes every DB query by `user.organization_id` (or your tenant key).
- Returns a clean envelope: `{...result..., "success": True}` on write,
  `[...]` or `{...}` on read, `{"error": "..."}` on user-level failures.
- Lets programming bugs (`AttributeError`, `KeyError`) propagate to your
  error tracker — only catch domain exceptions.

Write 3–5 tools first. Validate the loop end-to-end before adding more.

The full recipe (schema → handler → registration → parity check) is in
`references/adding-tools.md`. The starter scaffold is in
`scripts/python/chat_tools_template/`.

### Step 6 — Wire the multi-turn loop

**Copy `scripts/python/chat_service.py`.** This is the canonical multi-turn
tool-calling loop with the *conditional `tools` kwarg* fix (lines marked with
`### CONDITIONAL ###`). The fix matters — explicit `tools=None` is rejected
by the OpenAI API, so on the final turn you must omit the kwarg entirely.

The loop:

1. First call: `messages + tools + tool_choice="auto"`.
2. While model emits `tool_calls` and `turn < MAX_TURNS`:
   - Append assistant's tool_calls message.
   - For each tool_call: dispatch, append tool result.
   - On final turn (`turn == MAX_TURNS - 1`): omit `tools` to force a text
     summary.
3. Return `{response, actions}`.

Bound `MAX_TURNS` (5 is a good default). Add an anti-hedge instruction to
the system prompt — see `assets/system-prompt-template.md`.

### Step 7 — Add the chat endpoint

A single POST endpoint. Required behavior:

- Auth required (whatever your auth is — JWT, session, etc.).
- Rate limit: 20 req/min per user is a reasonable start.
- Validate `message` length (≤ 2000 chars).
- Sanitize `history` — only allow `role ∈ {"user", "assistant"}`, reject
  `"system"` (prompt injection).
- Optional `context` dict for FE state ("user is on quote page Q-...").
- Optional daily quota check (so a runaway loop doesn't burn $$$).

Request/response shape is in `references/architecture.md` § "Endpoint
contract".

### Step 8 — Verify the loop end-to-end (don't skip)

Before moving on, prove the loop works:

1. **Parity check** — every schema name has a handler:
   ```python
   from chat_tools import ALL_TOOLS, ALL_HANDLERS
   defs = {t["function"]["name"] for t in ALL_TOOLS}
   handlers = set(ALL_HANDLERS)
   assert defs == handlers, defs ^ handlers
   ```
2. **Curl smoke test** — hit the endpoint with a known intent ("create a test
   customer named Ada"). Expect `200`, an `actions` array with the tool
   call, and a DB row.
3. **Multi-turn smoke test** — give a prompt that requires chaining
   ("create a quote for the customer Ada and add a $500 line item"). Watch
   the logs — you should see ≥ 2 tool calls in one request. If the model
   says "I'll do that for you" in plain text and stops, your anti-hedge
   prompt is missing or weak.

### Step 9 — (Optional but recommended) Add the intent router

Worth it when you have ≥ 5 high-frequency intents. Skips the LLM entirely
on common requests, saving 80%+ of API costs and ~1s latency.

Copy `scripts/python/intent_matcher.py` and `scripts/python/intent_extractors.py`. Define your intents (~5–10 example phrases each), let the matcher pre-compute
centroids on first use, route by confidence band:

- HIGH (≥ 0.85): execute directly via `dispatch_tool`.
- MEDIUM (0.70–0.84): execute with a "Going to do X" prefix.
- AMBIGUOUS (top-2 Δ < 0.05): ask user to clarify.
- LOW / NONE: fall back to the multi-turn LLM loop.

For destructive intents (`delete_customer`, `cancel_subscription`), require a
confirmation word ("yes", "confirm", "proceed") before executing.

Deeper guidance in `references/intent-routing.md`.

### Step 10 — (Optional) Add MCP integration

Add MCP servers when you need third-party data (Stripe, GitHub, Slack,
internal data lake) and the data lives outside your transactional DB.

- For third parties with official MCP servers: install and configure them.
- For your internal data: build a server with `scripts/python/fastmcp_server.py`.
- Bridge MCP tools into the same `dispatch_tool` surface using
  `scripts/python/mcp_bridge.py` — list MCP tools at boot, convert schemas to
  the LLM's tool format, register alongside native tools with an `mcp:`
  prefix in the name.

This is Pattern C in action. To `chat_service.py`, MCP tools look identical
to native tools — same dispatch, same logging, same gating.

Full primer + transports + OAuth in `references/mcp-integration.md`.

### Step 11 — Frontend

A chat component needs to:

- POST `{message, history[≤20], context}` to the chat endpoint with auth.
- Auto-refresh the auth token on 401, then retry.
- Render the assistant response, plus any *suggestion chips* the backend
  returned (3 short follow-up prompts, click → new request).
- If the backend returns `navigate_to`, route to it *without* rendering an
  assistant message. This avoids "I'm taking you there" clutter.
- On `error_code: "requires_pro"`, render the upsell payload as an inline
  CTA, not as raw error text.

The TS scaffold in `scripts/typescript/chat-component.tsx` is React-shaped
but trivial to port. The request/response contract is identical regardless
of framework.

### Step 12 — Verify and ship

Before declaring victory:

- Run the parity check (Step 8).
- Run a 5-prompt golden conversation test — record real prompts, assert the
  model emitted tool calls from a known allowlist, never assert the model's
  exact text. Save these for regression.
- Check the logs for *every* tool call: `(conversation_id, turn, tool_name,
  args, result_or_error, latency_ms)`. This is your debugging log + audit
  trail + golden corpus.
- Hit the endpoint with a free user and a Pro user (or your equivalent
  tiers) and confirm gating works.

`references/verification-checklist.md` has the full list.

---

## Production gotchas (read these — they bite)

1. **The `tools=None` trap.** Both vendors reject explicit `tools=None`. To
   omit tools on the final turn, omit the kwarg entirely. The scaffold
   does this.
2. **The hedge-and-stop trap.** Without a strong anti-hedge prompt, the
   model says "I'll do that for you" and stops *without calling the tool*.
   Use the system prompt in `assets/system-prompt-template.md`.
3. **Infinite loops.** Cap `MAX_TURNS` (3–6) and dedupe identical
   `(name, normalized_args)` calls. A documented Claude Code recursion
   incident burned 1.67B tokens before someone hit Ctrl+C.
4. **Idempotency.** Every write tool gets a server-generated idempotency
   key the LLM never sees: hash of `(user_id, tool_name, normalized_args,
   conversation_id)`. Stripe-style. Otherwise a transient retry duplicates
   work.
5. **Prompt caching.** Put the system prompt + tool list at the top of the
   message array. OpenAI caches it automatically; Anthropic needs explicit
   `cache_control: {type: "ephemeral", ttl: "1h"}`. With ~30+ tools the
   prefix is 3–5k tokens — caching it pays for itself within 2 turns.
6. **Don't trust the model for auth.** Gate at dispatch. Returning a
   `requires_pro` envelope from the dispatcher is fine; expecting the model
   to "know" not to call a Pro tool is not.
7. **History role allowlist.** Only accept `user` and `assistant` in
   submitted history. Rejecting `system` blocks a class of prompt
   injection.
8. **Sanitize args before logging.** PII in args (emails, phones) shouldn't
   land in cleartext logs. Hash or redact.

---

## Reference files (read as needed)

- `references/architecture.md` — full ASCII flows, request/response
  contract, observability schema.
- `references/vendor-cheatsheet.md` — OpenAI vs Anthropic schema diffs,
  `tool_choice`, parallel calls, caching TTLs.
- `references/intent-routing.md` — embedding centroid pre-pass, when to
  use it, threshold tuning, fast-path arg extraction.
- `references/mcp-integration.md` — MCP primer, transports, OAuth 2.1,
  bridging MCP tools into your existing dispatcher.
- `references/adding-tools.md` — the recipe for adding a new tool
  (schema → handler → register → parity check → smoke test).
- `references/verification-checklist.md` — the pre-ship checklist.

## Scaffolds (copy and adapt)

- `scripts/python/chat_service.py` — multi-turn loop with conditional
  `tools` kwarg fix.
- `scripts/python/dispatch_tool.py` — central dispatch + feature gating.
- `scripts/python/intent_matcher.py` — cosine centroid intent matcher.
- `scripts/python/intent_extractors.py` — regex fast-path arg extraction.
- `scripts/python/mcp_bridge.py` — MCP client → tool list adapter.
- `scripts/python/fastmcp_server.py` — minimal MCP server template.
- `scripts/python/chat_tools_template/` — domain-module starter
  (`__init__.py`, `definitions.py`, `example_tools.py`).
- `scripts/typescript/chat-service.ts` — Anthropic-shaped multi-turn loop.
- `scripts/typescript/mcp-bridge.ts` — MCP → Anthropic tools bridge.
- `scripts/typescript/chat-component.tsx` — React chat UI starter.
- `assets/system-prompt-template.md` — anti-hedge system prompt.

These are starting points, not final code. Copy them into your codebase,
adapt imports/types/auth, and edit freely. The skeletons exist to save you
from rediscovering the gotchas above.
