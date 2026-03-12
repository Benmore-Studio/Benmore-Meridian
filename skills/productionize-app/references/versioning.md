# Semantic Versioning + Keep a Changelog

## Semver Rules (MAJOR.MINOR.PATCH)

| Bump | When |
|------|------|
| PATCH | Bug fixes, typos, minor docs |
| MINOR | New features, backward-compatible |
| MAJOR | Breaking API changes |

## CHANGELOG.md Format (Keep a Changelog)

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- (add new features here)

### Fixed
- (add fixes here)

## [1.4.0] - 2026-02-24

### Added
- In-app notification banner + Android channel + APNS config

### Fixed
- Reset unsaved-changes baseline after successful save

## [1.3.0] - 2026-02-18

### Added
- RBAC gap fill, FCM push, closeout math corrections

[Unreleased]: https://github.com/org/repo/compare/v1.4.0...HEAD
[1.4.0]: https://github.com/org/repo/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/org/repo/compare/v1.2.0...v1.3.0
```

## Deriving Entries from Git Log

```bash
git log --oneline v1.3.0..HEAD
# Use commit messages to populate Added/Fixed/Changed sections
# Conventional commit prefixes:
#   feat:  → Added
#   fix:   → Fixed
#   refactor: → Changed
#   docs: → (skip or include under Changed)
#   chore: → (skip unless notable)
```

## Where to Store Version Strings

| File | How |
|------|-----|
| `mobile/package.json` | `"version": "1.4.0"` |
| `backend/config/base.py` | `APP_VERSION = "1.4.0"` (optional) |
| `CHANGELOG.md` | Latest version header |
| Git tag | `v1.4.0` (annotated) |

Keep all four in sync. The git tag is the authoritative source of truth.
