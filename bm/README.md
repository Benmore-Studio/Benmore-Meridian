# bm — Benmore Skill Manager

Lightweight CLI for managing Claude Code skills from the Benmore-Meridian repo.

## Install

```bash
git clone <repo> && cd Benmore-Meridian
pipx install ./bm
# or: pip install -e ./bm
```

## Quick Start

```bash
bm install          # symlink all skills → ~/.claude/skills/
bm plugins          # guide Superpowers + Double Shot Latte
bm doctor           # full health check
```

## Commands

```
bm install [--rsync]              Install all skills (symlinks by default, --rsync forces copy)
bm status [--json]                Show skill link status (--json for agent use)
bm update [name] [--rsync]        git pull + reinstall one or all skills
bm plugins                        Check/guide plugin installation
bm doctor                         Full health check

bm skill add <name>               Add new general skill
bm skill add <name> --project p   Add project-scoped skill (e.g. --project pcs)
bm skill list [--project p]       List skills, filtered by project
bm skill generalize <name>        Promote project skill → general (moves + re-symlinks)
bm skill info <name>              Show skill path, scope, status, source

bm registry sync                  Scan ~/.claude/skills/ and update registry
bm registry list [--json]         List all registered skills
```

## Project-Specific Skills

```bash
# Add a project skill
bm skill add my-deploy --project my-project
# Edit skills/my-project/my-deploy/SKILL.md
bm install

# Later: promote to general
bm skill generalize my-deploy
```

## How It Works

- Skills live in `skills/` (or `skills/pcs/` for PCS-scoped skills)
- `bm install` symlinks each skill into `~/.claude/skills/`
- PCS skills are flattened: `skills/pcs/pcs-migration/` → `~/.claude/skills/pcs-migration`
- A registry at `~/.bm/registry.json` tracks every installed skill
- `bm registry sync` detects externally installed skills and adds them to the registry

## Development

```bash
cd bm
make install     # uv sync --all-extras
make check-all   # ruff + mypy + pytest (< 30s)
```

### Tech Stack

- **Typer** — CLI framework (Click under the hood, fully typed)
- **Rich** — tables, panels, console output
- **dataclasses + Enums** — typed data models, no extra deps
- **uv** — fast Python package management
- **ruff** — lint + format
- **mypy** — strict type checking
- **pytest + pytest-cov** — tests with coverage
