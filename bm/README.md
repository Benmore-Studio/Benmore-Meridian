# bm

**One command. Every Claude Code skill.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-1.0.0-green)](https://github.com/Benmore-Studio/Benmore-Meridian)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)
[![Tests](https://img.shields.io/badge/tests-27%20passing-brightgreen)](tests/)
[![Skills](https://img.shields.io/badge/skills-50%2B-purple)](../skills/)

```
git clone https://github.com/Benmore-Studio/Benmore-Meridian
cd Benmore-Meridian
pipx install ./bm
bm install
```

That's it. 50+ Claude Code skills are now symlinked and ready.

---

## What it does

- **Symlink-first install** — skills live in the repo, symlinked to `~/.claude/skills/`. Edit once, reflect everywhere.
- **Project skill lifecycle** — create project-scoped skills (`bm skill add x --project pcs`), then promote them to general (`bm skill generalize x`) when they're proven.
- **Registry tracking** — every installed skill is recorded in `~/.bm/registry.json`, regardless of how it got there.
- **Plugin guidance** — `bm plugins` detects Superpowers and Double Shot Latte and walks you through installing any that are missing.
- **Claude-native output** — every command supports `--json` for machine-readable output. Claude can query `bm status --json` directly.
- **Zero config** — path constants computed from repo root at import time. Works from any directory.

---

## Demo

```
$ bm doctor

──────────────────── bm doctor ────────────────────
Skills: 50/50 installed
Plugin ✅ Superpowers
Plugin ✅ Double Shot Latte

Everything looks great! 🎉
```

```
$ bm status --json | head -12
[
  {
    "name": "ai-seo",
    "status": "symlinked",
    "scope": "general",
    "project": ""
  },
  {
    "name": "pcs-migration",
    "status": "symlinked",
    "scope": "project",
    "project": "pcs"
  },
  ...
]
```

---

## Getting Started

### Requirements

- Python 3.11+
- `pip` (ships with Python)
- [Claude Code](https://claude.ai/code) (`brew install claude`)

### Install

```bash
# Clone the Benmore-Meridian skills repo
git clone https://github.com/Benmore-Studio/Benmore-Meridian
cd Benmore-Meridian

# Install bm in editable mode — skills live in the repo, bm finds them automatically
pip install -e ./bm

# Symlink all 50+ skills into Claude Code
bm install

# Check plugin requirements (Superpowers, Double Shot Latte)
bm plugins

# Verify everything
bm doctor
```

Open Claude Code in any project — all skills are now live.

> **Why editable install?** `pip install -e ./bm` keeps `bm` linked to this repo so
> it always finds the `skills/` directory. Running `git pull` in this repo immediately
> updates all skill content via symlinks — no reinstall needed.

### Update

```bash
cd Benmore-Meridian
git pull
bm update          # pulls + reinstalls all skills
```

---

## Commands

```
Core
  bm install [--rsync]          Symlink all skills → ~/.claude/skills/
  bm status  [--json]           Show skill status (rich table or JSON)
  bm update  [name] [--rsync]   git pull + reinstall one or all
  bm plugins                    Detect + guide Superpowers / Double Shot Latte
  bm doctor                     Full health check

Skills
  bm skill add <name>                   Add a new general skill
  bm skill add <name> --project <p>     Add a project-scoped skill
  bm skill list [--project <p>] [--json] List skills, filter by project
  bm skill generalize <name>            Promote project skill → general
  bm skill info <name>                  Show path, scope, status, source

Registry
  bm registry sync              Scan ~/.claude/skills/ and reconcile
  bm registry list [--json]     List all registered skills
```

All commands support `--help` for detailed usage.

---

## Project Skill Lifecycle

Skills start project-specific and graduate to general:

```bash
# 1. Create a project-scoped skill
bm skill add my-deploy --project my-project

# 2. Edit the generated SKILL.md
$EDITOR skills/my-project/my-deploy/SKILL.md

# 3. Install it (symlinked as ~/.claude/skills/my-deploy)
bm install

# 4. Later, when it proves useful everywhere:
bm skill generalize my-deploy
# → moves skills/my-project/my-deploy/ to skills/my-deploy/
# → updates symlink
# → updates registry
```

---

## Claude Integration

`bm` is designed so Claude agents can query it directly:

```bash
# In a Claude Code session or hook:
bm status --json          # → JSON array of {name, status, scope, project}
bm registry list --json   # → JSON array of all registry entries
bm skill list --json      # → JSON array of skills with paths
```

**In your CLAUDE.md:**

```markdown
## Skills

Run `bm status --json` to see all installed skills and their status.
Run `bm doctor` for a health check before working on skill-related tasks.
```

**Claude can also install skills directly:**

```bash
# Agent adds a project skill, installs it, verifies
bm skill add new-feature --project my-project
bm install
bm skill info new-feature
```

---

## How to Test

### Unit Tests

```bash
cd bm
uv sync --all-extras          # install dev deps
uv run pytest -v              # 27 tests
uv run mypy bm/               # strict type check — 0 errors
uv run ruff check bm/ tests/  # lint
```

Or with make:

```bash
make check-all   # ruff + mypy + pytest in < 30s
```

### Manual End-to-End

```bash
# 1. Verify CLI loads
bm --help
bm skill --help
bm registry --help

# 2. Full status (JSON — pipe to jq or python3)
bm status --json | python3 -m json.tool | head -20

# 3. Install and verify a symlink
bm install
ls -la ~/.claude/skills/vercel-cli         # → .../Benmore-Meridian/skills/vercel-cli
ls -la ~/.claude/skills/pcs-migration      # → .../skills/pcs/pcs-migration  (flat!)

# 4. Project skill lifecycle
bm skill add smoketest --project testing
bm install
ls -la ~/.claude/skills/smoketest          # → symlink
bm skill generalize smoketest
ls skills/smoketest/                       # now in top-level skills/
bm doctor                                  # still green

# 5. Registry
bm registry sync
bm registry list --json | python3 -c \
  "import sys,json; print(len(json.load(sys.stdin)), 'skills in registry')"

# 6. Cleanup smoke test
rm -rf skills/testing skills/smoketest
bm install
```

---

## Skills Overview

| Category | Skills |
|----------|--------|
| 🚀 Production | `django-production`, `frontend-productionize`, `productionize-app`, `fastapi-templates`, `vercel-cli` |
| 🔒 Security | `dependency-security-audit`, `audit-trail`, `gdpr-compliance`, `multi-tenant-guard` |
| 🌐 SEO | `ai-seo`, `seo-audit`, `programmatic-seo` |
| 📄 Documents | `pdf`, `xlsx`, `presentation-maker`, `release-notes` |
| 🛠️ Dev Tools | `mcp-builder`, `modern-terminal-setup`, `skill-creator`, `find-skills` |
| 💳 Payments | `stripe-integration`, `stripe_processing` |
| 🏗️ PCS (scoped) | `pcs-migration`, `pcs-new-service`, `pcs-add-endpoint`, + 4 more |

Full list: [`skills/SKILLS_INVENTORY.md`](../skills/SKILLS_INVENTORY.md)

---

## Development

```bash
cd bm

# Install with dev dependencies
uv sync --all-extras

# Format + lint
make fmt

# Full check suite
make check-all
```

### Adding a Skill

1. `bm skill add my-skill` (or `--project p` for scoped)
2. Edit `skills/my-skill/SKILL.md` — add frontmatter + instructions
3. `bm install` — symlinks immediately
4. Test in Claude Code
5. Commit + PR

### Tech Stack

| Tool | Purpose |
|------|---------|
| [Typer](https://typer.tiangolo.com/) | CLI framework — Click + type annotations |
| [Rich](https://rich.readthedocs.io/) | Terminal output — tables, panels, progress |
| `dataclasses` + `Enum` | Typed models — zero extra deps |
| [uv](https://github.com/astral-sh/uv) | Fast package management |
| [ruff](https://github.com/astral-sh/ruff) | Lint + format |
| [mypy](https://mypy.readthedocs.io/) | Strict type checking |
| [pytest](https://pytest.org/) | Tests with coverage |

---

## License

MIT — see [LICENSE](../LICENSE)

---

> Part of [Benmore-Meridian](https://github.com/Benmore-Studio/Benmore-Meridian) — the Claude Code skills repo for Benmore Studio.
