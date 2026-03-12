# Releasing bm CLI

This document describes the steps to cut a new release of the `bm` CLI.

---

## Pre-release Checklist

- [ ] All feature work merged to `main`
- [ ] `make check-all` passes (ruff, mypy, pytest)
- [ ] `CHANGELOG.md` updated with a new version section (see format below)
- [ ] Version bumped in `bm/pyproject.toml`

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

## Step 4 — Push

```bash
git push origin main
git push origin vX.Y.Z
```

Push the tag explicitly. GitHub will create a release automatically if `.github/workflows/release.yml` is configured, or you can create one manually via the GitHub UI.

---

## Step 5 — (Optional) Build and Publish

If distributing the package via PyPI:

```bash
cd bm
pip install build twine
python -m build
twine upload dist/*
```

For internal use, `pip install -e ./bm` (editable install) is the recommended approach. See `bm/README.md`.

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
