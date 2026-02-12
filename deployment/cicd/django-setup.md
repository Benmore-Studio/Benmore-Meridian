# Django CI/CD Setup with Claude Code

A step-by-step guide for adding production-ready CI/CD to your Django project using Claude Code.

---

## Prerequisites

- A Django project in a GitHub repository
- [Claude Code](https://claude.ai/code) installed
- [GitHub CLI](https://cli.github.com/) installed (`brew install gh`)

---

## Step 1: Add the GITLEAKS_LICENSE Secret

This is the **only required secret** for CI to pass.

Run this command in your repo directory:

```bash
gh secret set GITLEAKS_LICENSE --body "798620-5A7AE5-F51154-DB60A3-A67AAB-V3"
```

> 📌 This license key enables secret scanning in your CI pipeline.

---

## Step 2: Install the django-production Skill

```bash
# Clone the skills repository (one-time setup)
git clone https://github.com/Benmore-Studio/ArkashJ_projects.git ~/ArkashJ_projects

# Create Claude Code skills directory
mkdir -p ~/.claude/skills

# Copy the skill
cp -r ~/ArkashJ_projects/skills/django-production ~/.claude/skills/
```

**Alternative:** If you have the skills in this repository:

```bash
cp -r skills/django-production ~/.claude/skills/
```

---

## Step 3: Run the Skill

Open your Django project in Claude Code and run:

```
/django-production
```

The skill will:
1. Audit your current setup
2. Identify what's missing
3. Add the necessary CI/CD files

---

## Step 4: Verify Locally

```bash
# Install dependencies
uv sync --all-groups

# Run all checks locally
make check-all
```

This should pass all checks:
- ✅ Code formatting (ruff format)
- ✅ Linting (ruff check)
- ✅ Type checking (mypy)
- ✅ Tests (pytest)
- ✅ Security scan (gitleaks)
- ✅ Django system checks

---

## Step 5: Push and Verify CI

```bash
# Commit the changes
git add .
git commit -m "Add CI/CD configuration"

# Push to GitHub
git push origin main
```

Check GitHub Actions - you should see **5 passing checks**:
- ✅ Lint & Format
- ✅ Test
- ✅ Security Scan
- ✅ Django System Checks
- ✅ Docker Build

---

## What the Skill Adds

| File | Purpose |
|------|---------|
| `.github/workflows/ci.yml` | CI pipeline (lint, test, security, docker) |
| `pyproject.toml` | Dependencies + ruff/pytest/coverage config |
| `Makefile` | Local dev commands (`make check-all`) |
| `.pre-commit-config.yaml` | Git hooks for code quality |
| `.gitleaks.toml` | Security scanner config |
| `Dockerfile` | Production container |
| `docker-compose.yml` | Local development with Docker |

---

## CI Pipeline Breakdown

### Workflow: `.github/workflows/ci.yml`

The CI pipeline runs on every push and pull request to `main`:

```yaml
name: Django CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    # Runs ruff format check and ruff linting

  test:
    # Runs pytest with coverage (fails if <80%)

  security:
    # Scans for secrets with gitleaks

  django-checks:
    # Runs Django system checks

  docker:
    # Builds Docker image to verify containerization
```

---

## Optional: Pre-commit Hooks

Install pre-commit hooks to run checks before every commit:

```bash
# Install pre-commit
uv add --dev pre-commit

# Install the git hooks
pre-commit install
```

Now checks run automatically when you commit:
- ✅ Ruff formatting
- ✅ Ruff linting
- ✅ Gitleaks secret scanning
- ✅ Trailing whitespace removal
- ✅ YAML/JSON validation

Skip hooks when needed (not recommended):
```bash
git commit --no-verify -m "Emergency fix"
```

---

## Optional: AI Code Review on PRs

If you want Claude to automatically review pull requests, add this secret:

```bash
gh secret set CLAUDE_CODE_OAUTH_TOKEN --body "your-token-here"
```

**How to get the token:**
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Generate an API key
3. Add it with the command above

This enables the `claude-code-review.yml` workflow that posts AI review comments on PRs.

> ⚠️ This is **not required** for the 5 CI checks to pass.

---

## Optional: Error Monitoring (Sentry)

For production error tracking:

1. Create a Sentry account at [sentry.io](https://sentry.io)
2. Create a new Django project in Sentry
3. Copy the DSN and add it:

```bash
gh secret set SENTRY_DSN --body "https://xxx@xxx.ingest.sentry.io/xxx"
```

4. Install Sentry in your Django project:

```bash
uv add sentry-sdk
```

5. Add to `settings.py`:

```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN"),
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)
```

---

## Makefile Commands

The `django-production` skill adds these helpful commands:

| Command | What it does |
|---------|--------------|
| `make check-all` | Run all checks (lint, test, security) |
| `make format` | Auto-format code with ruff |
| `make lint` | Check code with ruff linter |
| `make test` | Run tests with coverage |
| `make security` | Scan for secrets |
| `make django-check` | Run Django system checks |
| `make migrate` | Run database migrations |
| `make run` | Start development server |

**Example workflow:**
```bash
# Before committing
make check-all

# If formatting issues
make format

# If tests fail, fix them and re-run
make test

# When all checks pass
git add .
git commit -m "Add feature"
git push
```

---

## Troubleshooting

### "Gitleaks detected a secret"

- **False positive**: Add pattern to `.gitleaks.toml` allowlist:
  ```toml
  [allowlist]
  paths = [
      '''\.env\.example$''',
  ]
  regexes = [
      '''sk-test-''',  # Stripe test keys
  ]
  ```

- **Real secret**:
  1. Rotate the secret immediately
  2. Remove from git history:
     ```bash
     git filter-branch --force --index-filter \
       "git rm --cached --ignore-unmatch path/to/file" \
       --prune-empty --tag-name-filter cat -- --all
     ```

### "Coverage below 80%"

Lower the threshold temporarily in `pyproject.toml`:
```toml
[tool.coverage.report]
fail_under = 60
```

Then gradually increase coverage by adding tests.

### "Missing migrations"

```bash
uv run python manage.py makemigrations
uv run python manage.py migrate
git add */migrations/
git commit -m "Add migrations"
```

### "Ruff formatting failed"

Auto-fix with:
```bash
make format
git add .
git commit -m "Apply ruff formatting"
```

### "Docker build failed"

Check your `Dockerfile` and ensure all dependencies are in `pyproject.toml`:

```bash
# Test Docker build locally
docker build -t myapp .

# If it fails, check the logs
docker build --progress=plain -t myapp .
```

---

## CI/CD Best Practices

### Branch Protection Rules

Require status checks before merging:

1. Go to GitHub repository settings
2. Navigate to Branches → Add branch protection rule
3. Set pattern: `main`
4. Enable:
   - ✅ Require status checks to pass
   - ✅ Require branches to be up to date
   - ✅ Include administrators
5. Select required checks:
   - Lint & Format
   - Test
   - Security Scan
   - Django System Checks

### Dependabot

Enable automatic dependency updates:

Create `.github/dependabot.yml`:
```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
```

### Deployment Pipeline

Extend CI to include deployment:

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    needs: [lint, test, security]  # Run after CI passes
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Heroku
        uses: akhileshns/heroku-deploy@v3.12.12
        with:
          heroku_api_key: ${{secrets.HEROKU_API_KEY}}
          heroku_app_name: "your-app-name"
          heroku_email: "your-email@example.com"
```

---

## Need Help?

- Run `/django-production` in Claude Code for guided setup
- Check the [Django Production Guide](../django/02-detailed-checklist.md) for detailed explanations
- Review GitHub Actions logs for specific error messages

---

## Related Guides

- [Django Production Checklist](../django/02-detailed-checklist.md) - Complete production readiness guide
- [Heroku Django Deployment](01-heroku-django.md) - Deploy Django to Heroku
- [DigitalOcean Operations](02-digitalocean-ops.md) - Manage Django on DigitalOcean

---

## Quick Reference

```bash
# Local development
make check-all          # Run all checks
make format             # Auto-format code
make test               # Run tests
make run                # Start dev server

# Git workflow
git add .
git commit -m "message"
make check-all          # Verify before pushing
git push origin main

# CI troubleshooting
gh run list             # List recent workflow runs
gh run view <run-id>    # View specific run
gh run watch            # Watch current run
```
