---
name: productionize-app
description: >
  Productionize a full-stack application by completing all release-readiness tasks in parallel
  using an agent team. Covers: (1) writing/updating a comprehensive README.md, (2) adding an
  Apache 2.0 or project-appropriate open source license, (3) configuring DRF Spectacular for
  Swagger UI + ReDoc API docs, (4) establishing semantic versioning with CHANGELOG.md,
  (5) activating GitHub Dependabot for automated dependency security PRs, (6) creating a
  signed Git release tag and GitHub Release. Use when asked to "productionize", "prep for
  release", "add docs and versioning", "make the app production-ready", or any combination
  of docs/license/API-docs/changelog/dependabot/release tasks.
context: fork
---

# Productionize App

Prepare a Django + React Native (or any web/mobile) application for production by completing
six release-readiness tasks **in parallel** using an agent team.

## Agent Team Strategy

All 6 tasks touch different files — spawn them simultaneously.

```
Lead orchestrator
├── Agent A → README.md
├── Agent B → LICENSE file
├── Agent C → DRF Spectacular (Swagger + ReDoc)
├── Agent D → Versioning + CHANGELOG.md
├── Agent E → Dependabot (.github/dependabot.yml)
└── Agent F → Git release tag + GitHub Release
```

## Pre-flight: Inspect the Repo

Before spawning agents, gather context to pass in each prompt:

```bash
git tag --sort=-version:refname | head -5
ls *.md LICENSE* .github/ 2>/dev/null
cat mobile/package.json | grep '"version"'
grep -r "VERSION" backend/config/ | head -3
git log --oneline -10
```

---

## Task Specs

### Agent A — README.md

See [references/readme.md](references/readme.md) for section guide and template.

Key sections to produce:

- Project title + tagline
- Badges (CI, license, version)
- Feature highlights
- Tech stack table
- Quick start (<10 commands for backend + mobile)
- Architecture overview (reference CLAUDE.md or inline diagram)
- Contributing stub + License section

### Agent B — LICENSE

See [references/license.md](references/license.md) for Apache 2.0 full text and substitution rules.

- Check if `LICENSE` already exists → skip if present and correct
- Create `LICENSE` in repo root using Apache 2.0 full text
- Substitute `[year]` and `[fullname]` from `git config user.name` / `git remote -v`

### Agent C — DRF Spectacular

See [references/drf-spectacular.md](references/drf-spectacular.md) for full setup.

- Install `drf-spectacular`
- Add `SPECTACULAR_SETTINGS` to Django settings
- Wire `/api/schema/`, `/api/docs/` (Swagger UI), `/api/redoc/` endpoints
- Add `@extend_schema` on 3-5 representative ViewSets
- Run smoke test: `python manage.py spectacular --validate-examples`

### Agent D — Versioning + CHANGELOG

See [references/versioning.md](references/versioning.md) for semver rules and Keep a Changelog format.

- Read current version from `mobile/package.json`
- Create/update `CHANGELOG.md` with Keep a Changelog format
- Add `[Unreleased]` + backfill latest version section from `git log --oneline -30`
- Update version strings across: `package.json`, `backend/config/base.py` (if present)

### Agent E — Dependabot

See [references/dependabot.md](references/dependabot.md) for YAML config.

- Create `.github/dependabot.yml`
- Entries for: `pip` (backend), `npm` (mobile), `github-actions`
- Schedule: weekly; group minor+patch; assign reviewer from `git log` contributors

### Agent F — Release Tag + GitHub Release

See [references/release-tagging.md](references/release-tagging.md) for tag conventions.

- Read current version from CHANGELOG.md or package.json
- `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
- `git push origin vX.Y.Z`
- `gh release create vX.Y.Z --notes-from-tag` (or generate notes from CHANGELOG)

---

## Lead: Coordination + Final Steps

1. Spawn all 6 agents simultaneously (different files — no conflicts).
2. Wait for all completions.
3. Smoke test:
   ```bash
   cd backend && python manage.py spectacular --color --validate-examples 2>&1 | tail -5
   cat .github/dependabot.yml
   git tag --sort=-version:refname | head -3
   ```
4. Commit:
   ```bash
   git add README.md LICENSE CHANGELOG.md .github/dependabot.yml
   git add backend/
   git commit -m "chore(release): productionize — docs, license, API docs, versioning, dependabot"
   ```
5. Report to user: files created/updated, API docs URL, release tag, dependabot status.
