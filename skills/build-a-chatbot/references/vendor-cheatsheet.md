# Vendor Cheatsheet — OpenAI vs Anthropic

Both vendors converged on the same conceptual loop. Wire formats differ
enough that you need a small adapter for vendor portability.

## Side-by-side schema

| Concept | OpenAI | Anthropic |
|---|---|---|
| Tool definition | `{type:"function", function:{name, description, parameters:JSONSchema, strict?:true}}` | `{name, description, input_schema:JSONSchema}` |
| Model emits | `assistant.tool_calls = [{id, function:{name, arguments:str}}]` | `content: [{type:"tool_use", id, name, input:{...}}]` |
| You reply with | `{role:"tool", tool_call_id, content:str}` (one msg per call) | `{role:"user", content:[{type:"tool_result", tool_use_id, content}]}` |
| Stop signal | `finish_reason ∈ {"stop","tool_calls",...}` | `stop_reason ∈ {"end_turn","tool_use",...}` |
| Force any tool | `tool_choice:"required"` | `tool_choice:{type:"any"}` |
| Force specific | `tool_choice:{type:"function", function:{name:"x"}}` | `tool_choice:{type:"tool", name:"x"}` |
| Force text | `tool_choice:"none"` (or omit `tools`) | `tool_choice:{type:"none"}` |
| Strict JSON | `strict:true` inside function | input schemas honored without flag |
| Parallel calls | multiple entries in `tool_calls`; disabled when `strict:true` | multiple `tool_use` blocks; opt out via `disable_parallel_tool_use:true` |
| Caching | automatic prefix caching, 50–90% read discount | explicit `cache_control:{type:"ephemeral", ttl:"5m"|"1h"}` |
| Citations | via Structured Outputs / RAG | first-class Citations API; cited text doesn't count toward output |

## Anatomy of an OpenAI tool definition

```python
{
    "type": "function",
    "function": {
        "name": "create_customer",
        "description": "Create a new customer record.",
        "parameters": {
            "type": "object",
            "properties": {
                "name":  {"type": "string", "description": "Full name"},
                "email": {"type": "string", "description": "Email address"},
            },
            "required": ["name"],
        },
        # optional: "strict": True  (forces strict JSON arg generation)
    },
}
```

## Anatomy of an Anthropic tool definition

```python
{
    "name": "create_customer",
    "description": "Create a new customer record.",
    "input_schema": {
        "type": "object",
        "properties": {
            "name":  {"type": "string", "description": "Full name"},
            "email": {"type": "string", "description": "Email address"},
        },
        "required": ["name"],
    },
}
```

Note the field is `input_schema` for Anthropic, `parameters` (under
`function`) for OpenAI. Otherwise the JSON-Schema bodies are identical.

## Conversion (one-liner adapter)

```python
def openai_to_anthropic(t):
    fn = t["function"]
    return {
        "name": fn["name"],
        "description": fn.get("description", ""),
        "input_schema": fn["parameters"],
    }

def anthropic_to_openai(t):
    return {
        "type": "function",
        "function": {
            "name": t["name"],
            "description": t.get("description", ""),
            "parameters": t["input_schema"],
        },
    }
```

## Multi-turn loop, side-by-side

### OpenAI

```python
messages = [{"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg}]
for turn in range(MAX_TURNS):
    kwargs = {"model": "gpt-4o", "messages": messages, "max_tokens": 500}
    if turn < MAX_TURNS - 1:
        kwargs["tools"] = TOOLS
        kwargs["tool_choice"] = "auto"
    resp = client.chat.completions.create(**kwargs)
    msg = resp.choices[0].message
    if not msg.tool_calls:
        return msg.content
    messages.append(msg.model_dump(exclude_none=True))
    for call in msg.tool_calls:
        result = dispatch(call.function.name, json.loads(call.function.arguments))
        messages.append({"role":"tool", "tool_call_id":call.id,
                         "content":json.dumps(result, default=str)})
```

### Anthropic

```python
messages = [{"role": "user", "content": user_msg}]
for turn in range(MAX_TURNS):
    kwargs = {"model": "claude-opus-4-7", "max_tokens": 4096,
              "system": SYSTEM_PROMPT, "messages": messages}
    if turn < MAX_TURNS - 1:
        kwargs["tools"] = TOOLS
        kwargs["tool_choice"] = {"type": "auto"}
    resp = client.messages.create(**kwargs)
    messages.append({"role": "assistant", "content": resp.content})
    if resp.stop_reason != "tool_use":
        return "".join(b.text for b in resp.content if b.type == "text")
    tool_results = []
    for block in resp.content:
        if block.type != "tool_use": continue
        result = dispatch(block.name, block.input)
        tool_results.append({
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": json.dumps(result, default=str),
        })
    messages.append({"role": "user", "content": tool_results})
```

## Caching gotchas

- **OpenAI** prompt caching is automatic. Just keep the system prompt and
  tool list at the top of `messages`, stable across calls. 50% discount on
  reads, 90% on some newer models. Minimum 1024 tokens, 128-token granularity.
- **Anthropic** caching is opt-in via `cache_control:{type:"ephemeral",
  ttl:"5m"|"1h"}` on the *block* (system, tools, message). Default TTL was
  silently dropped from 1h to 5min on Mar 6 2026 — set `ttl:"1h"` explicitly
  if you want the long version. Cache writes cost 1.25× (5min) or 2× (1h);
  reads cost 0.1×.

For a 39-tool catalog (~3-4k tokens of schema), caching the system+tools
prefix pays back within 2 turns of any conversation.

## Streaming with tools

Both vendors stream tool-call argument deltas. Pattern:

1. Watch the stream for `tool_use` (Anthropic) or `tool_calls` (OpenAI)
   *start* events — these include the tool name immediately.
2. Render "Looking up customer…" the moment you see the name.
3. Accumulate JSON fragments per tool-call ID until the stop event.
4. Dispatch.

The UX win: paint the friendly label on first delta, before args fully
arrive. Vercel AI SDK and LangChain expose this as typed events; if you're
rolling your own SSE handler, the events to track are:

- OpenAI: `delta.tool_calls[i].function.arguments`
- Anthropic: `content_block_delta` with `delta.type == "input_json_delta"`

## Model selection (defaults as of May 2026)

| Use case | OpenAI | Anthropic |
|---|---|---|
| Quality, complex multi-tool flows | `gpt-4o` | `claude-opus-4-7` (1M ctx if needed) |
| Cost-sensitive, simple intents | `gpt-4o-mini` | `claude-haiku-4-5` |
| Embeddings (intent router) | `text-embedding-3-small` | (use OpenAI; Anthropic has no embeddings API) |
| Whisper transcription | `whisper-1` | (use OpenAI) |
| Text-to-speech | `tts-1` | (use OpenAI) |

Mix freely. Most production stacks use Claude for tool calling + GPT for
embeddings/voice.
