---
name: sentry-cli
description: Manage Sentry releases, sourcemaps, cron monitors, issues, and deployments from the command line using sentry-cli
context: fork
---

# Sentry CLI Skill

`sentry-cli` is the official CLI for Sentry error tracking. Manage releases, upload sourcemaps, track deployments, monitor crons, and triage issues. Use `sentry-cli <command> --help` for full flag details.

## Installation

```bash
# macOS/Linux automatic installer
curl -sL https://sentry.io/get-cli/ | sh

# Pin a specific version (reproducible builds)
curl -sL https://sentry.io/get-cli/ | SENTRY_CLI_VERSION="3.3.5" sh

# Via Homebrew
brew install getsentry/tools/sentry-cli

# Via npm (useful for JS build pipelines)
npm install @sentry/cli
# Then: ./node_modules/.bin/sentry-cli --help

# Verify installation
sentry-cli --version
sentry-cli --help
```

## Authentication

Three methods, in order of preference:

### 1. Interactive Login (recommended for local dev)

```bash
# Opens browser to create/copy an auth token
sentry-cli login

# For self-hosted Sentry
sentry-cli --url https://sentry.mycompany.com/ login
```

This saves the token to `~/.sentryclirc` automatically.

### 2. Environment Variable (recommended for CI/CD)

```bash
export SENTRY_AUTH_TOKEN=sntrys_YOUR_TOKEN_HERE
```

### 3. Config File (`~/.sentryclirc`)

```ini
[auth]
token=sntrys_YOUR_TOKEN_HERE
```

### Creating Auth Tokens

1. Go to **Settings > Auth Tokens** in Sentry (or https://sentry.io/settings/auth-tokens/)
2. Click "Create New Token"
3. **Organization Tokens** (recommended): scoped to an org, used for CI/CD and automation
4. **User Auth Tokens**: scoped to your user account

### Verify Authentication

```bash
# Check config and auth status
sentry-cli info

# Check config without org/project validation
sentry-cli info --no-defaults

# Get config status as JSON (for tooling)
sentry-cli info --config-status-json
```

## Configuration

### Config File (`.sentryclirc`)

The CLI searches upward from the current directory for `.sentryclirc`, then falls back to `~/.sentryclirc`. Uses INI syntax.

```ini
[defaults]
url = https://sentry.io/
org = my-org
project = my-project

[auth]
token = sntrys_YOUR_TOKEN_HERE
```

**Project-level config** (`.sentryclirc` in repo root):

```ini
[defaults]
org = benmore-tech
project = my-django-app
```

### Environment Variables

| Variable | Config Key | Purpose |
|----------|-----------|---------|
| `SENTRY_AUTH_TOKEN` | `auth.token` | Auth token for all API requests |
| `SENTRY_DSN` | `auth.dsn` | DSN for cron monitoring and event sending |
| `SENTRY_URL` | `defaults.url` | Sentry server URL (default: `https://sentry.io/`) |
| `SENTRY_ORG` | `defaults.org` | Default organization slug |
| `SENTRY_PROJECT` | `defaults.project` | Default project slug |
| `SENTRY_API_KEY` | `auth.api_key` | Legacy API key (deprecated) |
| `SENTRY_LOG_LEVEL` | — | Log verbosity: trace, debug, info, warn, error |

### .env File Support

`sentry-cli` also reads `.env` files in the current directory, so you can set `SENTRY_AUTH_TOKEN` there for local development (but keep it out of version control).

## Releases

Releases link errors to specific code versions and enable commit tracking.

```bash
# Propose a version based on git
sentry-cli releases propose-version
# Output: e.g., "abc123def456"

# Create a new release
sentry-cli releases new <version> -o <org> -p <project>
sentry-cli releases new "1.0.0" -o benmore-tech -p my-app

# Set commits (links errors to git commits)
sentry-cli releases set-commits <version> --auto
# Or manually specify repo + commit range:
sentry-cli releases set-commits <version> --commit "repo@from..to"

# Finalize a release (marks it as deployed)
sentry-cli releases finalize <version>

# List recent releases
sentry-cli releases list -o <org> -p <project>

# Get release info
sentry-cli releases info <version> -o <org> -p <project>

# Delete a release
sentry-cli releases delete <version> -o <org> -p <project>

# Archive/restore a release
sentry-cli releases archive <version> -o <org> -p <project>
sentry-cli releases restore <version> -o <org> -p <project>
```

### Typical Release Flow

```bash
VERSION=$(sentry-cli releases propose-version)
sentry-cli releases new "$VERSION" -o my-org -p my-project
sentry-cli releases set-commits "$VERSION" --auto
# ... deploy your app ...
sentry-cli releases finalize "$VERSION"
sentry-cli deploys new -r "$VERSION" -o my-org -p my-project -e production
```

## Sourcemaps

Upload sourcemaps so Sentry can show readable stack traces for minified JS.

```bash
# Upload sourcemaps for a release
sentry-cli sourcemaps upload ./dist \
  -o <org> -p <project> -r <release>

# Inject debug IDs into source files and sourcemaps
sentry-cli sourcemaps inject ./dist

# Inject then upload (recommended workflow)
sentry-cli sourcemaps inject ./dist
sentry-cli sourcemaps upload ./dist -o <org> -p <project> -r <release>

# Resolve a sourcemap for debugging
sentry-cli sourcemaps resolve ./dist/app.js.map --line 42 --column 10
```

### Next.js / Webpack Example

```bash
# After build
VERSION=$(sentry-cli releases propose-version)
sentry-cli releases new "$VERSION" -o my-org -p my-nextjs-app
sentry-cli sourcemaps inject .next/
sentry-cli sourcemaps upload .next/ -o my-org -p my-nextjs-app -r "$VERSION"
sentry-cli releases finalize "$VERSION"
```

## Deployments

Track where and when releases are deployed.

```bash
# Create a deployment
sentry-cli deploys new \
  -r <release> \
  -o <org> \
  -p <project> \
  -e production

# With timestamp and optional name
sentry-cli deploys new \
  -r "1.0.0" \
  -o my-org \
  -p my-app \
  -e staging \
  --started $(date +%s) \
  --name "deploy-42"

# List deployments for a release
sentry-cli deploys list -r <release> -o <org> -p <project>
```

## Cron Monitors

Monitor cron jobs and scheduled tasks. Sentry alerts you when jobs fail or don't run on time.

```bash
# List all monitors
sentry-cli monitors list -o <org>

# Wrap a command — Sentry tracks start/finish/failure
sentry-cli monitors run <monitor-slug> -- <command>

# Example: wrap a Django management command
sentry-cli monitors run cleanup-job -- python manage.py cleanup

# Example: wrap a cron entry
# In crontab:
# */5 * * * * sentry-cli monitors run my-cron -- /path/to/script.sh
```

**DSN-based monitoring** (alternative, no auth token needed):

```bash
export SENTRY_DSN="https://key@sentry.io/123"
sentry-cli monitors run my-cron -- ./my-script.sh
```

## Issues Management

Triage issues in bulk from the CLI.

```bash
# List issues
sentry-cli issues list -o <org> -p <project>

# Filter by status
sentry-cli issues list -o <org> -p <project> --status unresolved

# Bulk resolve issues
sentry-cli issues resolve -o <org> -p <project> --all
sentry-cli issues resolve -o <org> -p <project> --id <issue-id>

# Bulk mute issues
sentry-cli issues mute -o <org> -p <project> --id <issue-id>

# Unresolve issues
sentry-cli issues unresolve -o <org> -p <project> --id <issue-id>
```

## Events

```bash
# List recent events
sentry-cli events list -o <org> -p <project>

# Send a test event
sentry-cli send-event -m "Test event from CLI"
sentry-cli send-event -m "Something broke" -l error --tag environment:production
```

## Organizations & Projects

```bash
# List organizations you have access to
sentry-cli organizations list

# List projects in an organization
sentry-cli projects list -o <org>
```

## Debug Files (Native Crashes)

For native apps (iOS, Android, C/C++).

```bash
# Check debug files
sentry-cli debug-files check ./path/to/dsym

# Upload debug symbols
sentry-cli debug-files upload ./path/to/dsym -o <org> -p <project>

# Upload ProGuard mappings (Android)
sentry-cli upload-proguard ./mapping.txt -o <org> -p <project>
```

## React Native

```bash
# Upload source bundle for React Native
sentry-cli react-native gradle --bundle ./index.android.bundle --sourcemap ./index.android.bundle.map
sentry-cli react-native xcode
```

## CI/CD Integration

### GitHub Actions

```yaml
- name: Create Sentry Release
  env:
    SENTRY_AUTH_TOKEN: ${{ secrets.SENTRY_AUTH_TOKEN }}
    SENTRY_ORG: my-org
    SENTRY_PROJECT: my-project
  run: |
    VERSION=$(sentry-cli releases propose-version)
    sentry-cli releases new "$VERSION"
    sentry-cli releases set-commits "$VERSION" --auto
    sentry-cli sourcemaps inject ./dist
    sentry-cli sourcemaps upload ./dist -r "$VERSION"
    sentry-cli releases finalize "$VERSION"
    sentry-cli deploys new -r "$VERSION" -e production
```

### Django Deploy Script

```bash
#!/bin/bash
set -e
VERSION=$(sentry-cli releases propose-version)
sentry-cli releases new "$VERSION" -o my-org -p my-django-app
sentry-cli releases set-commits "$VERSION" --auto

# Deploy
git push heroku main  # or your deploy command

sentry-cli releases finalize "$VERSION"
sentry-cli deploys new -r "$VERSION" -o my-org -p my-django-app -e production
echo "Deployed and tracked in Sentry: $VERSION"
```

## Global Flags

These flags work with any command:

```bash
--url <URL>              # Sentry server URL (default: https://sentry.io/)
--auth-token <TOKEN>     # Override auth token
--header <KEY:VALUE>     # Custom HTTP headers
--log-level <LEVEL>      # trace, debug, info, warn, error
--quiet                  # Suppress output (preserves exit code)
-o, --org <ORG>          # Organization slug
-p, --project <PROJECT>  # Project slug
```

## Troubleshooting

```bash
# Verify config and auth
sentry-cli info

# Debug HTTP requests
sentry-cli --log-level debug releases list -o my-org -p my-project

# Check which config file is loaded
sentry-cli info --config-status-json | jq .

# Test connectivity
sentry-cli send-event -m "test" --log-level debug

# Update sentry-cli
brew upgrade sentry-cli
# or
curl -sL https://sentry.io/get-cli/ | sh

# Check version
sentry-cli --version
```
