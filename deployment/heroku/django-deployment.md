# Deploying Django to Heroku with uv

This guide outlines the modern process for deploying a Python Django application to Heroku using `uv` as the package manager. `uv` provides significantly faster dependency resolution and simplified project management compared to `pip` or `pipenv`.

## Prerequisites

- **Heroku CLI** installed and logged in (`heroku login`)
- **uv** installed locally (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **Git** initialized repository

## 1. Project Initialization

If you are migrating or starting fresh, initialize `uv` in your project root (same directory as `manage.py`):

```bash
# Initialize uv (creates pyproject.toml)
uv init

# Add dependencies (migrates from requirements.txt automatically if present, or add manually)
uv add django gunicorn psycopg[binary] dj-database-url
# Add other packages:
# uv add djangorestframework django-cors-headers ...
```

Ensure `uv.lock` is generated:
```bash
uv lock
```

## 2. Configuration Files

### `Procfile`
Define your process types. Heroku needs this to know how to start your app.

```text
web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
release: python manage.py migrate
```

### `runtime.txt` (Optional but Recommended)
Explicitly pin your Python version to avoid buildpack surprises.

```text
python-3.12.8
```

### `pyproject.toml`
Ensure your `requires-python` matches a Heroku-supported runtime (e.g., `>=3.12`).

```toml
[project]
name = "your-app-name"
version = "0.1.0"
requires-python = ">=3.12"
# ... dependencies list ...
```

## 3. Prepare for Heroku

1.  **Remove legacy files**: Delete `requirements.txt`, `Pipfile`, `Pipfile.lock`, and `.python-version` to prevent buildpack conflicts. Heroku's Python buildpack will auto-detect `uv.lock` and use `uv` for installation.
2.  **Commit changes**:
    ```bash
    git add pyproject.toml uv.lock Procfile runtime.txt
    git commit -m "Configure project for Heroku with uv"
    ```

## 4. Deploy

### Create the App
```bash
heroku create your-app-name
```

### Add Databases
```bash
heroku addons:create heroku-postgresql:essential-0
heroku addons:create heroku-redis:mini
```

### Configure Environment Variables
Set your production secrets. `uv` doesn't handle `.env` in production; Heroku config vars do.

```bash
heroku config:set SECRET_KEY="<your-secret>" \
    DEBUG=False \
    ALLOWED_HOSTS="your-app-name.herokuapp.com" \
    DJANGO_SETTINGS_MODULE="config.settings.production"
```

### Push Code
Deploy your `main` branch to Heroku.

**Option A: Project Root Deployment**
If your `pyproject.toml` is in the root:
```bash
git push heroku main
```

**Option B: Monorepo / Subdirectory Deployment**
If your backend is in a folder (e.g., `backend/`):
```bash
# Push only the backend folder to Heroku's root
git subtree push --prefix backend heroku main
```

## 5. Troubleshooting (Common Issues)

*   **Build Failure (Python Version)**: If Heroku complains about python versions, ensure `runtime.txt` exists and specifies a [supported version](https://devcenter.heroku.com/articles/python-support#supported-runtimes). Also check `pyproject.toml` constraints.
*   **Missing Dependencies**: Run `uv lock` locally to ensure `uv.lock` is up-to-date and commit it.
*   **"Push rejected"**: If git history diverges (common with `git subtree`), force a clean push:
    ```bash
    git push heroku `git subtree split --prefix backend main`:main --force
    ```
*   **Application Error**: Check logs with `heroku logs --tail` to identify startup issues
*   **Database Connection Issues**: Verify `DATABASE_URL` is set with `heroku config:get DATABASE_URL`
*   **Static Files Not Loading**: Ensure `STATIC_ROOT` is configured and run `python manage.py collectstatic` in your release phase

## 6. Post-Deployment

### Verify Deployment
```bash
# Check app status
heroku ps

# View logs
heroku logs --tail

# Open app in browser
heroku open
```

### Run Management Commands
```bash
# Create superuser
heroku run python manage.py createsuperuser

# Run migrations manually (if needed)
heroku run python manage.py migrate

# Open Django shell
heroku run python manage.py shell
```

### Monitor Your App
```bash
# Check dyno status
heroku ps

# Monitor metrics
heroku metrics

# Restart app
heroku restart
```

## 7. Scaling and Performance

### Scale Dynos
```bash
# Scale web dynos
heroku ps:scale web=2

# Scale worker dynos (if you have background tasks)
heroku ps:scale worker=1
```

### Add Performance Monitoring
Consider adding these add-ons for production:
```bash
# Application performance monitoring
heroku addons:create newrelic:wayne

# Log aggregation
heroku addons:create papertrail:choklad
```

## 8. Continuous Deployment

### Connect to GitHub
Enable automatic deploys from your GitHub repository:

1. Go to your app's dashboard on heroku.com
2. Click "Deploy" tab
3. Connect to GitHub
4. Enable automatic deploys from your main branch
5. (Optional) Enable "Wait for CI to pass before deploy"

### Using GitHub Actions
Alternatively, set up GitHub Actions for deployment:

```yaml
# .github/workflows/deploy.yml
name: Deploy to Heroku

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: akhileshns/heroku-deploy@v3.12.12
        with:
          heroku_api_key: ${{secrets.HEROKU_API_KEY}}
          heroku_app_name: "your-app-name"
          heroku_email: "your-email@example.com"
```

---

## Quick Reference Commands

| Task | Command |
|------|---------|
| Create app | `heroku create app-name` |
| Add PostgreSQL | `heroku addons:create heroku-postgresql:essential-0` |
| Add Redis | `heroku addons:create heroku-redis:mini` |
| Set config var | `heroku config:set KEY=value` |
| View config | `heroku config` |
| Deploy | `git push heroku main` |
| View logs | `heroku logs --tail` |
| Run command | `heroku run python manage.py <command>` |
| Open app | `heroku open` |
| Restart app | `heroku restart` |
| Check status | `heroku ps` |
| Scale dynos | `heroku ps:scale web=2` |

---

## Next Steps

- Set up **CI/CD** with GitHub Actions (see [Django CI/CD Setup Guide](03-django-cicd-setup.md))
- Add **monitoring** with Sentry for error tracking
- Configure **custom domain** with `heroku domains:add yourdomain.com`
- Set up **automated backups** for your database
- Review **Heroku's best practices**: https://devcenter.heroku.com/articles/django-app-configuration

---

**Related Guides:**
- [Django CI/CD Setup](03-django-cicd-setup.md) - Add automated testing and deployment
- [DigitalOcean Operations](02-digitalocean-ops.md) - Alternative deployment platform
- [Django Production Guide](../django/02-detailed-checklist.md) - Production readiness checklist
