# AGENTS.md — Claude Code Integration Guide

This file tells Claude Code agents how to work with the Benmore-Meridian skills repo
and the `bm` CLI tool.

## Quick Context

```bash
bm status --json          # JSON array of all skills and their install status
bm registry list --json   # JSON array of registry entries (source, scope, install method)
bm skill list --json      # JSON array of skills with paths and descriptions
bm doctor                 # Human-readable health check
```

## What bm Does

`bm` (Benmore Skill Manager) manages Claude Code skills:
- Skills live in `skills/` in this repo
- `bm install` symlinks them all into `~/.claude/skills/`
- PCS project skills live in `skills/pcs/` but are installed flat as `pcs-*`
- A registry at `~/.bm/registry.json` tracks every installed skill

## Skill Lifecycle (Agent Workflow)

```bash
# Add a project-scoped skill
bm skill add <name> --project <project>
# → creates skills/<project>/<name>/SKILL.md

# Install it (agents can run this)
bm install
# → ~/.claude/skills/<name> is now a symlink

# Check status
bm skill info <name>

# Promote to general when proven
bm skill generalize <name>
# → moves skills/<project>/<name>/ → skills/<name>/
# → re-symlinks, updates registry
```

## JSON Output Schema

### `bm status --json`

```json
[
  {
    "name": "vercel-cli",
    "status": "symlinked",  // symlinked | copied | missing | broken
    "scope": "general",     // general | project
    "project": ""           // project name if scope == "project"
  }
]
```

### `bm registry list --json`

```json
[
  {
    "name": "vercel-cli",
    "installed_path": "/Users/.../.claude/skills/vercel-cli",
    "source": "repo",       // repo | marketplace | external
    "scope": "general",
    "project": "",
    "version": "1.0.0",
    "install_method": "symlink"  // symlink | copy | external | none
  }
]
```

## Available Skills by Category

Run `bm skill list --json` for the live list. Key categories:

| Category | Skills |
|----------|--------|
| Deployment | `vercel-cli`, `fastapi-templates`, `django-production` |
| Security | `audit-trail`, `gdpr-compliance`, `multi-tenant-guard`, `dependency-security-audit` |
| SEO | `ai-seo`, `seo-audit`, `programmatic-seo` |
| Documents | `pdf`, `xlsx`, `presentation-maker`, `release-notes` |
| PCS (scoped) | `pcs-migration`, `pcs-new-service`, `pcs-add-endpoint`, `pcs-add-kafka-event`, `pcs-integration-test`, `pcs-kong-route`, `pcs-pr-review` |

## Running Tests

```bash
cd bm
uv run pytest -v              # 27 unit tests
uv run mypy bm/               # strict type check
make check-all                # ruff + mypy + pytest
```

## Adding a New Skill

1. `bm skill add <name>` (or `--project <p>` for scoped)
2. Edit `skills/<name>/SKILL.md` — add `name:`, `description:`, trigger conditions, instructions
3. `bm install` — symlinks it immediately
4. Verify: `bm skill info <name>`
5. Commit and PR

## Repo Structure

```
Benmore-Meridian/
├── bm/              ← CLI package (pipx install ./bm)
│   ├── bm/          ← Python source (cli, installer, registry, status, updater, plugins)
│   └── tests/       ← 27 pytest tests
├── skills/          ← All general skills
│   └── pcs/         ← Project-scoped PCS skills
├── guides/          ← Documentation and guides
├── AGENTS.md        ← This file
├── CHANGELOG.md     ← Release history
└── LICENSE          ← MIT
```
