# Getting Started with DigitalOcean

## How To: Connect to the Server

1. Open your browser and go to the DigitalOcean Droplet Console:

**[https://cloud.digitalocean.com/droplets/520157979/access](https://cloud.digitalocean.com/droplets/520157979/access)**

2. Log in with your DigitalOcean account credentials if prompted

3. Click the **"Launch Droplet Console"** button

4. A new browser window will open with a terminal session

5. You're now inside the server. You'll see:

```
root@ubuntu-s-1vcpu-1gb-nyc3-01:~#
```

6. To disconnect, simply close the browser tab

### Why we use the web console

- More secure than direct SSH access
- No need to manage SSH keys
- Access from any computer with a browser
- Audit trail through DigitalOcean

---

## How To: Set Up as a New Developer

### First time setup

1. Get DigitalOcean account access from team lead

2. Connect to server via the web console (see above)

3. Create your repos folder:

```bash
mkdir /root/yourname_repos
```

4. Deploy your first project (see [Deployment Guide](03-deployment.md))

### Daily workflow

1. Make code changes locally

2. Push to GitHub

3. Connect to server via the web console

4. Pull changes and restart:

```bash
cd /root/yourname_repos/yourproject
git pull origin main
cd backend_folder
uv run python manage.py migrate  # if model changes
pm2 restart yourproject
```

### When things break

1. Check logs first: `pm2 logs yourproject --lines 50`

2. **Use Claude on the server** to help debug:

```bash
claude
```

Claude can help you:
- Analyze error logs and suggest fixes
- Debug migration issues
- Make code changes directly on the server
- Run commands and verify they work

3. Google the error message

4. Check the [Troubleshooting Guide](06-troubleshooting.md)

5. Ask in team chat with the error message

---

## Understanding the Server Structure

### Project Organization

Each developer has their own repos folder:

```
/root/
├── charles_repos/
│   ├── propurti_backend/
│   └── another_project/
├── john_repos/
│   └── johns_project/
└── shared/
    └── common_resources/
```

### Your Project Structure

When you deploy, your project looks like this:

```
/root/yourname_repos/yourproject/
├── backend/
│   ├── manage.py
│   ├── config/
│   │   ├── settings.py
│   │   └── wsgi.py
│   ├── apps/
│   └── .env              # Your environment variables
├── frontend/ (if applicable)
└── README.md
```

### Logs Location

PM2 stores logs for each project:

```
/root/logs/yourname_repos/
├── yourproject-error.log
├── yourproject-out.log
├── yourproject-celery-worker-error.log
└── yourproject-celery-worker-out.log
```

---

## Key Services

### PM2 (Process Manager)

Keeps your Django app running 24/7:
- Auto-restarts if app crashes
- Manages multiple apps
- Centralized logging
- Memory management

**Check what's running:**
```bash
pm2 status
```

### PostgreSQL (Database)

All projects share one PostgreSQL instance:
- Each project has its own database
- Default credentials in your `.env`
- Backups run nightly

**Access database:**
```bash
sudo -u postgres psql yourproject_db
```

### Redis (Cache & Celery)

Used for:
- Session storage
- Caching
- Celery task queue

**Check Redis:**
```bash
redis-cli ping
```

Should return `PONG`.

### Nginx (Web Server)

Routes traffic to your apps:
- Handles SSL/HTTPS
- Serves static files
- Reverse proxy to Django

Your app is accessible at:
```
https://yourproject.dev.benmore.tech
```

---

## Environment Variables

Every project needs a `.env` file in the backend folder:

```bash
# Location
/root/yourname_repos/yourproject/backend/.env
```

**Required variables:**

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourproject.dev.benmore.tech,localhost,127.0.0.1
DJANGO_SETTINGS_MODULE=config.settings.production

# Database
DB_NAME=yourproject_db
DB_USER=postgres
DB_PASSWORD=BMore123
DB_HOST=localhost
DB_PORT=5432

# Redis (if using Celery)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# External Services (if needed)
SENTRY_DSN=your-sentry-dsn
CLOUDINARY_URL=your-cloudinary-url
MAILJET_API_KEY=your-mailjet-key
MAILJET_SECRET_KEY=your-mailjet-secret
```

**Create/Edit `.env`:**
```bash
nano /root/yourname_repos/yourproject/backend/.env
```

Save: `Ctrl+X`, `Y`, `Enter`

---

## Security Notes

1. **Never commit `.env` files to GitHub**
   - Add `.env` to `.gitignore`
   - Store secrets in `.env` on server only

2. **Use strong SECRET_KEY**
   - Generate with: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
   - Unique per project

3. **Set DEBUG=False in production**
   - Prevents exposing sensitive info
   - Required for security

4. **Use ALLOWED_HOSTS**
   - Only list your actual domain
   - Don't use `*` in production

---

## Next Steps

Now that you're set up, you can:

1. **Deploy your first project:** [Deployment Guide](03-deployment.md)
2. **Learn daily operations:** [Daily Operations Guide](04-daily-operations.md)
3. **Familiarize with commands:** [Commands Reference](05-commands-reference.md)

---

**Server Console:** [https://cloud.digitalocean.com/droplets/520157979/access](https://cloud.digitalocean.com/droplets/520157979/access)

**Back to:** [Overview](01-overview.md)
