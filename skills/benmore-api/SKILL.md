---
name: benmore-api
description: Query the Benmore project management API from Claude Code sessions — look up projects by BEN number, fetch full project context (team, meetings, Slack, GitHub, blockers), summarize channel activity, list team members, and browse assigned projects. Wraps the `bm benmore` CLI and the async `benmore_client` Python library. Trigger when the user mentions a BEN number (e.g. "BEN-128"), asks "what's the status of X", "who's on the team for Y", "summarize the Slack channel for Z", "what's everyone working on", "find that Benmore project", "give me context on [project]", or "what blockers does [project] have".
---

# benmore-api

The Benmore API is the source of truth for client **project data**: phase, team, Slack channel *linkage*, meetings + transcripts, GitHub board, blockers, financials, and **documents we produced** (deliverables like user flows). This skill is the fastest way to pull that data into a Claude Code session.

> ⚠️ **Slack comms boundary — read this first.** To read or summarize a client channel's **messages**, use your **Slack integration** — a Slack MCP/CLI tool (e.g. `slack_read_channel`) or a `slack:*` skill — **not** the Benmore API. The API's only job here is to resolve a project → its **channel ID**: use `bm benmore channels` / `context` (or `comms_channel_info`) for that — **not** `summary`. The `bm benmore summary` / `comms_messages` paths read the API's *stored copy* of messages and are **deprecated for message content**; fall back to them only when no Slack tooling is available in the session (see [Slack tooling availability](#slack-tooling-availability)). The API stays the source of truth for everything else — project context, **meeting transcripts**, deliverables we produced, team, blockers, GitHub, financials.

There are two entry points:

1. **`bm benmore` CLI** — the right answer 95% of the time. Pretty tables in the terminal, `--json` for piping, works from any shell.
2. **`benmore_client` Python library** — for scripts, custom queries, or composing calls the CLI doesn't expose.

## When to use this skill

Trigger on any of these user intents:

| Intent | Run |
|---|---|
| "Find project BEN-128" / "look up BEN-185" | `bm benmore lookup BEN-128` |
| "What's the status of [project]" | `bm benmore status <id>` |
| "Give me context on [project]" | `bm benmore context <id>` |
| "Who's on the team for [project]" | `bm benmore team <id>` |
| "Summarize the Slack channel for [project] this week" | **Your Slack integration, not this API.** Use `bm benmore channels` (or `context`) to get the channel ID, then read via a connected Slack tool (e.g. `slack_read_channel`) — else fall back to `bm benmore summary <id>`. See the boundary callout. |
| "What's everyone working on" / "show me all projects" | `bm benmore list` or `bm benmore overview` |
| "What blockers does [project] have" | `bm benmore status <id>` (blockers live on status) |
| "Which projects are in implementation" | `bm benmore list --phase implementation` |
| "Find projects about auth" | `bm benmore projects --search auth` |
| "List all Slack channels" | `bm benmore channels` |
| "What workflow prompts are available" | `bm benmore workflows` |

When in doubt, start with `bm benmore lookup <query>` to resolve to a project ID, then pipe that ID into `context`, `status`, or `team`. (For channel messages, resolve the channel ID and read via your Slack integration — see the boundary callout above.)

## Authentication setup

Every `bm benmore` command needs an API key. Set it one of two ways:

```bash
# Option A: env var (current shell only)
export BM_API_KEY="bpk_your_api_key_here"

# Option B: persistent config file
mkdir -p ~/.benmore
echo '{"api_key": "bpk_your_api_key_here"}' > ~/.benmore/config
chmod 600 ~/.benmore/config
```

API keys start with the `bpk_` prefix. If a command prints "No API key found", suggest one of the above. If it prints `401 Unauthorized`, the key is invalid/expired/revoked — direct the user to the Benmore portal to rotate it. Never invent or hardcode a key in examples; use the literal placeholder `bpk_your_api_key_here`.

## The `bm benmore` CLI — command reference

Every command accepts `--json` for machine-readable output.

### Discovery — find projects

```bash
# Resolve a BEN number → project info (title, UUID, phase)
bm benmore lookup BEN-128
bm benmore lookup 185              # bare digits are normalized to BEN-185
bm benmore lookup "Jason Steele"   # also searches by title / partial match
bm benmore lookup BEN-128 --id     # print only the UUID (for piping)

# List all assigned projects (simple table)
bm benmore projects
bm benmore projects --search "auth"   # search across all projects, not just yours
bm benmore projects --json

# Numbered list grouped by phase (like Richard's Slack format)
bm benmore list
bm benmore list --phase implementation    # filter: implementation | discovery | stalled | completed
bm benmore list --mine                    # only your assigned projects
bm benmore list --json

# Inline metadata updates
bm benmore list --set-working-on "BEN-185:Building onboarding flow"
bm benmore list --set-phase "BEN-166:implementation"

# Single-command dashboard — all projects, teams, channels, health
bm benmore overview              # ~3.6s for 29 projects (parallelized enrichment)
bm benmore overview --json
```

### Project detail — get context

```bash
# Full context: project info, team, meetings, Slack, GitHub, blockers, financials
bm benmore context <project-id>
bm benmore context <project-id> --full         # include meeting transcripts
bm benmore context <project-id> --days 30      # look back N days
bm benmore context <project-id> --json

# Health / blockers / completion
bm benmore status <project-id>

# Team members and their roles
bm benmore team <project-id>

# Slack channel summary over a time window
# ⚠️ DEPRECATED for message content — reads the API's *stored copy* of messages.
# Prefer the channel ID (below) + your Slack integration; use this only as a
# fallback when no Slack tooling is connected in the session.
bm benmore summary <project-id> --days 7       # default is 7
bm benmore summary <project-id> --days 14
bm benmore summary <project-id> --json
```

### Communications — Slack

**The API discovers the channel ID; your Slack integration reads the messages.**

```bash
# List all Slack channels across all assigned projects (gives you channel IDs)
bm benmore channels
bm benmore channels --projects proj1,proj2     # filter by project IDs
bm benmore channels --json | jq

# Then read the messages via your Slack integration (Slack MCP/CLI), e.g.:
#   slack_read_channel(channel_id="C0123ABC", oldest=<unix_ts>, limit=100)
# or a slack:* skill, if one is installed. Tool and parameter names depend on
# your setup — check the session's available tools rather than assuming these.
```

### Slack tooling availability

`slack_read_channel` and the `slack:*` skills are **not part of this repo** — they come from a separate Slack MCP server / Slack CLI that has to be connected in the session, and exact tool/parameter names depend on that integration. Before steering a Slack read, confirm such a tool is actually available. If none is connected:

- Tell the user no Slack tooling is connected, and offer `bm benmore summary <id>` (the API's stored copy) as a **fallback** rough summary, **or**
- Point them to connect the Slack MCP/CLI for real message access.

Never invent a Slack tool call you can't see in the session.

### Workflow prompts

```bash
# List the Claude Code workflow prompts available for project work
bm benmore workflows
# Lists /client-kickoff, /create-project-tickets, /user-flows-with-edge-cases,
# /client-value-maximizer, /full-pr-review-audit, /qa-plan, and more.
```

## Composed workflow patterns

These are the real power moves. Copy-paste friendly.

```bash
# Resolve a BEN number → its Slack channel ID, then read messages via your Slack integration:
#   cid=$(bm benmore channels --json | jq -r '.[] | select(...) | .channel_id')   # find the channel ID
#   slack_read_channel(channel_id="$cid", oldest=<unix_ts>, limit=100)            # read via Slack MCP/CLI
# (bm benmore summary $(bm benmore lookup BEN-128 --id) --days 14 reads the API's
#  stored copy — deprecated for message content, use only as a fallback)

# Get full context for a project by BEN number in one line
bm benmore context $(bm benmore lookup 185 --id) --full --days 30

# List only projects that have a connected Slack channel
bm benmore overview --json | jq '.[] | select(.channel != null)'

# Count projects by phase
bm benmore overview --json | jq 'group_by(.phase) | map({phase: .[0].phase, count: length})'

# Find all projects whose title mentions "auth" and print their IDs
bm benmore projects --search auth --json | jq -r '.[].id'

# Check blockers across every active project
bm benmore overview --json | jq -r '.[] | .id' | while read id; do
  bm benmore status "$id" --json | jq --arg id "$id" '{id: $id, blockers}'
done
```

## Direct Python client usage

Drop to the Python library when the CLI doesn't expose what you need (custom filtering, complex joins, scripts, long-running jobs). Import path: `benmore_client`.

```python
import asyncio
import os
from benmore_client import BenmoreClient, BenmoreAPIError

async def main() -> None:
    async with BenmoreClient(api_key=os.environ["BM_API_KEY"]) as client:
        # List all assigned projects
        projects = await client.projects_list()
        for p in projects.results:
            print(p.title, p.phase)

        # Search across all projects
        hits = await client.projects_search("onboarding")

        # Full context for one project
        ctx = await client.projects_context(projects.results[0].id, full=True, days=30)

        # Handle the "no channel connected" case gracefully
        try:
            channel = await client.comms_channel_info(projects.results[0].id)
            print(f"#{channel.name} — {channel.member_count} members")
        except BenmoreAPIError as e:
            print(f"No channel: {e}")

asyncio.run(main())
```

### Main async methods on `BenmoreClient`

**Projects**
- `projects_list()` → `ProjectListResponse` — assigned projects
- `projects_search(q)` → `ProjectListResponse` — search all projects by query
- `projects_context(id, *, full=False, days=None)` → `ProjectContext` — everything about a project in one call
- `projects_status(id)` → `ProjectStatus` — health, blockers, completion

**Team**
- `team_list(id)` → `list[TeamMember]`

**Communications (Slack)** — *use these for channel linkage/metadata + meetings only; read actual messages via Slack CLI/MCP*
- `comms_channel_info(id)` → `Channel` — channel ID + metadata; raises `BenmoreAPIError` if no channel is connected. **Use this to get the channel ID, then read messages via Slack CLI/MCP.**
- `comms_raw(id)` → `dict` — raw channel payload (metadata)
- `comms_messages(id, ...)` → ⚠️ **deprecated for this workflow** — reads messages via the Benmore API. Prefer `slack_read_channel` / `slack:*` skills.
- `comms_meetings(id, ...)` → meetings linked to the project (✅ fine — meetings/transcripts are an approved Benmore-API use)

**GitHub**
- `github_board(id)` → `GitHubBoard` — raises `BenmoreAPIError` if no GitHub Project is connected
- `github_repos(id)` → linked repositories

**Flash documents**
- `flash_documents_list()` → `list[Document]`

**Convenience helpers**
- `get_team_channels(project_ids=None)` → `dict[project_id, list[Channel]]` — batch-fetches channels for every project and swallows `BenmoreAPIError` for projects with no channel
- `get_project_team_by_role(id, role)` — filter team list by role

All list methods return Pydantic models, so `.model_dump()` gives you plain dicts for JSON serialization.

## Error handling — the two failure modes

The Benmore API is a bit unusual: it returns **HTTP 200 with `{"error": "..."}`** for the "no resource connected" cases (no Slack channel, no GitHub Project, etc.). The client detects this and raises `BenmoreAPIError`. Catch it when you're probing for optional resources:

```python
from benmore_client import BenmoreAPIError

try:
    channel = await client.comms_channel_info(project_id)
except BenmoreAPIError:
    channel = None   # project has no Slack channel linked — expected case
```

For genuine HTTP errors (4xx/5xx), the client raises `httpx.HTTPStatusError` after retries are exhausted. `401` means the API key is invalid/expired/revoked — not retryable.

### Retry behavior

- **GET requests** are auto-retried on `429`, `502`, `503`, `504`, and network errors with exponential backoff (3 retries by default, configurable via `max_retries`/`retry_backoff_base` on `BenmoreClient(...)`). `Retry-After` headers are honored on `429`.
- **POST / PATCH / DELETE** are **never retried** — retrying writes risks duplicates. If a write fails transiently, it surfaces to the caller immediately.

## ASCII flow: resolving a BEN number to a Slack summary

**The API resolves the project → channel ID; your Slack integration reads the messages (or fall back to the API's stored copy).**

```
User: "Summarize the Slack channel for BEN-128 this week"
                       │
                       ▼
         bm benmore lookup BEN-128 --id
                       │
                       ▼  (searches by "BEN-128", normalizes bare digits)
              <project-uuid>
                       │
                       ▼
       client.comms_channel_info(uuid)  ─── Benmore API: get the channel ID
                       │                     (raises BenmoreAPIError if none)
                       ▼
              <slack_channel_id>
                       │
                       ▼  ⟵ HAND OFF TO YOUR SLACK INTEGRATION HERE
              Slack tool connected in this session?
            ┌──────────────┴───────────────┐
          yes                              no
            │                               │
            ▼                               ▼
 slack_read_channel(channel_id,    Tell the user no Slack tooling is
   oldest=cutoff, limit=100)        connected; offer the fallback:
 (or a slack:* skill)               bm benmore summary <uuid> --days 7
            │                       (API's stored copy — rough summary)
            ▼
 Summary from real Slack messages
```

## Key gotchas

- **`BM_API_KEY` is required.** If missing, `bm benmore` exits with a clear error — don't try to proceed without it.
- **Project IDs are UUIDs, not BEN numbers.** `bm benmore context BEN-128` will NOT work — always resolve with `lookup` first (or use `$(bm benmore lookup BEN-128 --id)` inline).
- **Titles contain `[BEN-XXX]` brackets.** When building your own Rich output, wrap titles in `escape(...)` from `rich.markup` — otherwise Rich interprets the brackets as markup tags.
- **`HTTP 200 + {"error": ...}` is not a bug.** It's how the API signals "no resource connected." Catch `BenmoreAPIError`, don't treat it as a hard failure for optional fields like Slack channels or GitHub boards.
- **`benmore_team_channels.json` is gitignored.** Never commit files matching that name — they contain real client PII.
- **Writes don't retry.** `projects_update`, `team_add`, `comms_message_post`, etc. fail immediately on transient errors. If you need idempotency, build it into the caller.
- **`overview` is parallelized; `list` is parallelized too.** Both fan out team + channel enrichment via `asyncio.gather`. A 29-project overview runs in ~3.6s, not ~30s.

## REST API endpoint reference

The full REST API reference — every endpoint, scope, request/response schema, error code, and the scheduled task workflow — lives in [`references/api-reference.md`](references/api-reference.md). Use it when:

- Building scripts or scheduled tasks that call the API directly (not via the CLI or Python client)
- Checking exact query parameters, response field types, or scope requirements
- Debugging 401/403/404 errors — the error codes table explains each
- Setting up the daily/weekly dashboard report flow (see "Scheduled Task Workflow" section)

### Key endpoints for scheduled tasks

| Endpoint | Purpose |
|----------|---------|
| `GET /reports/active-projects-summary/` | Entry point — all active projects with health indicators |
| `GET /reports/project-status/<id>/` | Deep status: meetings, action items, blockers, kanban, financials, intelligence |
| `GET /reports/project-assets/<id>/` | All assets in one call: documents, presentations, transcripts, invoices |

### Endpoints not yet in the CLI or Python client

These API endpoints exist but aren't exposed via `bm benmore` or `benmore_client` yet:

| Endpoint | Description |
|----------|-------------|
| `GET/POST/PATCH/DELETE /projects/<id>/qa/` | QA log CRUD with GitHub sync |
| `POST /projects/<id>/qa/sync-github/` | Batch-sync QA logs to GitHub Project |
| `GET/POST /projects/<id>/diagrams/` | Mermaid.js user flow diagrams |
| `GET/POST/PATCH/DELETE /projects/<id>/documents/` | Project document management |
| `GET/POST/PATCH/DELETE /projects/<id>/dynamic-assets/` | Dynamic HTML assets |
| `GET/POST/PATCH/DELETE /projects/<id>/signature-documents/` | Signature documents with `/sign/` |
| `POST /github/create-project/` | Create a new GitHub Project v2 |
| `POST /projects/create/` | Create a new project |
| `GET /reports/active-projects-summary/` | Active projects overview (no client method) |

To call these directly, use the Python client's `_request` method or plain `curl`/`httpx`.

> **Note:** `_request()` is an internal method — its signature may change without notice. Prefer dedicated client methods when available.

```python
import os
from benmore_client import BenmoreClient

async with BenmoreClient(api_key=os.environ["BM_API_KEY"]) as client:
    # QA logs (not yet a dedicated method)
    qa_logs = await client._request("GET", f"/projects/{project_id}/qa/")

    # Create a diagram
    diagram = await client._request("POST", f"/projects/{project_id}/diagrams/", json={
        "title": "User Signup Flow",
        "mermaid_diagram": "graph TD\n  A[Landing] --> B[Signup] --> C[Dashboard]"
    })
```

## Related skills and references

- [`using-bm`](../using-bm/SKILL.md) — the broader `bm` CLI (skills, prompts, tools, hooks) — `bm benmore` is one subcommand among many.
- [REST API Reference](references/api-reference.md) — full endpoint documentation with scopes, schemas, and error codes.
- Python client source: `benmore_client/client.py` — full method signatures and Pydantic models.
- CLI source: `bm/bm/benmore.py` — definitive reference for every flag and behavior of `bm benmore`.
