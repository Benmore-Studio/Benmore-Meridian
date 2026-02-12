# DigitalOcean Deployment

## How To: Deploy a New Django Project

### Before you start

- Your code must be on GitHub
- You need your `.env` file contents ready
- Pick a port number not already in use

### Steps

1. Connect to the server (see [Getting Started](02-getting-started.md))

2. Go to the root folder:

```bash
cd /root
```

3. Run the deployment script:

```bash
node add-project.js
```

4. Enter your project name when asked:
   - Must be lowercase
   - No spaces, no hyphens, no special characters
   - Example: `myproject` ✅
   - Example: `my-project` ❌
   - Example: `MyProject` ❌

5. Select your repos folder:
   - Type the number next to your folder (e.g., `2` for charles_repos)
   - Press Enter

6. Paste your GitHub repository URL:

```
https://github.com/Benmore-Studio/your-repo-name
```

7. Press Enter for branch (uses `main` by default), or type your branch name

8. Enter a port number:
   - Pick any unused port like `8016`, `8017`, etc.
   - Script will tell you if port is taken

9. Wait for packages to install

10. When script pauses and asks for `.env` file:
    - Open a NEW browser tab
    - Go to [https://cloud.digitalocean.com/droplets/520157979/access](https://cloud.digitalocean.com/droplets/520157979/access)
    - Click **"Launch Droplet Console"** to open a second terminal session
    - Create the .env file:

```bash
nano /root/YOUR_REPOS/YOUR_PROJECT_FOLDER/.env
```

- Paste your environment variables
- **Important:** Add these database settings:

```env
DB_NAME=yourproject_db
DB_USER=postgres
DB_PASSWORD=BMore123
DB_HOST=localhost
DB_PORT=5432
```

- **Important:** Add your allowed hosts:

```env
ALLOWED_HOSTS=yourproject.dev.benmore.tech,localhost,127.0.0.1
```

- Save: Press `Ctrl+X`, then `Y`, then `Enter`

11. Go back to first terminal tab and press Enter

12. Wait for migrations to complete

13. Check if app is running:

```bash
pm2 status | grep yourproject
```

14. Test your URL in browser:

```
https://yourproject.dev.benmore.tech
```

---

## How To: Create Admin/Superuser

1. Go to your backend folder:

```bash
cd /root/YOUR_REPOS/YOUR_PROJECT/BACKEND
```

2. Create superuser:

```bash
uv run python manage.py createsuperuser
```

3. Enter username, email, password when prompted

4. Access admin at:

```
https://yourproject.dev.benmore.tech/admin
```

---

## How To: Add Celery (Background Tasks)

### When you need this

- Your app sends emails
- Your app sends SMS
- Your app has scheduled jobs
- Your app processes things in the background

### Steps

1. Check Redis is running:

```bash
redis-cli ping
```

Should return `PONG`

2. Add Redis settings to your .env:

```bash
nano /root/YOUR_REPOS/YOUR_PROJECT/BACKEND/.env
```

Add:

```env
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

3. Open the PM2 config:

```bash
nano /root/ecosystem.config.js
```

4. Add these entries before the closing `]`:

```javascript
{
  name: 'yourproject-celery-worker',
  cwd: '/root/YOUR_REPOS/YOUR_PROJECT/BACKEND',
  script: 'uv',
  interpreter: 'none',
  args: 'run celery -A config worker -l info',
  instances: 1,
  autorestart: true,
  watch: false,
  max_memory_restart: '500M',
  error_file: '/root/logs/YOUR_REPOS/yourproject-celery-worker-error.log',
  out_file: '/root/logs/YOUR_REPOS/yourproject-celery-worker-out.log',
  log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
},
{
  name: 'yourproject-celery-beat',
  cwd: '/root/YOUR_REPOS/YOUR_PROJECT/BACKEND',
  script: 'uv',
  interpreter: 'none',
  args: 'run celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler',
  instances: 1,
  autorestart: true,
  watch: false,
  max_memory_restart: '300M',
  error_file: '/root/logs/YOUR_REPOS/yourproject-celery-beat-error.log',
  out_file: '/root/logs/YOUR_REPOS/yourproject-celery-beat-out.log',
  log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
},
```

**Note:** Replace `config` in `-A config` with your Django project name (the folder with settings.py)

5. Save: `Ctrl+X`, `Y`, `Enter`

6. Start Celery:

```bash
cd /root
pm2 start ecosystem.config.js --only yourproject-celery-worker
pm2 start ecosystem.config.js --only yourproject-celery-beat
pm2 save
```

7. Restart main app:

```bash
pm2 restart yourproject
```

8. Verify all running:

```bash
pm2 status | grep yourproject
```

You should see 3-4 services:
- `yourproject` (main Django app)
- `yourproject-celery-worker` (processes background tasks)
- `yourproject-celery-beat` (scheduler for periodic tasks)
- `zrok-yourproject` (if using zrok tunneling)

---

## Deployment Checklist

After deploying, verify these:

- [ ] App shows as `online` in `pm2 status`
- [ ] URL loads in browser: `https://yourproject.dev.benmore.tech`
- [ ] Admin panel accessible: `/admin`
- [ ] Database migrations completed
- [ ] Static files loading correctly
- [ ] `.env` file configured with all required variables
- [ ] Celery workers running (if applicable)
- [ ] Logs show no errors: `pm2 logs yourproject --lines 20`

---

## Common Deployment Issues

### Port Already in Use

**Error:** `EADDRINUSE: address already in use`

**Fix:**
```bash
# Find what's using the port
sudo lsof -i :8016

# Kill the process
sudo kill -9 <PID>

# Or choose a different port in the deployment script
```

### Git Authentication Failed

**Error:** `fatal: could not read Username for 'https://github.com'`

**Fix:**
- Make sure repo is public, OR
- Use GitHub personal access token in URL:
  ```
  https://YOUR_TOKEN@github.com/Benmore-Studio/your-repo-name
  ```

### Database Connection Refused

**Error:** `FATAL: database "yourproject_db" does not exist`

**Fix:**
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
```

### Missing Dependencies

**Error:** `ModuleNotFoundError: No module named 'xyz'`

**Fix:**
```bash
cd /root/YOUR_REPOS/YOUR_PROJECT/BACKEND
uv sync
pm2 restart yourproject
```

### Static Files Not Loading

**Error:** CSS/JS not loading, 404 errors

**Fix:**
```bash
cd /root/YOUR_REPOS/YOUR_PROJECT/BACKEND
uv run python manage.py collectstatic --noinput
pm2 restart yourproject
```

---

## Next Steps

After deployment:

1. **Test your app thoroughly**
2. **Set up monitoring** (Sentry for errors)
3. **Configure backups** (database, media files)
4. **Learn daily operations:** [Daily Operations Guide](04-daily-operations.md)
5. **Bookmark commands:** [Commands Reference](05-commands-reference.md)

---

**Back to:** [Overview](01-overview.md) | **Next:** [Daily Operations](04-daily-operations.md)
