# bm CLI UX Overhaul — Design Spec

**Date:** 2026-03-12
**Status:** Approved

## Summary

Transform `bm` from a passive command reference into a smart, actionable tool manager. Five changes:

1. **Dashboard** — `bm` (no args) shows health stats + full command guide
2. **`bm setup`** — one-shot install everything (skills, tools, prereqs)
3. **Smart doctor** — diagnose + offer auto-fix
4. **Sentry bug fix** — external skill deletion guard uses `source` not `install_method`
5. **Prereqs module** — detect Python, uv, brew/apt/winget/scoop, Claude CLI

## Cross-Platform Support

All prereq checks and tool installation must work on:
- **macOS** — Homebrew
- **Linux** — apt-get
- **Windows** — winget (primary), scoop (fallback), chocolatey (fallback)

## 1. Dashboard (`bm` with no args)

### Behavior

Running `bm` with no arguments shows a Rich-formatted dashboard:

```
╭─ bm · Benmore Skill Manager v1.1.0 ───────────────────────────────╮
│  Skills: 24/24 ✅   │   Tools: 6/8 ⚠    │   Plugins: 2/2 ✅       │
╰────────────────────────────────────────────────────────────────────╯

⚠  2 tools missing: bat, delta
   → bm setup                        # fix everything automatically

── Getting Started ──────────────────────────────────────────────────

  bm setup                 Install everything: skills, tools, plugins
  bm doctor                Full health check — find and fix problems
  bm update                Git pull latest + reinstall all skills

── Skills ───────────────────────────────────────────────────────────

  bm install               Symlink all skills → ~/.claude/skills/
  bm skill list            Browse all available skills
  bm skill info <name>     Details on a specific skill
  bm skill add <name>      Create a new skill from scratch
  bm skill write <name>    Interactive skill builder with prompts
  bm skill remove <name>   Uninstall a skill
  bm skill generalize <name>  Promote project skill → general

── Tools ────────────────────────────────────────────────────────────

  bm tools list            Show dev tools (ripgrep, bat, fzf, etc.)
  bm tools install         Install all missing tools via brew/apt
  bm tools install bat     Install a specific tool

── Plugins ──────────────────────────────────────────────────────────

  bm plugins               Check Superpowers + Double Shot Latte

── Registry ─────────────────────────────────────────────────────────

  bm registry list         Show all tracked skills
  bm registry sync         Detect externally installed skills

── Options ──────────────────────────────────────────────────────────

  --json                   Machine-readable output (status, skill list)
  --dry-run                Preview changes without writing
  --rsync                  Force file copy instead of symlinks
```

### Implementation

- Add a Typer `@app.callback(invoke_without_command=True)` that renders the dashboard when no subcommand is given
- Pass `ctx: typer.Context` and check `ctx.invoked_subcommand is None`
- Health stats come from existing `discover_skills()`, `TOOLS`, `get_plugin_status()`
- Warnings are context-aware: only show sections with problems

## 2. `bm setup`

### Behavior

One-shot command that installs everything missing:

1. Check prerequisites (Python, uv, brew/apt/winget, claude)
2. Install skills (`bm install` logic)
3. Install missing tools (`bm tools install` logic)
4. Check plugins (print guidance for missing ones)

### Flags

- `--yes` — skip confirmation prompts (for Claude agents)
- `--dry-run` — preview what would happen

### Output

```
🔍 Checking prerequisites...
  ✅ Python 3.12
  ✅ uv
  ✅ brew
  ⚠  claude CLI not found
     → brew install claude-code

📦 Installing 24 skills...
  ✅ 24 skills → ~/.claude/skills/

🛠  Installing missing tools...
  ✅ bat installed
  ✅ delta installed

🔌 Plugins:
  ✅ Superpowers
  ⚠  Double Shot Latte
     → claude plugins install compound-engineering

✅ Setup complete! 24 skills, 8/8 tools
```

## 3. Smart Doctor

### Behavior

Current doctor just reports. New doctor diagnoses AND offers to fix:

- Broken/missing skills → offer to reinstall
- Missing tools → offer to install
- Missing plugins → print install command
- `--yes` auto-fixes without prompting

### Implementation

Rewrite `doctor()` command to:
1. Check skills → if broken, ask to reinstall
2. Check tools → if missing, ask to install
3. Check plugins → print commands
4. Check prereqs → warn if missing

## 4. Sentry Bug Fix

### Problem

`installer.py:155` checks `entry.install_method == InstallMethod.EXTERNAL` but `registry.sync()` never assigns `InstallMethod.EXTERNAL` to non-symlinked dirs — it assigns `InstallMethod.COPY`.

### Fix

Change guard to `entry.source == SkillSource.EXTERNAL` which IS correctly set by sync().

## 5. Prereqs Module

### New file: `bm/bm/prereqs.py`

```python
@dataclass
class Prereq:
    name: str
    check_cmd: str        # command to verify (e.g. "uv")
    install_commands: dict[str, str]  # platform → install command
    required: bool        # True = blocks setup, False = warning only

PREREQS = [
    Prereq("Python 3.11+", "python3", {...}, required=True),
    Prereq("uv", "uv", {
        "darwin": "brew install uv",
        "linux": "curl -LsSf https://astral.sh/uv/install.sh | sh",
        "win32": "winget install astral-sh.uv",
    }, required=False),
    Prereq("brew", "brew", {
        "darwin": '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"',
    }, required=False),  # macOS only
    Prereq("Claude Code", "claude", {
        "darwin": "brew install claude-code",
        "linux": "npm install -g @anthropic-ai/claude-code",
        "win32": "npm install -g @anthropic-ai/claude-code",
    }, required=False),
]
```

Returns list of `(prereq, is_installed)` tuples. Used by `setup` and `doctor`.

## File Ownership (for parallel agents)

| Agent | Owns (creates/edits) |
|-------|---------------------|
| 1 — Prereqs | `bm/bm/prereqs.py` (new), `bm/tests/test_prereqs.py` (new) |
| 2 — Sentry fix | `bm/bm/installer.py`, `bm/bm/registry.py` |
| 3 — Dashboard | `bm/bm/cli.py` (callback + `_render_dashboard()` helper) |
| 4 — Setup cmd | `bm/bm/cli.py` (new `setup()` command) |
| 5 — Smart Doctor | `bm/bm/cli.py` (rewrite `doctor()` command) |

**Note:** Agents 3, 4, 5 all touch cli.py — use worktrees and merge sequentially.
