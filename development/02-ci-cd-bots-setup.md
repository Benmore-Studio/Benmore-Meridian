# CI/CD Bots & Automated Checks

## 📋 Overview

Every repository should have **4 automated checks** on pull requests before merging. These catch bugs, enforce code quality, verify deployments, and provide AI-assisted review — without manual effort.

| Check | Type | What It Does |
|-------|------|-------------|
| **Sentry Bot** | GitHub App | Catches unhandled errors tied to your PR changes |
| **Vercel Bot** | GitHub App | Auto-deploys preview URLs for every PR |
| **GitHub Actions** | CI Runner | Runs lints, formatting, and tests on every push/PR |
| **Claude Bot** | GitHub App + Action | AI-powered code review triggered by `@claude` |

**Setup order matters** — Sentry first (error tracking foundation), then Vercel (deploy previews), then GitHub Actions (code quality gate), then Claude (AI review layer).

---

## 1. Sentry Bot

### What & Why

Sentry monitors your application for runtime errors, crashes, and performance issues. The **Sentry GitHub integration** connects your repos so that:

- Sentry comments on PRs when your changes touch functions with known unhandled errors
- Stack traces link directly to the file + line in your repo
- Releases are tracked per deploy so you know *which commit* introduced a bug
- CODEOWNERS-based auto-assignment routes alerts to the right developer

### How to Add

**Prerequisites:** You must be a **Manager or Owner** on your Sentry organization.

1. **Create a Sentry project** (if not already):
   - Go to [sentry.io](https://sentry.io) → Create Project
   - Select your platform (Django, Next.js, etc.)
   - Copy the DSN for your `.env` file

2. **Install the Sentry GitHub App:**
   - In Sentry: **Settings → Integrations → GitHub** → Click **Install**
   - In the modal: Click **Add Installation**
   - A GitHub popup will appear → Click **Install**
   - Select which repositories Sentry should have access to (recommend: **all repos** in your org)

   Alternatively, install directly from GitHub: [github.com/apps/sentry](https://github.com/apps/sentry)

3. **Install the SDK in your project:**

   **Django (backend):**
   ```bash
   pip install sentry-sdk
   # or: uv add sentry-sdk
   ```

   Add to `settings.py`:
   ```python
   import sentry_sdk

   sentry_sdk.init(
       dsn=os.environ.get("SENTRY_DSN"),
       traces_sample_rate=1.0,
       profiles_sample_rate=1.0,
   )
   ```

   **Next.js (frontend):**
   ```bash
   npx @sentry/wizard@latest -i nextjs
   ```
   This auto-configures `sentry.client.config.ts`, `sentry.server.config.ts`, and `next.config.js`.

4. **Set environment variable:**
   ```bash
   # .env
   SENTRY_DSN=https://your-key@o123.ingest.sentry.io/456
   ```

### Verification

- [ ] Sentry project exists at sentry.io
- [ ] GitHub integration shows "Installed" in Sentry → Settings → Integrations
- [ ] SDK is installed and `SENTRY_DSN` is in `.env`
- [ ] Trigger a test error and confirm it appears in Sentry dashboard

**Docs:** [docs.sentry.io/organization/integrations/source-code-mgmt/github/](https://docs.sentry.io/organization/integrations/source-code-mgmt/github/)

---

## 2. Vercel Bot

### What & Why

Vercel auto-deploys your **frontend** (Next.js) on every PR and push. The Vercel GitHub integration:

- Creates a **preview deployment URL** for every PR (so reviewers can see changes live)
- Comments on PRs with the preview link and deploy status
- Auto-deploys to production on merges to `main`
- Shows build errors directly in the PR checks

### How to Add

1. **Install the Vercel GitHub App:**
   - Go to [github.com/apps/vercel](https://github.com/apps/vercel) → Click **Install**
   - Select your organization and the repositories to connect

2. **Link your project on Vercel:**
   - Go to [vercel.com/new](https://vercel.com/new)
   - Import your GitHub repository
   - Configure the build settings:
     - **Framework:** Next.js (auto-detected)
     - **Root Directory:** Set if your frontend is in a subdirectory (e.g., `frontend/`)
     - **Build Command:** `npm run build` or `next build`
     - **Output Directory:** `.next`
   - Click **Deploy**

3. **Configure environment variables on Vercel:**
   - Vercel Dashboard → Your Project → Settings → Environment Variables
   - Add all required env vars (`NEXT_PUBLIC_API_URL`, `SENTRY_DSN`, etc.)
   - Set per environment: Production, Preview, Development

4. **Verify bot comments on PRs:**
   - Create a test PR with a frontend change
   - Vercel bot should comment with a preview URL within 1-2 minutes

### Verification

- [ ] Vercel GitHub app installed on your org
- [ ] Project imported and first deploy successful
- [ ] Environment variables set for Production and Preview
- [ ] Test PR triggers a preview deployment comment from Vercel bot

**Docs:** [vercel.com/docs/git/vercel-for-github](https://vercel.com/docs/git/vercel-for-github)

---

## 3. GitHub Actions (Lints, Formats, Tests)

### What & Why

GitHub Actions runs your **code quality checks** automatically on every push and PR. This enforces that all code meets standards before it can be merged. You need workflows for both your **Django backend** and **Next.js frontend**.

### How to Add

Create the `.github/workflows/` directory in your repo root:

```bash
mkdir -p .github/workflows
```

#### Backend Workflow (Django + Python)

Create `.github/workflows/backend.yml`:

```yaml
name: Backend CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint-format-test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install uv
        run: pip install uv

      - name: Install dependencies
        run: uv pip install -r requirements.txt --system

      - name: Lint with ruff
        run: ruff check .

      - name: Format check with ruff
        run: ruff format --check .

      - name: Type check with mypy
        run: mypy . --ignore-missing-imports

      - name: Run tests with pytest
        env:
          DATABASE_URL: postgres://postgres:postgres@localhost:5432/test_db
          DJANGO_SETTINGS_MODULE: config.settings.test
        run: pytest --tb=short -q
```

#### Frontend Workflow (Next.js + TypeScript)

Create `.github/workflows/frontend.yml`:

```yaml
name: Frontend CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint-format-test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        working-directory: frontend
        run: npm ci

      - name: Lint
        working-directory: frontend
        run: npm run lint

      - name: Type check
        working-directory: frontend
        run: npx tsc --noEmit

      - name: Format check
        working-directory: frontend
        run: npx prettier --check .

      - name: Run tests
        working-directory: frontend
        run: npm test -- --passWithNoTests
```

**Note:** Adjust `working-directory` if your frontend is at the repo root instead of `frontend/`.

#### Combined Workflow (Optional)

If you prefer a single workflow file, create `.github/workflows/ci.yml` that combines both jobs.

### Verification

- [ ] `.github/workflows/backend.yml` exists with lint + format + test steps
- [ ] `.github/workflows/frontend.yml` exists with lint + typecheck + format + test steps
- [ ] Push to a branch → Actions tab shows workflows running
- [ ] PR shows green/red check status from GitHub Actions

**Docs:** [docs.github.com/en/actions](https://docs.github.com/en/actions)

---

## 4. Claude Bot (AI-Powered Code Review)

### What & Why

Claude reviews your PRs with AI-powered analysis. When someone comments `@claude` on a PR or issue, Claude:

- Reads the entire PR diff and linked issues
- Provides hyper-critical code review with actionable feedback
- Can implement changes directly by pushing commits
- Reviews against acceptance criteria from linked tickets

### How to Add

**There are 2 parts:** the GitHub App (for the bot identity) and the GitHub Action (for the compute).

#### Part 1: Install the Claude GitHub App

Run this command **inside Claude Code** in your terminal:

```
/install-github-app
```

This walks you through installing the [Claude GitHub App](https://github.com/apps/claude) on your organization. You need to be an **Owner** on the GitHub org.

Alternatively, install manually:
- Go to [github.com/apps/claude](https://github.com/apps/claude)
- Click **Install** → Select your organization → Select repositories

#### Part 2: Add the GitHub Action Workflow

1. **Add your Anthropic API key as a repository secret:**
   - Go to your repo → **Settings → Secrets and variables → Actions**
   - Click **New repository secret**
   - Name: `ANTHROPIC_API_KEY`
   - Value: Your Anthropic API key (starts with `sk-ant-`)

   **Alternative for Pro/Max users:** Generate an OAuth token instead:
   ```bash
   claude setup-token
   ```
   Then add as secret named `CLAUDE_CODE_OAUTH_TOKEN`.

2. **Create the workflow file** `.github/workflows/claude.yml`:

```yaml
name: Claude Code

on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]
  issues:
    types: [opened, assigned]
  pull_request_review:
    types: [submitted]

jobs:
  claude:
    if: |
      (github.event_name == 'issue_comment' && contains(github.event.comment.body, '@claude')) ||
      (github.event_name == 'pull_request_review_comment' && contains(github.event.comment.body, '@claude')) ||
      (github.event_name == 'pull_request_review' && contains(github.event.review.body, '@claude')) ||
      (github.event_name == 'issues' && (contains(github.event.issue.body, '@claude') || contains(github.event.issue.title, '@claude')))
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
      issues: write
      id-token: write
      actions: read
    steps:
      - name: Checkout repository
        uses: actions/checkout@v6
        with:
          fetch-depth: 1

      - name: Run Claude Code
        id: claude
        uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

3. **Commit and push the workflow file.**

#### Usage

- Comment `@claude` on any PR or issue to trigger a review
- Claude reads the context (diff, issue body, comments) and responds
- On PRs, Claude can push commits directly if asked to implement changes

### Verification

- [ ] Claude GitHub App installed on your organization
- [ ] `ANTHROPIC_API_KEY` (or `CLAUDE_CODE_OAUTH_TOKEN`) added as repo secret
- [ ] `.github/workflows/claude.yml` committed to the repo
- [ ] Test: comment `@claude review this PR` on a test PR → Claude responds

**Docs:**
- [github.com/anthropics/claude-code-action](https://github.com/anthropics/claude-code-action)
- [code.claude.com/docs/en/github-actions](https://code.claude.com/docs/en/github-actions)

---

## Complete PR Checks Summary

After setup, every PR should show these 4 checks before merging:

```
✅ Sentry         — No new unhandled errors introduced
✅ Vercel          — Preview deployment successful (click to view)
✅ GitHub Actions  — Lints pass, format clean, tests green
✅ Claude          — AI review completed (if triggered)
```

### Quick Reference: What You Need

| Bot | Install From | Secret/Key Needed | Org Permission |
|-----|-------------|-------------------|----------------|
| Sentry | [github.com/apps/sentry](https://github.com/apps/sentry) | `SENTRY_DSN` in `.env` | Manager/Owner on Sentry |
| Vercel | [github.com/apps/vercel](https://github.com/apps/vercel) | Env vars on Vercel dashboard | Vercel team member |
| GitHub Actions | Built-in (add YAML files) | None (or DB creds for tests) | Repo write access |
| Claude | [github.com/apps/claude](https://github.com/apps/claude) | `ANTHROPIC_API_KEY` repo secret | Org Owner on GitHub |

---

## ✅ Full Setup Checklist

### Sentry Bot
- [ ] Sentry project created at sentry.io
- [ ] Sentry GitHub App installed (Settings → Integrations → GitHub)
- [ ] SDK installed in backend (`sentry-sdk`) and/or frontend (`@sentry/nextjs`)
- [ ] `SENTRY_DSN` set in `.env`
- [ ] Test error appears in Sentry dashboard

### Vercel Bot
- [ ] Vercel GitHub App installed from github.com/apps/vercel
- [ ] Project imported on Vercel dashboard
- [ ] Environment variables configured (Production + Preview)
- [ ] Test PR triggers preview deployment

### GitHub Actions
- [ ] `.github/workflows/backend.yml` — lint, format, test for Django
- [ ] `.github/workflows/frontend.yml` — lint, typecheck, format, test for Next.js
- [ ] Both workflows pass on a test push

### Claude Bot
- [ ] Claude GitHub App installed (`/install-github-app` in Claude Code)
- [ ] `ANTHROPIC_API_KEY` added as repository secret
- [ ] `.github/workflows/claude.yml` committed
- [ ] Test `@claude` comment triggers a response

---

## 🔗 Related Guides

- [Developer Workflow](./00-developer-workflow.md) — End-to-end development process
- [PR Review Workflow](./01-pr-review-workflow.md) — How to review PRs with AI
- [Claude Code Ecosystem](./03-claude-code-ecosystem.md) — MCP tools, plugins, and skills
- [Dev Toolkit](../toolkit/) — Development environment setup
