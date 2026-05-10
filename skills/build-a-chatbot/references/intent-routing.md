# Intent Routing Reference

The embedding-based intent router is an *optional* pre-pass that sits in
front of the LLM. Worth it when you have ≥ 5 high-frequency intents that
account for ~80% of traffic. Skips the LLM round trip entirely on those,
saving ~1s latency and ~$0.01 per request.

## When to add this

Add it when:

- You have ≥ 5 high-frequency intents that cluster cleanly in embedding
  space ("show overdue invoices", "create a quote", "send this to
  customer", etc.).
- Wrong-intent recovery is cheap (the user can say "no, I meant X").
- You're paying meaningful API costs at scale.

Skip it when:

- Tool surface is < 10 tools.
- Most requests are open-ended ("explain why this number is high").
- Intents don't separate cleanly (every example phrase looks similar).

## How it works

```
on boot:
  for each intent in INTENT_DEFINITIONS:
    embed all example_phrases
    centroid = mean(embeddings)
    centroid /= ||centroid||              # L2-normalize
    cache[intent.name] = centroid

on request:
  user_vec = embed(message); user_vec /= ||user_vec||
  scores = {name: dot(user_vec, vec) for name, vec in cache.items()}
  best, runner_up = top-2 by score
  ─ HIGH      if best ≥ 0.85 and (best - runner_up) ≥ 0.05
  ─ AMBIGUOUS if best ≥ 0.70 and (best - runner_up) < 0.05
  ─ MEDIUM    if best ≥ 0.70
  ─ LOW       if best ≥ 0.50
  ─ NO_MATCH  if best < 0.50
```

Cosine similarity = dot product on L2-normalized vectors. Per-request cost:
1 embedding API call (~30ms, ~$0.00002 with `text-embedding-3-small`) + 33
dot products (microseconds).

## Recommended thresholds

| Band | Threshold | Action |
|---|---|---|
| HIGH | ≥ 0.85 | Execute tool directly, no LLM |
| MEDIUM | 0.70–0.84 | Execute with "Going to do X" prefix |
| AMBIGUOUS | top-2 Δ < 0.05 | Ask user to clarify between top-2 |
| LOW | 0.50–0.69 | Fall back to multi-turn LLM with full catalog |
| NO_MATCH | < 0.50 | Same as LOW |

These come from production tuning. Adjust by 0.05 increments based on what
you see in `chat.metrics` logs.

## Intent definitions — the recipe

Each intent gets:

- `name` — must match a tool name in your `ALL_HANDLERS`.
- `description` — used in clarification prompts and metrics.
- `example_phrases` — 5–10 paraphrases. Cover formal/casual, with/without
  arg names, with/without entity names. The more paraphrases, the more
  robust the centroid.
- `requires_pro` — for tier gating in the router.
- `read_only` — for auditor-role gating.
- `is_destructive` — gate behind a confirmation word ("yes", "confirm").

```python
IntentDefinition(
    name="create_customer",
    description="Create a new customer in the system",
    example_phrases=[
        "add a new client",
        "register a customer",
        "create customer named Acme",
        "new contact",
        "save customer details",
        "I need to add someone to my customers",
        "make a new client record",
    ],
    requires_pro=False,
    read_only=False,
    is_destructive=False,
),
```

Empirical sweet spot: 7 phrases per intent. Below 5, centroids are noisy.
Above 10, you're hitting embedding API costs on boot for diminishing returns.

## Fast-path argument extraction

Intent matching tells you *which* tool to call. To skip the LLM entirely,
you also need the *args* — extract them with regex.

```python
INTENT_EXTRACTORS = {
    "get_dashboard_summary":  lambda msg: {},                 # no args
    "get_overdue_invoices":   lambda msg: {},
    "get_followups":          extract_days_ahead,             # → {"days_ahead": 7}
    "search_customers":       extract_query,
    "send_quote":             extract_quote_number,           # → {"quote_number": "Q-..."}
    "delete_customer":        extract_customer_name,
    ...
}
```

Each extractor returns:

- `{}` — no args needed (e.g. `get_dashboard_summary`).
- `{...}` — args extracted successfully.
- `None` — couldn't extract; fall back to LLM.

Combined dispatch:

```python
args = INTENT_EXTRACTORS[intent.name](message)
if args is not None and intent.name in ALL_HANDLERS:
    result = dispatch_tool(user, intent.name, args)   # FAST PATH ✓
else:
    result = chat_service.process_message(message)    # SLOW PATH (LLM)
```

In production, ~80% of requests take the fast path.

## Context fill-in (referential language)

When a user says "send this", "delete it", "show that one", you want the
fast path to still work. The trick: the FE attaches view state to every
request:

```json
{
  "context": {
    "current_quote_number": "Q-202601-0042",
    "current_customer_id": "cus_123"
  }
}
```

The router fills missing args from `context` when:

1. The user message contains a referential pronoun (`this`, `that`, `it`,
   `current`, `these`).
2. The required arg isn't already in the regex extraction.
3. The intent has a known `(arg_name → context_key)` mapping.

```python
CONTEXT_FILL = {
    "send_quote":         ("quote_number", "current_quote_number"),
    "get_quote_details":  ("quote_number", "current_quote_number"),
    "delete_customer":    ("customer_name", "current_customer_name"),
}

def apply_context(intent, args, message, context):
    if not context: return args
    mapping = CONTEXT_FILL.get(intent)
    if not mapping: return args
    arg_name, ctx_key = mapping
    if args is not None and arg_name in args: return args   # already extracted
    if not REFERENTIAL.search(message): return args         # no "this"/"that"/...
    ctx_value = context.get(ctx_key)
    if not ctx_value: return args
    return {**(args or {}), arg_name: ctx_value}
```

Where `REFERENTIAL = re.compile(r"\b(this|that|these|those|it|current)\b", re.I)`.

Result: a user on a quote detail page can say "send this" and skip the LLM.

## Confidence band routing decisions

Don't just route HIGH straight through. Add these guards:

- **Auditor / read-only roles** — block writes regardless of confidence.
- **Pro-gated intents + free user** — return upsell, never execute.
- **Destructive intents without confirmation** — return a confirmation
  prompt with chips ("Yes, delete customer Ada" vs "Cancel").

```python
if intent.read_only is False and user.role == "auditor":
    return {"response": "As an auditor you have read-only access...", ...}

if intent.requires_pro and user.role == "free":
    return {"error_code": "requires_pro", "upsell": {...}, ...}

if intent.is_destructive and not CONFIRMATION_RE.search(message):
    return {"response": f"Just to confirm — {action}? This can't be undone.",
            "suggestions": [
                {"label": f"Yes, {action}", "message": f"Yes, {action} {target}"},
                {"label": "Cancel",         "message": "Cancel that"},
            ]}
```

`CONFIRMATION_RE = re.compile(r"\b(yes|confirm|proceed|do it|delete it|reject it)\b", re.I)`.

## Centroid singleton

Compute centroids once per process, cache forever:

```python
from functools import lru_cache

@lru_cache(maxsize=1)
def get_intent_matcher() -> IntentMatcher:
    return IntentMatcher()   # __init__ pre-computes vectors
```

Boot cost: ~1s for 30 intents × 7 phrases = 210 phrases batched into one
embedding API call. Per-request cost after that: 1 embedding call.

## When to bypass the router

Some intents are special:

- **`navigate`** — short-circuit: if `intent == "navigate"`, return a
  `navigate_to` URL and skip both LLM and tool execution. The FE routes
  there without rendering an assistant message.
- **`general_chat`** — fall through to the LLM with the full catalog. Don't
  let general-chat have a high centroid score (its example phrases are
  usually sparse and conversational).
