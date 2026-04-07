---
name: using-bm
description: Use the bm CLI (Benmore skill manager) to install, update, and manage Claude Code skills, prompts, dev tools, and the Benmore project management API. Trigger when the user wants to install/update skills, sync after git pull, browse or create skills/prompts, install dev tools (ripgrep, fd, bat, fzf, etc.), set up git auto-sync hooks, query Benmore projects/teams/Slack channels, look up a project by BEN number, get a project context or status, or run a Benmore API command. Triggers include "install bm skills", "sync skills", "after git pull", "save this prompt", "what projects am I on", "find a skill for X", "bm benmore", "look up BEN-XXX", "channel summary", "team for project".
---

# Using bm

`bm` is the Benmore skill manager — one CLI for skills, prompts, dev tools, plugins, git hooks, and the Benmore project management API.

## Decision tree — which command?

| User intent | Run |
|---|---|
| First-time setup on a fresh machine | `bm setup --yes` |
| Activate / refresh all skills | `bm install` |
| Update everything (git pull + reinstall) | `bm update` |
| Health check | `bm doctor` (add `-y` to auto-fix) |
| Show current state | `bm status` (add `--json` for agents) |
| Browse skills | `bm skill list` |
| Get info about a skill | `bm skill info <name>` |
| Create a new skill (interactive) | `bm skill write <name>` |
| Create a project-scoped skill | `bm skill write <name> -p <project>` |
| Promote project skill → general | `bm skill generalize <name>` |
| Remove a skill | `bm skill remove <name>` |
| Discover skills relevant to a project | `bm suggest <path>` |
| Browse / search saved prompts | `bm prompt list` / `bm prompt search <q>` |
| Save a prompt template | `bm prompt add <name>` |
| Export prompt as Claude `/slash` command | `bm prompt export <name>` (or `--all`) |
| Install dev CLI tools (ripgrep, fd, bat, fzf, etc.) | `bm tools install` |
| Auto-sync skills after `git pull` | `bm hooks install` |
| List all assigned Benmore projects | `bm benmore list` |
| Single dashboard view | `bm benmore overview` |
| Resolve a BEN number → project ID | `bm benmore lookup BEN-XXX` (use `--id` to pipe) |
| Full project context (team, channel, blockers) | `bm benmore context <id>` |
| Project health / blockers | `bm benmore status <id>` |
| Team members for a project | `bm benmore team <id>` |
| Channel summary over time | `bm benmore summary <id> --days 7` |
| Inline update project metadata | `bm benmore list --set-working-on "BEN-185:..."` |

## Core principles

- **Symlink-first.** `bm install` symlinks `skills/<name>` → `~/.claude/skills/<name>`. Editing the source file reflects everywhere instantly — no reinstall needed.
- **Always prefer `bm` commands** over manual `cp`/`ln`/`mkdir` into `~/.claude/`. The registry tracks every install; manual operations bypass tracking and break `bm doctor`.
- **`--json` everywhere.** Every list/status command supports `--json` for piping to `jq` or feeding agents.
- **Pipe-friendly.** Use `bm benmore lookup BEN-185 --id` to get just the UUID, then pipe into `bm benmore summary $(...) --days 7`.

## Common workflows

### After cloning the repo (new machine)

```bash
pip install -e ./bm
bm setup --yes        # installs skills + tools + plugins
bm hooks install      # auto-sync on future git pulls
```

### After `git pull` (without auto-sync hooks)

```bash
bm install            # or `bm update` to git pull + install
```

### Creating a new skill from scratch

```bash
bm skill write my-thing      # interactive — prompts for description + triggers
# (edit skills/my-thing/SKILL.md as needed)
bm install                    # activate via symlink
bm doctor                     # verify
```

For the actual skill *contents*, follow the `skill-creator` skill's 6-step process (understand → plan → init → edit → package → iterate). `bm skill write` creates the directory and a SKILL.md stub, but the structure and writing principles come from `skill-creator`.

### Project skill that becomes generally useful

```bash
bm skill write deploy-helper -p pcs   # starts as project-scoped
# (use it for a while, prove it works)
bm skill generalize deploy-helper      # promotes to general (any project)
```

### Querying Benmore projects in your terminal

```bash
# Find a project by BEN number or name
bm benmore lookup 185             # → Kimmah Lewis [BEN-185]
bm benmore lookup "Jason Steele"

# Get its full context
bm benmore context $(bm benmore lookup 185 --id)

# Channel activity over the last week
bm benmore summary $(bm benmore lookup 185 --id) --days 7

# Full numbered list grouped by phase (like the team Slack format)
bm benmore list

# Update inline
bm benmore list --set-working-on "BEN-185:Building onboarding flow"
```

### Saving and reusing prompts

```bash
bm prompt add my-template        # creates prompts/my-template/PROMPT.md
# (edit the file)
bm prompt export my-template     # becomes /my-template in Claude Code
bm prompt star my-template       # bookmark a favorite
```

## Required setup before using `bm benmore`

Set the API key — one of:

```bash
# Option A: env var (current session)
export BM_API_KEY="bpk_your_api_key_here"

# Option B: persistent config file
mkdir -p ~/.benmore
echo '{"api_key": "bpk_your_api_key_here"}' > ~/.benmore/config
chmod 600 ~/.benmore/config
```

If `bm benmore` says "No API key found", suggest one of the above. If it says "401 Unauthorized", the key is invalid or expired — point the user to the Benmore portal to rotate it.

## When to suggest `bm` proactively

| Situation | Suggest |
|---|---|
| Just finished implementing a reusable pattern | `bm skill add <name> --project <p>` (or `bm skill write` for interactive) |
| Pattern proves generally useful across projects | `bm skill generalize <name>` |
| User added new files under `skills/` manually | `bm install` to register + symlink them |
| User just ran `git pull` and skills look stale | `bm update` |
| Skills behave oddly or symlinks broken | `bm doctor -y` |
| New team member onboarding | `bm setup --yes` (one-shot install) |
| User reuses the same prompt many times | `bm prompt add <name>` then `bm prompt export <name>` |
| User wants machine-readable output | Add `--json` to `status`, `skill list`, `prompt list`, `benmore *` |
| User mentions a BEN number / Benmore project | `bm benmore lookup` then `context`/`status`/`summary` |

## Key gotchas

- **`bm benmore` requires `BM_API_KEY`.** Never invent a key or hardcode one in docs/scripts. Use the placeholder `bpk_your_api_key_here` in any examples written into the repo.
- **`benmore_team_channels.json` is gitignored** — contains real client PII. Do not commit any file matching that name pattern.
- **Project titles contain `[BEN-XXX]` brackets** which collide with Rich markup. When printing them via `console.print()`, always wrap in `escape(...)` from `rich.markup`.
- **Don't bypass the registry.** Manual `ln -s` into `~/.claude/skills/` works once but `bm doctor` will flag it as untracked. Use `bm skill add-external <source> --skill <name>` instead.
- **Hooks are scoped.** `bm hooks install` only adds bm-managed hooks; it preserves any other hooks already in `.git/hooks/`.

## Reference docs in this repo

For the full command reference, architecture diagrams, and troubleshooting:

- [**docs/BM-GUIDE.md**](../../docs/BM-GUIDE.md) — comprehensive bm guide (skills, prompts, tools, hooks, benmore API)
- [**docs/BENMORE-API.md**](../../docs/BENMORE-API.md) — Python `benmore_client` API reference
- [**docs/BM-BENMORE-INTEGRATION.md**](../../docs/BM-BENMORE-INTEGRATION.md) — `bm benmore` CLI reference
- [**docs/BENMORE-QUICKREF.md**](../../docs/BENMORE-QUICKREF.md) — one-page cheat sheet
- [**README.md**](../../README.md) — project overview and quick start

Read these only when the user needs detail beyond what is in this SKILL.md. The goal of this skill is to know **which command to suggest**, not to duplicate the reference material.
