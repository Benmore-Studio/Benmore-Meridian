# bm v1.3.0 — Release Automation, Code Discovery, Debrief

**Date:** 2026-03-14
**Status:** Approved for implementation

---

## Overview

Three features that make `bm` a smarter, self-maintaining skill manager:

1. **Release automation** — GitHub Action auto-bumps version and publishes a GitHub Release on every merge to `main`; `bm update` shows a changelog diff; dashboard shows an "update available" badge.
2. **Code discovery** — `bm suggest`, `bm context`, and `bm explore` scan a project and recommend relevant skills with zero API cost.
3. **Session debrief** — `bm debrief` reads recent git history and heuristically surfaces candidate skills worth codifying, headlessly and without spawning Claude.

---

## Feature A — Release Automation

### A1. GitHub Action (`release.yml`)

**Trigger:** `push` to `main` — but only when `bm/pyproject.toml` or `skills/**` changed. Pure-docs commits (only `.md` files outside `bm/`) are skipped via path filters.

**Version bump rules (semver):**
| Commit prefix | Bump |
|---|---|
| `fix:`, `chore:`, `docs:` | Patch (`1.2.0 → 1.2.1`) |
| `feat:` | Minor (`1.2.0 → 1.3.0`) |
| `BREAKING:` | Major (`1.2.0 → 2.0.0`) |

**Steps:**
1. Parse current version from `bm/pyproject.toml`
2. Inspect squashed commit message(s) since last tag to determine bump type
3. Write new version back to `bm/pyproject.toml`
4. Prepend CHANGELOG.md section (`## vX.Y.Z — YYYY-MM-DD`) from PR titles since last tag
5. Commit with `chore: bump vX.Y.Z [skip ci]`
6. `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
7. `git push origin main --tags`
8. `gh release create vX.Y.Z --notes <CHANGELOG section>`

**Tools used:** `actions/checkout@v4`, `actions/setup-python@v5`, inline Python for version parsing, `gh` CLI (available in GitHub-hosted runners).

### A2. `bm update` — version-aware pull

Current behaviour: `git pull --ff-only` + reinstall all skills.

New behaviour:
1. Record version before pull (`git describe --tags`)
2. `git pull --ff-only`
3. Record version after pull
4. If version advanced: extract CHANGELOG section between old and new tag, print in a Rich panel titled "What's new in vX.Y.Z"
5. Reinstall skills as before

### A3. Dashboard — "update available" badge

On every `bm` invocation (dashboard or subcommand):
1. `git fetch --tags -q` (silent, fast)
2. Compare `git describe --tags HEAD` vs `git describe --tags origin/main`
3. If behind: show `⚠ update available — run bm update` in the dashboard header panel

Timeout: 2s max; if fetch times out, silently skip the check.

---

## Feature B — Code Discovery

### Shared: skill metadata index

All three commands share a `SkillMatcher` class that:
- Reads each installed skill's `SKILL.md` frontmatter (`triggers:` list)
- Falls back to parsing the first 20 lines for trigger keywords if no frontmatter
- Builds an in-memory `{skill_name: [keywords]}` map

### Detection signals (scanned in target `<path>` or cwd)

| File/Pattern | Detected signals |
|---|---|
| `pyproject.toml`, `requirements*.txt` | Python package names |
| `package.json` | JS package names |
| `Dockerfile`, `docker-compose.yml` | containerization |
| `.github/workflows/` | CI/CD present |
| Top-level dirs (`mobile/`, `backend/`, `frontend/`) | monorepo shape |
| `CLAUDE.md` | already-used skills (excluded from suggestions to avoid noise) |
| Django `settings*.py` | Django project |
| `manage.py` | Django confirmed |
| `celery*.py`, `tasks.py` | Celery |
| `stripe` in any dep file | Stripe |

### `bm suggest [path]`

- Fast terminal command; pure static analysis, no API calls
- Scans signals, scores skills by keyword overlap, deduplicates
- Prints a Rich table: Rank · Skill · Why · Status (installed ✓ / `bm install`)
- `--top N` flag (default 8)
- `--json` for machine-readable output

### `bm context [path]`

- Runs same scan as `suggest`
- Emits a markdown snippet to stdout
- `--copy` flag copies to clipboard (via `pbcopy`/`xclip`/`clip` depending on OS)
- Output format:
  ```markdown
  ## Project Stack (auto-detected by bm context)
  - <detected stack summary>
  - Recommended skills: skill-a, skill-b, skill-c
  ```
- Designed to be pasted into project `CLAUDE.md`

### `bm explore [path]`

- Deeper scan: reads up to 20 key files (settings, urls.py, models.py, package.json, Dockerfile, etc.)
- Scores skills with higher confidence (file content, not just filename signals)
- Writes `docs/bm-suggestions.md` with:
  - Detected stack summary
  - Ranked skill table with per-skill reasoning
  - Copy-paste `bm install` commands
  - "Already installed" section
- Prints summary to terminal on completion

---

## Feature C — `bm debrief`

### Inputs (no API calls, no Claude subagent)

```bash
git log --oneline -15
git diff HEAD~15..HEAD --stat
git diff HEAD~15..HEAD --name-only
```

Also checks:
- New/modified `SKILL.md` files in recent commits
- New directories under `skills/` without a `SKILL.md`
- Lines added to `CLAUDE.md` (captured patterns worth codifying)

### Heuristic scoring

Signals that increase a candidate's score:
- Same file type / library touched in 2+ commits (`+2`)
- Commit subject contains reusable noun after `feat:` / `add:` / `refactor:` (`+2`)
- New directory created, no `SKILL.md` yet (`+3`)
- `CLAUDE.md` gained new instruction lines (`+1`)
- Candidate name doesn't overlap with any existing skill name (`+1`)

Threshold: score ≥ 3 → surface as candidate.

### Output

Printed as a Rich panel to terminal:

```
 bm debrief — N skill candidates from last 15 commits

 1. stripe-webhook-handler        score: 5
    Rationale: 3 commits touched webhook validation; no existing skill covers it
    → bm skill write stripe-webhook-handler

 2. export-pipeline               score: 4
    Rationale: new pattern in utils/exports.py introduced in feat: add export pipeline
    → bm skill write export-pipeline
```

If no candidates meet threshold: "No reusable patterns detected in last 15 commits."

### Flags

- `--since <tag|date>` — override look-back window
- `--limit N` — max commits to scan (default 15)
- `--json` — machine-readable output for agent use

### Cursor persistence

Last debrief timestamp stored in `~/.bm/debrief_cursor`. `--since` defaults to this timestamp if present, falling back to `HEAD~15`. Updated on every successful run.

---

## Architecture Notes

- All three discovery commands share `bm/skill_matcher.py` — a single `SkillMatcher` class
- `bm debrief` lives in `bm/debrief.py`
- GitHub Action lives at `.github/workflows/release.yml` — no new Python module needed for this
- `bm update` enhancement is a change to `bm/updater.py` only
- Dashboard badge is a change to `bm/cli.py` `_render_dashboard()` only
- New CLI commands registered in `bm/cli.py` via `app.command()`

---

## Success Criteria

- [ ] `push` to `main` with `feat:` prefix → minor version bump + GitHub Release created automatically
- [ ] `bm update` on a stale clone shows the CHANGELOG diff before reinstalling
- [ ] `bm` dashboard shows "update available" when remote is ahead
- [ ] `bm suggest` correctly identifies Django + Celery in a sample project
- [ ] `bm context` output can be copy-pasted into CLAUDE.md without editing
- [ ] `bm explore` writes `docs/bm-suggestions.md` with ranked skill table
- [ ] `bm debrief` surfaces at least one candidate from a repo with 3+ feature commits
- [ ] All new commands have `--json` flag for agent use
- [ ] `make check-all` passes (ruff, mypy, pytest)
