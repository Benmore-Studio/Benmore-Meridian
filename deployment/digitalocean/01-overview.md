# DigitalOcean Deployment & Management Guide

Quick reference for deploying and managing Django projects on the Benmore DigitalOcean server.

## Quick Links

| Guide | Description |
|-------|-------------|
| [Getting Started](02-getting-started.md) | How to connect to server, new developer setup |
| [Deployment](03-deployment.md) | How to deploy new projects, add Celery, create admin |
| [Daily Operations](04-daily-operations.md) | How to pull code, run migrations, update sites |
| [Commands Reference](05-commands-reference.md) | PM2, Django, Git, Database commands |
| [Troubleshooting](06-troubleshooting.md) | How to fix common errors, check logs |

## Quick Start

1. **Connect to server:** [cloud.digitalocean.com/droplets/520157979/access](https://cloud.digitalocean.com/droplets/520157979/access) → Click "Launch Droplet Console"

2. **Update your project:**

```bash
cd /root/YOUR_REPOS/YOUR_PROJECT
git pull origin main
pm2 restart yourproject
```

3. **Check if it's running:**

```bash
pm2 status | grep yourproject
```

4. **View logs if something breaks:**

```bash
pm2 logs yourproject --lines 50
```

5. **Use Claude to debug:**

```bash
claude
```

---

## Server Information

**Droplet Details:**
- **Provider:** DigitalOcean
- **Plan:** 1 vCPU, 1GB RAM
- **Region:** NYC3
- **OS:** Ubuntu
- **Access:** Web console (browser-based)

**Services Running:**
- **Web Server:** Nginx (reverse proxy)
- **Process Manager:** PM2
- **Database:** PostgreSQL
- **Cache:** Redis
- **Python:** uv package manager

---

## Common Workflows

### Deploying a New Project
See: [Deployment Guide](03-deployment.md)

1. Run deployment script: `node add-project.js`
2. Configure `.env` file
3. Run migrations
4. Verify with `pm2 status`

### Updating an Existing Project
See: [Daily Operations Guide](04-daily-operations.md)

1. Pull latest code: `git pull origin main`
2. Update dependencies: `uv sync` (if needed)
3. Run migrations: `uv run python manage.py migrate` (if needed)
4. Restart: `pm2 restart yourproject`

### Debugging Issues
See: [Troubleshooting Guide](06-troubleshooting.md)

1. Check status: `pm2 status | grep yourproject`
2. View logs: `pm2 logs yourproject --lines 50`
3. Use Claude: `claude` (AI assistant on server)
4. Check specific errors in guide

---

## Project Structure on Server

```
/root/
├── yourname_repos/
│   └── yourproject/
│       ├── backend/
│       │   ├── manage.py
│       │   ├── config/
│       │   └── .env
│       └── frontend/ (if applicable)
├── ecosystem.config.js (PM2 configuration)
├── add-project.js (deployment script)
└── logs/
    └── yourname_repos/
        ├── yourproject-error.log
        └── yourproject-out.log
```

---

## Quick Command Reference

See [Commands Reference](05-commands-reference.md) for complete list.

### PM2 (Process Manager)
```bash
pm2 status                    # See all apps
pm2 logs yourproject         # View logs
pm2 restart yourproject      # Restart app
pm2 save                     # Save PM2 state
```

### Django
```bash
cd /root/YOUR_REPOS/YOUR_PROJECT/BACKEND
uv run python manage.py migrate           # Run migrations
uv run python manage.py createsuperuser   # Create admin
uv run python manage.py shell             # Open shell
```

### Git
```bash
git pull origin main         # Pull latest code
git status                   # Check status
git log --oneline -5         # Recent commits
```

### Database
```bash
sudo -u postgres psql dbname      # Enter database
sudo -u postgres pg_dump dbname   # Backup database
```

---

## Need Help?

1. **Check logs first:** `pm2 logs yourproject --lines 50`
2. **Use Claude:** `claude` (AI assistant on the server)
3. **Check guides:**
   - [Getting Started](02-getting-started.md) - First time setup
   - [Deployment](03-deployment.md) - Deploy new projects
   - [Daily Operations](04-daily-operations.md) - Common tasks
   - [Troubleshooting](06-troubleshooting.md) - Fix errors
   - [Commands Reference](05-commands-reference.md) - All commands
4. **Ask team:** Post in team chat with error details

---

**Server Console Access:** [https://cloud.digitalocean.com/droplets/520157979/access](https://cloud.digitalocean.com/droplets/520157979/access)
