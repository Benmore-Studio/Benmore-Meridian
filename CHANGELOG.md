# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

---

## v1.6.0 — 2026-04-02

### New Features

- **`bm prompt`** — Save, search, and reuse prompt templates. Prompts live in `prompts/` as `PROMPT.md` files with YAML frontmatter (tags, description, scope). Supports `$1`, `$2`, `$ARGUMENTS` for parameterized templates.
  - `bm prompt list` — Browse prompts with `--tag`, `--starred`, `--popular` filters
  - `bm prompt add <name>` — Create a new prompt template
  - `bm prompt search <query>` — Fuzzy-search by name, description, or tags
  - `bm prompt info <name>` — Show full prompt content and metadata
  - `bm prompt copy <name> [args]` — Render with arguments and copy to clipboard
  - `bm prompt export <name>` — Symlink into `~/.claude/commands/` so it becomes a Claude Code `/command`
  - `bm prompt export --all` — Export all prompts as slash commands
  - `bm prompt unexport <name>` — Remove from Claude Code commands
  - `bm prompt star/unstar <name>` — Bookmark favorite prompts
  - `bm prompt remove <name>` — Delete a prompt
- **`bm hooks`** — Git hook management for auto-syncing skills on pull and branch switch.
  - `bm hooks install` — Install `post-merge` and `post-checkout` hooks that run `bm install --quiet` when `skills/` or `prompts/` change
  - `bm hooks remove` — Remove bm-managed hooks (preserves other hooks)
  - `bm hooks status` — Check which hooks are installed
- **`bm install --quiet`** — Minimal output mode for use in git hooks and automation.
- **Dashboard tips** — Random helpful tips shown at the bottom of the `bm` dashboard to aid discoverability. Shows prompts count in header panel.
- **Dashboard warnings** — Shows warning when git hooks aren't installed with install command.

### Starter Prompts

- `productionize-django` — Audit and productionize a Django project
- `quick-pr-review` — Fast code review focusing on bugs, security, and style
- `client-kickoff` — Prepare for a new client kickoff meeting
- `full-pr-review-audit` — Full PR review + audit pipeline with parallel agents
- `create-project-tickets` — GitHub issues with parent/child via gh CLI
- `skill-chain-loop` — Automated skill loops with feedback and memory

### Fixes

- **prompt_registry**: Corrupt `~/.bm/prompts.json` no longer crashes the CLI — gracefully starts fresh
- **prompt_registry**: Atomic writes via tempfile+rename prevent data corruption on concurrent access
- **prompts**: Broken `PROMPT.md` files (permission errors, bad encoding) are skipped gracefully instead of crashing discovery
- **prompts**: Export copy fallback now verifies success before returning true
- **cli**: Clipboard commands use proper list construction (not `cmd.split()`), check return codes, and fallback to printing on failure
- **hooks**: Per-hook file I/O wrapped in try-except — only claims success on hooks that actually installed
- **hooks**: UTF-8 encoding on all read/write operations for Windows compatibility
- **hooks**: Hook block removal uses proper boundary detection instead of fragile keyword matching

### Internal

- New modules: `prompts.py`, `prompt_registry.py`, `hooks.py`
- Prompt user state stored in `~/.bm/prompts.json` (stars, usage counts)
- Extracted `_copy_to_clipboard()` and `_find_prompt()` helpers in CLI
- 22 new tests (84 total, all passing)

---

## v1.5.1 — 2026-03-27

### Features
- **Auto-install new skills on dashboard** — `bm` (no-args dashboard) now silently installs any repo skills that aren't yet linked into `~/.claude/skills/`. Reports newly installed skills with a `✨` notice. No more "N skills not installed → run bm install" prompts.
- **`bm update` reports new skills** — When `bm update` pulls in commits that add new skills, it prints `✨ N new skill(s) added: <names>` after reinstalling.

---

## v1.5.0 — 2026-03-27

### New Skills
- **`docx`** — Create, read, edit, and manipulate Word documents (.docx). Supports tables of contents, headings, page numbers, find-and-replace, tracked changes, image insertion, and polished report/memo/letter generation.
- **`imap-smtp-email`** — Read and send email via IMAP/SMTP. Supports inbox browsing, search, reply, compose, and attachment handling across any email provider.
- **`video-download`** — Download videos from Douyin, Xiaohongshu, Bilibili, YouTube, Twitter/X, Instagram, and 1700+ sites. Triggers on any video URL share or download request.

### Version Bump
- `bm` CLI bumped from 1.3.0 → 1.5.0 (catches up to CHANGELOG; v1.4.0 features shipped but package version was not updated).

### Registry
- Registry synced: 63 repo skills + 1 external (`alpha`) = 64 total entries.

---

## v1.4.0 — 2026-03-26

### New Skills
- **`hipaa-compliance-guard`** — Audits HealthTech applications for HIPAA technical safeguards (encryption, audit logs, access controls, breach notification).
- **`security-compliance-audit`** — Comprehensive security compliance auditing for SOC 2, GDPR, HIPAA frameworks.
- **`healthcare-audit-logger`** — Generates audit logs and trails for healthcare applications meeting regulatory standards.
- **`feature-alignment`** — Analyzes meeting transcripts and client documents to extract and align features with requirements.
- **`expo-push-notifications`** — Complete Expo Push Notification setup for React Native (frontend) and Django (backend).
- **`django-react-2fa`** — Full-stack TOTP two-factor authentication for Django + React/Next.js applications.

### New Guides
- **`onboarding/fde/`** — Forward Deployed Engineer onboarding guide with setup checklist, tools, and resources.

### Fixes
- Resolved UTF-8 encoding errors in `bm` CLI on Windows — explicit encoding for SKILL.md reads and console output.
- Fixed circular symlinks in `bm install` — skip symlinks in source dir, refuse overlapping paths.
- Fixed HTML entity encoding in Developer Onboarding presentation.

---

## v1.3.0 — 2026-03-14

### New Commands
- **`bm suggest [path]`** — Scan a project directory and print a ranked table of relevant skills based on detected stack (Django, Celery, Stripe, React, etc.). Zero API cost, pure static analysis.
- **`bm context [path]`** — Generate a markdown snippet for pasting into CLAUDE.md with detected stack + top 5 recommended skills. Use `--copy` to copy to clipboard.
- **`bm explore [path]`** — Deep project scan that writes a full `docs/bm-suggestions.md` report with ranked skills and reasoning.
- **`bm debrief`** — Headless post-session skill discovery: reads recent git history and surfaces candidate skills worth codifying. Use `--since <tag|date>` to control look-back window.

### New Features
- **Dashboard update badge** — `bm` dashboard now checks if a newer version is available on `origin` and shows `⚠ update available — run bm update` when behind.
- **`bm update` changelog diff** — After pulling, displays the CHANGELOG section for what changed in a Rich panel.
- **GitHub Actions release automation** — New `.github/workflows/release.yml` auto-bumps version and creates GitHub Releases on every merge to `main`.

### Architecture
- New `bm/bm/skill_matcher.py`: `SkillMatcher` class with project signal detection and skill scoring.
- New `bm/bm/debrief.py`: Headless `run_debrief()` with heuristic git-log analysis and cursor persistence.
- `bm/bm/updater.py`: Added `get_current_tag()`, `get_remote_tag()`, `is_update_available()`, `get_changelog_section()`.

---

## v1.1.0 — 2026-03-12

### New Commands
- **`bm skill remove <name> [--dry-run]`** — Safely uninstall a repo-managed skill from `~/.claude/skills/` and the registry. Refuses EXTERNAL skills with a clear error message.
- **`bm tools list`** — List available developer CLI tools (ripgrep, fzf, lazygit, bat, eza, zoxide, delta, gh) with install status.
- **`bm tools install [name...]`** — Install developer CLI tools via Homebrew (macOS) or apt (Linux).
- **`bm skill write <name>`** — Interactively create a new skill with guided prompts for description and triggers.

### New Features
- **`--dry-run` flag** on `bm install`, `bm update`, `bm skill remove`, and `bm registry sync` — Shows a Rich table of planned operations without writing anything. Safe to run anywhere.
- **SKILL.md frontmatter validation** — `discover_skills()` now validates required fields (`name`, `description`) and warns on missing optional fields (`version`, `author`, `tags`). Invalid skills are blocked at install time with a clear error.

### Architecture
- New `bm/bm/dryrun.py`: `DryRunOp` and `DryRunContext` dataclasses — collect planned operations for dry-run preview.
- New `bm/bm/validator.py`: `validate_skill()` and `ValidationResult` — frontmatter validation with structured errors and warnings.
- New `bm/bm/tools.py`: `DevTool` dataclass + `TOOLS` registry of curated developer tools.
- `install_skill()`, `Registry.batch_add()`, `Registry.remove()`, `Registry.sync()` all accept optional `ctx: DryRunContext`.

### Quality
- Test suite expanded from 27 to 38+ tests
- mypy strict: 0 errors
- ruff: all clean

---

## [v1.0.1] — 2026-03-11

### Fixed — `bm` CLI

- **Registry corruption** (Sentry severity: MEDIUM): Skills that fail to install are no longer added to `~/.bm/registry.json`. Only `SYMLINKED` or `COPIED` results are recorded.
- **N×1 registry writes**: `Registry.add()` no longer auto-saves on every call. Added `batch_add(entries)` for bulk installs (one write per `bm install` run, not one per skill).
- **REPO_ROOT portability**: `config.py` now walks up the directory tree looking for `skills/ + bm/` siblings instead of hardcoding three `parent` jumps. Fallback: reads `~/.bm/repo_root`. Works with `pip install -e` and any install layout.
- **Project folder auto-discovery**: `discover_skills()` no longer hardcodes `"pcs"` as the only project subfolder. Any directory without its own `SKILL.md` that contains skill subdirectories is treated as a project container — `skills/myteam/`, `skills/chatbot/`, etc. all work automatically.
- **cli.py imports**: `SkillEntry`, `shutil`, `asdict` moved to top-level imports; local imports inside function bodies removed.
- **`Optional[X]` → `X | None`**: All `typing.Optional` usage replaced with modern union syntax (Python 3.11+).
- **StrEnum upgrade**: All four model enums (`SkillScope`, `SkillSource`, `InstallResult`, `SkillStatus`) now inherit from `StrEnum` (Python 3.11+), removing the `(str, Enum)` workaround.
- **Unused `field` import** removed from `models.py`.
- **Code helpers extracted**: `_scope_label()`, `_find_skill()`, `_RESULT_ICON` dict added to `cli.py` to eliminate three instances of duplicated scope formatting and linear skill search.
- **`status` command**: Removed wasteful `SkillStatus` round-trip (building dict of `.value` strings then reconstructing enum from string). Status objects are kept throughout.

### Changed

- `bm/README.md`: Install instruction changed from `pipx install ./bm` to `pip install -e ./bm` with explanation of why editable install is required.
- `CLAUDE.md`: Added `bm CLI` section with three ASCII flow diagrams (install, project lifecycle, project folder discovery) and a proactive hints table for Claude agents.

---

## [v1.0.0] — 2026-03-11

## [v1.0.0] — 2026-03-11

### Added — `bm` CLI (Benmore Skill Manager)

New Python CLI package at `bm/` — install via `pipx install ./bm`.

**Core commands:**
- `bm install [--rsync]` — symlinks all repo skills into `~/.claude/skills/`; copytree fallback for restrictive systems
- `bm status [--json]` — rich table of skill status (symlinked / copied / missing / broken); `--json` for agent use
- `bm update [name]` — `git pull --ff-only` + reinstall one or all skills
- `bm plugins` — detects Superpowers + Double Shot Latte; prints install guide for missing plugins
- `bm doctor` — full health check: skills + plugins + summary

**Skill lifecycle commands:**
- `bm skill add <name> [--project p]` — create general or project-scoped skill with SKILL.md stub
- `bm skill list [--project p] [--json]` — list skills, filter by project
- `bm skill generalize <name>` — promote project skill → general (moves file, re-symlinks, updates registry)
- `bm skill info <name>` — show path, scope, status, source, description

**Registry commands:**
- `bm registry sync` — scan `~/.claude/skills/` and reconcile `~/.bm/registry.json`; source detection: REPO / MARKETPLACE / EXTERNAL
- `bm registry list [--json]` — list all registered skills

**27 unit tests** — models, config, installer, registry, status — all passing; mypy strict 0 errors.

### Added — 29 new skills

**Marketplace snapshots (16)** from Double Shot Latte:
`ai-seo`, `django-celery-expert`, `fastapi-templates`, `find-skills`, `mcp-builder`, `pdf`, `programmatic-seo`, `receiving-code-review`, `release-notes`, `remotion-best-practices`, `seo-audit`, `stripe-integration`, `vercel-cli`, `vercel-react-best-practices`, `web-design-guidelines`, `xlsx`

**Locally-owned (6)**:
`audit-trail`, `gdpr-compliance`, `multi-tenant-guard`, `presentation-maker`, `productionize-app`, `tickets`

**PCS microservice skills (7)** — project-scoped in `skills/pcs/`:
`pcs-add-endpoint`, `pcs-add-kafka-event`, `pcs-integration-test`, `pcs-kong-route`, `pcs-migration`, `pcs-new-service`, `pcs-pr-review`

### Added — Repo files

- `bm/pyproject.toml`, `bm/Makefile`, `bm/pyrightconfig.json`, `bm/.pre-commit-config.yaml`
- `skills/pcs/README.md` — project skill lifecycle docs
- `AGENTS.md` — Claude Code integration guide with JSON schemas
- `CHANGELOG.md` updated to Keep a Changelog format
- `LICENSE` — MIT
- `.github/dependabot.yml` — weekly updates for pip + github-actions

### Changed

- `skills/README.md` — `bm install` quickstart at top
- `skills/SKILLS_INVENTORY.md` — full inventory of all 50+ skills with categories

---

## [v0.3.0] - 2026-02-12

### Added

#### Configuration Guides
- **LSP Configuration Guide** (`development/04-lsp-configuration.md`) - Comprehensive Language Server Protocol setup for enhanced code intelligence
  - Multi-language support: Python (pylsp, pyright), TypeScript, Rust, Go, Ruby, C/C++
  - Real-time error checking and autocompletion
  - Integration with Claude Code, MCP servers, and skills
  - Troubleshooting guides and performance optimization
  - Project-specific and global configuration examples
  - Performance optimization for large codebases
- **Sandboxing Setup Guide** (`development/05-sandboxing-setup.md`) - Open-source sandbox runtime configuration
  - File and network isolation for improved safety
  - Reduced permission prompts during development (20-30 down to 2-5 per session)
  - Platform support (macOS, Linux; Windows coming Q2 2026)
  - Based on Boris Cherny's announcement and official Anthropic sandbox runtime
  - Integration with MCP servers and skills
  - Security best practices and troubleshooting

#### Deployment Guides (9 new guides across 4 platforms)
- **Deployment Category** (`deployment/`) - New category for platform-specific deployment documentation
  - **Heroku Platform** (`deployment/heroku/`)
    - `django-deployment.md` - Deploy Django to Heroku using modern `uv` package manager
      - Procfile, runtime.txt, environment variables configuration
      - PostgreSQL and Redis add-ons
      - Monorepo/subdirectory deployment with git subtree
      - Continuous deployment workflows
  - **DigitalOcean Platform** (`deployment/digitalocean/`) - 6 comprehensive guides
    - `01-overview.md` - Quick reference with links and command lookup
    - `02-getting-started.md` - First-time server connection and setup
    - `03-deployment.md` - Deploy Django projects with deployment script
    - `04-daily-operations.md` - Pull code, run migrations, restart services
    - `05-commands-reference.md` - PM2, Django, Git, PostgreSQL command reference
    - `06-troubleshooting.md` - Common issues, fixes, and diagnostic commands
  - **CI/CD Automation** (`deployment/cicd/`)
    - `django-setup.md` - Add production-ready CI/CD to Django projects
      - GitHub Actions workflow configuration
      - Automated testing, linting, security scanning
      - Pre-commit hooks setup
      - Makefile commands for local development
  - **Mobile Development** (`deployment/mobile/`)
    - `react-native-setup.md` - React Native project setup with Expo and TypeScript
      - Development environment configuration
      - Running on physical devices (iOS/Android)
      - Simulators and emulators setup
      - Claude Code skills for professional UI design
- **Documentation**: Enhanced project documentation with comprehensive CLAUDE.md file providing Claude Code guidance
- **README**: Improved README.md with better organization and navigation
- **Skills Inventory**: Complete production skills inventory with categorization (Production, Security, DevTools, Utilities)
- **CI/CD Bots Setup Guide**: Comprehensive guide to CI/CD automation including:
  - Sentry bot integration for runtime error tracking
  - Vercel bot for preview deployments and testing
  - GitHub Actions configuration and automation
  - Claude bot for AI-powered code review
  - Complete setup and troubleshooting instructions
- **Claude Code Ecosystem Guide**: Detailed documentation of AI-powered development tools including:
  - MCP servers (Context7, Hyperbrowser, Agent Browser)
  - Plugins and marketplaces
  - Skills system and custom skill creation
  - Subagents and Agent Teams for parallel work
- **Developer Onboarding Presentation**: Comprehensive 30+ page presentation covering:
  - Development toolkit setup with 10 step-by-step instructions
  - CI/CD bots configuration walkthrough
  - Claude Code ecosystem overview
  - Complete developer workflow from meetings to production
  - Django production setup with modern tooling
  - Next.js frontend with TypeScript and OpenAPI integration
  - Professional dark navy design with table of contents and code blocks
- **HTML Guide Presentations**: Interactive HTML versions of key guides:
  - Claude Code Agent Teams reference guide
  - Dev onboarding toolkit checklist (BEN-2001)
  - Django production checklist (14-phase guide)
- **GitHub Dependabot Compliance Guide**: Complete setup guide for Vanta compliance including:
  - Comprehensive HTML presentation guide
  - Detailed README with feature descriptions
  - Automation scripts for Patriot-Compliance-Systems org
  - Automation scripts for benmore-studio org
  - Coverage of FREE Dependabot features with zero monthly cost
  - Troubleshooting and step-by-step setup instructions
- **Dependabot Guide Folder**: Organized repository structure for Dependabot-related documentation

### Changed

- **Skills Inventory**: Updated SKILLS_INVENTORY.md to reflect actual production skills
  - Replaced outdated superpowers skill list with verified skills in directory
  - Added modern-terminal-setup skill to inventory
  - Categorized skills by function (Production, Security, DevTools, Utilities)
  - Clarified that superpowers skills are external and optional
- **Repository Organization**: Improved folder structure for Dependabot-related files

### Enhanced

- **Development Workflow**: Updated developer workflow guide with enhanced Step 3 (Build Implementation Action Plans) including:
  - Screenshots of frontend and backend running
  - Screenshots of available skills and superpowers
  - Structured plan generation workflow documentation
  - Claude Code superpowers integration guidance
  - Comprehensive instructions for leveraging brainstorming, planning, and testing superpowers
- **Project Structure**: Better organization of guides and documentation across categories

## [v0.2.0] - 2026-02-09

### Added

- **Forward Deployed Engineering Documentation**: New documentation category for forward-deployed engineering practices
- **Skills System Documentation**: Comprehensive documentation of the skills ecosystem
- **Development Guides**: Multiple new guides in the development category

### Changed

- Repository structure reorganized for better navigation
- Enhanced existing guides with more detailed examples

## [v0.1.0] - 2026-01-29

### Added

- **Initial Repository Structure**: Established core documentation repository with five main categories
  - `django/`: Django production readiness guides (3 complementary versions)
  - `development/`: Complete development lifecycle documentation
  - `review/`: Code review and PR workflow guides
  - `toolkit/`: Developer environment setup and tools
  - `team/`: Team-specific documentation (placeholder structure)
- **Django Production Guides**: Three complementary guides at different detail levels
  - `01-simple-checklist.md`: Quick reference checklist format (95 items)
  - `02-detailed-checklist.md`: Step-by-step implementation guide (45-60 minutes)
  - `03-comprehensive-guide.md`: Complete reference with full explanations
- **Development Workflow Guides**: Complete end-to-end documentation
  - `00-developer-workflow.md`: Full workflow from requirements to execution
  - `01-pr-review-workflow.md`: PR review and project management processes
  - Supporting visual assets (20+ images)
- **Repository Documentation**: Comprehensive CLAUDE.md and README.md files
- **Skills System**: Production-ready skills including:
  - django-production: Production-ready Django setup with modern tooling
  - frontend-productionize: Next.js + Django integration
  - django-auth-react-native: Complete JWT authentication system
  - dependency-security-audit: Security vulnerability scanning
  - modern-terminal-setup: Modern CLI tools configuration
  - skill-creator: Guide for creating new skills
  - Additional utility skills (gh_issue, nano_banana, stripe_processing, presentation_maker)
- **Toolkit Documentation**: Comprehensive development environment setup guide
- **GitHub Configuration**: Git setup guidelines and commit conventions

### Design Decisions

- **Three Django Guides**: Accommodates different audience needs (quick reference vs. detailed implementation vs. comprehensive learning)
- **Category-Based Organization**: Groups guides by topic for easy discovery and consistent expansion
- **Skills System**: Integrated AI-powered tools for development automation
- **No Application Code**: Repository contains documentation only for portability and reusability

---

## Release Highlights

### Current Development (Feb 2026)

**Focus**: Automation, AI Integration, and Compliance
- Complete CI/CD bot ecosystem documentation
- Claude Code integration for intelligent development
- Vanta compliance and Dependabot setup
- Professional presentation formats for easy sharing
- Comprehensive onboarding materials for new developers

### January 2026

**Focus**: Foundation and Organization
- Established core repository structure
- Created multiple complementary guides for different use cases
- Built comprehensive documentation for development practices
- Implemented skills system for automation

---

## How to Use This Changelog

- **For users**: Check the latest additions to understand new guides and features
- **For contributors**: Review sections to understand what types of changes belong here
- **For maintainers**: Update this file when merging significant changes (new guides, new skills, major restructuring)

## Contributing to the Changelog

When adding new guides or making significant changes:
1. Update the appropriate section (Added, Changed, Enhanced, etc.)
2. Be specific about what was added (include file names and descriptions)
3. Group related changes together
4. Use clear, descriptive language

## Release Schedule

This repository follows a continuous documentation update model:
- Minor updates: Added to "Unreleased" section
- Major versions: Released periodically with tagged commits
- See `README.md` for current navigation and guide index

---

## Related Files

- **README.md** - Main index and quick start guide
- **CLAUDE.md** - Claude Code instance guidance
- **django/README.md** - Django guide selector with comparison
- **development/README.md** - Development workflow overview
- **toolkit/README.md** - Toolkit setup guide
- **skills/SKILLS_INVENTORY.md** - Complete skills reference
