# AGENTS.md — Claude Code Integration Guide

This file tells Claude Code agents how to work with the Benmore-Meridian skills repo
and the `bm` CLI tool.

## Quick Context

```bash
bm status --json          # JSON array of all skills and their install status
bm suggest . --top 4 --cache --install
                          # Recommend, cache, and install a small relevant skill set
bm uninstall --all --yes   # Remove bm-managed installed skills without deleting source files
bm registry list --json   # JSON array of registry entries (source, scope, install method)
bm skill list --json      # JSON array of skills with paths and descriptions
bm schema json status     # JSON Schema for a public --json output
bm schema openapi         # Generated OpenAPI for benmore_client models
bm doctor                 # Human-readable health check
```

## What bm Does

`bm` (Benmore Skill Manager) manages Claude Code skills:
- Skills live in `skills/` in this repo
- `bm install` symlinks them all into `~/.claude/skills/`
- `bm suggest . --install --cache` installs only relevant skills and saves the recommendation set in `~/.bm/suggestions.json`
- `bm uninstall --all` unlinks bm-managed skills and preserves external skills
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
| Security | `audit-trail`, `gdpr-compliance`, `multi-tenant-guard`, `multi-tenant-scan`, `dependency-security-audit`, `hipaa-compliance-guard`, `security-compliance-audit`, `healthcare-audit-logger`, `django-react-2fa`, `otp-verification`, `role-based-authentication`, `universal-auth`, `service-invariant-guard` |
| SEO | `ai-seo`, `seo-audit`, `programmatic-seo` |
| Documents | `pdf`, `xlsx`, `presentation-maker`, `release-notes` |
| PCS (scoped) | `pcs-migration`, `pcs-new-service`, `pcs-add-endpoint`, `pcs-add-kafka-event`, `pcs-integration-test`, `pcs-kong-route`, `pcs-pr-review` |

## Running Tests

```bash
cd bm
uv run pytest -q              # 93 tests
uv run ruff format --check bm/ tests/
uv run ruff check bm/ tests/
uv run mypy bm/               # strict type check
uv run --extra dev basedpyright
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
│   ├── bm/          ← Python source (cli, installer, registry, schemas, native fallback)
│   ├── native/      ← Optional PyO3 helper crate
│   └── tests/       ← 88 pytest tests
├── skills/          ← All general skills
│   └── pcs/         ← Project-scoped PCS skills
├── guides/          ← Documentation and guides
├── AGENTS.md        ← This file
├── CHANGELOG.md     ← Release history
└── LICENSE          ← MIT
```
