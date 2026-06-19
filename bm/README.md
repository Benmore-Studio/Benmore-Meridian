# bm

**The skill manager for Claude Code.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-1.10.1-green)](https://github.com/Benmore-Studio/Benmore-Meridian)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)
[![Tests](https://img.shields.io/badge/tests-88%20passing-brightgreen)](tests/)
[![Skills](https://img.shields.io/badge/skills-50%2B-purple)](../skills/)
[![skills.sh](https://skills.sh/b/Benmore-Studio/Benmore-Meridian)](https://skills.sh/Benmore-Studio/Benmore-Meridian)

```bash
uv tool install benmore-bm
bm install
```

That's it. 50+ Claude Code skills are now symlinked and ready.

---

## Why bm?

**Without bm:**

- You copy skill directories by hand into `~/.claude/skills/` — and they go stale the moment you run `git pull`.
- There is no record of what is installed, where it came from, or whether it still works.
- Project-specific skills live in the same flat pile as general ones — no way to scope, promote, or retire them.
- Claude agents have no machine-readable way to query what skills are available.

**With bm:**

- **Symlink-first install** — skills live in the repo. `bm install` creates symlinks in `~/.claude/skills/`. Edit a skill file once, and every Claude Code session sees the change immediately.
- **Clean uninstall** — `bm uninstall --all` unlinks bm-managed installed skills without deleting source files or external skills.
- **Context-aware suggestions** — `bm suggest . --top 4 --install --cache` recommends only relevant skills, installs them, and saves the recommendation cache.
- **Project skill lifecycle** — create project-scoped skills (`bm skill add x --project myapp`), then promote them to general availability (`bm skill generalize x`) once they prove universal.
- **Registry tracking** — every installed skill is recorded in `~/.bm/registry.json` with its source, scope, and install method, regardless of how it got there.
- **Claude-native output** — every command supports `--json` so Claude agents can query `bm status --json` directly and act on the result.

---

## Installation

### Requirements

- Python 3.11+
- [Claude Code](https://claude.ai/code) (`brew install claude`)

### Install bm

PyPI installs are the default for users:

```bash
uv tool install benmore-bm
# or
pipx install benmore-bm

bm install
bm doctor
```

Contributor installs keep the CLI editable against this repository:

```bash
git clone https://github.com/Benmore-Studio/Benmore-Meridian
cd Benmore-Meridian

uv tool install --editable ./bm
# or
pip install -e ./bm

bm install
bm plugins
bm doctor
```

Native acceleration is optional. Source installs run with the pure Python fallback.
To build the PyO3 helper locally, install a Rust toolchain and run:

```bash
cd bm
uv run --extra dev maturin develop --manifest-path native/Cargo.toml
```

### Update

```bash
cd Benmore-Meridian
git pull
bm update          # git pull + reinstall all skills
```

---

## Commands Reference

All commands support `--help` for detailed usage.

```
Core
  bm install  [--rsync] [--dry-run]              Symlink all skills → ~/.claude/skills/
  bm uninstall [names...] [--all] [--dry-run]    Unlink bm-managed installed skills
  bm status   [--json]                           Show skill status table or JSON
  bm update   [name] [--rsync] [--dry-run]       git pull + reinstall one or all skills
  bm doctor                                      Full health check: skills + plugins
  bm plugins                                     Detect + guide Superpowers / Double Shot Latte

Skills
  bm skill add <name> [--project <p>] [--from <path>]   Create a new skill
  bm skill list [--project <p>] [--json]                List skills with optional filter
  bm skill info <name>                                   Show skill path, scope, status, source
  bm skill generalize <name>                             Promote project skill to general
  bm skill remove <name> [--dry-run]                     Remove a skill (v1.1)

Discovery
  bm suggest [path] [--top N] [--install] [--cache]       Recommend and optionally install/cache skills

Registry
  bm registry list [--json]                      List all registry entries
  bm registry sync [--dry-run]                   Scan ~/.claude/skills/ and reconcile registry

Schemas
  bm schema json <name> [--output <path>]        Print a CLI JSON Schema artifact
  bm schema openapi [--output <path>]            Print generated benmore_client OpenAPI
```

---

### `bm install`

```
bm install [--rsync]
```

Symlinks every skill discovered in the repo's `skills/` directory into `~/.claude/skills/`. Idempotent — safe to run repeatedly. Existing symlinks and copies are replaced cleanly before re-installing.

**Install strategy:** symlink first, `shutil.copytree` fallback on `OSError`. Pass `--rsync` to force a file copy for every skill (useful on systems where symlinks across filesystems are unreliable).

**Example:**

```
$ bm install

╭─────────────────── Installing Skills ───────────────────╮
│ Skill                  Scope      Result                 │
│ ai-seo                 general    ✅ symlinked            │
│ audit-trail            general    ✅ symlinked            │
│ dependency-security-audit general ✅ symlinked            │
│ pcs-migration          pcs        ✅ symlinked            │
│ pcs-new-service        pcs        ✅ symlinked            │
│ vercel-cli             general    ✅ symlinked            │
│ ...                                                      │
╰──────────────────────────────────────────────────────────╯

Done! 52 skills → /Users/you/.claude/skills
Run bm plugins to verify plugin requirements.
```

**Flags:**

| Flag | Description |
|------|-------------|
| `--rsync` | Force file copy instead of symlinks |
| `--dry-run` | Preview what would be installed without writing (v1.1) |

---

### `bm status`

```
bm status [--json]
```

Shows the installation status of every skill discovered in the repo. Displays a Rich table by default, or a JSON array with `--json` for machine consumption.

**Status values:**

| Status | Meaning |
|--------|---------|
| `symlinked` | Symlink exists and resolves correctly |
| `copied` | Directory copy exists in `~/.claude/skills/` |
| `missing` | Not installed at all |
| `broken` | Symlink exists but target path is gone |

**Example (table):**

```
$ bm status

╭──────────────────────── Skill Status ────────────────────────╮
│ Skill                       Status   Scope                   │
│ ai-seo                        ✅     general                 │
│ pcs-migration                 ✅     pcs                     │
│ my-new-skill                  ❌     general                 │
╰───────────────────────────────────────────────────────────────╯
╭───── Plugins ─────╮
│   ✅ Superpowers  │
│   ✅ Double Shot  │
╰────────────────────╯
```

**Example (JSON — for Claude agents):**

```bash
$ bm status --json
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
  }
]
```

**Flags:**

| Flag | Description |
|------|-------------|
| `--json` | Emit JSON array instead of Rich table |

---

### `bm update`

```
bm update [name] [--rsync]
```

Runs `git pull --ff-only` in the repo root, then reinstalls skills. Without a `name` argument all skills are reinstalled. With a name, only that skill is updated.

**Example (all skills):**

```
$ bm update

Pulling latest changes...
Already up to date.
✅ 52 linked  ⚙️  0 copied
```

**Example (one skill):**

```
$ bm update vercel-cli
Pulling latest changes...
From github.com:Benmore-Studio/Benmore-Meridian
   7d609a3..a1b2c3d  main -> origin/main
✅ vercel-cli: symlinked
```

**Flags:**

| Flag | Description |
|------|-------------|
| `name` | Optional skill name. Omit to update all. |
| `--rsync` | Force copy instead of symlinks after pulling |
| `--dry-run` | Preview reinstall operations without writing (v1.1) |

---

### `bm doctor`

```
bm doctor
```

Full health check. Reports how many skills are installed, highlights missing or broken ones, and checks that Superpowers and Double Shot Latte plugins are present.

**Example (healthy):**

```
$ bm doctor

──────────────────── bm doctor ────────────────────
Skills: 52/52 installed
Plugin ✅ Superpowers
Plugin ✅ Double Shot Latte

Everything looks great! 🎉
```

**Example (issues detected):**

```
$ bm doctor

──────────────────── bm doctor ────────────────────
Skills: 49/52 installed
  → run bm install to fix 3 missing, 0 broken
Plugin ✅ Superpowers
Plugin ⚠️  Double Shot Latte
  → run bm plugins for instructions
```

No flags.

---

### `bm plugins`

```
bm plugins
```

Checks whether Superpowers and Double Shot Latte Claude plugins are installed by inspecting their expected filesystem markers. For any missing plugin it prints a full installation guide inside a panel.

**Detection markers:**

| Plugin | Detected by |
|--------|-------------|
| Superpowers | `~/.claude/plugins/cache/claude-plugins-official` |
| Double Shot Latte | `~/.agents/skills/` |

**Example (both present):**

```
$ bm plugins
✅ Superpowers — installed
✅ Double Shot Latte — installed

All plugins ready!
```

**Example (one missing):**

```
$ bm plugins
✅ Superpowers — installed
╭──── Install Double Shot Latte ─────────────────────────────────╮
│ Install Double Shot Latte (compound-engineering):              │
│   claude plugins install compound-engineering                  │
│   GitHub: https://github.com/EveryInc/compound-engineering-plugin │
╰────────────────────────────────────────────────────────────────╯
```

No flags.

---

### `bm skill add`

```
bm skill add <name> [--project <p>] [--from <path>]
```

Scaffolds a new skill. Without `--project` the skill is created as a general skill at `skills/<name>/SKILL.md`. With `--project` it is placed at `skills/<project>/<name>/SKILL.md` and registered as project-scoped.

The generated `SKILL.md` includes minimal frontmatter and placeholder instructions. Edit it before running `bm install`.

**Example (general):**

```
$ bm skill add stripe-webhooks
✅ Created general skill 'stripe-webhooks' at skills/stripe-webhooks
Edit skills/stripe-webhooks/SKILL.md, then run bm install to activate.
```

**Example (project-scoped):**

```
$ bm skill add auth --project myapp
✅ Created project 'myapp' skill 'auth' at skills/myapp/auth
Edit skills/myapp/auth/SKILL.md, then run bm install to activate.
```

**Example (copy from existing directory):**

```
$ bm skill add auth-v2 --from skills/myapp/auth
✅ Created general skill 'auth-v2' at skills/auth-v2
```

**Flags:**

| Flag | Description |
|------|-------------|
| `<name>` | Required. Skill name (used as directory name and in SKILL.md). |
| `--project`, `-p` | Project scope. Creates under `skills/<project>/`. |
| `--from` | Copy content from an existing directory instead of generating a template. |

---

### `bm skill list`

```
bm skill list [--project <p>] [--json]
```

Lists all skills discovered in the repo. Filter to a single project with `--project`. Use `--json` for machine-readable output including file paths.

**Example (table):**

```
$ bm skill list

 Skill                       Scope     Description
 ai-seo                      general   Optimize for AI search engines...
 audit-trail                 general   Add audit logging to API endpoi...
 pcs-migration               pcs       Create Alembic database migrati...
```

**Example (filtered):**

```
$ bm skill list --project pcs

 Skill                Scope   Description
 pcs-add-endpoint     pcs     Add CRUD endpoints to PCS microservic...
 pcs-migration        pcs     Create Alembic database migrations
 pcs-new-service      pcs     Scaffold a complete new PCS microservi...
```

**Example (JSON):**

```bash
$ bm skill list --json
[
  {
    "name": "ai-seo",
    "scope": "general",
    "project": "",
    "path": "/Users/you/Benmore-Meridian/skills/ai-seo"
  },
  {
    "name": "pcs-migration",
    "scope": "project",
    "project": "pcs",
    "path": "/Users/you/Benmore-Meridian/skills/pcs/pcs-migration"
  }
]
```

**Flags:**

| Flag | Description |
|------|-------------|
| `--project`, `-p` | Filter results to one project. |
| `--json` | Emit JSON array with file paths. |

---

### `bm skill info`

```
bm skill info <name>
```

Shows the full details for a single skill: its path in the repo, scope, current installation status, source, version, and description read from `SKILL.md` frontmatter.

**Example:**

```
$ bm skill info pcs-migration

pcs-migration
  Path:    /Users/you/Benmore-Meridian/skills/pcs/pcs-migration
  Scope:   project (project: pcs)
  Status:  ✅ symlinked
  Source:  repo
  Version: 1.0.0
  Desc:    Create Alembic database migrations for PCS microservices
```

---

### `bm skill generalize`

```
bm skill generalize <name>
```

Promotes a project-scoped skill to general availability. Moves the skill directory from `skills/<project>/<name>/` to `skills/<name>/`, updates its symlink in `~/.claude/skills/`, and updates its registry entry (`scope` → `general`, `project` → `""`).

Use this when a skill that started as project-specific proves useful across all projects.

**Example:**

```
$ bm skill generalize auth

✅ Moved 'auth' from skills/myapp → skills/auth
Reinstalled: symlinked
```

After this command:
- `skills/myapp/auth/` no longer exists
- `skills/auth/` contains the skill
- `~/.claude/skills/auth` symlink points to the new location
- Registry reflects `scope: general`

---

### `bm skill remove` *(v1.1)*

```
bm skill remove <name> [--dry-run]
```

Removes a skill: deletes its directory from `skills/`, removes the symlink or copy from `~/.claude/skills/`, and removes its registry entry. Pass `--dry-run` to preview what would be deleted without writing.

**Example:**

```
$ bm skill remove smoketest
✅ Removed skill 'smoketest'
```

**Example (dry-run):**

```
$ bm skill remove smoketest --dry-run

╭─────────── Dry-run: planned operations ───────────────╮
│ Action    Target                                      │
│ remove    ~/.claude/skills/smoketest                  │
│ remove    skills/smoketest/                           │
│ registry_remove  smoketest                            │
╰───────────────────────────────────────────────────────╯
Dry-run complete — 3 operations would run (nothing written).
```

**Flags:**

| Flag | Description |
|------|-------------|
| `--dry-run` | Preview deletions without writing. |

---

### `bm registry list`

```
bm registry list [--json]
```

Lists all entries in `~/.bm/registry.json`. Each entry records the skill name, its source (`repo` / `marketplace` / `external`), scope, and how it was installed.

**Example (table):**

```
$ bm registry list

Registry (52 skills)
 Name                    Source       Scope     Install
 ai-seo                  repo         general   symlink
 pcs-migration           repo         project   symlink
 my-external-skill       external     general   copy
```

**Example (JSON):**

```bash
$ bm registry list --json
[
  {
    "name": "ai-seo",
    "installed_path": "/Users/you/.claude/skills/ai-seo",
    "source": "repo",
    "scope": "general",
    "project": "",
    "version": "1.0.0",
    "install_method": "symlink"
  }
]
```

**Flags:**

| Flag | Description |
|------|-------------|
| `--json` | Emit full JSON array with all fields. |

---

### `bm registry sync`

```
bm registry sync
```

Scans `~/.claude/skills/` and reconciles the registry to match reality. Detects skills installed outside of `bm` (from Claude marketplace, manually copied, etc.) and records their source. Safe to run any time; preserves existing scope and project metadata.

**Source detection logic:**

- Symlink resolves into the repo directory → `repo`
- Symlink resolves into `~/.agents/` → `marketplace`
- Plain directory or symlink pointing elsewhere → `external`

**Example:**

```
$ bm registry sync
Registry synced. 50 → 52 entries (+2 new)
```

No flags. (A `--dry-run` flag is planned for v1.1.)

---

## --dry-run (v1.1)

Several commands accept `--dry-run` to preview what would happen without writing any files.

This is implemented via `DryRunContext` in `bm/dryrun.py`. Each operation that would touch the filesystem calls `ctx.record(verb, target, source)` instead of executing. At the end, `ctx.render()` prints a Rich table of planned operations.

**Operations recorded:**

| Verb | What it represents |
|------|--------------------|
| `symlink` | Create symlink in `~/.claude/skills/` |
| `copy` | Copy skill directory into `~/.claude/skills/` |
| `remove` | Delete symlink, copy, or source directory |
| `registry_add` | Write entry to `~/.bm/registry.json` |
| `registry_remove` | Remove entry from `~/.bm/registry.json` |

**Example output:**

```
$ bm install --dry-run

╭──────────── Dry-run: planned operations ──────────────────╮
│ Action   Target                            Source          │
│ symlink  ~/.claude/skills/ai-seo           skills/ai-seo  │
│ symlink  ~/.claude/skills/vercel-cli       skills/vercel-cli │
│ symlink  ~/.claude/skills/pcs-migration    skills/pcs/pcs-migration │
│ ...                                                        │
╰────────────────────────────────────────────────────────────╯
Dry-run complete — 52 operations would run (nothing written).
```

When `dry_run=False` (the default), `ctx.record()` is a no-op and `ctx.render()` is never called — zero overhead on normal runs.

---

## SKILL.md Validation (v1.1)

Every skill must contain a `SKILL.md` file with YAML frontmatter. `bm install` (and `bm skill add`) validate frontmatter before installing; invalid skills are skipped with a warning.

### Frontmatter format

```yaml
---
name: my-skill
description: Does something useful for the team
version: 1.2.0
author: Your Name
tags: python, django, api
---

# my-skill

Full skill instructions follow the frontmatter...
```

### Required vs optional fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Must match the directory name |
| `description` | Yes | One-line summary shown in `bm skill list` |
| `version` | No | Defaults to `1.0.0` if absent |
| `author` | No | Skill author name |
| `tags` | No | Comma-separated tags for discovery |

### On validation failure

When a required field is missing or `name` does not match the directory name, `bm install` prints a warning and skips that skill:

```
⚠️  Skipping 'my-skill': frontmatter missing required field 'description'
```

The skill is not added to the registry and no symlink is created. Fix the `SKILL.md` and run `bm install` again.

The current installer already reads `description` from frontmatter (`installer._read_skill_description`). Full frontmatter validation via `bm/validator.py` is shipping in v1.1.

---

## Architecture

`bm` is a small, dependency-light Python package. Each module has a single responsibility.

```
bm/
├── cli.py          Typer CLI — entry point for all commands
├── config.py       Path constants + REPO_ROOT discovery
├── models.py       SkillEntry, RegistryEntry, all enums (pure dataclasses)
├── installer.py    Symlink-first install + skill discovery
├── registry.py     ~/.bm/registry.json persistence
├── status.py       Installed / missing / broken detection per skill
├── dryrun.py       DryRunContext — collect ops without writing (v1.1)
├── validator.py    SKILL.md frontmatter validation (v1.1)
├── updater.py      git pull + reinstall
├── plugins.py      Superpowers + Double Shot Latte detection
└── __init__.py
```

### Module responsibilities

**`config.py`** — Computes `REPO_ROOT` at import time by walking up from `__file__` until it finds a directory containing both `skills/` and `bm/`. Exports `SKILLS_DIR`, `CLAUDE_SKILLS_DIR`, `REGISTRY_FILE`, and `PLUGIN_MARKERS`. No side effects beyond the path walk.

**`models.py`** — All enums (`SkillScope`, `SkillSource`, `InstallResult`, `InstallMethod`, `SkillStatus`) and dataclasses (`SkillEntry`, `RegistryEntry`). Zero external dependencies. `RegistryEntry.from_dict` handles JSON deserialization.

**`installer.py`** — `discover_skills(skills_dir)` crawls the `skills/` tree and returns `SkillEntry` objects. Distinguishes general skills (top-level dirs with `SKILL.md`) from project containers (top-level dirs without `SKILL.md` whose children have `SKILL.md`). `install_skill()` performs symlink-first install with `shutil.copytree` fallback.

**`registry.py`** — `Registry` class wraps `~/.bm/registry.json`. `add()` mutates in-memory only; callers must call `save()`. `batch_add()` adds multiple entries and saves once — avoiding N disk writes during `bm install`. `sync()` reconciles the registry against the live `~/.claude/skills/` directory.

**`status.py`** — `check_skill_status(skill, claude_skills_dir)` inspects the target path: symlink resolves → `SYMLINKED`, symlink broken → `BROKEN`, directory exists → `COPIED`, nothing → `MISSING`.

**`dryrun.py`** — `DryRunContext` collects `DryRunOp` records when `dry_run=True`. `render()` prints a Rich table. When `dry_run=False`, `record()` is a no-op with zero overhead.

**`validator.py`** *(v1.1)* — Reads and validates `SKILL.md` frontmatter. Raises structured errors for missing required fields or name mismatches. Called by `installer.py` before each install.

**`updater.py`** — `git_pull(repo_root)` runs `git pull --ff-only` as a subprocess. `reinstall_all()` calls `discover_skills` + `install_skill` for every skill and returns a `dict[str, InstallResult]`.

**`plugins.py`** — `get_plugin_status()` checks each plugin's filesystem marker (a path that exists when the plugin is installed). `format_install_guide()` returns the human-readable install instructions for a given plugin name.

**`cli.py`** — Typer app with two sub-apps (`skill`, `registry`). All commands are thin wrappers: parse args, delegate to the appropriate module, format output with Rich. `--json` flags bypass Rich rendering and emit raw JSON to stdout.

---

### ASCII Flow: `bm install`

```
bm install [--rsync]
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
  symlink_to(skill.path.resolve())
     ├── success → SYMLINKED
     └── OSError → copytree fallback → COPIED
     │
  result != FAILED?
     └── yes → append to registry batch
     │
     ▼
reg.batch_add(entries)   ← single JSON write (not N writes)
```

---

### ASCII Flow: Project Skill Lifecycle

```
bm skill add pcs-migration --project pcs
     │
     ▼
creates skills/pcs/pcs-migration/SKILL.md
scope = PROJECT, project = "pcs"
     │
bm install
     │
     ▼
~/.claude/skills/pcs-migration → symlink → skills/pcs/pcs-migration/
     │
     │   (skill proves useful everywhere)
     │
bm skill generalize pcs-migration
     │
     ▼
mv skills/pcs/pcs-migration/ → skills/pcs-migration/
re-symlink ~/.claude/skills/pcs-migration → skills/pcs-migration/
update registry: scope=GENERAL, project=""
     │
     ▼
available to all projects
```

---

### ASCII Flow: Auto-discovery of Project Folders

```
skills/
├── vercel-cli/
│   └── SKILL.md      ← has SKILL.md → GENERAL skill
├── pcs/
│   ├── (no SKILL.md) ← no SKILL.md → project container
│   └── pcs-migration/
│       └── SKILL.md  ← PROJECT skill, project="pcs"
└── myteam/           ← any new folder without SKILL.md
    └── myteam-deploy/  is auto-detected as project container
        └── SKILL.md
```

Any directory under `skills/` that lacks a `SKILL.md` at its own level but contains subdirectories that have `SKILL.md` files is treated as a project container. No configuration is required.

---

## Project Skill Lifecycle

The full lifecycle from creation to general availability:

**Step 1: Create a project-scoped skill**

```bash
bm skill add auth --project myapp
# Creates: skills/myapp/auth/SKILL.md
# Registry: scope=project, project=myapp
```

**Step 2: Write the skill**

```bash
$EDITOR skills/myapp/auth/SKILL.md
```

Add your frontmatter and instructions:

```markdown
---
name: auth
description: Django JWT auth setup for the myapp project
version: 1.0.0
author: Your Name
tags: django, auth, jwt
---

# auth

Instructions for Claude to follow when setting up authentication...
```

**Step 3: Install and verify**

```bash
bm install
bm skill info auth
# Status: ✅ symlinked
# Scope: project (project: myapp)
```

The skill is now available as `/auth` in Claude Code sessions.

**Step 4: Graduate to general (when it proves universally useful)**

```bash
bm skill generalize auth
# Moves: skills/myapp/auth/ → skills/auth/
# Updates symlink: ~/.claude/skills/auth → skills/auth/
# Updates registry: scope=general, project=""

bm doctor   # confirm all green
```

The skill is now available across all projects and will survive future `bm install` runs as a general skill.

---

## Registry

The registry lives at `~/.bm/registry.json` and is the single source of truth for what `bm` knows about installed skills.

### File format

```json
{
  "ai-seo": {
    "name": "ai-seo",
    "installed_path": "/Users/you/.claude/skills/ai-seo",
    "source": "repo",
    "scope": "general",
    "project": "",
    "version": "1.0.0",
    "install_method": "symlink"
  },
  "pcs-migration": {
    "name": "pcs-migration",
    "installed_path": "/Users/you/.claude/skills/pcs-migration",
    "source": "repo",
    "scope": "project",
    "project": "pcs",
    "version": "1.0.0",
    "install_method": "symlink"
  }
}
```

### `SkillSource` enum

| Value | Meaning |
|-------|---------|
| `repo` | Installed by `bm install` from this repository |
| `marketplace` | Symlink resolves into `~/.agents/` (Claude marketplace plugin) |
| `external` | Plain directory or symlink pointing to an unrecognized location |

### Why `batch_add` exists

During `bm install`, every skill in the repo is processed in a loop. If each skill called `registry.save()` independently, a 50-skill install would write `~/.bm/registry.json` 50 times. `batch_add(entries)` instead collects all updates in memory and writes the file exactly once. The `add()` method is for single-skill operations (like `bm skill add`) where one write is acceptable.

### `registry sync`

`bm registry sync` scans `~/.claude/skills/` directly and reconciles the registry against what is actually installed — including skills that were installed by means other than `bm` (e.g., a Claude marketplace plugin that drops directories there). It preserves any `scope`, `project`, and `version` metadata already recorded for a skill, updating only `source` and `install_method` based on the current filesystem state.

---

## Claude Integration

`bm` is designed so Claude agents can query it directly during Claude Code sessions.

**Query skill health before working on skill-related tasks:**

```bash
bm status --json          # → JSON array of {name, status, scope, project}
bm registry list --json   # → full registry entries with source and install method
bm skill list --json      # → skills with file paths
```

**In your CLAUDE.md:**

```markdown
## Skills

Run `bm status --json` to see all installed skills and their status.
Run `bm doctor` for a health check before working on skill-related tasks.
```

**Agent can install and verify a new skill in one session:**

```bash
bm skill add new-feature --project my-project
bm install
bm skill info new-feature   # confirm: Status: ✅ symlinked
```

---

## Testing & Development

### Running tests

```bash
cd bm

# Install dev dependencies
uv sync --extra dev

# Release gate
uv run ruff format --check bm/ tests/
uv run ruff check bm/ tests/
uv run mypy bm/
uv run --extra dev basedpyright
uv run pytest tests/ -q
cargo test --manifest-path native/Cargo.toml
```

The optional native helper has a pure Python fallback, but Rust tests must pass
before publishing wheels.

### Manual end-to-end

```bash
# 1. Verify CLI loads
bm --help
bm skill --help
bm registry --help

# 2. Full status in JSON
bm status --json | python3 -m json.tool | head -20

# 3. Install and verify a symlink
bm install
ls -la ~/.claude/skills/vercel-cli         # → .../Benmore-Meridian/skills/vercel-cli
ls -la ~/.claude/skills/pcs-migration      # → .../skills/pcs/pcs-migration (flat name)

# 4. Project skill lifecycle
bm skill add smoketest --project testing
bm install
ls -la ~/.claude/skills/smoketest          # → symlink
bm skill generalize smoketest
ls skills/smoketest/                       # now in top-level skills/
bm doctor                                  # all green

# 5. Registry
bm registry sync
bm registry list --json | python3 -c \
  "import sys,json; print(len(json.load(sys.stdin)), 'skills in registry')"

# 6. Cleanup smoke test
rm -rf skills/testing skills/smoketest
bm install
```

### Tech stack

| Tool | Purpose |
|------|---------|
| [Typer](https://typer.tiangolo.com/) | CLI framework — Click with type annotations |
| [Rich](https://rich.readthedocs.io/) | Terminal output — tables, panels |
| `dataclasses` + `StrEnum` | Typed models — zero extra dependencies |
| [uv](https://github.com/astral-sh/uv) | Fast package management |
| [ruff](https://github.com/astral-sh/ruff) | Lint + format |
| [mypy](https://mypy.readthedocs.io/) | Strict type checking |
| [pytest](https://pytest.org/) | Tests with coverage |
| [hatchling](https://hatch.pypa.io/) | Build backend |

---

## Skills Overview

| Category | Skills |
|----------|--------|
| Production | `django-production`, `frontend-productionize`, `productionize-app`, `fastapi-templates`, `vercel-cli` |
| Security & Compliance | `dependency-security-audit`, `audit-trail`, `gdpr-compliance`, `multi-tenant-guard`, `multi-tenant-scan`, `hipaa-compliance-guard`, `security-compliance-audit`, `healthcare-audit-logger`, `django-react-2fa`, `otp-verification`, `role-based-authentication`, `universal-auth`, `service-invariant-guard` |
| SEO | `ai-seo`, `seo-audit`, `programmatic-seo` |
| Documents | `pdf`, `xlsx`, `presentation-maker`, `release-notes` |
| Dev Tools | `mcp-builder`, `modern-terminal-setup`, `skill-creator`, `find-skills` |
| Payments | `stripe-integration` |
| PCS (project-scoped) | `pcs-migration`, `pcs-new-service`, `pcs-add-endpoint`, and more |

Full inventory: [`skills/SKILLS_INVENTORY.md`](../skills/SKILLS_INVENTORY.md)

---

## License

MIT — see [LICENSE](../LICENSE)

---

> Part of [Benmore-Meridian](https://github.com/Benmore-Studio/Benmore-Meridian) — the Claude Code skills repository for Benmore Studio.
