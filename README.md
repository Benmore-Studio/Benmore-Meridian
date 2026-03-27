# bm

**An extremely fast Claude Code skill manager.**

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-38%2B%20passing-brightgreen.svg)](#contributing)
[![Version](https://img.shields.io/badge/version-1.4.0-blue.svg)](CHANGELOG.md)

Install 50+ Claude Code skills in one command. Edit once, reflect everywhere via symlinks.

---

## Table of Contents

- [Highlights](#highlights)
- [New? Start Here 🚀](#new-start-here-)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Commands](#commands)
- [Skills](#skills)
- [Plugin Ecosystem](#plugin-ecosystem)
- [Developer Tools](#developer-tools)
- [Technology Stack](#technology-stack)
- [Repository Structure](#repository-structure)
- [Guides](#guides)
- [Contributing](#contributing)

---

## New? Start Here 🚀

**Forward Deployed Engineer?** → [**FDE Onboarding Guide**](onboarding/fde/README.md)

Read the FDE principles, install Ghostty + Raycast, then run `bm setup --yes` — that's it. The CLI handles everything else.

---

## Highlights

- ⚡ **One command install** — `bm install` symlinks all 50+ skills into Claude Code instantly.
- ✅ **Symlink-first** — skills live in the repo; edit once and changes reflect everywhere with no reinstall.
- 🎯 **Project skill lifecycle** — create scoped skills with `bm skill add x --project p`, promote to general when proven.
- 🔧 **Registry tracking** — every installed skill is recorded in `~/.bm/registry.json`, however it was installed.
- **Claude-native JSON output** — every command supports `--json` so agents can query `bm status --json` directly.
- **Plugin guidance** — `bm plugins` detects [Superpowers](#plugin-ecosystem) and [Double Shot Latte](#plugin-ecosystem) and walks you through any missing installs.
- **Zero config** — path constants computed from repo root at import time; works from any directory.

---

## Installation

**Requirements:** Python 3.11+, [Claude Code](https://claude.ai/code)

```bash
git clone https://github.com/Benmore-Studio/Benmore-Meridian
cd Benmore-Meridian
pip install -e ./bm
```

`pip install -e ./bm` keeps `bm` linked to the repo so it always finds the `skills/` directory. Running `git pull` immediately updates all skill content through symlinks — no reinstall needed.

---

## Quick Start

```bash
# Symlink all 50+ skills into Claude Code
bm install

# Verify skill status
bm status

# Check plugin requirements (Superpowers, Double Shot Latte)
bm plugins

# Full health check
bm doctor
```

Open Claude Code in any project — all skills are live.

**Update to latest:**

```bash
git pull
bm update    # git pull + reinstalls all skills
```

---

## Commands

### Core

| Command | Description |
|---------|-------------|
| **`bm install [--rsync] [--dry-run]`** | Symlink all skills → `~/.claude/skills/` (idempotent) |
| **`bm status [--json]`** | Show skill status as rich table or JSON |
| **`bm update [name] [--rsync] [--dry-run]`** | `git pull` + reinstall one or all skills |
| **`bm plugins`** | Detect and guide Superpowers / Double Shot Latte install |
| **`bm doctor`** | Full health check: skills + plugins + registry |

### Skills

| Command | Description |
|---------|-------------|
| **`bm skill add <name>`** | Scaffold a new general skill |
| **`bm skill add <name> --project <p>`** | Scaffold a project-scoped skill |
| **`bm skill list [--project <p>] [--json]`** | List skills, optionally filtered by project |
| **`bm skill generalize <name>`** | Promote a project skill to general |
| **`bm skill info <name>`** | Show path, scope, status, and source |
| **`bm skill remove <name> [--dry-run]`** | Uninstall a skill from `~/.claude/skills/` and registry ✨ v1.1 |
| **`bm skill write <name>`** | Interactively generate a new SKILL.md with guided prompts ✨ v1.1 |
| **`bm skill add-external <source> --skill <name>`** | Install a skill from plugins/agents directories ✨ v1.3 |

### Discovery ✨ v1.3

| Command | Description |
|---------|-------------|
| **`bm suggest [path] [--top N] [--json]`** | Scan project → ranked skill suggestions (static, no API) |
| **`bm context [path] [--copy]`** | Generate CLAUDE.md snippet with detected stack + top 5 skills |
| **`bm explore [path]`** | Deep scan → writes `docs/bm-suggestions.md` report |
| **`bm debrief [--since <tag>] [--limit N] [--json]`** | Surface skill candidates from recent git history |

### Registry

| Command | Description |
|---------|-------------|
| **`bm registry sync [--dry-run]`** | Scan `~/.claude/skills/` and reconcile registry |
| **`bm registry list [--json]`** | List all registered skills |

### Tools

| Command | Description |
|---------|-------------|
| **`bm tools list`** | Show available developer CLI tools with install status ✨ v1.1 |
| **`bm tools install [name...]`** | Install tools via Homebrew (macOS) or apt (Linux) ✨ v1.1 |

All commands support `--help` for detailed usage.

---

## Skills

Skills are markdown files (`SKILL.md`) that give Claude Code domain expertise and step-by-step workflows for specialized tasks. They live in `skills/` and are symlinked to `~/.claude/skills/` where Claude Code picks them up automatically.

### Available Skills

| Category | Skills |
|----------|--------|
| 🚀 Production | `django-production`, `frontend-productionize`, `productionize-app`, `fastapi-templates`, `vercel-cli` |
| 🔒 Security & Compliance | `dependency-security-audit`, `audit-trail`, `gdpr-compliance`, `multi-tenant-guard`, `hipaa-compliance-guard`, `security-compliance-audit`, `healthcare-audit-logger` |
| 🌐 SEO | `ai-seo`, `seo-audit`, `programmatic-seo` |
| 📱 Mobile | `django-auth-react-native`, `expo-deployment`, `expo-push-notifications`, `django-react-2fa` |
| 📄 Documents | `pdf`, `xlsx`, `presentation-maker`, `release-notes` |
| 🔧 Dev Tools | `mcp-builder`, `modern-terminal-setup`, `skill-creator`, `find-skills` |
| 🤝 Workflow | `feature-alignment`, `github-pr-review-workflow`, `receiving-code-review` |
| 💳 Payments | `stripe-integration` |
| 🏗️ PCS (scoped) | `pcs-migration`, `pcs-new-service`, `pcs-add-endpoint`, + 4 more |

Full inventory: [`skills/SKILLS_INVENTORY.md`](skills/SKILLS_INVENTORY.md)

### Creating a Skill

```bash
# 1. Scaffold a new skill
bm skill add my-skill

# 2. Edit the generated SKILL.md
$EDITOR skills/my-skill/SKILL.md

# 3. Activate via symlink
bm install

# 4. Invoke it in Claude Code
# "Run my-skill on this project"
```

### Project Skill Lifecycle

Skills start project-scoped and graduate to general when proven:

```bash
# Create scoped to a project
bm skill add deploy-hook --project my-project

# Edit and test in Claude Code
$EDITOR skills/my-project/deploy-hook/SKILL.md
bm install

# Promote when it proves universally useful
bm skill generalize deploy-hook
# → moves skills/my-project/deploy-hook/ → skills/deploy-hook/
# → updates symlink and registry
```

### Claude-Native JSON Output

```bash
# Claude agents can query bm directly
bm status --json          # [{name, status, scope, project}, ...]
bm registry list --json   # [{name, source, scope, install_method, ...}, ...]
bm skill list --json      # [{name, scope, project, path}, ...]
```

---

## Plugin Ecosystem

`bm` integrates with two Claude Code plugin marketplaces. Run **`bm plugins`** to check your install status and get setup instructions.

### [Superpowers](https://superpowers.club)

Advanced skills for systematic debugging, test-driven development, parallel subagent execution, git worktrees, and more. Installs into `~/.claude/skills/superpowers/`.

### [Double Shot Latte](https://github.com/doubleshottlatte)

Compound engineering workflows: browser automation, frontend design, brainstorming, PR review, and agent-native architecture patterns.

```bash
# Check which plugins are installed
bm plugins

# Doctor will also surface missing plugins
bm doctor
```

---

## Developer Tools

`bm` can install a curated set of modern CLI tools via Homebrew (macOS) or apt (Linux):

```bash
bm tools list                          # see available tools + install status
bm tools install ripgrep fzf lazygit   # install specific tools
bm tools install                       # install everything
```

| Tool | Purpose | Install |
|------|---------|---------|
| [ripgrep](https://github.com/BurntSushi/ripgrep) | Extremely fast `grep` replacement (`rg`) | `brew install ripgrep` |
| [fzf](https://github.com/junegunn/fzf) | Fuzzy finder for shell history, files, git | `brew install fzf` |
| [lazygit](https://github.com/jesseduffield/lazygit) | Terminal UI for git branches and diffs | `brew install lazygit` |
| [bat](https://github.com/sharkdp/bat) | `cat` with syntax highlighting and git markers | `brew install bat` |
| [eza](https://github.com/eza-community/eza) | Modern `ls` with icons and git status | `brew install eza` |
| [zoxide](https://github.com/ajeetdsouza/zoxide) | Smarter `cd` — jump to frecent directories | `brew install zoxide` |
| [delta](https://github.com/dandavison/delta) | Syntax-highlighted git diff viewer | `brew install git-delta` |
| [gh](https://cli.github.com/) | GitHub CLI — PRs, issues, releases | `brew install gh` |

---

## Technology Stack

| Tool | Purpose |
|------|---------|
| [Claude Code](https://claude.ai/code) | AI coding assistant — skill runtime |
| [uv](https://github.com/astral-sh/uv) | Python package manager |
| [Ruff](https://github.com/astral-sh/ruff) | Python linter and formatter |
| [Typer](https://github.com/tiangolo/typer) | CLI framework built on Click + type annotations |
| [Rich](https://github.com/Textualize/rich) | Terminal UI — tables, panels, progress bars |
| [mypy](https://mypy-lang.org/) | Static type checker (strict mode, 0 errors) |
| [pytest](https://pytest.org/) | Test framework |
| [ripgrep](https://github.com/BurntSushi/ripgrep) | Fast code search referenced in dev skills |
| [fzf](https://github.com/junegunn/fzf) | Fuzzy finder referenced in terminal skills |
| [lazygit](https://github.com/jesseduffield/lazygit) | Git TUI referenced in dev tooling skills |

---

## Repository Structure

```
Benmore-Meridian/
├── bm/                    # The bm CLI tool
│   ├── bm/                # Python package
│   │   ├── cli.py         # All commands (Typer)
│   │   ├── installer.py   # Symlink-first install + SKILL.md validation
│   │   ├── registry.py    # ~/.bm/registry.json persistence
│   │   ├── dryrun.py      # DryRunContext — safe preview of any write ✨ v1.1
│   │   ├── validator.py   # SKILL.md frontmatter validation ✨ v1.1
│   │   ├── tools.py       # Developer tool definitions ✨ v1.1
│   │   ├── status.py      # Installed/missing/broken detection
│   │   ├── plugins.py     # Superpowers + Double Shot Latte detection
│   │   ├── updater.py     # git pull + reinstall orchestration
│   │   ├── config.py      # Path constants + REPO_ROOT discovery
│   │   └── models.py      # All dataclasses and enums
│   ├── tests/             # 38+ tests, mypy strict, ruff clean
│   └── README.md          # Full bm command reference + architecture
├── skills/                # 50+ Claude Code skills (symlinked to ~/.claude/skills/)
├── guides/                # Developer onboarding documentation
│   ├── django/            # Production readiness (3 complementary guides)
│   ├── deployment/        # Heroku, DigitalOcean, CI/CD, React Native
│   ├── development/       # Dev workflow, Claude Code ecosystem
│   ├── review/            # PR review with AI
│   └── toolkit/           # Environment setup
└── docs/                  # Design specs + implementation plans
```

## Guides

| Guide | Description |
|-------|-------------|
| [**FDE Onboarding**](onboarding/fde/README.md) | **Start here if you're new — full setup in one command** |
| [Django Production](guides/django/) | Simple → detailed → comprehensive productionization |
| [Deployment](guides/deployment/) | Heroku, DigitalOcean (6 ops guides), CI/CD, React Native |
| [Development Workflow](guides/development/) | Meeting notes → production, Claude Code ecosystem |
| [PR Review](guides/review/) | AI-assisted review + GitHub Projects setup |
| [Developer Toolkit](guides/toolkit/) | Environment setup checklist (ripgrep, gh, uv, etc.) |

## Contributing

Guides for deployment, Django, CI/CD, and team workflows live in [`guides/`](guides/). See [`guides/README.md`](guides/README.md) for the full index.

```bash
# Run the full check suite before submitting
cd bm
uv sync --all-extras
make check-all    # ruff + mypy + pytest in < 30s
```

Pull requests welcome. When adding a new skill, follow the project skill lifecycle above — start scoped, generalize when proven.

---

> Part of [Benmore-Meridian](https://github.com/Benmore-Studio/Benmore-Meridian) — the Claude Code skills repo for [Benmore Studio](https://benmore.studio).
