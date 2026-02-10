# Dev Onboarding Guides

A comprehensive collection of guides to help developers onboard and follow best practices.

---

## 📚 Guide Categories

### 1. **Django Production** 🚀
Guides for productionizing Django applications with modern tooling and best practices.

- **Simple Checklist** (95 items) - Pure checkbox format for quick reference
- **Detailed Checklist** (45-60 min) - Step-by-step implementation with context
- **Comprehensive Guide** (Reference) - Deep dive with complete explanations

**Location:** `django/README.md`

---

### 2. **Development Workflow & CI/CD** 🔧
Guides for the full development lifecycle — from meeting notes to automated checks.

- Developer workflow: transcripts → requirements → plans → execution
- **CI/CD Bots**: Sentry, Vercel, GitHub Actions, Claude Bot setup
- **Claude Code Ecosystem**: MCP tools, plugins, skills, subagents
- PR review workflow with AI

**Location:** `development/`

---

### 3. **PR Review & Project Management** 🔍
Workflow for setting up GitHub, managing projects, and performing AI-assisted PR reviews.

- Setup GitHub and Sentry integration
- Organize projects with GitHub Projects
- Use Claude for hyper-critical PR reviews
- Track tickets and link them to PRs

**Location:** `review/01-pr-review-workflow.md`

---

### 4. **Dev Toolkit & Setup** 🛠️
Comprehensive checklist for installing and setting up your development environment.

- Core development tools (terminal, package managers, search)
- System utilities (window management, productivity)
- Version control & deployment platforms
- External services & APIs
- Installation verification & setup script

**Location:** `toolkit/01-toolkit-checklist.md`

---

### 5. **Team Guides** 👥
Team-specific onboarding and process documentation.

**Location:** `team/`

---

### 6. **Claude Code Skills** 🤖
Production-grade skills that extend Claude Code's capabilities with domain expertise.

**Skills included:**
- django-production - Django production best practices
- frontend-productionize - Next.js + Django integration
- dependency-security-audit - Security scanning and CVE fixes
- django-auth-react-native - Mobile app authentication
- modern-terminal-setup - Developer environment setup
- skill-creator - Create your own skills

**Installation:** `cp -r skills/* ~/.claude/skills/`

**Location:** `skills/README.md`

---

## 🎯 Quick Start

**New to the project?**
1. Start with the [Dev Toolkit](toolkit/) - get your environment set up
2. Read [PR Review Workflow](review/) - understand our review process
3. Check [Django Production](django/) - if working on Django projects

**Implementing Django production setup?**
- Start with [Detailed Checklist](django/02-detailed-checklist.md) for hands-on implementation
- Reference [Comprehensive Guide](django/03-comprehensive-guide.md) for details
- Use [Simple Checklist](django/01-simple-checklist.md) for quick reference

---

## 📊 File Structure

```
guides/
├── README.md (this file)
├── development/
│   ├── README.md (development guides index)
│   ├── 00-developer-workflow.md
│   ├── 01-pr-review-workflow.md
│   ├── 02-ci-cd-bots-setup.md        ← NEW
│   ├── 03-claude-code-ecosystem.md    ← NEW
│   └── assets/
├── django/
│   ├── README.md (django guides index)
│   ├── 01-simple-checklist.md
│   ├── 02-detailed-checklist.md
│   └── 03-comprehensive-guide.md
├── review/
│   ├── 01-pr-review-workflow.md
│   └── assets/
├── toolkit/
│   └── 01-toolkit-checklist.md
└── team/
    └── jacobs_devs/
        └── ore.md
```

---

## ✅ Onboarding Checklist

Track your onboarding progress:

- [ ] **Environment Setup** - Complete the [Dev Toolkit](toolkit/)
- [ ] **Review Process** - Read the [PR Review Workflow](review/)
- [ ] **Team Guides** - Check [Team Documentation](team/)
- [ ] **Django Setup** (if applicable) - Follow [Django Production](django/) guides

---

## 🔗 Quick Links

| Guide | Duration | Best For |
|-------|----------|----------|
| [Dev Toolkit](toolkit/01-toolkit-checklist.md) | 30-60 min | Setting up your dev environment |
| [Developer Workflow](development/00-developer-workflow.md) | 15 min read | End-to-end feature workflow |
| [CI/CD Bots Setup](development/02-ci-cd-bots-setup.md) | 30-45 min | Sentry, Vercel, Actions, Claude |
| [Claude Code Ecosystem](development/03-claude-code-ecosystem.md) | 20 min read | MCP, plugins, skills, agents |
| [PR Review Workflow](development/01-pr-review-workflow.md) | 20 min read | Understanding our review process |
| [Django Simple Checklist](django/01-simple-checklist.md) | 45-60 min | Quick Django production checklist |
| [Django Detailed Checklist](django/02-detailed-checklist.md) | 45-60 min | Guided Django implementation |
| [Django Comprehensive Guide](django/03-comprehensive-guide.md) | Reference | Complete Django reference |

---

**Happy onboarding! 🎉**
