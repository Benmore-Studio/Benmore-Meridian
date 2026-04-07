# bm CLI — Benmore API Integration

Complete reference for using Benmore API through the `bm` CLI tool manager.

## Quick Start (60 seconds)

### 1. Set API Key

```bash
export BM_API_KEY="bpk_6PhdfyHRz5U7xBR4mQ7movGIMslK91sbNsSnTxzLOcE"

# Or save to config for persistence
mkdir -p ~/.benmore && cat > ~/.benmore/config << EOF
{"api_key": "bpk_6PhdfyHRz5U7xBR4mQ7movGIMslK91sbNsSnTxzLOcE"}
EOF
```

### 2. Try a Command

```bash
bm benmore projects     # List your assigned projects
bm benmore channels    # List Slack channels across projects
bm benmore status proj123   # Get project health
```

### 3. Shell Aliases (Optional)

```bash
# Auto-setup
bash scripts/setup_benmore_shell.sh

# Manual setup
echo 'alias benmore="bm benmore"' >> ~/.zshrc
source ~/.zshrc

# Now use
benmore projects
benmore channels --json | jq
```

---

## All Available Commands

### `bm benmore projects`

List projects assigned to you.

```bash
# List all projects
bm benmore projects

# Search projects
bm benmore projects --search "api redesign"

# JSON output (pipe to jq)
bm benmore projects --json | jq '.[] | {id, title, status}'

# Filter results
bm benmore projects --json | jq '.[] | select(.status == "active")'
```

**Output:**
```
┌─────────────┬──────────────────────┬──────────┬────────┬────────┐
│ ID          │ Title                │ Status   │ Phase  │ Team   │
├─────────────┼──────────────────────┼──────────┼────────┼────────┤
│ proj-auth   │ Auth Redesign        │ active   │ dev    │ 4      │
│ proj-api    │ API v3 Migration     │ active   │ test   │ 6      │
│ proj-mobile │ Mobile App           │ active   │ plan   │ 8      │
└─────────────┴──────────────────────┴──────────┴────────┴────────┘
```

### `bm benmore channels`

Get all Slack channels across projects.

```bash
# List all channels
bm benmore channels

# Filter to specific projects
bm benmore channels --projects proj-auth,proj-api

# JSON output
bm benmore channels --json | jq 'to_entries[] | .value[].name'

# Find inactive channels
bm benmore channels --json | jq '.[] | select(.last_message == null)'
```

**Output:**
```
┌────────────┬───────────────┬─────────┬──────────────┬──────────┐
│ Project    │ Channel       │ Members │ Last Message │ Archived │
├────────────┼───────────────┼─────────┼──────────────┼──────────┤
│ proj-auth  │ #team-alpha   │ 8       │ 2h ago       │ —        │
│ proj-api   │ #dev-beta     │ 12      │ 1m ago       │ —        │
│ proj-mobile│ (no channel)  │         │              │          │
└────────────┴───────────────┴─────────┴──────────────┴──────────┘
```

### `bm benmore context <project-id>`

Get complete project context (info + team + meetings + Slack + GitHub + blockers).

```bash
# Full context
bm benmore context proj-auth

# Include raw meeting transcripts
bm benmore context proj-auth --full

# Look back 30 days
bm benmore context proj-auth --days 30

# JSON output
bm benmore context proj-auth --json | jq '.team[] | {name, email, role}'
```

**Output:**
```
Project: Auth Redesign
ID: proj-auth
Phase: development | Status: active
Description: Complete overhaul of authentication system

Team (4):
  • Alice Johnson (alice) - lead
  • Bob Smith (bob) - developer
  • Charlie Brown (charlie) - designer
  • Diana Prince (diana) - developer

Slack Channels (1):
  • #team-alpha (8 members)

Recent Meetings (3):
  • Sprint Planning (2026-04-07)
    Planning and prioritization for Q2...
  • Sync (2026-04-06)
    Weekly status update and blockers...
  • Design Review (2026-04-05)
    Authentication flow mockups and feedback...

Blockers (2):
  • Waiting for payment processor approval
  • OAuth provider API rate limits

GitHub Repos (2):
  • benmore/auth-service
  • benmore/auth-frontend
```

### `bm benmore status <project-id>`

Get project health, completion %, blockers, team capacity.

```bash
# Get status
bm benmore status proj-auth

# JSON output
bm benmore status proj-auth --json | jq '{phase, health, completion_percentage, blockers}'
```

**Output:**
```
Project proj-auth
Phase: development
Health: yellow
Completion: 65%

Blockers (2):
  • Waiting for payment processor approval
  • OAuth provider API rate limits

Next Milestone: Beta Launch (2026-05-01)
```

### `bm benmore team <project-id>`

List project team members with roles.

```bash
# All team members
bm benmore team proj-auth

# Filter by role
bm benmore team proj-auth --role lead

# JSON output
bm benmore team proj-auth --json | jq '.[] | {name, email}'

# Email all developers
bm benmore team proj-auth --role developer --json | jq -r '.[] | .email'
```

**Output:**
```
┌─────────────┬──────────┬────────────────┬──────────┐
│ Name        │ Username │ Email          │ Role     │
├─────────────┼──────────┼────────────────┼──────────┤
│ Alice       │ alice    │ alice@...      │ lead     │
│ Bob Smith   │ bob      │ bob@...        │ dev      │
│ Charlie     │ charlie  │ charlie@...    │ designer │
│ Diana       │ diana    │ diana@...      │ dev      │
└─────────────┴──────────┴────────────────┴──────────┘
```

---

## Advanced Usage

### Scripting & Automation

```bash
#!/bin/bash
# Daily health check across all projects

for proj in $(bm benmore projects --json | jq -r '.[] | .id'); do
  echo "▶ $proj"
  bm benmore status "$proj" --json | jq '.{health, completion_percentage, blockers: (.blockers | length)}'
done
```

### Slack Integration

```bash
# Post results to Slack
projects=$(bm benmore projects --json)
message="📊 Active projects: $(echo "$projects" | jq '.[] | select(.status == "active") | .title' | wc -l)"

# Send via Slack webhook
curl -X POST -H 'Content-type: application/json' \
  --data "{\"text\":\"$message\"}" \
  $SLACK_WEBHOOK_URL
```

### Team Onboarding

```bash
# Get all Slack channels for new team member
echo "=== Channels to Join ===" 
bm benmore channels --json | jq -r '.[] | .[] | .name'

# Get all projects they'll work on
echo "=== Projects ===" 
bm benmore projects --json | jq '.[] | {title, team_size}'
```

### Project Assessment

```bash
# Check project health across all projects
echo "=== Project Health ===" 
for proj in $(bm benmore projects --json | jq -r '.[] | .id'); do
  health=$(bm benmore status "$proj" --json | jq -r '.health')
  echo "$proj: $health"
done | sort
```

---

## Environment Configuration

### Option 1: Environment Variable (Temporary)

```bash
export BM_API_KEY="bpk_..."
bm benmore projects
```

### Option 2: Config File (Persistent)

```bash
mkdir -p ~/.benmore
cat > ~/.benmore/config << 'EOF'
{
  "api_key": "bpk_6PhdfyHRz5U7xBR4mQ7movGIMslK91sbNsSnTxzLOcE"
}
EOF

chmod 600 ~/.benmore/config  # Secure the file
```

### Option 3: Shell Aliases (Convenience)

```bash
# Add to ~/.zshrc or ~/.bashrc
alias benmore="bm benmore"
alias bchannel="bm benmore channels"
alias bprojects="bm benmore projects"
alias bcontext="bm benmore context"
alias bstatus="bm benmore status"
alias bteam="bm benmore team"
```

Then reload: `source ~/.zshrc`

---

## Error Handling

### "No API key found"

```bash
# Set environment variable
export BM_API_KEY="bpk_..."

# Or create config file
mkdir -p ~/.benmore
echo '{"api_key": "bpk_..."}' > ~/.benmore/config
```

### "401 Unauthorized"

API key is invalid. Get a new one from Benmore portal and update:

```bash
export BM_API_KEY="bpk_new_key_here"
```

### "404 Project not found"

Project ID doesn't exist. List valid projects:

```bash
bm benmore projects --json | jq '.[] | .id'
```

### "Connection timeout"

API server may be down. Check:

```bash
curl -I https://client.benmore.tech/api/v1/docs/
```

Or check Benmore status page.

---

## Integration with Other Tools

### GitHub Actions

```yaml
name: Daily Project Health Check

on:
  schedule:
    - cron: "0 9 * * 1"  # Monday morning

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install bm
        run: pip install -e .
      
      - name: Check projects
        env:
          BM_API_KEY: ${{ secrets.BM_API_KEY }}
        run: bm benmore projects --json | jq '.[] | {id, title, status}'
```

### Slack Workflow

```bash
# In your Slack workflow integration
bm benmore channels --json | jq -r '.[] | .[] | .name'
```

### Monitoring/Alerting

```bash
# Check for blockers
blockers=$(bm benmore status proj-auth --json | jq '.blockers | length')
if [[ $blockers -gt 0 ]]; then
  # Send alert
  echo "⚠ Project has $blockers blockers"
fi
```

---

## Python API (Direct)

If you need more control, use the Python client directly:

```python
from benmore_client import BenmoreClient
import asyncio

async def main():
    async with BenmoreClient(api_key="bpk_...") as client:
        # List projects
        projects = await client.projects_list()
        for p in projects.results:
            print(f"{p.title} ({p.id})")
        
        # Get project context
        context = await client.projects_context("proj-auth")
        print(f"Team size: {len(context.team)}")
        print(f"Blockers: {context.blockers}")
        
        # Get team
        members = await client.team_list("proj-auth")
        for m in members:
            print(f"{m.name} - {m.role}")

asyncio.run(main())
```

See `docs/BENMORE-API.md` for complete Python documentation.

---

## API Endpoints Reference

| Command | Endpoint | Purpose |
|---------|----------|---------|
| `bm benmore projects` | GET /projects/ | List projects |
| `bm benmore projects --search X` | GET /projects/search/ | Search projects |
| `bm benmore context <id>` | GET /projects/<id>/context/ | Full project context |
| `bm benmore status <id>` | GET /projects/<id>/status/ | Project status |
| `bm benmore team <id>` | GET /projects/<id>/team/ | Team members |
| `bm benmore channels` | GET /projects/<id>/comms/ | Slack channels |

For more endpoints (meetings, GitHub, documents), see Python API docs.

---

## Support & Troubleshooting

**Testing the API directly:**

```bash
curl -H "X-API-KEY: bpk_..." \
  https://client.benmore.tech/api/v1/projects/ \
  | jq '.'
```

**Check API documentation:**

```bash
curl -H "X-API-KEY: bpk_..." \
  https://client.benmore.tech/api/v1/docs/endpoints/ \
  | jq '.'
```

**View all available commands:**

```bash
bm benmore --help
```

---

## Next Steps

1. **Setup shell integration:** `bash scripts/setup_benmore_shell.sh`
2. **Explore your projects:** `bm benmore projects`
3. **Check project status:** `bm benmore status <project-id>`
4. **Review team members:** `bm benmore team <project-id>`
5. **Integrate with your workflow** (see scripting examples above)
