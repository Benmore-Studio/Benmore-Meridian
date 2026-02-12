# DigitalOcean Daily Operations

## How To: Pull New Code & Update Live Site

### When to do this

- You pushed changes to GitHub
- Live site doesn't show your updates

### Steps

1. Connect to the server (see [Getting Started](02-getting-started.md))

2. Go to your project folder:

```bash
cd /root/YOUR_REPOS/YOUR_PROJECT
```

3. Pull the latest code:

```bash
git pull origin main
```

Replace `main` with your branch name if different.

4. If you have new Python packages:

```bash
cd BACKEND_FOLDER
uv sync
```

5. If you have model changes:

```bash
uv run python manage.py migrate
```

6. Restart the app:

```bash
pm2 restart yourproject
```

7. Verify it's running:

```bash
pm2 status | grep yourproject
```

Should show `online`.

8. Check logs if something is wrong:

```bash
pm2 logs yourproject --lines 50
```

---

## How To: Run Migrations

### When to do this

- You added/changed a model in Django
- You pulled new code that has model changes
- You see "no such table" or "column does not exist" errors

### Steps

1. Connect to the server (see [Getting Started](02-getting-started.md))

2. Go to your project's backend folder:

```bash
cd /root/YOUR_REPOS/YOUR_PROJECT/BACKEND_FOLDER
```

Example:

```bash
cd /root/charles_repos/propurti_backend
```

3. Run migrations:

```bash
uv run python manage.py migrate
```

4. If you created new models, run makemigrations first:

```bash
uv run python manage.py makemigrations
uv run python manage.py migrate
```

5. Restart your app:

```bash
pm2 restart yourproject
```

---

## How To: Run Django Commands on the Server

### Steps

1. Connect to the server (see [Getting Started](02-getting-started.md))

2. Go to your project's backend folder:

```bash
cd /root/YOUR_REPOS/YOUR_PROJECT/BACKEND_FOLDER
```

3. Run any Django command using `uv run`:

```bash
uv run python manage.py <command>
```

### Common Django Commands

| What you want | Command |
|---------------|---------|
| Run migrations | `uv run python manage.py migrate` |
| Create migrations | `uv run python manage.py makemigrations` |
| Create admin user | `uv run python manage.py createsuperuser` |
| Collect static files | `uv run python manage.py collectstatic` |
| Open Django shell | `uv run python manage.py shell` |
| Check for issues | `uv run python manage.py check` |
| Show all URLs | `uv run python manage.py show_urls` |
| Clear sessions | `uv run python manage.py clearsessions` |

### Examples

**Create a superuser:**

```bash
cd /root/charles_repos/propurti_backend
uv run python manage.py createsuperuser
```

**Open Django shell to query data:**

```bash
cd /root/charles_repos/propurti_backend
uv run python manage.py shell
```

**Collect static files after frontend changes:**

```bash
cd /root/charles_repos/propurti_backend
uv run python manage.py collectstatic --noinput
```

### Tips

- Always `cd` to the backend folder first before running commands
- Use `--noinput` flag to skip confirmation prompts (e.g., `collectstatic --noinput`)
- After running commands that change the app, restart with `pm2 restart yourproject`
- Use Claude on the server (`claude`) if you need help with Django commands

---

## How To: View and Monitor Logs

### Quick Log Check

```bash
pm2 logs yourproject --lines 50
```

Shows last 50 lines of logs.

### Real-Time Log Streaming

```bash
pm2 logs yourproject
```

Press `Ctrl+C` to stop.

### Error Logs Only

```bash
pm2 logs yourproject --err
```

### Specific Number of Lines

```bash
pm2 logs yourproject --lines 100
```

### View Log Files Directly

```bash
# Error log
tail -f /root/logs/YOUR_REPOS/yourproject-error.log

# Output log
tail -f /root/logs/YOUR_REPOS/yourproject-out.log
```

---

## How To: Restart Services

### Restart Your Main App

```bash
pm2 restart yourproject
```

### Restart Celery Worker

```bash
pm2 restart yourproject-celery-worker
```

### Restart Celery Beat

```bash
pm2 restart yourproject-celery-beat
```

### Restart All Services for Your Project

```bash
pm2 restart yourproject yourproject-celery-worker yourproject-celery-beat
```

### Restart Everything on Server

```bash
pm2 restart all
```

**Warning:** This restarts all projects, not just yours!

---

## How To: Check App Status

### Quick Status Check

```bash
pm2 status | grep yourproject
```

Shows only your project.

### Detailed Status

```bash
pm2 describe yourproject
```

Shows:
- Uptime
- Memory usage
- CPU usage
- Restart count
- Log paths

### Real-Time Monitoring

```bash
pm2 monit
```

Interactive dashboard. Press `q` to quit.

---

## How To: Update Dependencies

### When to do this

- You added new packages to `pyproject.toml` or `requirements.txt`
- You see `ModuleNotFoundError` errors
- After pulling code with dependency changes

### Steps

1. Go to backend folder:

```bash
cd /root/YOUR_REPOS/YOUR_PROJECT/BACKEND
```

2. Update dependencies:

```bash
uv sync
```

3. Restart app:

```bash
pm2 restart yourproject
```

4. Verify:

```bash
pm2 logs yourproject --lines 20
```

---

## How To: Backup Database

### Manual Backup

```bash
# Create backup file
sudo -u postgres pg_dump yourproject_db > ~/backups/yourproject_$(date +%Y%m%d).sql

# Verify backup created
ls -lh ~/backups/
```

### Restore from Backup

```bash
# Stop your app first
pm2 stop yourproject

# Restore database
sudo -u postgres psql yourproject_db < ~/backups/yourproject_20260115.sql

# Start app
pm2 start yourproject
```

---

## How To: Check Disk Space

### View Disk Usage

```bash
df -h
```

### Check Project Size

```bash
du -sh /root/YOUR_REPOS/YOUR_PROJECT
```

### Find Large Files

```bash
find /root/YOUR_REPOS/YOUR_PROJECT -type f -size +100M
```

### Clean Up

```bash
# Remove Python cache
find /root/YOUR_REPOS/YOUR_PROJECT -type d -name "__pycache__" -exec rm -rf {} +

# Remove log files older than 30 days
find /root/logs -name "*.log" -mtime +30 -delete
```

---

## Daily Operations Checklist

Common tasks you'll do regularly:

### Morning Check

- [ ] `pm2 status` - Verify all apps running
- [ ] `pm2 logs yourproject --lines 20` - Check for overnight errors
- [ ] Check app URL loads correctly

### After Code Push

- [ ] `git pull origin main` - Pull latest code
- [ ] `uv sync` - Update dependencies (if needed)
- [ ] `uv run python manage.py migrate` - Run migrations (if model changes)
- [ ] `pm2 restart yourproject` - Restart app
- [ ] `pm2 status | grep yourproject` - Verify online
- [ ] Test changes on live URL

### Weekly Maintenance

- [ ] Review error logs
- [ ] Check disk space: `df -h`
- [ ] Backup database
- [ ] Clear old logs
- [ ] Update system packages (coordinate with team)

---

## Quick Reference Commands

```bash
# Navigation
cd /root/YOUR_REPOS/YOUR_PROJECT           # Go to project
cd /root/YOUR_REPOS/YOUR_PROJECT/BACKEND   # Go to backend

# Code Updates
git pull origin main                        # Pull code
uv sync                                     # Update deps
uv run python manage.py migrate             # Run migrations
pm2 restart yourproject                     # Restart

# Monitoring
pm2 status | grep yourproject               # Check status
pm2 logs yourproject --lines 50             # View logs
pm2 monit                                   # Real-time monitor

# Database
sudo -u postgres psql yourproject_db        # Access database
sudo -u postgres pg_dump yourproject_db     # Backup database

# Debugging
pm2 logs yourproject --err                  # Error logs only
claude                                      # AI assistant
```

---

**Back to:** [Overview](01-overview.md) | **See also:** [Commands Reference](05-commands-reference.md) | [Troubleshooting](06-troubleshooting.md)
