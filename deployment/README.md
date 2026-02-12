# Deployment Guides

Comprehensive guides for deploying Django applications, managing servers, setting up CI/CD, and configuring mobile development environments.

---

## 📁 Guide Organization

Guides are organized by platform and purpose:

```
deployment/
├── heroku/              # Heroku cloud platform
├── digitalocean/        # DigitalOcean self-hosted
├── cicd/               # CI/CD automation
└── mobile/             # Mobile development
```

---

## 🌐 Deployment Platforms

### Heroku (Cloud Platform)

**Location:** `heroku/`

| Guide | Description |
|-------|-------------|
| [Django Deployment](heroku/django-deployment.md) | Deploy Django to Heroku with uv |

**Best for:**
- Quick Django deployments
- Managed database (PostgreSQL)
- Zero-config deployments
- Free tier available
- Automatic HTTPS

**Tech stack:** Python 3.12+ with `uv`, PostgreSQL, Redis, Gunicorn

---

### DigitalOcean (Self-Hosted)

**Location:** `digitalocean/`

| Guide | Description |
|-------|-------------|
| [Overview](digitalocean/01-overview.md) | Quick reference & navigation |
| [Getting Started](digitalocean/02-getting-started.md) | Server connection & setup |
| [Deployment](digitalocean/03-deployment.md) | Deploy new projects |
| [Daily Operations](digitalocean/04-daily-operations.md) | Pull code, run migrations |
| [Commands Reference](digitalocean/05-commands-reference.md) | PM2, Django, Git, Database |
| [Troubleshooting](digitalocean/06-troubleshooting.md) | Fix common errors |

**Best for:**
- Full server control
- Cost-effective for larger apps
- Custom configurations
- Multiple apps on one server
- SSH access for debugging

**Tech stack:** Ubuntu, PM2, PostgreSQL, Nginx, Python with `uv`

**Quick start:**
1. Start with [Overview](digitalocean/01-overview.md) for quick reference
2. New developer? Read [Getting Started](digitalocean/02-getting-started.md)
3. Deploying? Follow [Deployment](digitalocean/03-deployment.md)
4. Daily updates? See [Daily Operations](digitalocean/04-daily-operations.md)

---

## ⚙️ CI/CD & Automation

**Location:** `cicd/`

| Guide | Description |
|-------|-------------|
| [Django CI/CD Setup](cicd/django-setup.md) | Automated testing & deployment |

**Automated checks:**
- ✅ Linting and formatting (ruff)
- ✅ Type checking (mypy)
- ✅ Test suite with coverage (pytest)
- ✅ Security scanning (gitleaks)
- ✅ Django system checks
- ✅ Docker build verification

**Use when:** Setting up quality checks and deployment pipelines

---

## 📱 Mobile Development

**Location:** `mobile/`

| Guide | Description |
|-------|-------------|
| [React Native Setup](mobile/react-native-setup.md) | Mobile app development with Expo |

**Best for:**
- Quick mobile app development
- Cross-platform (iOS + Android)
- Live updates without app store
- Simplified build process

**Tech stack:** Expo SDK, TypeScript, React Native

---

## 🎯 Quick Start Workflows

### New Django Project → Production

```bash
# 1. Set up CI/CD (10-15 min)
# Follow: cicd/django-setup.md

# 2. Deploy to Heroku (15-20 min)
# Follow: heroku/django-deployment.md

# 3. Verify deployment
heroku open
heroku logs --tail
```

### Django Project → DigitalOcean

```bash
# 1. Connect to server
# Follow: digitalocean/02-getting-started.md

# 2. Deploy project
# Follow: digitalocean/03-deployment.md

# 3. Daily updates
# Follow: digitalocean/04-daily-operations.md
```

### Django Backend + React Native Frontend

```bash
# 1. Set up backend CI/CD
# Follow: cicd/django-setup.md

# 2. Deploy backend
# Follow: heroku/django-deployment.md OR digitalocean/03-deployment.md

# 3. Set up React Native app
# Follow: mobile/react-native-setup.md

# 4. Connect frontend to backend API
```

---

## 📊 Platform Comparison

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

See platform-specific troubleshooting:
- [Heroku Troubleshooting](heroku/django-deployment.md#5-troubleshooting-common-issues)
- [DigitalOcean Troubleshooting](digitalocean/06-troubleshooting.md)

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

## 🗺️ Navigation

**By platform:**
- [Heroku guides](heroku/) - Cloud deployment
- [DigitalOcean guides](digitalocean/) - Self-hosted deployment
- [CI/CD guides](cicd/) - Automated testing
- [Mobile guides](mobile/) - React Native development

**By task:**
- **First deployment:** Start with [Heroku](heroku/django-deployment.md) or [DigitalOcean](digitalocean/03-deployment.md)
- **Daily updates:** See [Heroku workflow](heroku/django-deployment.md#6-post-deployment) or [DO daily ops](digitalocean/04-daily-operations.md)
- **CI/CD setup:** Follow [Django CI/CD guide](cicd/django-setup.md)
- **Mobile app:** Start with [React Native setup](mobile/react-native-setup.md)

---

**Happy deploying! 🚀**
