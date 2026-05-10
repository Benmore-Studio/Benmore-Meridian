# Architecture Reference

Full ASCII flows, request/response contracts, observability schema.

## End-to-end flow

```
┌──────────────────────────────────────────────────────────────────┐
│  CHAT UI                                                          │
│  ─ user types in textarea (or speaks via STT)                    │
│  ─ POST {message, history[≤20], context} with auth header        │
└────────────────────┬─────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────────┐
│  CHAT ENDPOINT       (your framework's POST handler)             │
│  ─ require auth                                                  │
│  ─ rate limit (20 req/min default)                               │
│  ─ validate message length ≤ 2000                                │
│  ─ sanitize history (drop role:"system")                         │
│  ─ consume daily quota                                           │
└────────────────────┬─────────────────────────────────────────────┘
                     │
                     ▼  (optional)
┌──────────────────────────────────────────────────────────────────┐
│  INTENT ROUTER                                                    │
│  ─ embed message (text-embedding-3-small)                        │
│  ─ cosine sim against pre-computed centroids                     │
│  ─ band: HIGH | MEDIUM | AMBIGUOUS | LOW | NO_MATCH              │
└────────────────────┬─────────────────────────────────────────────┘
                     │
       ┌─────────────┼──────────────┬──────────┐
       ▼             ▼              ▼          ▼
   HIGH+MEDIUM   AMBIGUOUS    LOW/NO_MATCH    NAVIGATE
       │             │              │          │
       │             │              │          │ (return navigate_to,
       │             │              │          │  no LLM, no message)
       │             │              │          ▼
       │             │              │       END
       │             ▼              │
       │       (return clarify      │
       │        chips, no LLM)      │
       │             ▼              │
       │           END              │
       │                            │
       └────────────┬───────────────┘
                    ▼
┌──────────────────────────────────────────────────────────────────┐
│  MULTI-TURN LOOP   (LLM ↔ tool_calls)                            │
│  ─ first call:  messages + tools + tool_choice="auto"            │
│  ─ for turn in MAX_TURNS:                                        │
│       if no tool_calls → return text                             │
│       for each tool_call: dispatch + append result               │
│       on final turn: omit `tools` to force summary               │
└────────────────────┬─────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────────┐
│  DISPATCH         dispatch_tool(user, name, args)                │
│  ─ unknown name? → {"error": "Unknown tool: ..."}                │
│  ─ Pro-only & free user? → {"error":"requires_pro", ...}         │
│  ─ else: handler(user, args) → {...}                             │
└────────────────────┬─────────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
  NATIVE HANDLERS            MCP-BRIDGED TOOLS
  (your DB, Celery,          (Stripe, GitHub, Slack,
   transactional safety)      internal data lake)
```

## Endpoint contract

### Request

```http
POST /api/v1/chat/
Authorization: Bearer <token>
Content-Type: application/json
Idempotency-Key: <client-generated>

{
  "message": "create a quote for Acme",
  "history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "context": {
    "page": "/app/customers",
    "current_customer_id": "cus_123",
    "current_quote_number": "Q-202601-0042"
  }
}
```

`history` must be ≤ 20 messages. Reject `role: "system"`. `context` is
optional; the FE attaches state from the current view so the backend can
fill missing args via referential language ("send this", "delete it").

### Response

```json
{
  "response": "Created quote Q-202601-0042 for Acme.",
  "actions": [
    {
      "tool": "create_quick_quote",
      "args": {"customer_id": "cus_123", "amount": 5000},
      "result": {"quote_number": "Q-...", "success": true}
    }
  ],
  "confidence": 0.91,
  "intent_matched": "create_quick_quote",
  "suggestions": [
    {"label": "Send to customer", "message": "Send Q-...0042"},
    {"label": "View quote",      "message": "Show Q-...0042"}
  ],
  "navigate_to": null,
  "error_code": null,
  "upsell": null,
  "quota": {"daily_limit": 100, "used_today": 5, "remaining": 95}
}
```

If `navigate_to` is set, the FE routes there *without rendering an assistant
message*. If `error_code: "requires_pro"`, the FE renders `upsell` as a CTA.

## Observability schema

Log one structured line per request to a separate sink (`chat.metrics`):

```json
{
  "ts": "2026-05-10T14:32:11Z",
  "user_id": "u_123",
  "org_id": "o_456",
  "intent": "create_quick_quote",
  "confidence": 0.91,
  "confidence_band": "HIGH",
  "fast_path": true,
  "gpt_fallback": false,
  "tool": "create_quick_quote",
  "destructive_gated": false,
  "access_denied": false,
  "success": true,
  "error": null,
  "latency_ms": 84,
  "message_len": 28
}
```

Plus one row per tool call to a `chat_tool_calls` table:

```sql
create table chat_tool_calls (
  id            bigserial primary key,
  conversation_id text not null,
  turn          int not null,
  user_id       text not null,
  tool_name     text not null,
  source        text not null check (source in ('native', 'mcp')),
  args_json     jsonb,        -- redact PII before insert
  result_json   jsonb,
  is_error      boolean,
  latency_ms    int,
  created_at    timestamptz default now()
);
create index on chat_tool_calls(conversation_id, turn);
create index on chat_tool_calls(user_id, created_at desc);
```

This table is your debugging log + audit trail + golden-conversation
regression corpus all in one.

## File layout (recommended)

```
backend/
└── apps/  (or src/, services/)
    └── chat/
        ├── views.py              ← endpoint
        ├── chat_service.py       ← multi-turn loop
        ├── smart_chat_service.py ← intent routing wrapper (optional)
        ├── intent_matcher.py     ← cosine centroids (optional)
        ├── intent_extractors.py  ← regex fast-path (optional)
        ├── mcp_bridge.py         ← MCP→tool adapter (optional)
        └── chat_tools/
            ├── __init__.py       ← ALL_TOOLS, ALL_HANDLERS, dispatch_tool, gating
            ├── definitions.py    ← schema builder + all schemas
            ├── customer_tools.py ← domain handler module
            ├── order_tools.py
            └── billing_tools.py
```
