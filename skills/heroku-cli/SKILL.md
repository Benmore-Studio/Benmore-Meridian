---
name: heroku-cli
description: Deploy, manage, and operate apps on Heroku from the command line — dynos, databases, config, logs, and pipelines
context: fork
---

# Heroku CLI Skill

The Heroku CLI manages apps, dynos, databases, config vars, and deployments on the Heroku platform. Use `heroku <command> --help` for full flag details.

## Installation & Authentication

```bash
# Install via Homebrew
brew install heroku

# Login (opens browser for OAuth)
heroku login

# Login via CLI only (no browser)
heroku login -i

# Check who you're logged in as
heroku whoami

# Logout
heroku logout
```

## Configuration & Auth Tokens

Heroku CLI uses OAuth by default via `heroku login`. Auth tokens are stored in `~/.netrc`.

```bash
# View current auth token
heroku auth:token

# Create a long-lived authorization (for CI/scripts)
heroku authorizations:create --description "CI token"

# List authorizations
heroku authorizations

# Revoke an authorization
heroku authorizations:revoke <id>

# Set token via environment variable (for CI/CD)
export HEROKU_API_KEY="your-token-here"
```

**Environment variables:**

| Variable | Purpose |
|----------|---------|
| `HEROKU_API_KEY` | Auth token (overrides `~/.netrc`) |
| `HEROKU_APP` | Default app (skip `-a` flag) |
| `HEROKU_TEAM` | Default team |
| `HEROKU_DEBUG` | Enable debug output (`1`) |
| `HEROKU_DEBUG_HEADERS` | Show HTTP headers (`1`) |

**MCP Server** (for AI agent integration):

```bash
# Start Heroku MCP server (stdio mode)
heroku mcp
```

## App Management

```bash
# List all apps
heroku apps
heroku apps --json

# App info
heroku apps:info -a <app-name>
heroku apps:info -a <app-name> --json

# Create a new app
heroku apps:create <app-name>
heroku apps:create <app-name> --region eu

# Rename app
heroku apps:rename <new-name> -a <old-name>

# Delete app (destructive!)
heroku apps:destroy -a <app-name>

# Open app in browser
heroku open -a <app-name>

# App maintenance mode
heroku maintenance:on -a <app-name>
heroku maintenance:off -a <app-name>
```

## Deployment

```bash
# Deploy via Git
git push heroku main

# Deploy a specific branch
git push heroku feature-branch:main

# Set Git remote
heroku git:remote -a <app-name>

# View releases
heroku releases -a <app-name>

# Rollback to previous release
heroku rollback -a <app-name>
heroku rollback v42 -a <app-name>
```

## Dynos (Process Management)

```bash
# List running dynos
heroku ps -a <app-name>

# Scale dynos
heroku ps:scale web=1 -a <app-name>
heroku ps:scale web=2:standard-1x -a <app-name>
heroku ps:scale worker=1 -a <app-name>

# Restart dynos
heroku ps:restart -a <app-name>
heroku ps:restart web -a <app-name>
heroku ps:restart web.1 -a <app-name>

# Stop a dyno
heroku ps:stop worker.1 -a <app-name>

# Resize dyno type
heroku ps:type web=standard-2x -a <app-name>

# One-off dyno (run a command)
heroku run bash -a <app-name>
heroku run python manage.py migrate -a <app-name>
heroku run python manage.py createsuperuser -a <app-name>
heroku run python manage.py shell -a <app-name>
```

## Config Vars (Environment Variables)

```bash
# List all config vars
heroku config -a <app-name>
heroku config -a <app-name> --json

# Get a specific var
heroku config:get DATABASE_URL -a <app-name>

# Set config vars
heroku config:set SECRET_KEY="my-secret" -a <app-name>
heroku config:set KEY1=val1 KEY2=val2 -a <app-name>

# Remove config var
heroku config:unset KEY_NAME -a <app-name>

# Edit interactively
heroku config:edit -a <app-name>
```

## Logs

```bash
# View recent logs
heroku logs -a <app-name>

# Tail logs (live stream)
heroku logs --tail -a <app-name>

# Filter by process type
heroku logs --process-type=web -a <app-name>
heroku logs --process-type=worker -a <app-name>

# Filter by dyno name
heroku logs --dyno-name=web-123-456 -a <app-name>

# Limit number of lines
heroku logs --num=100 -a <app-name>

# Filter by source
heroku logs --source=app -a <app-name>
heroku logs --source=heroku -a <app-name>
```

## PostgreSQL Database

```bash
# Database info
heroku pg -a <app-name>
heroku pg:info -a <app-name>

# Open psql shell
heroku pg:psql -a <app-name>

# Create backup
heroku pg:backups:capture -a <app-name>

# List backups
heroku pg:backups -a <app-name>

# Download latest backup
heroku pg:backups:download -a <app-name>

# Restore from backup
heroku pg:backups:restore <backup-url> DATABASE_URL -a <app-name>

# Push local DB to Heroku
heroku pg:push local_db DATABASE_URL -a <app-name>

# Pull Heroku DB locally
heroku pg:pull DATABASE_URL local_db -a <app-name>

# Reset database (destructive!)
heroku pg:reset -a <app-name>

# Database credentials
heroku pg:credentials:url -a <app-name>

# Run SQL
heroku pg:psql -a <app-name> -c "SELECT count(*) FROM users;"
```

## Redis

```bash
# Redis info
heroku redis -a <app-name>
heroku redis:info -a <app-name>

# Open Redis CLI
heroku redis:cli -a <app-name>
```

## Add-ons

```bash
# List add-ons on an app
heroku addons -a <app-name>

# List all add-ons across apps
heroku addons --all

# Provision an add-on
heroku addons:create heroku-postgresql:essential-0 -a <app-name>
heroku addons:create heroku-redis:mini -a <app-name>
heroku addons:create papertrail:choklad -a <app-name>

# Add-on info
heroku addons:info <addon-name> -a <app-name>

# Open add-on dashboard
heroku addons:open <addon-name> -a <app-name>

# Destroy add-on
heroku addons:destroy <addon-name> -a <app-name>

# List available add-on plans
heroku addons:plans <addon-service>
```

## Domains & SSL

```bash
# List domains
heroku domains -a <app-name>

# Add custom domain
heroku domains:add www.example.com -a <app-name>
heroku domains:add example.com -a <app-name>

# Remove domain
heroku domains:remove www.example.com -a <app-name>

# SSL certificates
heroku certs -a <app-name>
heroku certs:auto -a <app-name>
heroku certs:auto:enable -a <app-name>
```

## Pipelines (Staging/Production)

```bash
# List pipelines
heroku pipelines

# Create pipeline
heroku pipelines:create <pipeline-name> -a <app-name> --stage production

# Add app to pipeline
heroku pipelines:add <pipeline-name> -a <staging-app> --stage staging

# Promote staging to production
heroku pipelines:promote -a <staging-app>

# Pipeline info
heroku pipelines:info <pipeline-name>
```

## Buildpacks

```bash
# List buildpacks
heroku buildpacks -a <app-name>

# Set buildpack
heroku buildpacks:set heroku/python -a <app-name>

# Add buildpack (multi-buildpack)
heroku buildpacks:add heroku/nodejs -a <app-name>

# Set buildpack order
heroku buildpacks:set heroku/nodejs --index 1 -a <app-name>
```

## Access & Teams

```bash
# List collaborators
heroku access -a <app-name>

# Add collaborator
heroku access:add user@example.com -a <app-name>

# Remove collaborator
heroku access:remove user@example.com -a <app-name>

# List teams
heroku teams

# List team members
heroku members -t <team-name>
```

## Container Deployment (Docker)

```bash
# Login to container registry
heroku container:login

# Push image
heroku container:push web -a <app-name>

# Release image
heroku container:release web -a <app-name>

# Push + release in one step
heroku container:push web -a <app-name> && heroku container:release web -a <app-name>
```

## Local Development

```bash
# Run app locally using Procfile
heroku local

# Run specific process
heroku local web

# Run with specific .env file
heroku local --env .env.local
```

## SSH Keys

```bash
# List SSH keys
heroku keys

# Add SSH key
heroku keys:add ~/.ssh/id_ed25519.pub

# Remove SSH key
heroku keys:remove user@example.com
```

## Django-Specific Workflows

```bash
# Run migrations
heroku run python manage.py migrate -a <app-name>

# Create superuser
heroku run python manage.py createsuperuser -a <app-name>

# Django shell
heroku run python manage.py shell -a <app-name>

# Collect static files
heroku run python manage.py collectstatic --noinput -a <app-name>

# Run management command
heroku run python manage.py <command> -a <app-name>

# Check Celery worker
heroku ps -a <app-name> | grep worker
heroku logs --process-type=worker -a <app-name>
```

## Troubleshooting

```bash
# Check app status
heroku ps -a <app-name>
heroku logs --tail -a <app-name>

# Check Heroku platform status
heroku status

# Restart everything
heroku ps:restart -a <app-name>

# Check buildpacks
heroku buildpacks -a <app-name>

# Check releases for recent changes
heroku releases -a <app-name>

# Debug: run bash on a dyno
heroku run bash -a <app-name>

# Check CLI version
heroku --version

# Update CLI
heroku update
```

## Common Procfile Examples

```
# Django with Gunicorn
web: gunicorn myproject.wsgi --log-file -
worker: celery -A myproject worker --loglevel=info
beat: celery -A myproject beat --loglevel=info

# Django with uv
web: uv run gunicorn myproject.wsgi --log-file -
release: uv run python manage.py migrate
```

## Environment Tips

- Always use `heroku config:set` instead of hardcoding secrets
- Use `heroku pg:credentials:url` to get the current DATABASE_URL
- `heroku run` spins up a one-off dyno — it does NOT run on your web dyno
- `heroku local` reads from `.env` file (not Heroku config vars)
- Add `-a <app-name>` to every command, or set `HEROKU_APP` env var, or run from a directory with the Heroku git remote
