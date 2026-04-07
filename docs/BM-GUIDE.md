# bm — The Benmore CLI Guide

Complete guide to `bm`, the Benmore skill manager CLI. Manages skills, prompts, tools, plugins, and the Benmore project management API integration.

---

## Quick Start

```bash
# One-time setup
pip install -e ./bm        # Install bm CLI (editable)
bm setup                    # Install all skills, tools, and plugins

# Daily commands
bm                          # Show dashboard
bm install                  # Install all skills
bm doctor                   # Health check everything
bm benmore list             # Show all your projects (Benmore API)
```

---

## Table of Contents

1. [What is bm?](#what-is-bm)
2. [Installation](#installation)
3. [Core Commands](#core-commands)
4. [Skills](#skills)
5. [Prompts](#prompts)
6. [Tools](#tools)
7. [Hooks (Auto-Sync)](#hooks-auto-sync)
8. [Benmore API Integration](#benmore-api-integration)
9. [Common Workflows](#common-workflows)
10. [Troubleshooting](#troubleshooting)

---

## What is bm?

`bm` (Benmore) is the unified CLI for everything Claude Code at Benmore Technologies:

- **Skills** — Symlink Claude Code skills from this repo into `~/.claude/skills/`
- **Prompts** — Save, search, and reuse prompt templates as `/slash` commands
- **Tools** — Install developer CLI tools (ripgrep, fd, bat, fzf, etc.)
- **Plugins** — Manage Superpowers and Double Shot Latte marketplaces
- **Hooks** — Git hooks that auto-sync skills after `git pull`
- **Benmore API** — Query the Benmore project management platform from your terminal

Everything is one command away.

---

## Installation

### First-time setup (run once)

```bash
# 1. Install bm CLI in editable mode
pip install -e ./bm

# 2. Run the all-in-one setup
bm setup                    # Installs skills + tools + plugins
bm setup --yes              # Skip all confirmation prompts
bm setup --dry-run          # Preview what setup would do
```

### Verify installation

```bash
bm                          # Should show the dashboard
bm doctor                   # Full health check
bm --help                   # See all commands
```

### For Benmore API (optional)

```bash
# Set your API key
export BM_API_KEY="bpk_your_api_key_here"

# Or save to config (persistent)
mkdir -p ~/.benmore
cat > ~/.benmore/config << 'EOF'
{"api_key": "bpk_your_api_key_here"}
EOF
chmod 600 ~/.benmore/config

# Verify
bm benmore list
```

---

## Core Commands

### Dashboard

```bash
bm                          # Show dashboard — skills/tools/plugins at a glance
```

### Install / Update

```bash
bm install                  # Symlink all repo skills → ~/.claude/skills/
bm install --rsync          # Force file copy instead of symlinks
bm install --dry-run        # Preview what would be installed
bm install --quiet          # Silent mode (used by hooks)

bm update                   # git pull + reinstall all skills
bm update <skill-name>      # Pull + reinstall one specific skill
bm update --rsync           # Pull + reinstall with file copies
bm update --dry-run         # Preview updates
```

### Health Check

```bash
bm doctor                   # Full health check (skills + tools + plugins)
bm doctor --yes             # Auto-fix all issues without prompting
bm doctor -y                # Short form of --yes
```

### Status

```bash
bm status                   # Rich table: skill name, status icon, scope
bm status --json            # Machine-readable JSON for agents/scripts
```

---

## Skills

Skills are reusable Claude Code instruction packages stored in `skills/` and symlinked into `~/.claude/skills/`.

### Browse skills

```bash
bm skill list                       # Browse all skills
bm skill list --json                # JSON output for agents
bm skill list --project pcs        # Filter by project scope
bm skill list -p pcs               # Short form
```

### Get info about a skill

```bash
bm skill info <name>               # Show path, scope, status, version
```

### Create a new skill

```bash
bm skill add <name>                # Create general skill with SKILL.md stub
bm skill add <name> -p pcs        # Project-scoped skill
bm skill add <name> --from ./path # Create from existing directory
bm skill write <name>              # Interactive builder (prompts for desc + triggers)
bm skill write <name> -p pcs      # Interactive builder for project skill
```

### Promote a project skill to general

```bash
bm skill generalize <name>         # Move + re-symlink, update registry
```

### Remove a skill

```bash
bm skill remove <name>             # Uninstall + remove from registry
bm skill remove <name> --dry-run   # Preview removal
```

### Install external skills

```bash
bm skill add-external <source> --skill <name>   # Install from plugins/agents dirs
```

### Skill Discovery (auto-suggest)

```bash
bm suggest [path]                  # Scan project → ranked skill suggestions
bm suggest [path] --top 5          # Limit to top 5
bm suggest [path] --json           # Machine-readable output

bm context [path]                  # Generate CLAUDE.md snippet with stack + top 5 skills
bm context [path] --copy           # Copy snippet to clipboard

bm explore [path]                  # Deep scan → writes docs/bm-suggestions.md report
bm debrief                         # Surface skill candidates from recent git history
bm debrief --since v1.2.0          # Look back to a specific tag
bm debrief --limit 30              # Scan last 30 commits (default: 15)
bm debrief --json                  # Machine-readable
```

---

## Prompts

Prompts are reusable templates stored in `prompts/` that can be exported as Claude Code `/slash` commands.

### Browse prompts

```bash
bm prompt list                     # Browse all prompts
bm prompt list --tag django        # Filter by tag
bm prompt list --starred           # Favorites only
bm prompt list --popular           # Most-used
bm prompt list --json              # Machine-readable
```

### Search prompts

```bash
bm prompt search <query>           # Fuzzy-search by name/desc/tags
bm prompt info <name>              # Show full prompt content + metadata
```

### Create a prompt

```bash
bm prompt add <name>               # Create new prompt template
bm prompt add <name> -p pcs       # Project-scoped prompt
```

### Use a prompt

```bash
bm prompt copy <name> [args]       # Render with args → clipboard
```

### Export to Claude Code as a /slash command

```bash
bm prompt export <name>            # Symlink → ~/.claude/commands/ (becomes /command)
bm prompt export --all             # Export all prompts as /commands
bm prompt unexport <name>          # Remove from /commands
```

### Star and remove

```bash
bm prompt star <name>              # Bookmark a favorite
bm prompt unstar <name>            # Remove bookmark
bm prompt remove <name>            # Delete a prompt
```

---

## Tools

`bm tools` manages developer CLI tools — ripgrep, fd, bat, fzf, eza, delta, jq, yq.

```bash
bm tools list                      # Show all 8 dev tools with install status
bm tools install                   # Install all missing tools (via brew/apt)
bm tools install ripgrep bat       # Install specific tools by name
```

---

## Plugins

```bash
bm plugins                         # Check Superpowers + Double Shot Latte status
```

---

## Hooks (Auto-Sync)

Git hooks that automatically run `bm install --quiet` after `git pull` so skills/prompts always stay in sync.

```bash
bm hooks install                   # Install post-merge + post-checkout git hooks
bm hooks remove                    # Remove bm-managed hooks (preserves others)
bm hooks status                    # Check which hooks are installed
```

After installing hooks, every `git pull` automatically syncs your skills.

---

## Registry

The registry tracks every installed skill so `bm` knows what it manages.

```bash
bm registry list                   # Show all tracked skills
bm registry list --json            # JSON output
bm registry sync                   # Detect externally installed skills
bm registry sync --dry-run         # Preview what sync would find
```

---

## Benmore API Integration

`bm benmore` provides direct access to the Benmore project management platform — projects, teams, Slack channels, GitHub boards.

### Setup

```bash
# Set API key (one of these)
export BM_API_KEY="bpk_your_api_key_here"

# OR save to config
mkdir -p ~/.benmore
echo '{"api_key": "bpk_your_api_key_here"}' > ~/.benmore/config
chmod 600 ~/.benmore/config
```

### Core commands

```bash
bm benmore list                    # Numbered project list grouped by phase
bm benmore list --phase implementation     # Filter by phase
bm benmore list --json             # JSON output

bm benmore overview                # Single-command dashboard
bm benmore projects                # Simple project list
bm benmore projects --search "api"  # Search projects

bm benmore lookup BEN-185          # Resolve BEN number → project ID
bm benmore lookup "Jason Steele"   # Resolve name → project ID
bm benmore lookup BEN-166 --id     # Print just the UUID (for piping)

bm benmore context <project-id>    # Get full project context
bm benmore context <id> --full     # With raw meeting transcripts
bm benmore context <id> --days 30  # Last 30 days

bm benmore status <project-id>     # Project health, completion, blockers

bm benmore team <project-id>       # List team members
bm benmore team <id> --role lead   # Filter by role

bm benmore channels                # List Slack channels across projects

bm benmore summary <project-id> --days 7    # Channel summary over time period

bm benmore workflows               # Show workflow prompts (PR review, QA, etc.)
```

### Update project metadata inline

```bash
bm benmore list --set-working-on "BEN-185:Building API client"
bm benmore list --set-phase "BEN-166:implementation"
```

### Pipe commands together

```bash
# Get summary for a project by name
bm benmore summary $(bm benmore lookup "Pam Olsen" --id) --days 14

# List all blocked projects
bm benmore list --json | jq '.projects[] | select(.phase == "stalled")'

# Get all team member emails for a project
bm benmore team <id> --json | jq '.[] | .email'
```

### Architecture

```
┌─────────────────────────────────────────┐
│ bm benmore <command>                    │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│ benmore_client (Python)                 │
│ - Async httpx client                    │
│ - 30+ endpoint methods                  │
│ - Pydantic models for type safety       │
│ - Parallel via asyncio.gather           │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│ Benmore API v2                          │
│ https://client.benmore.tech/api/v1/     │
│ Auth: X-API-KEY header                  │
└─────────────────────────────────────────┘
```

For complete API docs, see [BENMORE-API.md](BENMORE-API.md).

---

## Common Workflows

### New team member setup

```bash
git clone https://github.com/Benmore-Studio/Benmore-Meridian
cd Benmore-Meridian
pip install -e ./bm
bm setup --yes              # Install everything
bm hooks install            # Auto-sync on git pull
export BM_API_KEY="bpk_..."  # Get from team lead
bm benmore list             # Verify Benmore API access
```

### After git pull

```bash
git pull
# (hooks installed → bm install runs automatically)
# OR manually:
bm install                  # Or: bm update
```

### Building a new skill

```bash
bm skill write my-skill     # Interactive — prompts for description + triggers
# (edit skills/my-skill/SKILL.md as needed)
bm install                  # Activate via symlink
bm doctor                   # Verify it's installed correctly
```

### Building a project-scoped skill, then promoting

```bash
bm skill write my-thing -p pcs    # Project skill (only for pcs)
bm install                         # Activate
# (use it for a while...)
bm skill generalize my-thing       # Promote to general (available everywhere)
```

### Saving a prompt for reuse

```bash
bm prompt add my-template          # Create new prompt
# (edit prompts/my-template/PROMPT.md)
bm prompt export my-template       # Becomes /my-template in Claude Code
bm prompt star my-template         # Bookmark it
```

### Full health check after a long absence

```bash
bm update --dry-run         # See what would change
bm update                   # Pull + reinstall everything
bm doctor -y                # Auto-fix any issues
bm status                   # Verify state
```

---

## JSON Output for Agents

Most commands support `--json` for machine-readable output:

```bash
bm status --json            # → [{name, status, scope, project}, ...]
bm registry list --json     # → [{name, source, scope, install_method, ...}]
bm skill list --json        # → [{name, scope, project, path}, ...]
bm prompt list --json       # → [{name, description, tags, starred, use_count}]
bm benmore list --json      # → {projects: [...], by_phase: {...}}
bm benmore lookup BEN-185 --json  # → [{id, title, phase}]
```

---

## Architecture: How bm Works

### Skill Discovery & Install Flow

```
bm install
     │
     ▼
ensure ~/.claude/skills/ exists
     │
     ▼
discover_skills(skills/)
  ├── skills/vercel-cli/SKILL.md   → GENERAL skill
  ├── skills/pdf/SKILL.md          → GENERAL skill
  └── skills/pcs/                  → project container (no SKILL.md at root)
       └── pcs-migration/SKILL.md  → PROJECT skill (project="pcs")
     │
     for each skill:
     ▼
target = ~/.claude/skills/<name>
  remove existing (unlink or rmtree)
     │
  --rsync?  ──yes──▶  copytree → COPIED
     │ no
     ▼
  symlink_to(skill.path)
     ├── success → SYMLINKED
     └── OSError → copytree fallback → COPIED
     │
     ▼
reg.batch_add(entries)   ← single JSON write
```

### Prompt Export to /slash Commands

```
bm prompt export <name>
     │
     ▼
discover_prompts(prompts/)
     │
     ▼
~/.claude/commands/<name>.md
  symlink → prompts/<name>/PROMPT.md
     │
     ▼
/<name> now works as a Claude Code slash command
```

### Git Hook Auto-Sync

```
git pull (or branch switch)
     │
     ▼
.git/hooks/post-merge fires
     │
     ▼
git diff --name-only HEAD@{1} HEAD
     │
     ▼
skills/ or prompts/ changed?
     │ yes                  │ no
     ▼                      ▼
bm install --quiet &      (nothing)
     │
     ▼
symlinks updated silently
```

### Benmore API Parallel Fetch

```
bm benmore list (29 projects)
     │
     ▼
projects_list() ──► [P1, P2, ..., P29]
     │
     ▼
asyncio.gather(  ◄── 58 parallel HTTP calls
  team(P1) + comms(P1),
  team(P2) + comms(P2),
  ...
  team(P29) + comms(P29)
)
     │
     ▼
~3 seconds total (vs. 30+ seconds sequentially)
     │
     ▼
group by phase → render numbered list
```

---

## Troubleshooting

### `bm: command not found`

```bash
pip install -e ./bm         # Install editable
which bm                    # Should show the path
```

### Skills not syncing after git pull

```bash
bm hooks install            # Install auto-sync hooks
bm hooks status             # Verify they're active
```

### `bm benmore` says "No API key found"

```bash
# Set the env var
export BM_API_KEY="bpk_..."
echo $BM_API_KEY            # Verify

# Or save to config
mkdir -p ~/.benmore
echo '{"api_key": "bpk_..."}' > ~/.benmore/config
chmod 600 ~/.benmore/config
```

### `bm benmore` says "401 Unauthorized"

Your API key is invalid or expired. Get a new one from the Benmore portal and update.

### Skill installed but Claude Code doesn't see it

```bash
bm doctor                   # Check for symlink issues
bm install                  # Reinstall
ls -la ~/.claude/skills/    # Verify symlinks
```

### `bm doctor` reports failures

```bash
bm doctor -y                # Auto-fix
# If still broken:
bm registry sync            # Re-detect installed skills
bm install --rsync          # Force copy instead of symlinks
```

### Need to start fresh

```bash
bm registry list            # See what's tracked
bm skill remove <name>      # Remove individual skills
bm install                  # Reinstall everything
```

---

## Cheat Sheet

| Want to... | Run this |
|------------|----------|
| See everything | `bm` |
| Install all skills | `bm install` |
| Update everything | `bm update` |
| Check health | `bm doctor` |
| Browse skills | `bm skill list` |
| Create a skill | `bm skill write <name>` |
| Save a prompt | `bm prompt add <name>` |
| Export prompt as `/slash` | `bm prompt export <name>` |
| Install dev tools | `bm tools install` |
| Auto-sync after pull | `bm hooks install` |
| List Benmore projects | `bm benmore list` |
| Get project context | `bm benmore context <id>` |
| Find project by name | `bm benmore lookup "name"` |
| Channel summary | `bm benmore summary <id> --days 7` |

---

## Files & Directories

```
bm/                         # bm CLI Python package
├── bm/
│   ├── cli.py             # Main Typer app
│   ├── benmore.py         # Benmore API subcommands
│   ├── installer.py       # Skill install logic
│   ├── registry.py        # Skill registry
│   ├── prompts.py         # Prompt management
│   ├── tools.py           # Dev tool installer
│   ├── hooks.py           # Git hook management
│   ├── plugins.py         # Plugin detection
│   ├── skill_matcher.py   # Auto-suggest scoring
│   ├── debrief.py         # Git history skill discovery
│   └── updater.py         # Update logic
└── pyproject.toml

skills/                     # Skill source files
├── <skill>/SKILL.md       # General skills
└── <project>/<skill>/     # Project-scoped skills

prompts/                    # Prompt templates
└── <name>/PROMPT.md

benmore_client/             # Benmore API Python client
├── client.py              # Async httpx client
├── models.py              # Pydantic models
├── enums.py               # Type-safe enums
└── __init__.py            # Public exports

~/.claude/                  # Claude Code config (managed by bm)
├── skills/<name>          # Symlinks to skills/<name>
├── commands/<name>.md     # Symlinks to prompts/<name>/PROMPT.md
└── agent-memory/          # Subagent memory (per-skill)

~/.benmore/config           # Benmore API key (chmod 600)
```

---

## Support

- **Bug?** Open an issue on [Benmore-Studio/Benmore-Meridian](https://github.com/Benmore-Studio/Benmore-Meridian)
- **Question?** Ask in #bm-cli Slack channel
- **Skill ideas?** Run `bm debrief` to surface skill candidates from your recent commits
- **More docs:**
  - [BENMORE-API.md](BENMORE-API.md) — Full Python API reference
  - [BM-BENMORE-INTEGRATION.md](BM-BENMORE-INTEGRATION.md) — Benmore API CLI reference
  - [BENMORE-SETUP-GUIDE.md](BENMORE-SETUP-GUIDE.md) — Architecture & setup
  - [BENMORE-QUICKREF.md](BENMORE-QUICKREF.md) — Quick reference card
