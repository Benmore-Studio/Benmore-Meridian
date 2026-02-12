# Deployment Guides

Comprehensive guides for deploying Django applications, managing servers, setting up CI/CD, and configuring React Native mobile apps.

---

## 📚 Guide Overview

| Guide | Duration | Best For |
|-------|----------|----------|
| [Heroku Django Deployment](01-heroku-django.md) | 15-20 min | Deploying Django to Heroku with uv |
| [DigitalOcean Operations](02-digitalocean-ops.md) | 5 min (reference) | Managing deployed apps on DO droplets |
| [Django CI/CD Setup](03-django-cicd-setup.md) | 10-15 min | Adding automated testing and deployment |
| [React Native Setup](04-react-native-setup.md) | 20-30 min | Setting up React Native with Expo |

---

## 🚀 Deployment Platforms

### Heroku

**Guide:** [01-heroku-django.md](01-heroku-django.md)

**Best for:**
- Quick Django deployments
- Managed database (PostgreSQL)
- Zero-config deployments
- Free tier available
- Automatic HTTPS

**Use when:**
- You want to deploy quickly without server management
- You need managed add-ons (Redis, PostgreSQL, monitoring)
- Your project is a straightforward Django app

**Tech stack:**
- Python 3.12+ with `uv`
- PostgreSQL (via Heroku Postgres)
- Redis (via Heroku Redis)
- Gunicorn as WSGI server

---

### DigitalOcean

**Guide:** [02-digitalocean-ops.md](02-digitalocean-ops.md)

**Best for:**
- Full server control
- Cost-effective for larger apps
- Custom configurations
- Multiple apps on one server
- SSH access for debugging

**Use when:**
- You need more control over your environment
- You want to run multiple apps on one server
- Cost optimization is important
- You're comfortable with Linux/server management

**Tech stack:**
- Ubuntu droplets
- PM2 for process management
- PostgreSQL (self-hosted)
- Nginx as reverse proxy
- Python with `uv`

---

## ⚙️ CI/CD & Automation

### Django CI/CD Setup

**Guide:** [03-django-cicd-setup.md](03-django-cicd-setup.md)

**Automated checks:**
- ✅ Linting and formatting (ruff)
- ✅ Type checking (mypy)
- ✅ Test suite with coverage (pytest)
- ✅ Security scanning (gitleaks)
- ✅ Django system checks
- ✅ Docker build verification

**Use when:**
- Setting up a new Django project
- Adding quality checks to existing project
- Configuring GitHub Actions CI/CD
- Implementing pre-commit hooks

**Success criteria:**
- All checks pass in < 2 minutes
- Test coverage ≥ 80%
- No secrets in git history
- Docker builds successfully

---

## 📱 Mobile Development

### React Native with Expo

**Guide:** [04-react-native-setup.md](04-react-native-setup.md)

**Best for:**
- Quick mobile app development
- Cross-platform (iOS + Android)
- Live updates without app store
- Simplified build process

**Use when:**
- Building a mobile frontend for your Django backend
- You want to test on your phone immediately
- You need rapid iteration and hot reloading
- You want to avoid complex native builds

**Tech stack:**
- Expo SDK
- TypeScript
- React Native
- Expo Go for testing

---

## 🎯 Quick Start Workflows

### New Django Project → Production

```bash
# 1. Set up CI/CD (10-15 min)
# Follow: 03-django-cicd-setup.md

# 2. Deploy to Heroku (15-20 min)
# Follow: 01-heroku-django.md

# 3. Verify deployment
heroku open
heroku logs --tail
```

### Existing Django Project → DigitalOcean

```bash
# 1. Deploy to DO droplet
# Use your existing deployment process

# 2. Reference operational commands
# Follow: 02-digitalocean-ops.md

# 3. Add CI/CD
# Follow: 03-django-cicd-setup.md
```

### Django Backend + React Native Frontend

```bash
# 1. Set up backend CI/CD
# Follow: 03-django-cicd-setup.md

# 2. Deploy backend to Heroku
# Follow: 01-heroku-django.md

# 3. Set up React Native app
# Follow: 04-react-native-setup.md

# 4. Connect frontend to backend API
# Use the Heroku app URL as your API base URL
```

---

## 📊 Deployment Comparison

### Heroku vs DigitalOcean

| Feature | Heroku | DigitalOcean |
|---------|--------|--------------|
| **Setup time** | 15 min | 1-2 hours |
| **Management** | Fully managed | Self-managed |
| **Cost** | Higher | Lower |
| **Scalability** | Easy (slider) | Manual |
| **Database** | Managed add-on | Self-hosted |
| **SSH access** | Limited | Full |
| **Custom config** | Limited | Unlimited |
| **Best for** | Quick deploys, startups | Cost-sensitive, control |

### When to choose Heroku:
- ✅ MVP/prototype stage
- ✅ Small team without DevOps expertise
- ✅ Need managed database/Redis
- ✅ Want automatic HTTPS
- ✅ Focus on code, not infrastructure

### When to choose DigitalOcean:
- ✅ Cost optimization is critical
- ✅ Need full server control
- ✅ Running multiple projects on one server
- ✅ Have DevOps experience
- ✅ Need custom system-level configurations

---

## 🔄 Common Deployment Workflows

### Deploy Code Update

**Heroku:**
```bash
git push heroku main
heroku logs --tail
```

**DigitalOcean:**
```bash
cd /root/YOUR_PROJECT
git pull origin main
cd backend
uv sync
uv run python manage.py migrate
uv run python manage.py collectstatic --noinput
pm2 restart yourproject
```

### Run Migrations

**Heroku:**
```bash
heroku run python manage.py migrate
```

**DigitalOcean:**
```bash
cd /root/YOUR_PROJECT/backend
uv run python manage.py migrate
pm2 restart yourproject
```

### View Logs

**Heroku:**
```bash
heroku logs --tail
heroku logs --source app --tail
```

**DigitalOcean:**
```bash
pm2 logs yourproject
pm2 logs yourproject --lines 100
```

---

## 🛠️ Tools & Technologies

### Package Managers
- **uv** - Ultra-fast Python package manager (recommended)
- **npm/pnpm** - Node.js package management

### Web Servers
- **Gunicorn** - Python WSGI server for Django
- **Nginx** - Reverse proxy (DigitalOcean)

### Process Managers
- **PM2** - Node.js process manager (used for Django on DO)
- **Heroku Dynos** - Managed processes (Heroku)

### Databases
- **PostgreSQL** - Primary database (both platforms)
- **Redis** - Caching and sessions (optional)

### CI/CD
- **GitHub Actions** - Automated testing and checks
- **pre-commit** - Git hooks for local quality checks
- **gitleaks** - Secret scanning
- **ruff** - Python linting and formatting
- **pytest** - Testing framework

---

## 📖 Related Documentation

**Cross-references:**
- [Django Production Guides](../django/) - Production readiness checklists
- [Development Workflow](../development/) - CI/CD bots and automation
- [Dev Toolkit](../toolkit/) - Environment setup

**External resources:**
- [Heroku Python Documentation](https://devcenter.heroku.com/categories/python-support)
- [DigitalOcean Tutorials](https://www.digitalocean.com/community/tutorials)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Expo Documentation](https://docs.expo.dev/)

---

## 🚨 Troubleshooting

### Common issues across platforms:

**Application won't start**
- Check logs first (heroku logs / pm2 logs)
- Verify environment variables are set
- Ensure migrations have run
- Check Python version compatibility

**Database connection failed**
- Verify DATABASE_URL is set correctly
- Check database credentials
- Ensure database service is running
- Test connection manually

**Static files not loading**
- Run `collectstatic` command
- Check STATIC_ROOT configuration
- Verify whitenoise is installed (Heroku)
- Check Nginx config (DigitalOcean)

**After code update, changes not reflected**
- Clear cache (browser and server)
- Restart application process
- Verify git push succeeded
- Check for migration errors

See individual guides for platform-specific troubleshooting.

---

## ✅ Deployment Checklist

Before deploying to production:

- [ ] CI/CD pipeline configured and passing
- [ ] Environment variables set (SECRET_KEY, DEBUG=False, etc.)
- [ ] Database migrations applied
- [ ] Static files collected
- [ ] ALLOWED_HOSTS configured
- [ ] Security settings enabled (CSRF, HSTS, etc.)
- [ ] Error monitoring configured (Sentry)
- [ ] Backup strategy in place
- [ ] Domain/DNS configured (if applicable)
- [ ] HTTPS enabled
- [ ] Test deployment in staging first

---

**Happy deploying! 🚀**
