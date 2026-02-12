# DigitalOcean Troubleshooting

## Quick Checklist

When something goes wrong, follow this order:

1. **Check if app is running:**
   ```bash
   pm2 status | grep yourproject
   ```

2. **View recent logs:**
   ```bash
   pm2 logs yourproject --lines 50
   ```

3. **Check error logs only:**
   ```bash
   pm2 logs yourproject --err
   ```

4. **Use Claude for help:**
   ```bash
   claude
   ```
   Then describe your issue.

5. **Restart the app:**
   ```bash
   pm2 restart yourproject
   ```

6. **Verify deployment:**
   - Test URL in browser
   - Check for 500/404 errors
   - Review server logs

---

## App Not Loading at All

### Symptom
- [ ] Site returns "502 Bad Gateway"
- [ ] Site times out
- [ ] "Connection refused" error

### Diagnosis

**Is the app running?**
```bash
pm2 status | grep yourproject
```

If status shows `stopped` or `errored`:

**Check the error:**
```bash
pm2 logs yourproject --err --lines 50
```

### Common Causes & Fixes

#### App crashed on startup

**Symptoms:** Status shows `errored`, app keeps restarting

**Check logs:**
```bash
pm2 logs yourproject --err
```

**Common errors:**

1. **"ModuleNotFoundError: No module named 'xyz'"**
   ```bash
   cd /root/YOUR_REPOS/YOUR_PROJECT/BACKEND
   uv sync
   pm2 restart yourproject
   ```

2. **"django.db.utils.OperationalError: FATAL: database does not exist"**
   ```bash
   sudo -u postgres createdb yourproject_db
   cd /root/YOUR_REPOS/YOUR_PROJECT/BACKEND
   uv run python manage.py migrate
   pm2 restart yourproject
   ```

3. **"django.core.exceptions.ImproperlyConfigured: Set the SECRET_KEY"**
   ```bash
   nano /root/YOUR_REPOS/YOUR_PROJECT/BACKEND/.env
   # Add: SECRET_KEY=your-secret-key-here
   pm2 restart yourproject
   ```

#### Port already in use

**Error:** `EADDRINUSE: address already in use`

**Find what's using the port:**
```bash
sudo lsof -i :8016  # Replace with your port
```

**Kill the process:**
```bash
sudo kill -9 <PID>
pm2 restart yourproject
```

Or choose a different port in PM2 config:
```bash
nano /root/ecosystem.config.js
# Change the port number
pm2 restart yourproject
```

---

## Static Files Not Loading

### Symptom
- [ ] Page loads but looks broken (no CSS)
- [ ] JavaScript not working
- [ ] Images not showing
- [ ] Console shows 404 errors for CSS/JS files

### Diagnosis

**Check browser console:**
- Press F12 in browser
- Look for 404 errors on static files

### Fixes

#### Collect static files

```bash
cd /root/YOUR_REPOS/YOUR_PROJECT/BACKEND
uv run python manage.py collectstatic --noinput
pm2 restart yourproject
```

#### Check STATIC_ROOT in settings.py

```bash
cd /root/YOUR_REPOS/YOUR_PROJECT/BACKEND
uv run python manage.py diffsettings | grep STATIC
```

Should show:
```
STATIC_ROOT = '/root/YOUR_REPOS/YOUR_PROJECT/BACKEND/staticfiles'
STATIC_URL = '/static/'
```

#### Verify Nginx config

Check if Nginx is serving static files:
```bash
sudo nginx -t
sudo systemctl status nginx
```

If Nginx has errors:
```bash
sudo systemctl restart nginx
```

---

## Database Errors

### Symptom
- [ ] "no such table" error
- [ ] "column does not exist" error
- [ ] "relation does not exist" error
- [ ] "FATAL: database does not exist"

### Diagnosis

**Check if database exists:**
```bash
sudo -u postgres psql -l | grep yourproject
```

**Check migrations status:**
```bash
cd /root/YOUR_REPOS/YOUR_PROJECT/BACKEND
uv run python manage.py showmigrations
```

### Fixes

#### Database doesn't exist

```bash
# Create database
sudo -u postgres createdb yourproject_db

# Grant permissions
sudo -u postgres psql
GRANT ALL PRIVILEGES ON DATABASE yourproject_db TO postgres;
\q

# Run migrations
cd /root/YOUR_REPOS/YOUR_PROJECT/BACKEND
uv run python manage.py migrate

# Restart app
pm2 restart yourproject
```

#### Migrations not applied

```bash
cd /root/YOUR_REPOS/YOUR_PROJECT/BACKEND
uv run python manage.py migrate
pm2 restart yourproject
```

#### Migration file missing

If you deleted migration files or they're out of sync:

```bash
cd /root/YOUR_REPOS/YOUR_PROJECT/BACKEND

# Create new migrations
uv run python manage.py makemigrations

# Apply them
uv run python manage.py migrate

# Restart
pm2 restart yourproject
```

#### Database connection refused

**Error:** `FATAL: password authentication failed for user "postgres"`

**Check .env file:**
```bash
nano /root/YOUR_REPOS/YOUR_PROJECT/BACKEND/.env
```

Verify these settings:
```env
DB_NAME=yourproject_db
DB_USER=postgres
DB_PASSWORD=BMore123
DB_HOST=localhost
DB_PORT=5432
```

**Restart PostgreSQL:**
```bash
sudo systemctl restart postgresql
pm2 restart yourproject
```

---

## After Pulling Code, Changes Not Showing

### Symptom
- [ ] Pulled latest code from GitHub
- [ ] Live site still shows old version
- [ ] New features not appearing

### Diagnosis

**Check if code actually pulled:**
```bash
cd /root/YOUR_REPOS/YOUR_PROJECT
git log --oneline -5
git status
```

**Check if app restarted:**
```bash
pm2 status | grep yourproject
```

### Fixes

#### Standard update procedure

```bash
# Pull code
cd /root/YOUR_REPOS/YOUR_PROJECT
git pull origin main

# Update dependencies (if needed)
cd backend
uv sync

# Run migrations (if model changes)
uv run python manage.py migrate

# Collect static files (if frontend changes)
uv run python manage.py collectstatic --noinput

# CRITICAL: Restart the app
pm2 restart yourproject

# Verify restart
pm2 status | grep yourproject
```

#### Hard refresh browser

- Chrome/Firefox: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
- This clears cached CSS/JS

#### Check if PM2 actually restarted

```bash
pm2 logs yourproject --lines 20
```

Should show recent restart in logs.

#### Force restart all

```bash
pm2 restart yourproject
pm2 save
```

---

## Celery Tasks Not Running

### Symptom
- [ ] Background tasks stuck in "PENDING"
- [ ] Emails not sending
- [ ] Scheduled tasks not executing

### Diagnosis

**Check if Celery workers are running:**
```bash
pm2 status | grep celery
```

Should see:
- `yourproject-celery-worker` - online
- `yourproject-celery-beat` - online

**Check Celery logs:**
```bash
pm2 logs yourproject-celery-worker --lines 50
pm2 logs yourproject-celery-beat --lines 50
```

### Fixes

#### Celery worker not running

```bash
# Restart worker
pm2 restart yourproject-celery-worker

# If still not working, check Redis
redis-cli ping
```

If Redis not responding:
```bash
sudo systemctl restart redis
pm2 restart yourproject-celery-worker
```

#### Celery beat not scheduling tasks

```bash
# Restart beat
pm2 restart yourproject-celery-beat

# Check for lock file issues
cd /root/YOUR_REPOS/YOUR_PROJECT/BACKEND
rm -f celerybeat.pid celerybeat-schedule

# Restart again
pm2 restart yourproject-celery-beat
```

#### Task stuck in PENDING

**Check Redis connection in .env:**
```bash
nano /root/YOUR_REPOS/YOUR_PROJECT/BACKEND/.env
```

Verify:
```env
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

**Restart everything:**
```bash
pm2 restart yourproject
pm2 restart yourproject-celery-worker
pm2 restart yourproject-celery-beat
```

---

## Permission Denied Errors

### Symptom
- [ ] "Permission denied" when writing files
- [ ] Can't create/modify .env
- [ ] Can't run migrations

### Fixes

#### Fix file permissions

```bash
# Make sure you own the project directory
chown -R root:root /root/YOUR_REPOS/YOUR_PROJECT

# Set correct permissions
chmod -R 755 /root/YOUR_REPOS/YOUR_PROJECT

# .env file should be readable only by owner
chmod 600 /root/YOUR_REPOS/YOUR_PROJECT/BACKEND/.env
```

#### PostgreSQL permission issues

```bash
sudo -u postgres psql
GRANT ALL PRIVILEGES ON DATABASE yourproject_db TO postgres;
\q
```

---

## Out of Memory / Server Slow

### Symptom
- [ ] App randomly crashes
- [ ] Server becomes unresponsive
- [ ] "ENOMEM: not enough memory"

### Diagnosis

**Check memory usage:**
```bash
free -h
```

**Check which process is using memory:**
```bash
pm2 monit
```

**Check disk space:**
```bash
df -h
```

### Fixes

#### Clear memory

```bash
# Restart all apps to free memory
pm2 restart all

# Clear system cache
sync; echo 3 > /proc/sys/vm/drop_caches
```

#### Reduce PM2 memory limits

Edit PM2 config:
```bash
nano /root/ecosystem.config.js
```

Add to each app:
```javascript
max_memory_restart: '300M',  // Restart if exceeds 300MB
```

Restart PM2:
```bash
pm2 restart all
```

#### Clean up disk space

```bash
# Remove old logs
find /root/logs -name "*.log" -mtime +30 -delete

# Clean Python cache
find /root -type d -name "__pycache__" -exec rm -rf {} +

# Clean old backups
find /root/backups -name "*.sql" -mtime +90 -delete
```

---

## Git Pull Fails

### Symptom
- [ ] "error: Your local changes would be overwritten"
- [ ] Merge conflicts
- [ ] Authentication failed

### Fixes

#### Local changes conflict

**Save your changes:**
```bash
cd /root/YOUR_REPOS/YOUR_PROJECT
git stash
git pull origin main
git stash pop  # Restore your changes
```

**Or discard local changes:**
```bash
git checkout -- .
git pull origin main
```

#### Merge conflicts

```bash
# View conflicts
git status

# Resolve conflicts in files, then:
git add .
git commit -m "Resolve merge conflicts"
```

Or reset to remote:
```bash
git fetch origin
git reset --hard origin/main
```

#### Authentication failed

If repo is private, use personal access token:
```bash
git remote set-url origin https://YOUR_TOKEN@github.com/Benmore-Studio/your-repo.git
git pull origin main
```

---

## Environment Variables Not Working

### Symptom
- [ ] Settings not taking effect
- [ ] "Environment variable not set" errors
- [ ] DEBUG still True in production

### Fixes

#### Check .env file exists

```bash
ls -la /root/YOUR_REPOS/YOUR_PROJECT/BACKEND/.env
```

If missing:
```bash
nano /root/YOUR_REPOS/YOUR_PROJECT/BACKEND/.env
# Add your environment variables
```

#### Verify .env is being loaded

In `settings.py`, check for:
```python
from dotenv import load_dotenv
load_dotenv()
```

#### Restart app after .env changes

```bash
pm2 restart yourproject
```

Environment variables are only loaded on startup!

#### Check variable names match

Common mistakes:
- `ALLOWED_HOST` vs `ALLOWED_HOSTS` (missing S)
- `DATABASE_URL` vs `DB_NAME` (wrong variable)
- Extra spaces around `=` in .env

---

## SSL / HTTPS Errors

### Symptom
- [ ] "Your connection is not private"
- [ ] SSL certificate expired
- [ ] Mixed content warnings

### Diagnosis

**Check SSL certificate:**
```bash
sudo certbot certificates
```

### Fixes

#### Renew SSL certificate

```bash
sudo certbot renew
sudo systemctl reload nginx
```

#### Force HTTPS in Django

In `settings.py`:
```python
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

Restart app:
```bash
pm2 restart yourproject
```

---

## Getting Help

### Step 1: Use Claude (AI Assistant)

```bash
claude
```

Claude can:
- Analyze your error logs
- Suggest specific fixes
- Run commands for you
- Explain what went wrong

### Step 2: Check Logs

```bash
# App logs
pm2 logs yourproject --lines 100

# Celery logs (if applicable)
pm2 logs yourproject-celery-worker --lines 50

# Nginx logs
sudo tail -f /var/log/nginx/error.log

# PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

### Step 3: Review Guides

- [Getting Started](02-getting-started.md) - Setup issues
- [Deployment](03-deployment.md) - Deployment errors
- [Daily Operations](04-daily-operations.md) - Common tasks
- [Commands Reference](05-commands-reference.md) - All commands

### Step 4: Ask Team

When posting in team chat, include:

1. **What you're trying to do**
2. **Error message** (exact text)
3. **What you've tried**
4. **Relevant logs** (pm2 logs output)

Example:
```
I'm trying to deploy myproject to DigitalOcean.

Error: ModuleNotFoundError: No module named 'celery'

I tried:
- uv sync (didn't help)
- pm2 restart myproject (still fails)

Logs show:
[error output here]
```

---

## Diagnostic Commands Cheat Sheet

```bash
# Check everything is running
pm2 status

# View app logs
pm2 logs yourproject --lines 50

# Check database
sudo -u postgres psql -l

# Test Redis
redis-cli ping

# Check disk space
df -h

# Check memory
free -h

# Test if site responds
curl -I https://yourproject.dev.benmore.tech

# Check Nginx
sudo nginx -t
sudo systemctl status nginx

# Check PostgreSQL
sudo systemctl status postgresql

# View recent git commits
cd /root/YOUR_REPOS/YOUR_PROJECT && git log --oneline -5

# Check if migrations applied
cd /root/YOUR_REPOS/YOUR_PROJECT/BACKEND
uv run python manage.py showmigrations
```

---

**Back to:** [Overview](01-overview.md) | **See also:** [Commands Reference](05-commands-reference.md)
