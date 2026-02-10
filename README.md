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
Team-specific onboarding and process documentation (currently a placeholder, ready for team content).

**Location:** `team/` (create `team/team_name/` directories for your team)

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
│   └── 01-pr-review-workflow.md
├── toolkit/
│   ├── README.md (toolkit overview)
│   └── 01-toolkit-checklist.md
└── team/
    └── .gitkeep (placeholder for team-specific guides)
```

---

## ✅ Onboarding Checklist

Track your onboarding progress:

- [ ] **Environment Setup** - Complete the [Dev Toolkit](toolkit/01-toolkit-checklist.md)
- [ ] **Development Workflow** - Read [Developer Workflow](development/00-developer-workflow.md)
- [ ] **PR Review Process** - Understand [PR Review Workflow](review/01-pr-review-workflow.md)
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

## 🏗️ Repository Architecture

### Five-Category Organization

This repository organizes guides across five complementary categories:

- **django/** - Productionizing Django applications (3 guides at different detail levels)
- **development/** - Full development lifecycle and CI/CD (4 guides covering workflow, PRs, automation, ecosystem)
- **review/** - Code review processes (1 focused guide, also integrated into development workflow)
- **toolkit/** - Developer environment setup (1 comprehensive checklist)
- **team/** - Team-specific customization (expandable structure, currently placeholder)

**Why multiple categories?**
- Developers find what they need without searching through monolithic documentation
- Multiple perspectives on related topics (e.g., PR review in both `development/` and `review/`)
- Easy expansion as new team needs arise without restructuring
- Clear separation of concerns while allowing cross-references between related guides

### Key Design Decisions

**Three Django Guides Instead of One**
Different audiences need different levels of detail:
- **Simple checklist** for experienced developers who want minimal context
- **Detailed checklist** for step-by-step implementation with tracking
- **Comprehensive guide** for deep understanding and team training

**Documentation Repository**
This repository contains guides and documentation only — no Python, JavaScript, or executable code. Implementation happens in separate project repositories.

---

## 🛠️ Tools & Technologies Referenced

**Development Tools:**
- `uv` - Ultra-fast Python package manager
- `ruff` - All-in-one Python linting + formatting
- `pytest` - Python testing framework
- `mypy` - Python type checking
- `gitleaks` - Secret scanning for git repos
- `pre-commit` - Git hooks framework

**Deployment & Monitoring:**
- GitHub Actions - CI/CD platform
- Docker - Containerization
- Sentry - Error tracking and monitoring
- Vercel - Frontend deployment platform

**Frameworks:**
- Django - Python web framework
- Django REST Framework (DRF) - API framework
- drf-spectacular - OpenAPI documentation
- Next.js - React framework

**AI & Automation:**
- Claude Code - AI-powered development tool
- MCP Servers - Context7 (docs), Hyperbrowser (web automation), Agent Browser
- Claude Code Skills - Domain-specific automated workflows

---

## 🤖 Claude Code Integration

This repository works seamlessly with Claude Code via:

### Skills System (Automated Workflows)
Pre-built skills that automate complex tasks:
- **django-production** - Production-ready Django setup auditing
- **frontend-productionize** - Next.js + Django integration with type-safe APIs
- **dependency-security-audit** - Security scanning and CVE fixes
- **django-auth-react-native** - Complete auth system for mobile apps
- **modern-terminal-setup** - Developer environment automation
- **skill-creator** - Create your own specialized skills

**Installation:** `cp -r skills/* ~/.claude/skills/`

### MCP Servers (AI-Enhanced Tools)
- **Context7** - Get up-to-date docs for any library (Context7-compatible library lookup)
- **Hyperbrowser** - Cloud-hosted browser automation for web testing
- **Agent Browser** - Local browser automation for headless testing

### Subagents & Teams
- **Subagents** - Parallel agents for focused tasks (search, analysis, implementation)
- **Agent Teams** - Coordinated teams of agents with shared task lists and inter-agent messaging
- **Parallel Execution** - Up to 50 subagents working simultaneously on independent work

See `development/03-claude-code-ecosystem.md` for detailed setup and usage.

---

## 📋 Development Guidelines

### Before Adding or Modifying Guides

1. **Maintain existing structure** - Keep folder organization and naming consistent
2. **Update category READMEs** - If adding new guides, update the relevant `README.md`
3. **Update main README.md** - Reflect any new guides or structural changes
4. **Use relative paths** - All markdown links should use relative paths for portability
5. **Test links and images** - Verify all links work from different locations

### Style & Format

**Markdown conventions:**
- Clear hierarchy with `#`, `##`, `###` headings
- Emoji for visual organization (📚 🚀 ☑️ ✅ 📖, etc.)
- Tables for comparisons
- Code blocks for commands and examples
- Checkboxes (`[ ]`) for tracking in checklists

**Content principles:**
- Checklists should be actionable with minimal explanation
- Include verification steps after major sections
- Provide troubleshooting guidance when applicable
- Copy-paste commands should be clearly formatted
- Link to external documentation when relevant

---

## 🎓 For Future Developers

**Getting oriented:**
1. Start with this README to understand the repository purpose
2. Explore the relevant category (`django/`, `development/`, `review/`, `toolkit/`, or `team/`)
3. Check the category `README.md` to understand guide scope
4. Read the specific guide file(s) as needed

**Common questions:**
- **Where do I add a new guide?** → Create it in the appropriate category folder and update that category's `README.md`
- **What's in the development/ folder?** → Complete end-to-end development workflow, CI/CD setup, Claude Code ecosystem tools (4 guides + 20 visual assets)
- **Are there images/assets?** → Yes, 20 images in `development/assets/` for visual workflow guidance
- **Why two PR review guides?** → `review/01-pr-review-workflow.md` and `development/01-pr-review-workflow.md` provide same content in different contexts
- **How do I link between guides?** → Use relative paths: `[Link Text](../other-category/guide.md)`
- **Is the team/ folder empty?** → Yes, it's a placeholder with `.gitkeep`, ready for team-specific content

---

**Happy onboarding! 🎉**
