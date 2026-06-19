# Releasing bm CLI

This document describes the steps to cut a new release of the `bm` CLI.

---

## Pre-release Checklist

- [ ] All feature work merged to `main`
- [ ] Quality gates pass:
  - `uv run ruff format --check bm/ tests/`
  - `uv run ruff check bm/ tests/`
  - `uv run mypy bm/`
  - `uv run --extra dev basedpyright`
  - `uv run pytest tests/ -q`
  - `cargo test --manifest-path native/Cargo.toml`
- [ ] Schemas regenerated and unchanged except for intentional API changes:
  - `uv run bm schema openapi --output bm/schemas/benmore.openapi.json`
  - `uv run bm schema json status --output bm/schemas/status.schema.json`
- [ ] `CHANGELOG.md` updated with a new version section (see format below)
- [ ] Version bumped in `bm/pyproject.toml`
- [ ] Wheel and sdist build cleanly with `uv build`

---

## Step 1 — Update CHANGELOG.md

Add a new section at the top of `CHANGELOG.md`, immediately after the `## [Unreleased]` block:

```markdown
## v<X.Y.Z> — YYYY-MM-DD

### New Commands
- ...

### New Features
- ...

### Architecture
- ...

### Quality
- ...
```

Keep the `## [Unreleased]` section in place (empty) for the next cycle.

---

## Step 2 — Bump the Version

Edit `bm/pyproject.toml`:

```toml
[project]
version = "X.Y.Z"
```

Follow [Semantic Versioning](https://semver.org/):
- **Patch** (`Z`): bug fixes, no new commands or breaking changes
- **Minor** (`Y`): new commands, new flags, new modules — backwards compatible
- **Major** (`X`): breaking CLI changes, removed commands, incompatible registry format

---

## Step 3 — Commit and Tag

```bash
git add CHANGELOG.md bm/pyproject.toml
git commit -m "chore: bump version to vX.Y.Z"
git tag -a vX.Y.Z -m "Release vX.Y.Z — <one-line summary of highlights>"
```

Do **not** use a lightweight tag — the `-a` flag creates an annotated tag with a message, which is required for `git describe` to work correctly.

---

## Step 4 — Build and Smoke Test

Build the distribution artifacts from `bm/`:

```bash
cd bm
uv build
```

Smoke test in a clean virtualenv before tagging:

```bash
python -m venv /tmp/bm-release-smoke
/tmp/bm-release-smoke/bin/pip install dist/benmore_bm-*.whl
/tmp/bm-release-smoke/bin/bm --help
/tmp/bm-release-smoke/bin/bm schema json status
```

The optional PyO3 helper is built separately for native-wheel jobs. Source
installs must continue to work through `bm.core`'s pure Python fallback.

---

## Step 5 — Push

```bash
git push origin main
git push origin vX.Y.Z
```

Push the tag explicitly. The release workflow must publish to PyPI through
trusted publishing and then create the GitHub Release.

---

## Step 6 — Publish

PyPI is the primary distribution target:

```bash
cd bm
uv publish
```

Use `uv publish` only for manual fallback releases. The normal path is GitHub
Actions trusted publishing after all CI checks pass.

User install commands after publication:

```bash
uv tool install benmore-bm
pipx install benmore-bm
```

Contributor editable installs remain supported:

```bash
uv tool install --editable ./bm
pip install -e ./bm
```

---

## Versioning Policy

| Change type | Version bump | Example |
|---|---|---|
| Bug fix, docs, refactor | Patch | `1.0.1 → 1.0.2` |
| New command, new flag, new module | Minor | `1.0.1 → 1.1.0` |
| Breaking CLI change, registry format change | Major | `1.1.0 → 2.0.0` |

---

## Notes

- The `bm/` subdirectory is the Python package root. Always run `make` commands from inside `bm/`.
- Annotated tags are used (`git tag -a`) so that `git describe --tags` returns the full version string.
- Do not delete or re-use version tags once pushed.
- Do not publish a tag if schema artifacts, OpenAPI, or native-core tests are out of sync.
