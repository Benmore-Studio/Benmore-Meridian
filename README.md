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

### 2. **PR Review & Project Management** 🔍
Workflow for setting up GitHub, managing projects, and performing AI-assisted PR reviews.

- Setup GitHub and Sentry integration
- Organize projects with GitHub Projects
- Use Claude for hyper-critical PR reviews
- Track tickets and link them to PRs

**Location:** `review/01-pr-review-workflow.md`

---

### 3. **Dev Toolkit & Setup** 🛠️
Comprehensive checklist for installing and setting up your development environment.

- Core development tools (terminal, package managers, search)
- System utilities (window management, productivity)
- Version control & deployment platforms
- External services & APIs
- Installation verification & setup script

**Location:** `toolkit/01-toolkit-checklist.md`

---

### 4. **Team Guides** 👥
Team-specific onboarding and process documentation.

**Location:** `team/`

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
├── django/
│   ├── README.md (django guides index)
│   ├── 01-simple-checklist.md
│   ├── 02-detailed-checklist.md
│   └── 03-comprehensive-guide.md
├── review/
│   ├── 01-pr-review-workflow.md
│   └── assets/
│       ├── install_claude_github.png
│       ├── Github_project.png
│       ├── add_project.png
│       ├── link_tickets.png
│       ├── prompt.png
│       ├── claude result.png
│       └── pr_review.png
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
| [PR Review Workflow](review/01-pr-review-workflow.md) | 20 min read | Understanding our review process |
| [Django Simple Checklist](django/01-simple-checklist.md) | 45-60 min | Quick Django production checklist |
| [Django Detailed Checklist](django/02-detailed-checklist.md) | 45-60 min | Guided Django implementation |
| [Django Comprehensive Guide](django/03-comprehensive-guide.md) | Reference | Complete Django reference |

---

**Happy onboarding! 🎉**
