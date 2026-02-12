# DigitalOcean Server Operations - Command Reference

A quick reference guide for managing Django applications deployed on DigitalOcean droplets using PM2, PostgreSQL, and uv.

---

## PM2 (Process Manager)

PM2 keeps your Django application running, manages restarts, and provides log management.

| What you want | Command |
|---------------|---------|
| See all apps | `pm2 status` |
| See specific app | `pm2 status \| grep yourproject` |
| View logs | `pm2 logs yourproject` |
| View last N lines | `pm2 logs yourproject --lines 100` |
| View error logs only | `pm2 logs yourproject --err` |
| Restart app | `pm2 restart yourproject` |
| Stop app | `pm2 stop yourproject` |
| Start app | `pm2 start yourproject` |
| Save current state | `pm2 save` |
| Real-time monitor | `pm2 monit` |
| Delete app from PM2 | `pm2 delete yourproject` |
| Reload app (zero-downtime) | `pm2 reload yourproject` |
| View app details | `pm2 describe yourproject` |

### PM2 Process File Example

Create an `ecosystem.config.js` file for easier management:

```javascript
module.exports = {
  apps: [{
    name: 'myproject',
    cwd: '/root/myrepo/myproject/backend',
    script: 'uv',
    args: 'run gunicorn config.wsgi:application --bind 0.0.0.0:8000',
    env: {
      DJANGO_SETTINGS_MODULE: 'config.settings.production'
    }
  }]
}
```

Then use: `pm2 start ecosystem.config.js`

---

## Django Management

First, navigate to your backend folder:
```bash
cd /root/YOUR_REPOS/YOUR_PROJECT/BACKEND
```

Then use `uv run` to execute Django commands:

| What you want | Command |
|---------------|---------|
| Run migrations | `uv run python manage.py migrate` |
| Create migration files | `uv run python manage.py makemigrations` |
| Show migrations | `uv run python manage.py showmigrations` |
| Create admin user | `uv run python manage.py createsuperuser` |
| Collect static files | `uv run python manage.py collectstatic` |
| Open Django shell | `uv run python manage.py shell` |
| Check for issues | `uv run python manage.py check` |
| Run development server | `uv run python manage.py runserver 0.0.0.0:8000` |
| Sync dependencies | `uv sync` |
| Add new dependency | `uv add package-name` |
| Remove dependency | `uv remove package-name` |

### Common Django Tasks

**Run migrations after code update:**
```bash
cd /root/YOUR_REPOS/YOUR_PROJECT/BACKEND
uv run python manage.py migrate
pm2 restart yourproject
```

**Create new admin user:**
```bash
cd /root/YOUR_REPOS/YOUR_PROJECT/BACKEND
uv run python manage.py createsuperuser
```

**Collect static files for production:**
```bash
cd /root/YOUR_REPOS/YOUR_PROJECT/BACKEND
uv run python manage.py collectstatic --noinput
```

---

## Database (PostgreSQL)

| What you want | Command |
|---------------|---------|
| Create database | `sudo -u postgres createdb dbname` |
| Delete database | `sudo -u postgres dropdb dbname` |
| List all databases | `sudo -u postgres psql -l` |
| Enter database shell | `sudo -u postgres psql dbname` |
| Backup database | `sudo -u postgres pg_dump dbname > backup.sql` |
| Restore database | `sudo -u postgres psql dbname < backup.sql` |
| Exit database shell | `\q` |

### PostgreSQL Shell Commands

Once inside `psql`:

| Command | What it does |
|---------|--------------|
| `\l` | List all databases |
| `\c dbname` | Connect to database |
| `\dt` | List all tables |
| `\d tablename` | Describe table structure |
| `\du` | List all users/roles |
| `\q` | Quit psql |

### Common Database Operations

**Create a new database and user:**
```bash
sudo -u postgres psql
```

Then in psql:
```sql
CREATE DATABASE myproject;
CREATE USER myuser WITH PASSWORD 'mypassword';
GRANT ALL PRIVILEGES ON DATABASE myproject TO myuser;
\q
```

**Backup and restore:**
```bash
# Backup
sudo -u postgres pg_dump myproject > backup_$(date +%Y%m%d).sql

# Restore
sudo -u postgres psql myproject < backup_20240115.sql
```

---

## Git Version Control

| What you want | Command |
|---------------|---------|
| Pull latest code | `git pull origin main` |
| Check current branch | `git branch` |
| Switch branch | `git checkout branch-name` |
| See recent commits | `git log --oneline -5` |
| Discard local changes | `git checkout -- .` |
| Check status | `git status` |
| View changes | `git diff` |
| Fetch remote changes | `git fetch origin` |
| Reset to remote | `git reset --hard origin/main` |

### Typical Deployment Workflow

```bash
# Navigate to your project
cd /root/YOUR_REPOS/YOUR_PROJECT

# Pull latest code
git pull origin main

# Update dependencies
cd backend
uv sync

# Run migrations
uv run python manage.py migrate

# Collect static files
uv run python manage.py collectstatic --noinput

# Restart the app
pm2 restart yourproject

# Check if running
pm2 status
```

---

## File System Operations

| What you want | Command |
|---------------|---------|
| List folder contents | `ls` |
| List with details | `ls -la` |
| List sorted by time | `ls -lt` |
| Go into folder | `cd foldername` |
| Go up one folder | `cd ..` |
| Go to home directory | `cd ~` |
| View file contents | `cat filename` |
| View file (paginated) | `less filename` |
| Edit file | `nano filename` |
| Search in file | `grep "text" filename` |
| Search in all files | `grep -r "text" .` |
| Find files | `find . -name "*.py"` |
| Check disk usage | `df -h` |
| Check folder size | `du -sh foldername` |

---

## System & Server Management

| What you want | Command |
|---------------|---------|
| Check running processes | `ps aux \| grep python` |
| Check port usage | `sudo lsof -i :8000` |
| Kill process by port | `sudo kill -9 $(lsof -t -i:8000)` |
| Check memory usage | `free -h` |
| Check CPU usage | `top` |
| Check disk space | `df -h` |
| Restart server | `sudo reboot` |
| Check system logs | `sudo journalctl -xe` |
| View nginx logs | `sudo tail -f /var/log/nginx/error.log` |

### Environment Variables

**View environment variables:**
```bash
env
printenv
echo $DJANGO_SETTINGS_MODULE
```

**Set environment variables:**
```bash
# Temporary (current session only)
export DJANGO_SETTINGS_MODULE=config.settings.production

# Permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export DJANGO_SETTINGS_MODULE=config.settings.production' >> ~/.bashrc
source ~/.bashrc
```

---

## Claude Code (AI Assistant)

| What you want | Command |
|---------------|---------|
| Start Claude | `claude` |
| Ask Claude to debug | Start claude, then describe your issue |
| Resume previous session | `claude --resume` |

### What Claude Can Help With

Claude can assist with:
- Analyzing error logs and suggesting fixes
- Debugging migration issues
- Making code changes directly on the server
- Running commands and verifying they work
- Troubleshooting deployment problems
- Explaining complex configurations

**Example workflow:**
```bash
# Start Claude
claude

# Then ask:
# "Check my Django logs for errors"
# "Help me debug this migration issue"
# "Update my settings.py for production"
# "Restart my PM2 process and verify it's working"
```

---

## Troubleshooting Common Issues

### App Won't Start

```bash
# Check PM2 logs
pm2 logs yourproject --err

# Check if port is already in use
sudo lsof -i :8000

# Restart PM2
pm2 restart yourproject
```

### Database Connection Failed

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Restart PostgreSQL
sudo systemctl restart postgresql

# Test connection
sudo -u postgres psql -d yourdb -c "SELECT 1;"
```

### Static Files Not Loading

```bash
# Collect static files
cd /root/YOUR_REPOS/YOUR_PROJECT/BACKEND
uv run python manage.py collectstatic --noinput

# Check STATIC_ROOT setting in settings.py
uv run python manage.py diffsettings | grep STATIC
```

### After Git Pull, Changes Not Reflected

```bash
# Ensure migrations ran
uv run python manage.py migrate

# Ensure static files collected
uv run python manage.py collectstatic --noinput

# Restart PM2 (important!)
pm2 restart yourproject

# Check PM2 status
pm2 status

# View recent logs
pm2 logs yourproject --lines 50
```

---

## Quick Deployment Checklist

After pulling code updates:

```bash
# 1. Navigate to project
cd /root/YOUR_REPOS/YOUR_PROJECT

# 2. Pull code
git pull origin main

# 3. Update dependencies
cd backend
uv sync

# 4. Run migrations
uv run python manage.py migrate

# 5. Collect static files
uv run python manage.py collectstatic --noinput

# 6. Restart app
pm2 restart yourproject

# 7. Verify
pm2 status
pm2 logs yourproject --lines 20
```

---

## Security Best Practices

**File Permissions:**
```bash
# Set secure permissions on sensitive files
chmod 600 .env
chmod 600 ~/YOUR_REPOS/YOUR_PROJECT/backend/.env
```

**Firewall (UFW):**
```bash
# Check status
sudo ufw status

# Allow SSH (important - do this first!)
sudo ufw allow 22

# Allow HTTP/HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Enable firewall
sudo ufw enable
```

**Keep System Updated:**
```bash
# Update package list
sudo apt update

# Upgrade installed packages
sudo apt upgrade -y

# Clean up
sudo apt autoremove -y
```

---

## Additional Resources

- **PM2 Documentation:** https://pm2.keymetrics.io/docs/usage/quick-start/
- **Django Deployment:** https://docs.djangoproject.com/en/stable/howto/deployment/
- **PostgreSQL Docs:** https://www.postgresql.org/docs/
- **DigitalOcean Tutorials:** https://www.digitalocean.com/community/tutorials

---

**Related Guides:**
- [Heroku Django Deployment](01-heroku-django.md) - Alternative deployment platform
- [Django CI/CD Setup](03-django-cicd-setup.md) - Automated testing and deployment
- [Django Production Guide](../django/02-detailed-checklist.md) - Production best practices
