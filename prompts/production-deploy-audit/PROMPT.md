---
name: production-deploy-audit
description: Full-stack production deploy audit and fix — backend (Heroku/Django), mobile (Expo/EAS), infra, security, performance. Learned from HSP v1.7.0 session.
tags: [production, deploy, heroku, expo, eas, django, react-native, sentry, uv, audit]
scope: general
project: ""
---

# Production Deploy Audit & Fix

Full-stack production readiness audit for Django + React Native/Expo + Heroku apps. Checks deploy pipeline, fixes blockers, hardens for thousands of users, and documents everything.

Born from a real session that went from "builds failing" to "v96 deployed on Python 3.13 + uv" in one sitting. Every check below caught a real issue.

## How to use

```
Run the production-deploy-audit prompt on this project.
```

Or with arguments:

```
Run the production-deploy-audit prompt. Backend is in django-backend/, mobile in mobile-app/. Deploy target is Heroku. $ARGUMENTS
```

---

## Phase 1: Backend Deploy Pipeline (Heroku)

### 1.1 Check if builds are working

```bash
heroku releases --app $APP_NAME --num 5
```

Look for "release command failed" — this means the build succeeded but the release phase (migrations, collectstatic) crashed. The app is still running on the previous good release.

**Common causes of release command failure:**
- Migration conflicts (multiple leaf nodes from branch merges)
- Missing environment variables the new code expects
- Collectstatic failures (missing static files config)

### 1.2 Fix migration conflicts

```bash
heroku releases:output $LATEST_FAILED_VERSION --app $APP_NAME
```

If you see `CommandError: Conflicting migrations detected; multiple leaf nodes`:

```bash
python manage.py makemigrations --merge --noinput
python manage.py makemigrations --check  # verify no more pending
```

**Key learning:** Merge migrations are empty — they just unify the dependency graph. They're always safe. Also run `makemigrations --check` afterward to catch any pending model changes that haven't been migrated yet.

### 1.3 Monorepo deploy (subdirectory backend)

If your Django app is in a subdirectory (e.g., `django-backend/`), the standard `heroku/python` buildpack won't find `requirements.txt` at the repo root.

**Fix:**
```bash
heroku config:set APP_BASE=django-backend --app $APP_NAME
heroku buildpacks:clear --app $APP_NAME
heroku buildpacks:set https://github.com/lstoll/heroku-buildpack-monorepo --app $APP_NAME
heroku buildpacks:add heroku/python --app $APP_NAME
```

Order matters: monorepo first (copies subdirectory to root), then Python (installs deps).

### 1.4 Migrate from pip to uv

Heroku now recommends uv. Migration steps:

1. **Ensure `pyproject.toml` has all dependencies** — check every package in `requirements.txt` is listed
2. **Add `[tool.uv] package = false`** — Django apps are NOT Python packages. Without this, setuptools tries to build the project and fails with "Multiple top-level packages discovered in a flat-layout" because every Django app (accounts, bookings, etc.) looks like a top-level package
3. **Fix dependency constraints** — uv is stricter than pip. If `django-filter>=25.2` requires Django 5.2+ but you're on Django 4.2, uv will reject it (pip silently installs an incompatible version)
4. **Generate `uv.lock`**: `uv lock`
5. **Delete `requirements.txt`** — Heroku rejects builds with multiple package manager files
6. **Replace `runtime.txt` with `.python-version`** — uv doesn't support `runtime.txt`. Use major.minor only (e.g., `3.13`) so patch updates apply automatically
7. **Verify `requires-python` matches `.python-version`** — if pyproject.toml says `>=3.12` but .python-version says `3.11`, uv will reject

**The trap:** Steps 2, 3, 5, and 6 are all separate Heroku build errors. Each one requires a commit-push-wait cycle. Do all of them in one commit.

### 1.5 Database backups

```bash
heroku pg:backups --app $APP_NAME  # Check if backups exist
heroku pg:backups:schedule DATABASE_URL --at '04:00 America/Denver' --app $APP_NAME
heroku pg:backups:capture --app $APP_NAME  # Immediate backup
```

**Key learning:** Heroku Essential-0 Postgres has continuous protection (point-in-time recovery) but NO logical backups by default. You must schedule them explicitly.

### 1.6 Sentry on backend

```bash
heroku config:set SENTRY_DSN="https://..." --app $APP_NAME
```

Check that `sentry-sdk[django,celery]` is in dependencies. The `[logging]` extra was removed in newer versions — drop it if you see a warning.

---

## Phase 2: Mobile App Production Hardening

Launch 5 parallel agents, each on non-overlapping files:

### Agent 1: Crash Reporting (Sentry)

**Files:** `index.ts`, `app.config.ts`, `ErrorBoundary.tsx`, `package.json`

- Install `@sentry/react-native`
- Call `Sentry.init()` BEFORE `registerRootComponent`
- Wrap root component with `Sentry.wrap(App)`
- Add `@sentry/react-native/expo` plugin to `app.config.ts` plugins array
- Replace TODO comments in ErrorBoundary with `Sentry.captureException(error, { contexts: { react: { componentStack } } })`
- Add `EXPO_PUBLIC_SENTRY_DSN` placeholder to all EAS build profiles
- Configuration: `enabled: process.env.APP_ENV !== 'development'`, `tracesSampleRate: 0.2`

### Agent 2: API Resilience

**Files:** `src/services/api.ts`

- Install `axios-retry`
- Add `axiosRetry(api, { retries: 3, retryDelay: axiosRetry.exponentialDelay, retryCondition: ... })`
- Retry on network errors + 5xx. NEVER retry 4xx (auth failures, validation)
- Smart timeout interceptor: 15s GET, 30s POST, 60s multipart uploads
- PRESERVE existing JWT token refresh interceptor — retry and refresh operate at different layers

### Agent 3: EAS Configuration

**Files:** `eas.json`, `.env`, `app.config.ts`

- Add `EXPO_PUBLIC_API_BASE_URL`, `EXPO_PUBLIC_STRIPE_PUBLISHABLE_KEY`, `EXPO_PUBLIC_SENTRY_DSN` to ALL build profiles (empty placeholders for production, real values for staging)
- Fix `.env` — common issues: missing protocol (`localhost:8001` → `http://localhost:8001/api`), missing path prefix
- Change `runtimeVersion.policy` from `appVersion` to `fingerprint` — prevents OTA update mismatches when native deps change
- Verify slug matches EAS project registration — mismatch breaks OTA updates

### Agent 4: List Virtualization

**Files:** Large screen files (1000+ lines)

- Find ALL screens using `ScrollView` + `.map()` for rendering lists
- Replace with `FlatList` or `SectionList`
- Wrap `renderItem` in `useCallback`, use `keyExtractor` with unique IDs (NOT array indices)
- Add performance props: `removeClippedSubviews={true}`, `windowSize={5}`, `initialNumToRender={10}`, `maxToRenderPerBatch={10}`
- For heterogeneous dashboards: define a discriminated union type for section items, build sections array with `useMemo`
- DO NOT refactor or split files — only add virtualization

**Why this matters:** `ScrollView` + `.map()` renders ALL items in memory simultaneously. With 50+ items, older devices crash with OOM. `FlatList` only renders visible items + a buffer window.

### Agent 5: Environment Validation

**Files:** `.env.example`, `.gitignore`, `src/utils/validateEnv.ts`, `src/services/api.ts`

- Create `.env.example` with documented placeholders
- Harden `.gitignore`: add `google-services.json`, `GoogleService-Info.plist`
- Create `validateEnv.ts`: typed `getEnvConfig()` function that throws in production if API URL missing, warns in development
- Wire `validateEnv.ts` into the API client (replace manual `process.env` reads)

---

## Phase 3: Security & Dependencies

### 3.1 Dependabot alerts

```bash
gh api repos/$OWNER/$REPO/dependabot/alerts --jq '[.[] | select(.state == "open")] | group_by(.dependency.package.ecosystem) | .[] | {ecosystem: .[0].dependency.package.ecosystem, count: length, packages: [.[] | .dependency.package.name] | unique}'
```

**Key learning:** Dependabot alerts can be STALE. If you have dual lock files (e.g., both `package-lock.json` and `pnpm-lock.yaml`), Dependabot reads the wrong one and reports vulnerabilities against outdated versions. Fix: pick ONE package manager and delete the other's lock file.

**What's actionable vs. not:**
- Direct dependencies (axios, vite) — update them
- Transitive dependencies deep in Expo/Jest/React Native toolchain — NOT directly fixable. They'll be fixed when upstream packages release updates.

### 3.2 Run `npm audit` / `pnpm audit` to get ground truth

Dependabot alerts != `npm audit`. The audit tool reads the actual resolved lock file. If `npm audit` says 0 vulnerabilities but Dependabot says 10, the lock file Dependabot is reading is stale.

---

## Phase 4: Documentation & Release

### 4.1 Update these files

| File | What to update |
|------|----------------|
| `CLAUDE.md` | Production readiness score, stack versions, recent changes, deploy commands, API doc URLs |
| `CHANGELOG.md` | New version entry with Fixed/Added/Infrastructure sections |
| `DRF Spectacular settings` | `VERSION` field to match release |
| Session docs | Deploy checklist with completed items |

### 4.2 Create release

```bash
git tag -a v$VERSION -m "v$VERSION — summary"
git push origin main --tags
gh release create v$VERSION --title "v$VERSION — Title" --notes "release notes"
```

---

## Lessons Learned (Things That Bit Us)

### 1. Heroku buildpack order matters
Monorepo buildpack MUST come before Python buildpack. If reversed, Python buildpack runs first, can't find `requirements.txt` at root, and fails.

### 2. uv is strict about dependency resolution
pip silently installs incompatible versions. uv refuses. You MUST fix all constraint conflicts before `uv lock` will succeed. Common: `django-filter>=25.2` requires Django 5.2+ but you're on 4.2.

### 3. Django apps are not Python packages
`[tool.uv] package = false` is REQUIRED for any Django project using uv. Without it, setuptools treats every Django app directory as a top-level package and refuses to build.

### 4. `runtime.txt` is incompatible with uv
uv requires `.python-version` file instead. Use major.minor only (e.g., `3.13`) — no patch version — so security updates apply automatically.

### 5. `requires-python` must match `.python-version`
If `pyproject.toml` says `>=3.12` and `.python-version` says `3.11`, uv rejects the build. These must be consistent.

### 6. Migration merge files are always safe
They contain zero operations — just dependency declarations. They unify a forked migration graph the same way a merge commit unifies diverged branches.

### 7. Heroku config:set triggers a release
Setting `SENTRY_DSN` via `heroku config:set` triggers the release command (migrations). If migrations are broken, this release also fails — even though you only changed a config var.

### 8. GitHub auto-deploy != git push heroku
Many Heroku apps use GitHub integration for deploys (via the Dashboard). This is a DIFFERENT pipeline from `git push heroku main`. The GitHub integration may support `APP_BASE` natively, while the git push does not without the monorepo buildpack.

### 9. Dual lock files confuse everything
Having both `package-lock.json` and `pnpm-lock.yaml` means Dependabot reads one, CI reads the other, and they disagree about what's installed. Pick one package manager.

### 10. ScrollView + .map() is a production crash waiting to happen
Works fine in development with 5 items. Crashes with 50+ items in production. Always use FlatList for any list that could grow.

### 11. Missing env vars fail silently
A mobile app with an empty API URL just... doesn't work. No error, no crash, just empty screens. A `validateEnv.ts` that throws on missing critical vars saves hours of debugging.

### 12. Force push to heroku is safe (and sometimes necessary)
When the heroku git remote has diverged from GitHub (e.g., from direct pushes by different team members), `git push heroku main` fails with non-fast-forward. `git push heroku main --force` is safe because GitHub is the source of truth, and Heroku is just a deployment target.

### 13. 5 parallel agents work great on non-overlapping files
The key constraint: each agent must touch DIFFERENT files. Two agents editing the same file causes merge conflicts. Plan file ownership before launching.

### 14. Each Heroku build error requires a full commit-push-wait cycle
When migrating to uv, you'll hit 3-4 sequential errors (dual package managers → runtime.txt incompatible → requires-python mismatch → flat-layout error). Each requires a fix, commit, push, and 2-minute build wait. Do your research and fix ALL of them in one commit.

---

## Checklist (Copy-Paste)

```
## Backend Deploy
- [ ] Check `heroku releases --app $APP` for failed releases
- [ ] Fix migration conflicts: `python manage.py makemigrations --merge`
- [ ] Verify migration graph: `python manage.py showmigrations`
- [ ] Set up DB backups: `heroku pg:backups:schedule`
- [ ] Set Sentry DSN: `heroku config:set SENTRY_DSN=...`
- [ ] If monorepo: configure buildpacks (monorepo + python)
- [ ] If migrating to uv: pyproject.toml + uv.lock + .python-version + package=false
- [ ] Deploy: `git push heroku main`
- [ ] Verify: all dynos up, migrations clean, no errors in logs

## Mobile App
- [ ] Install @sentry/react-native, wire ErrorBoundary
- [ ] Add axios-retry with exponential backoff (3 retries, 5xx only)
- [ ] Add smart timeouts (15s/30s/60s by request type)
- [ ] Convert ScrollView+map to FlatList on all list screens
- [ ] Add validateEnv.ts — crash in prod if API URL missing
- [ ] Fix EAS config: env placeholders, slug, fingerprint OTA
- [ ] Create .env.example, harden .gitignore
- [ ] Fill Sentry DSN in all EAS profiles
- [ ] TypeScript compiles: `npx tsc --noEmit`

## Security & Deps
- [ ] Run `npm audit` / `pnpm audit` for ground truth
- [ ] Check `gh api repos/.../dependabot/alerts` for open alerts
- [ ] Remove dual lock files if present
- [ ] Update direct vulnerable deps

## Documentation
- [ ] Update CLAUDE.md (readiness score, stack, recent changes, deploy)
- [ ] Update CHANGELOG.md (new version entry)
- [ ] Update DRF Spectacular VERSION
- [ ] Create git tag + GitHub release
- [ ] Write session docs
```

$ARGUMENTS
