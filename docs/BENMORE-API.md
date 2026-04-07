# Benmore Client API v2 — Python Integration Guide

Complete guide to using the Benmore API through Python, `bm` CLI, and shell integration.

**API Endpoint:** `https://client.benmore.tech/api/v1/`  
**Authentication:** `X-API-KEY` header  
**Scopes:** `projects:read`, `projects:write`, `flash-documents:read`, `flash-documents:write`

---

## Quick Start

### 1. Setup API Key

```bash
# Option A: Environment variable (recommended)
export BM_API_KEY="bpk_6PhdfyHRz5U7xBR4mQ7movGIMslK91sbNsSnTxzLOcE"

# Option B: Config file
mkdir -p ~/.benmore
cat > ~/.benmore/config << EOF
{
  "api_key": "bpk_6PhdfyHRz5U7xBR4mQ7movGIMslK91sbNsSnTxzLOcE"
}
EOF

# Verify
bm benmore projects
```

### 2. Install Python Client

```bash
# Already installed from benmore_client package
python3 -c "from benmore_client import BenmoreClient; print('✓ Ready')"
```

### 3. Try a Command

```bash
# List your projects
bm benmore projects

# List Slack channels
bm benmore channels

# Get project context
bm benmore context <project-id>
```

---

## bm CLI Commands

All commands are prefixed with `bm benmore`:

### Projects

```bash
# List assigned projects
bm benmore projects

# Search all projects
bm benmore projects --search "api redesign"

# JSON output
bm benmore projects --json
```

### Channels

```bash
# List all Slack channels across projects
bm benmore channels

# Filter to specific projects
bm benmore channels --projects proj1,proj2,proj3

# JSON output
bm benmore channels --json
```

### Context

Get complete project context in one call (info + team + meetings + Slack + GitHub + blockers).

```bash
# Basic context
bm benmore context proj123

# Include full meeting transcripts
bm benmore context proj123 --full

# Scope to last 30 days
bm benmore context proj123 --days 30

# JSON output
bm benmore context proj123 --json | jq '.team[]'
```

### Status

Detailed project status with health, completion %, blockers, team capacity.

```bash
# Get status
bm benmore status proj123

# JSON output
bm benmore status proj123 --json
```

### Team

List project team members with optional role filtering.

```bash
# All team members
bm benmore team proj123

# Filter by role
bm benmore team proj123 --role lead

# JSON output
bm benmore team proj123 --json | jq '.[] | {name, email}'
```

---

## Python Client Usage

### Basic Setup

```python
from benmore_client import BenmoreClient
import asyncio

async def main():
    async with BenmoreClient(api_key="bpk_...") as client:
        # Use client methods
        projects = await client.projects_list()
        print(f"You have {projects.count} projects")

asyncio.run(main())
```

### Projects

```python
# List assigned projects
projects = await client.projects_list()
for project in projects.results:
    print(f"{project.title} ({project.id}) — {project.status}")

# Search projects
results = await client.projects_search("api redesign")
print(f"Found {results.count} matching projects")

# Get summary dashboard
summary = await client.projects_summary()
print(f"Active: {summary['active_count']}, Blockers: {summary['blocker_count']}")
```

### Project Context (Golden Record)

```python
# Get complete project context
context = await client.projects_context("proj123", full=True, days=30)

# Access nested data
print(f"Project: {context.title}")
print(f"Team: {[m.name for m in context.team]}")
print(f"Channels: {[f'#{c.name}' for c in context.channels]}")
print(f"Blockers: {context.blockers}")
print(f"Meetings: {len(context.meetings)}")
print(f"Repos: {len(context.github_repos)}")
```

### Team Management

```python
# List team members
members = await client.team_list("proj123")
for member in members:
    print(f"{member.name} ({member.username}) — {member.role}")

# Filter by role
developers = await client.get_project_team_by_role("proj123", role="developer")

# Add team member (yourself)
result = await client.team_add("proj123")

# Add multiple members (superuser only)
result = await client.team_add("proj123", usernames=["alice", "bob"])

# Remove member
result = await client.team_remove("proj123", usernames=["alice"])
```

### Slack Communications

```python
# Get channel info
channel = await client.comms_channel_info("proj123")
print(f"#{channel.name} — {channel.member_count} members")

# Get message history
messages = await client.comms_messages("proj123", limit=50)
for msg in messages:
    print(f"{msg['user']}: {msg['text']}")

# Post message to project's Slack channel
await client.comms_message_post("proj123", "Hello team! 👋")

# Get meetings with summaries
meetings = await client.comms_meetings("proj123", full=False)
for meeting in meetings:
    print(f"{meeting.title} ({meeting.date.strftime('%Y-%m-%d')})")
    print(f"Summary: {meeting.summary}")

# Include full transcripts
meetings = await client.comms_meetings("proj123", full=True)
for meeting in meetings:
    print(meeting.transcript)

# Create meeting record
meeting = await client.comms_meeting_create(
    "proj123",
    title="Sprint Planning",
    date="2026-04-07T14:00:00",
    duration_minutes=60,
    attendees=["Alice", "Bob", "Charlie"],
)
```

### GitHub Planning

```python
# Get board data
board = await client.github_board("proj123")
print(f"Items: {len(board.items)}")
print(f"Status counts: {board.status_counts}")

# Get linked repos
repos = await client.github_repos("proj123")
for repo in repos:
    print(f"{repo['name']} — {repo['commits']} commits, {repo['prs']} PRs")

# Create ticket
item = await client.github_item_create(
    "proj123",
    title="Fix login bug",
    status="Todo",
    priority="high",
    size="medium",
)

# Update item field
await client.github_item_update("proj123", item_id, field="status", value="In Progress")

# Delete item
await client.github_item_delete("proj123", item_id)
```

### Flash Documents

```python
# List flash documents (global, not project-scoped)
docs = await client.flash_documents_list()

# Create document
doc = await client.flash_documents_create(
    title="API Spec v2",
    content="# API Specification\n...",
    doc_type="specification",
)

# Get document
doc = await client.flash_documents_get("api-spec-v2")

# Update document
updated = await client.flash_documents_update(
    "api-spec-v2",
    content="# Updated API Specification\n...",
)

# Delete document
await client.flash_documents_delete("api-spec-v2")
```

---

## ASCII Flows

### Request/Response Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Python Code / bm CLI Command                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ BenmoreClient._request()                                    │
│  - Add X-API-KEY header                                     │
│  - Build URL: https://client.benmore.tech/api/v1 + path    │
│  - Send HTTP request (GET/POST/PATCH/DELETE)               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │ Benmore API Server           │
        │ (client.benmore.tech/api/v1) │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │ Validate API Key             │
        │ Execute endpoint logic       │
        │ Query database / Slack API   │
        │ Aggregate response data      │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │ Return JSON response         │
        │ (200, 400, 401, 500, etc.)   │
        └──────────────┬───────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ httpx.AsyncClient receives response                         │
│  - Parse JSON                                               │
│  - Raise HTTP errors if needed                              │
│  - Return raw data dict                                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ BenmoreClient method validates with Pydantic                │
│  - ProjectContext(**data)                                   │
│  - [Meeting(**m) for m in data]                             │
│  - Raise ValidationError if schema mismatch                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Return typed model to caller                                │
│  - ProjectContext, list[Meeting], dict, etc.               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │ User code (Python / CLI)     │
        │ receives validated data      │
        │ with full type hints         │
        └──────────────────────────────┘
```

### Projects Discovery Flow

```
User Command
     │
     ▼
┌────────────────────────────────┐
│ bm benmore projects --search   │
│   "api redesign"               │
└──────────────┬─────────────────┘
               │
               ▼
┌────────────────────────────────┐
│ BenmoreClient                  │
│ .projects_search("api redesign")
└──────────────┬─────────────────┘
               │
               ▼
GET /projects/search/?q=api%20redesign
        │
        ▼
    [Full-Text Search]
    • Title matches
    • Description matches
    • Team mentions
        │
        ▼
{
  "results": [
    {
      "id": "proj-123",
      "title": "API Redesign v2",
      "status": "active",
      "phase": "development"
    },
    ...
  ],
  "count": 5
}
        │
        ▼
┌────────────────────────────────┐
│ ProjectListResponse            │
│  .results: [Project, ...]      │
│  .count: 5                     │
└──────────────┬─────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Pretty-print table or JSON output   │
│                                     │
│ Project    Status     Phase         │
│ ─────────────────────────────────   │
│ API Redesign v2  active  development
│ ...                                 │
└─────────────────────────────────────┘
```

### Full Project Context Aggregation

```
User Request
     │
     ▼
GET /projects/<id>/context/?full=true&days=30
     │
     ▼
┌──────────────────────────────────────────┐
│ Server aggregates from multiple sources: │
└──────────────────────────────────────────┘
         │
         ├─ Database: Project metadata
         │
         ├─ Slack API: Channel info + message history
         │
         ├─ Slack API: Meetings (from Slack history)
         │
         ├─ GitHub: Connected repos + commit stats
         │
         ├─ Finance DB: Budget, spend, ROI
         │
         └─ Internal: Blockers, team assignments
         │
         ▼
┌──────────────────────────────────────────┐
│ Combine into single response:            │
│                                          │
│ {                                        │
│   "id": "proj-123",                      │
│   "title": "...",                        │
│   "team": [...],          ← TeamMembers  │
│   "channels": [...],      ← Channels     │
│   "meetings": [...],      ← Meetings     │
│   "github_repos": [...],  ← Repos        │
│   "blockers": [...],                     │
│   "financials": {...}                    │
│ }                                        │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│ Client validates with Pydantic           │
│ ProjectContext(**data)                   │
│                                          │
│ Each nested field validates:             │
│ - Team: list[TeamMember]                 │
│ - Channels: list[Channel]                │
│ - Meetings: list[Meeting]                │
│ - etc.                                   │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│ Return validated ProjectContext to user  │
│                                          │
│ context.team[0].email                    │
│ context.channels[0].member_count         │
│ context.meetings[0].summary              │
│ context.blockers[0]                      │
└──────────────────────────────────────────┘
```

### Slack Channel Sync Sequence

```
Project A          Project B          Project C
    │                  │                  │
    ▼                  ▼                  ▼
┌──────────────────────────────────────────┐
│ User: bm benmore channels                │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│ 1. List assigned projects                │
│    GET /projects/                        │
│    → [proj-a, proj-b, proj-c]           │
└──────────────┬───────────────────────────┘
               │
               ├─────────────────────────────┐
               │    Parallel requests (3)    │
               │                             │
    ┌──────────▼──────────┐    ┌────────────▼────────┐    ┌──────────▼──────────┐
    │ GET /projects/a/    │    │ GET /projects/b/    │    │ GET /projects/c/    │
    │     comms/          │    │     comms/          │    │     comms/          │
    └──────────┬──────────┘    └────────────┬────────┘    └──────────┬──────────┘
               │                            │                        │
    ┌──────────▼──────────┐    ┌────────────▼────────┐    ┌──────────▼──────────┐
    │ Channel A           │    │ Channel B           │    │ (No channel)        │
    │ - #team-alpha       │    │ - #dev-beta         │    │ - Empty result      │
    │ - 8 members         │    │ - 12 members        │    │                     │
    │ - Last msg: 2h ago  │    │ - Last msg: 1m ago  │    │                     │
    └──────────┬──────────┘    └────────────┬────────┘    └──────────┬──────────┘
               │                            │                        │
               └────────────────┬───────────┴────────────┬───────────┘
                                │                        │
                                ▼                        ▼
                     ┌──────────────────────┐
                     │ Aggregate results:   │
                     │ {                    │
                     │   "proj-a": [ch-a],  │
                     │   "proj-b": [ch-b],  │
                     │   "proj-c": []       │
                     │ }                    │
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │ Pretty-print table   │
                     │ or JSON output       │
                     └──────────────────────┘
```

### Team Queries with Role Filtering

```
┌────────────────────────────────────────┐
│ bm benmore team proj123 --role lead    │
└────────────┬───────────────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│ client.get_project_team_by_role()      │
│  - project_id: "proj123"               │
│  - role: "lead"                        │
└────────────┬───────────────────────────┘
             │
             ▼
    GET /projects/proj123/team/
             │
             ▼
    ┌────────────────────────────────┐
    │ [                              │
    │   {name: "Alice", role: "lead"},
    │   {name: "Bob", role: "dev"},  │
    │   {name: "Charlie", role: "lead"},
    │ ]                              │
    └────────────┬───────────────────┘
                 │
                 ▼
         ┌─────────────────────────┐
         │ Client-side filtering:  │
         │ Keep only role="lead"   │
         └────────┬────────────────┘
                  │
                  ▼
         ┌─────────────────────────┐
         │ [                       │
         │   {name: "Alice", ...}, │
         │   {name: "Charlie", ...}│
         │ ]                       │
         └─────────┬───────────────┘
                   │
                   ▼
      Pretty-print filtered results
```

### Error Handling Flow

```
┌──────────────────────────────────┐
│ Python/CLI call                  │
└────────┬─────────────────────────┘
         │
         ▼
    ┌──────────────────────────────┐
    │ API key validation           │
    │ (env var or ~/.benmore/config)
    └────────┬─────────────────────┘
             │
             ├─ NOT FOUND ──▶ BadParameter exception
             │
             └─ FOUND ──────▶ Continue
                              │
                              ▼
                         ┌──────────────────┐
                         │ HTTP request     │
                         └────────┬─────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
              2xx OK          400s Client   5xx Server
                    │             │             │
                    ▼             ▼             ▼
            ┌────────────┐ ┌────────────┐ ┌────────────┐
            │ Success    │ │ BadRequest │ │ ServerError
            │ Parse JSON │ │ (Invalid   │ │ (Retry or │
            │ Validate   │ │  params)   │ │  Fail)    │
            │ return     │ │ 401        │ │           │
            │            │ │ (Invalid   │ │           │
            │            │ │  key)      │ │           │
            │            │ │ 403        │ │           │
            │            │ │ (Forbidden)│ │           │
            └────────────┘ └────────────┘ └────────────┘
                    │             │             │
                    └─────────────┼─────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │ Output to user           │
                    │ Pretty-print or raw JSON │
                    │ Exit code: 0/1           │
                    └──────────────────────────┘
```

---

## Integration with bm

The Benmore client is integrated into `bm` as a plugin subcommand group under `bm benmore`.

### Installation

Already installed as part of project setup. Verify:

```bash
bm benmore projects  # Should list your projects
```

If not available:

```bash
pip install -e .  # From project root
bm install        # Symlink all skills/tools
```

### Adding New Commands

To add a new `bm benmore` subcommand:

1. Add method to `BenmoreClient` in `benmore_client/client.py`
2. Add command function to `bm/bm/benmore.py` (using `@app.command()`)
3. Test: `bm benmore <command>`

Example:

```python
# benmore.py
@app.command()
def assets(project_id: str) -> None:
    """List all project assets (documents, diagrams)."""
    asyncio.run(_assets_impl(api_key, project_id))

async def _assets_impl(api_key: str, project_id: str) -> None:
    async with BenmoreClient(api_key=api_key) as client:
        assets = await client.projects_assets(project_id)
        console.print(json.dumps(assets, indent=2))
```

Then test:

```bash
bm benmore assets proj123
```

---

## Type Hints & Enums

All models are fully typed with Pydantic validation.

### Models Available

- `Project` — Summary with id, title, status, phase
- `ProjectContext` — Full context (team + comms + meetings + GitHub)
- `ProjectStatus` — Health, blockers, completion %
- `TeamMember` — User with role, email, joined date
- `Channel` — Slack channel with member count, last message
- `Meeting` — Meeting with summary, transcript, attendees
- `Document` — Project document with type, content, owner

### Enums Available

```python
from benmore_client import (
    Phase,      # discovery, planning, development, testing, launch, etc.
    Status,     # active, inactive, paused, completed, blocked
    Priority,   # critical, high, medium, low
    Size,       # xs, s, m, l, xl, xxl
    Severity,   # critical, high, medium, low, info
    DocumentType,  # specification, proposal, contract, meeting_notes, etc.
)

# Use in code:
if project.phase == Phase.DEVELOPMENT:
    print("In development")
```

---

## Global Shell Integration

To add `benmore` as a global command (not just `bm benmore`):

```bash
# Create shell alias
echo 'alias benmore="bm benmore"' >> ~/.zshrc

# Or create symlink
ln -s $(which bm) /usr/local/bin/benmore

# Then use:
benmore channels
benmore context proj123
benmore projects --search "api"
```

---

## Common Workflows

### Onboarding: Get Project Context

```bash
# Get complete project overview
bm benmore context proj123 --full --days 30

# Extract specific data
context=$(bm benmore context proj123 --json)
echo "$context" | jq '.team[].email'  # Get emails
echo "$context" | jq '.blockers[]'    # Get blockers
echo "$context" | jq '.meetings[].summary'  # Get meeting summaries
```

### Daily Check-In: Project Status

```bash
# Quick health check across all projects
for proj in $(bm benmore projects --json | jq -r '.[] | .id'); do
  echo "▶ $proj"
  bm benmore status "$proj" --json | jq '.{health, completion_percentage, blocker_count: (.blockers | length)}'
done
```

### Team Communication: Find Members

```bash
# Find all leads in a project
bm benmore team proj123 --role lead --json | jq -r '.[] | .email'

# Email all developers
bm benmore team proj123 --role developer --json | jq -r '.[] | .email' | xargs -I {} echo "Email: {}"
```

### Slack Channel Sync

```bash
# Get all channels your team is in
bm benmore channels --json | jq 'to_entries[] | .value[] | .name'

# Find inactive channels (no messages in X days)
bm benmore channels --json | jq '.[] | select(.last_message_ts == null)'
```

---

## Troubleshooting

### "No API key found"

```bash
# Check environment
echo $BM_API_KEY
ls ~/.benmore/config

# Set env var
export BM_API_KEY="bpk_..."
bm benmore projects
```

### "401 Unauthorized"

API key is invalid or revoked. Get a new key from Benmore portal and update.

### "404 Project not found"

Project ID doesn't exist or you don't have access. Verify:

```bash
bm benmore projects  # List valid projects
```

### "ValidationError: X field required"

API response format changed. Update benmore_client package:

```bash
pip install --upgrade benmore-client
```

---

## API Reference

Complete endpoint list from Benmore API v2:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/projects/` | GET | List assigned projects |
| `/projects/search/` | GET | Search all projects |
| `/projects/summary/` | GET | Active projects overview |
| `/projects/<id>/context/` | GET | Full project context |
| `/projects/<id>/status/` | GET | Project status + health |
| `/projects/<id>/assets/` | GET | All project assets |
| `/projects/<id>/update/` | PATCH | Update project metadata |
| `/projects/<id>/team/` | GET/POST/DELETE | Team management |
| `/projects/<id>/comms/` | GET/PATCH | Slack channel info |
| `/projects/<id>/comms/messages/` | GET/POST | Slack message history |
| `/projects/<id>/comms/thread/<ts>/` | GET | Thread replies |
| `/projects/<id>/comms/meetings/` | GET/POST | Meetings + summaries |
| `/projects/<id>/github/` | GET/PATCH | GitHub board data |
| `/projects/<id>/github/items/` | POST/PATCH/DELETE | Ticket management |
| `/projects/<id>/github/repos/` | GET/POST/DELETE | Linked repos |
| `/flash-documents/` | GET/POST | Global documents |
| `/flash-documents/<slug>/` | GET/PATCH/DELETE | Document CRUD |

For live API docs:

```bash
curl -H "X-API-KEY: bpk_..." \
  https://client.benmore.tech/api/v1/docs/endpoints/
```

---

## Support

- **API Issues:** Check Benmore portal status page
- **Client Issues:** See errors with `--json` flag for detailed output
- **Feature Requests:** Contact Benmore support
