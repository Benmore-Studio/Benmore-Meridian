# Benmore API — Complete Setup & Integration Guide

Production-ready Python client + bm CLI integration for Benmore project management platform.

---

## TL;DR — Setup in 30 Seconds

```bash
# 1. Add API key to shell
export BM_API_KEY="bpk_your_api_key_here"

# 2. Test it works
bm benmore projects

# 3. (Optional) Setup shell aliases
bash scripts/setup_benmore_shell.sh
```

Done! Now use:
```bash
benmore projects                    # List projects
benmore channels                   # List Slack channels
benmore context <project-id>       # Get project overview
benmore status <project-id>        # Get project health
benmore team <project-id>          # List team members
```

---

## What You're Getting

### 1. **Python Benmore Client Library**
   - Type-safe async HTTP client
   - Pydantic models for all API responses
   - Comprehensive enums for domain values
   - Full docstrings and type hints

### 2. **bm CLI Integration**
   - New `bm benmore` command group
   - 5 core subcommands (projects, channels, context, status, team)
   - JSON output for scripting
   - Pretty-printed tables for humans

### 3. **Shell Integration Scripts**
   - Global `benmore` command
   - Shell aliases for common operations
   - Config file management
   - Auto-verification

---

## Files Created

```
benmore_client/
├── __init__.py              # Package exports
├── client.py                # Main async HTTP client (600+ lines)
├── enums.py                 # Type-safe enums
├── models.py                # Pydantic models
└── py.typed                 # PEP 561 type stub marker

bm/bm/
└── benmore.py               # bm CLI subcommands (450+ lines)

scripts/
├── benmore_team_channels.py # Query team channels across projects
└── setup_benmore_shell.sh   # One-shot shell integration setup

docs/
├── BENMORE-API.md           # Complete Python API reference
├── BM-BENMORE-INTEGRATION.md # CLI command reference
└── BENMORE-SETUP-GUIDE.md   # This file
```

---

## Architecture Overview

### ASCII Flow: Request Lifecycle

```
User Command (CLI or Python)
       │
       ▼
┌──────────────────────────────┐
│ BenmoreClient               │
│ ├─ Prepare request headers   │
│ ├─ Build URL with params    │
│ └─ Send HTTP request        │
└──────────┬───────────────────┘
           │
           ▼
    ┌─────────────────────┐
    │ httpx.AsyncClient   │
    │ - Async/await       │
    │ - Connection pool   │
    │ - SSL verified      │
    └─────────┬───────────┘
              │
              ▼
    ┌──────────────────────────────────┐
    │ Benmore API Server               │
    │ https://client.benmore.tech/... │
    │                                  │
    │ X-API-KEY: bpk_...              │
    │ Content-Type: application/json   │
    └─────────┬────────────────────────┘
              │
              ▼
    ┌─────────────────────────┐
    │ JSON Response           │
    │ (200, 400, 401, 500)   │
    └─────────┬───────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Pydantic Validation                  │
│ ProjectContext(**data)               │
│ [Meeting(**m) for m in data]         │
│ ✓ Type checking                      │
│ ✓ Field validation                   │
│ ✗ ValidationError on mismatch        │
└──────────┬──────────────────────────┘
           │
           ▼
    ┌─────────────────────┐
    │ Typed Model         │
    │ model.team[0].email │
    │ model.blockers[]    │
    │ model.status        │
    └────────────────────┘
```

### ASCII Flow: CLI Request Handling

```
$ bm benmore context proj123 --full --json

                    │
                    ▼
        ┌───────────────────────────┐
        │ Parse CLI arguments       │
        │ project_id="proj123"      │
        │ full=True                 │
        │ json_output=True          │
        └───────────┬───────────────┘
                    │
                    ▼
    ┌──────────────────────────────────────┐
    │ Get API key from environment or      │
    │ ~/.benmore/config                    │
    └───────────┬──────────────────────────┘
                │
                ▼
    ┌──────────────────────────────────────┐
    │ Create BenmoreClient                 │
    │ async with BenmoreClient(...) as ... │
    └───────────┬──────────────────────────┘
                │
                ▼
    ┌──────────────────────────────────────┐
    │ await client.projects_context()      │
    │ GET /projects/proj123/context/       │
    │ ?full=true                           │
    └───────────┬──────────────────────────┘
                │
                ▼
    ┌──────────────────────────────────────┐
    │ Return ProjectContext model          │
    └───────────┬──────────────────────────┘
                │
        ┌───────┴───────┐
        │               │
    json_output?    Pretty print?
        │               │
        ▼               ▼
   JSON dump      Rich Table
   to stdout      to stdout
```

### ASCII Flow: Benmore API Aggregation

The `/projects/<id>/context/` endpoint is particularly powerful:

```
Single GET request: /projects/proj123/context/?full=true

        │
        ▼
┌──────────────────────────────────────┐
│ Server aggregates from multiple      │
│ sources in parallel                  │
└──────────────────────────────────────┘
        │
    ┌───┼───┬──────┬──────┬──────────┐
    │   │   │      │      │          │
    ▼   ▼   ▼      ▼      ▼          ▼
   DB Slack GitHub Finance Blockers  Repos
   │  API   API    DB      DB        DB
    │   │   │      │      │          │
    └───┼───┼──────┼──────┼──────────┘
        │
        ▼
┌───────────────────────────────────────┐
│ Combine all data into single JSON:    │
│                                       │
│ {                                     │
│   "id": "proj123",                    │
│   "title": "...",                     │
│   "team": [...],    ← Team members    │
│   "channels": [...],  ← Slack info   │
│   "meetings": [...],  ← Meetings     │
│   "github_repos": [...], ← Repos     │
│   "blockers": [...],    ← Blockers   │
│   "financials": {...}   ← Budget     │
│ }                                     │
└────────┬────────────────────────────┘
         │
         ▼
    Client-side
    Pydantic validation
    ✓ Nested models
    ✓ Type conversion
    ✓ Required fields
```

---

## API Endpoints — Complete List

### Projects

```
GET /projects/                      # List assigned projects
GET /projects/search/?q=...         # Search all projects
GET /projects/summary/              # Dashboard overview
GET /projects/<id>/context/         # Full project context (GOLDEN RECORD)
GET /projects/<id>/status/          # Project status & health
GET /projects/<id>/assets/          # All project assets
PATCH /projects/<id>/update/        # Update metadata
```

### Team Management

```
GET /projects/<id>/team/            # List team members
POST /projects/<id>/team/           # Add member(s)
DELETE /projects/<id>/team/         # Remove member(s)
```

### Communications (Slack)

```
GET /projects/<id>/comms/           # Channel info
PATCH /projects/<id>/comms/         # Connect Slack channel
GET /projects/<id>/comms/messages/  # Message history
POST /projects/<id>/comms/messages/ # Post message
GET /projects/<id>/comms/thread/<ts>/ # Get thread
GET /projects/<id>/comms/meetings/  # Meetings with summaries
POST /projects/<id>/comms/meetings/ # Create meeting record
```

### Planning (GitHub)

```
GET /projects/<id>/github/          # Board data
PATCH /projects/<id>/github/        # Connect GitHub Project
POST /projects/<id>/github/items/   # Create ticket
PATCH /projects/<id>/github/items/  # Update item
DELETE /projects/<id>/github/items/ # Delete item
GET /projects/<id>/github/repos/    # Linked repositories
POST /projects/<id>/github/repos/   # Link repo
DELETE /projects/<id>/github/repos/ # Unlink repo
```

### Flash Documents (Global)

```
GET /flash-documents/               # List documents
POST /flash-documents/              # Create document
GET /flash-documents/<slug>/        # Get document
PATCH /flash-documents/<slug>/      # Update document
DELETE /flash-documents/<slug>/     # Delete document
```

---

## bm CLI Subcommands

### Core Commands

| Command | Arguments | Purpose |
|---------|-----------|---------|
| `bm benmore projects` | `--search`, `--json` | List/search projects |
| `bm benmore channels` | `--projects`, `--json` | List Slack channels |
| `bm benmore context` | `project_id`, `--full`, `--days`, `--json` | Get complete context |
| `bm benmore status` | `project_id`, `--json` | Get project health |
| `bm benmore team` | `project_id`, `--role`, `--json` | List team members |

### Usage Examples

```bash
# List projects
bm benmore projects
bm benmore projects --json | jq '.'

# Search
bm benmore projects --search "api"
bm benmore projects --search "redesign" --json

# Channels
bm benmore channels
bm benmore channels --projects proj1,proj2
bm benmore channels --json | jq '.[] | .name'

# Context (golden record)
bm benmore context proj123
bm benmore context proj123 --full              # Raw transcripts
bm benmore context proj123 --days 30          # Last month
bm benmore context proj123 --json | jq '.blockers'

# Status
bm benmore status proj123
bm benmore status proj123 --json | jq '.{health, completion_percentage}'

# Team
bm benmore team proj123
bm benmore team proj123 --role lead
bm benmore team proj123 --json | jq '.[].email'
```

---

## Python API — Type Hints

All models are fully typed with Pydantic:

```python
from benmore_client import (
    BenmoreClient,
    # Models
    Project,
    ProjectContext,
    ProjectStatus,
    TeamMember,
    Channel,
    Meeting,
    Document,
    # Enums
    Phase,
    Status,
    Priority,
    Size,
    Severity,
    DocumentType,
)

async def example():
    async with BenmoreClient(api_key="bpk_...") as client:
        # Typed responses
        projects: ProjectListResponse = await client.projects_list()
        context: ProjectContext = await client.projects_context("proj123")
        members: list[TeamMember] = await client.team_list("proj123")
        channel: Channel = await client.comms_channel_info("proj123")
        meetings: list[Meeting] = await client.comms_meetings("proj123")
        
        # Full type hints
        for member in members:
            email: str = member.email
            role: str | None = member.role
        
        for blocker in context.blockers:
            print(blocker)  # str
```

---

## Your Current Setup

### Your Account

```
Username:     arkashjain
API Key:      bpk_your_api_key_here
Projects:     21 (found via API)
Channels:     0 (no Slack channels connected yet)
```

### Projects You Have Access To

```
1. Alex Titov Team [BEN-503]
2. Allan Bell [BEN-121]
3. ArkashJ Team [BEN-501]
4. Brad Pierce [BEN-128]
5. Chantal Wilson [BEN-175]
6. Christian Maldonado [BEN-169]
7. Daniel Adewumi - Propurti [BEN-109]
8. Dev Onboarding [BEN-2001]
9. Donald Carter [BEN-118]
10. Dr. Todd (BEN-119)
... and 11 more
```

**Note:** No Slack channels are currently connected to these projects. To enable Slack integration:
1. Go to Benmore portal
2. Configure Slack workspace connection
3. Link channels to projects
4. Then `bm benmore channels` will show active channels

---

## Quick Start Steps

### Step 1: Setup API Key (Choose One)

**Option A: Temporary (current session only)**
```bash
export BM_API_KEY="bpk_your_api_key_here"
```

**Option B: Permanent (config file)**
```bash
mkdir -p ~/.benmore
cat > ~/.benmore/config << 'EOF'
{
  "api_key": "bpk_your_api_key_here"
}
EOF
chmod 600 ~/.benmore/config
```

**Option C: Automated Setup**
```bash
bash scripts/setup_benmore_shell.sh
```

### Step 2: Verify Installation

```bash
# Test it works
bm benmore projects

# Should output a table with your 21 projects
```

### Step 3: (Optional) Add Shell Aliases

```bash
# Add to ~/.zshrc or ~/.bashrc
echo 'alias benmore="bm benmore"' >> ~/.zshrc

# Or run automated setup
bash scripts/setup_benmore_shell.sh

# Reload
source ~/.zshrc
```

### Step 4: Explore Your Data

```bash
# List projects
benmore projects

# Get project context
benmore context "ba1d059d-4ad3-49c9-ba4f-9ab74168fd3b"  # ArkashJ Team

# Check status
benmore status "ba1d059d-4ad3-49c9-ba4f-9ab74168fd3b"

# List team members
benmore team "ba1d059d-4ad3-49c9-ba4f-9ab74168fd3b"
```

---

## Team Channel Analysis

Script ran and analyzed all 21 projects:

```
Projects scanned:    21
Slack channels:      0 (not yet connected in Benmore portal)
Team members found:  0 in channels (but 21 projects have teams)

Your team members' channels:
- arkashjain:        0 channels
- connor:            0 channels  
- alex_dunne:        0 channels
- alex_titov:        0 channels

Why? Slack channels haven't been connected to projects yet in Benmore.
Once connected via portal, channels will appear here.
```

See `benmore_team_channels.json` for raw data.

---

## Common Workflows

### Daily Project Health Check

```bash
#!/bin/bash
for proj in $(bm benmore projects --json | jq -r '.[] | .id'); do
  echo "▶ $proj"
  bm benmore status "$proj" --json | jq '.{health, completion_percentage}'
done
```

### Find Team Members' Emails

```bash
bm benmore team "proj-id" --json | jq -r '.[] | .email'
```

### Export to CSV

```bash
bm benmore projects --json | jq -r '.[] | [.id, .title, .status, .phase] | @csv'
```

### Integration with GitHub

```bash
# Get GitHub repos for a project
bm benmore context "proj-id" --json | jq '.github_repos[]'
```

---

## Documentation Files

Three comprehensive guides created:

1. **BENMORE-API.md** (600+ lines)
   - Complete Python API reference
   - Type hints and Pydantic models
   - All 25+ API methods
   - ASCII flow diagrams

2. **BM-BENMORE-INTEGRATION.md** (400+ lines)
   - All `bm benmore` subcommands
   - CLI usage examples
   - Scripting & automation
   - Integration recipes

3. **BENMORE-SETUP-GUIDE.md** (this file)
   - Architecture overview
   - Quick setup (30 seconds)
   - Endpoint reference
   - Team channel analysis

---

## Troubleshooting

### API Key Issues

```bash
# Test API key directly
curl -H "X-API-KEY: bpk_..." \
  https://client.benmore.tech/api/v1/projects/ \
  -I

# Should return 200 OK
```

### Check Installation

```bash
# Verify client library
python3 -c "from benmore_client import BenmoreClient; print('✓')"

# Verify bm integration
bm benmore projects --help
```

### View Full Errors

```bash
# Get detailed error messages
bm benmore projects --json 2>&1 | head -50
```

---

## Next Steps

1. ✅ **Done:** Python client library created with full type hints
2. ✅ **Done:** bm CLI integration added with 5 core commands
3. ✅ **Done:** Shell integration scripts created
4. ✅ **Done:** API documentation written (600+ lines)
5. ✅ **Done:** Team channels analyzed (21 projects, 0 channels connected)

**Now you can:**
- Use `bm benmore` commands in your terminal
- Integrate with scripts and automation
- Query all 21 projects and teams
- Add Slack channels when available in portal
- Use Python client for advanced integrations

---

## Support

**API Status:** https://client.benmore.tech/api/v1/docs/endpoints/

**Live Docs:**
```bash
curl -H "X-API-KEY: bpk_..." \
  https://client.benmore.tech/api/v1/docs/endpoints/ | jq
```

**Issues:**
- Check API key validity
- Verify network connectivity
- Ensure project IDs are correct
- Use `--json` flag for debugging
