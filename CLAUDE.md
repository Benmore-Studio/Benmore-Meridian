# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

This repository contains a comprehensive collection of **developer onboarding guides and checklists** organized by topic. It's a knowledge base for teams to standardize development practices, from initial environment setup through production deployment.

**Key Focus Areas:**
- Django production readiness and best practices
- Development workflows, CI/CD automation, and AI-powered tools
- PR review workflows and project management
- Development toolkit setup and verification
- Team-specific onboarding materials

**Repository Type:** Documentation and guides (no application code)

---

## Repository Structure

### Core Organization

The guides are organized by topic with a consistent structure:

```
guides/
├── README.md                          # Main index & quick start
├── CLAUDE.md                          # This file
├── deployment/
│   ├── README.md                     # Deployment overview & platform comparison
│   ├── 01-heroku-django.md           # Deploy Django to Heroku with uv
│   ├── 02-digitalocean-ops.md        # Server management command reference
│   ├── 03-django-cicd-setup.md       # CI/CD setup with Claude Code
│   └── 04-react-native-setup.md      # React Native mobile development
├── django/
│   ├── README.md                     # Guide selector with comparisons
│   ├── 01-simple-checklist.md        # Pure checkbox format (95 items)
│   ├── 02-detailed-checklist.md      # Step-by-step implementation (45-60 min)
│   └── 03-comprehensive-guide.md     # Deep reference with full explanations
├── development/
│   ├── README.md                     # Development workflow overview
│   ├── 00-developer-workflow.md      # End-to-end developer workflow
│   ├── 01-pr-review-workflow.md      # PR review & project management
│   ├── 02-ci-cd-bots-setup.md        # CI/CD bots & automated checks
│   ├── 03-claude-code-ecosystem.md   # Claude Code tools & ecosystem
│   └── assets/                       # 20 supporting images
├── review/
│   └── 01-pr-review-workflow.md      # Complete PR review & GitHub setup
├── toolkit/
│   ├── README.md                     # Toolkit overview
│   └── 01-toolkit-checklist.md       # Development environment setup
└── team/
    └── .gitkeep                      # Team guides (currently empty/placeholder)
```

### File Naming Convention

- **Deployment guides:** `01-heroku-django.md`, `02-digitalocean-ops.md`, `03-django-cicd-setup.md`, `04-react-native-setup.md`
- **Django guides:** `01-simple-checklist.md`, `02-detailed-checklist.md`, `03-comprehensive-guide.md`
- **Development guides:** `00-developer-workflow.md`, `01-pr-review-workflow.md`, `02-ci-cd-bots-setup.md`, `03-claude-code-ecosystem.md`
- **Review guides:** `01-pr-review-workflow.md`
- **Toolkit guides:** `01-toolkit-checklist.md`
- **Category indexes:** `README.md` in each directory (where applicable)
- **Team guides:** `team_name/name.md` structure (future expansion)

---

## Guide Purposes and Use Cases

### Deployment & Infrastructure

**File:** `deployment/` (4 complementary guides)

Platform-specific deployment guides and server operations:

**01-heroku-django.md** (~15KB, 15-20 min)
- Deploy Django to Heroku using modern `uv` package manager
- Configure Procfile, runtime.txt, and environment variables
- Manage PostgreSQL and Redis add-ons
- Monorepo/subdirectory deployment with git subtree
- Continuous deployment workflows
- Best for: Quick Django deployments with managed infrastructure

**02-digitalocean-ops.md** (~11KB, 5 min reference)
- Server management command reference for DigitalOcean droplets
- PM2 process manager operations
- Django management commands with `uv`
- PostgreSQL database operations
- Git deployment workflows
- Best for: Managing Django on self-hosted infrastructure

**03-django-cicd-setup.md** (~10KB, 10-15 min)
- Add production-ready CI/CD to Django projects
- GitHub Actions workflow configuration
- Automated testing, linting, security scanning
- Pre-commit hooks setup
- Makefile commands for local development
- Best for: Setting up automated quality checks and deployment pipelines

**04-react-native-setup.md** (~8KB, 20-30 min)
- React Native project setup with Expo and TypeScript
- Development environment configuration
- Running on physical devices (iOS/Android)
- Using simulators and emulators
- Claude Code skills for professional UI design
- Best for: Mobile app development and deployment preparation

**Common Coverage:**
- Modern deployment platforms: Heroku, DigitalOcean
- Package management: `uv` for Python, `npm` for JavaScript
- Process managers: PM2, Heroku Dynos, Gunicorn
- CI/CD: GitHub Actions, pre-commit hooks, automated testing
- Mobile development: Expo, React Native, TypeScript
- Server operations: PostgreSQL, Redis, Nginx

**Success criteria:**
- Successful deployment to chosen platform
- Zero-downtime deployments with proper release process
- Automated CI/CD passing all checks
- Production monitoring and error tracking configured
- Mobile app running on physical devices

### Django Production Readiness

**File:** `django/` (3 complementary guides)

Guides for productionizing Django applications with modern tooling:

**01-simple-checklist.md** (95 items, ~5.6KB)
- Pure checkbox format for quick reference
- Commands on each line with minimal explanation
- Best for: developers who prefer a simple to-do list
- Tracks progress: `__ / 95 items complete`

**02-detailed-checklist.md** (45-60 min, ~14KB)
- Step-by-step implementation with context
- Real checkboxes for tracking, copy-paste commands, verification steps
- Best for: implementing production best practices in a new or existing project
- Includes: 11 implementation phases, daily command reference, troubleshooting guide

**03-comprehensive-guide.md** (~22KB, reference)
- Complete explanations with full code examples
- Covers WHY and HOW with rationale behind decisions
- Best for: team training, understanding architecture decisions, troubleshooting details

**Common Coverage:**
- Modern tooling: `uv`, `ruff`, `pytest`, `mypy`, `gitleaks`, `pre-commit`
- Production infrastructure: Django settings split, security hardening, Docker, GitHub Actions CI/CD
- Developer experience: All checks in <30 seconds, Makefile commands, pre-commit hooks
- Success criteria: `make check-all` passes, pre-commit works, tests at ≥80% coverage, no secrets in git, etc.

### Development Workflow & CI/CD Automation

**File:** `development/` (4 complementary guides + 20 supporting images)

Comprehensive guides for the complete development lifecycle using Claude Code and modern tooling:

**00-developer-workflow.md** (~6KB, 5-10 min)
- End-to-end developer workflow from requirements to execution
- Meeting transcript integration with Gemini
- Extracting requirements from client meetings
- Implementation planning with Claude Code
- Plan execution with skills and subagents
- Best for: Understanding the full development cycle end-to-end

**01-pr-review-workflow.md** (~3.8KB, 5-10 min)
- PR review and project management workflow
- GitHub integration and configuration
- GitHub Projects setup for roadmap visualization
- AI-assisted PR review process with Claude
- Automated checks and verification
- Best for: Code review procedures and team collaboration

**02-ci-cd-bots-setup.md** (~14KB, 15-20 min)
- Automated CI/CD bots and checks configuration
- Sentry Bot for runtime error tracking and monitoring
- Vercel Bot for preview deployments and testing
- GitHub Actions for linting, formatting, and test automation
- Claude Bot for AI-powered code review
- Best for: Setting up automated verification in repositories

**03-claude-code-ecosystem.md** (~13KB, 15-20 min)
- Claude Code tools and integrated ecosystem
- MCP Servers: Context7 for docs, Hyperbrowser for web automation, Agent Browser
- Plugins and marketplaces: Superpowers, Double Shot Latte
- Skills system and custom skill creation
- Subagents and Agent Teams for parallel work
- Best for: Mastering AI-powered development tools and workflows

**Common Coverage:**
- Modern tooling: Claude Code, MCP servers, GitHub Apps, Sentry, Vercel
- Workflow automation: CI/CD pipelines, pre-commit hooks, GitHub Actions
- AI integration: Claude for code review, requirement extraction, planning
- Team coordination: Project management, PR workflows, automated checks
- Visual guides: 20 supporting images in `development/assets/` for workflow illustration

**Success criteria:**
- Complete workflow understanding from meeting notes to production
- CI/CD bots configured and running
- Claude Code ecosystem tools installed and productive
- PR review process established with AI assistance

### PR Review & Project Management

**File:** `review/01-pr-review-workflow.md`

Complete workflow for collaborative development:
- GitHub integration and configuration
- Project management setup with GitHub Projects
- AI-assisted PR review process with Claude
- Automated checks and verification

**Note:** This guide also appears in `development/01-pr-review-workflow.md` as part of the comprehensive development workflow series. Both versions provide the same core PR review process but may have different context and integration points.

**Phases:**
1. Initial Setup - GitHub app installation, team setup, Sentry integration
2. Project Management - Creating projects, assigning to repos, linking tickets
3. PR Review Workflow - AI analysis, code verification, feedback posting
4. Final Checks - GitHub Actions CI/CD, deployment status, integration verification

### Development Toolkit & Setup

**File:** `toolkit/01-toolkit-checklist.md`

Comprehensive checklist for environment setup:
- Core development tools: ghostty, tree, uv, ripgrep, Rust
- System utilities: Rectangle (macOS), Raycast
- Version control: GitHub CLI
- Deployment platforms: Vercel, Heroku
- External services: Sentry, Cloudinary, Mailjet, Gemini
- Includes: installation commands, platform-specific instructions, verification steps, setup script

### Team-Specific Guides

**File:** `team/` (expandable structure, currently empty)

Team-specific onboarding and process documentation:
- **Current Status:** Placeholder directory with `.gitkeep` (ready for team content)
- **Extensible structure:** `team/team_name/` for individual team directories
- **Future additions:** Will support multiple teams with custom documentation
- **Best for:** Team-specific workflows, processes, and onboarding materials

**When to add team content:**
- Create `team/team_name/` directory for your team
- Add team-specific guides, conventions, and processes
- Update this section to reference your team's documentation

---

## Development Guidelines for Maintaining This Repository

### When Adding or Modifying Guides

1. **Maintain the existing structure** - Keep the folder organization and naming convention consistent
2. **Update category READMEs** - If adding new guides, update the relevant `README.md` in that category
3. **Update the main README.md** - Reflect any new guides or structural changes at the top level
4. **Image management** - Store guide images in appropriate `assets/` folders (e.g., `review/assets/`)
5. **Use relative paths** - All markdown links and image references should use relative paths for portability

### Style and Format

**Markdown conventions:**
- Use clear hierarchy with `#`, `##`, `###` headings
- Use emoji for visual organization (already established: 📚 🚀 ☑️ ✅ 📖, etc.)
- Use tables for comparisons (see `django/README.md` for examples)
- Use code blocks for commands and examples
- Use checkboxes (`[ ]`) for tracking in checklists

**Content principles:**
- Checklists should be actionable with minimal explanation
- Links to external documentation should be provided
- Copy-paste commands should be clearly formatted
- Include verification steps after major sections
- Provide troubleshooting guidance when applicable

### Verification and Testing

- Verify all markdown files render correctly
- Test all links (both internal and external)
- Confirm all image paths are correct
- Validate that relative paths work from different locations
- Check that category READMEs link correctly to guides

---

## Common Workflows

### Adding a New Guide to a Category

1. Create the guide file with appropriate naming (e.g., `03-guide-name.md`)
2. Add a section in the category's `README.md` describing the guide
3. Update the main `README.md` if it references that category
4. Commit with a clear message: "Add guide: [category] - [guide name]"

### Adding a New Team

1. Create `team/team_name/` directory
2. Create `team/team_name/README.md` with team overview
3. Add team-specific guides as needed
4. Update `team/README.md` to reference the new team
5. Update main `README.md` if team should be highlighted

### Updating Existing Guides

- Make edits directly to the guide file
- Keep the file numbering consistent
- Ensure all links and references remain valid
- Update category `README.md` if scope or description changes
- Commit with message: "Update: [guide name] - [change description]"

---

## Key Design Decisions

### Three Django Guides Instead of One

The repository provides three complementary Django guides because different audiences have different needs:
- **Simple checklist** for experienced developers who want minimal context
- **Detailed checklist** for step-by-step implementation with tracking
- **Comprehensive guide** for deep understanding and team training

This allows the same content to serve multiple use cases without bloat.

### Category-Based Organization

Guides are grouped by topic (django, review, toolkit, team) rather than by audience or project type. This makes it easy to:
- Find related content quickly
- Add new guides to a topic consistently
- Navigate to category READMEs for context
- Share specific categories with different team members

### Six-Category Organization

The repository organizes guides across six complementary categories:
- **django/** - Productionizing Django applications (3 guides at different detail levels)
- **deployment/** - Platform deployment and infrastructure (4 guides for Heroku, DO, CI/CD, mobile)
- **development/** - Full development lifecycle and CI/CD (4 guides covering workflow, PRs, automation, ecosystem)
- **review/** - Code review processes (1 focused guide, also integrated into development workflow)
- **toolkit/** - Developer environment setup (1 comprehensive checklist)
- **team/** - Team-specific customization (expandable structure, currently empty placeholder)

This multi-category approach allows:
- Developers to find what they need without searching through monolithic documentation
- Multiple perspectives on related topics (e.g., PR review in both development/ and review/, deployment in both deployment/ and development/)
- Easy expansion as new team needs arise without restructuring
- Clear separation of concerns while allowing cross-references between related guides

### No Application Code

This repository contains documentation only - no Python, JavaScript, or executable code. All tools and technologies are described, but implementation happens in separate project repositories.

---

## Tools and Technologies Referenced

**Development Tools:**
- `uv` - Ultra-fast Python package manager
- `ruff` - All-in-one Python linting + formatting
- `pytest` - Python testing framework
- `mypy` - Python type checking
- `gitleaks` - Secret scanning for git repos
- `pre-commit` - Git hooks framework
- GitHub Actions - CI/CD platform
- Docker - Containerization

**Services:**
- Sentry - Error tracking and monitoring
- Vercel - Frontend deployment platform
- Heroku - Application hosting
- Cloudinary - Media management
- Mailjet - Email service
- Google Gemini - AI API

**Frameworks:**
- Django - Python web framework
- Django REST Framework (DRF) - API framework
- drf-spectacular - OpenAPI documentation

---

## Related Documentation

**Main navigation points:**
- `README.md` - Main index and quick start (entry point for all users)
- `deployment/README.md` - Deployment platform comparison and guide index
- `django/README.md` - Guide selector with feature comparison
- `development/README.md` - Development workflow overview and guide index
- `toolkit/README.md` - Toolkit setup overview
- `team/` - Team guides placeholder (currently empty, ready for expansion)

**Note:** The `review/` category contains a single focused guide (`01-pr-review-workflow.md`) without a category README. This guide is also part of the development workflow series for cross-reference convenience.

**External resources linked in guides:**
- Django documentation: https://docs.djangoproject.com/
- GitHub documentation: https://docs.github.com/
- Tool documentation: See individual guide files for links

---

## Repository Git Setup

**Branch strategy:**
- `main` - Production guides (stable, reviewed)
- Feature branches for new guides or significant updates

**Commit conventions:**
- Use clear, descriptive commit messages
- Group related changes (e.g., all Django guide updates together)
- Reference issue numbers if applicable

**What's tracked:**
- All `.md` files (guides)
- All image files (`.png`, `.jpg`, `.svg`, etc.)
- `.gitignore` and configuration files
- `.claude/` settings for Claude Code integration

**.gitignore coverage:**
- IDE files: `.vscode/`, `.idea/`
- Environment files: `.env*`
- Dependencies: `node_modules/`, `venv/`, `__pycache__/`
- OS files: `.DS_Store`, `Thumbs.db`
- Temporary files: `*.tmp`, `*.swp`, `logs/`
- Markdown and images are explicitly NOT ignored (see `.gitignore` note)

---

## Claude Code Skills

This repository includes production-grade skills for Claude Code.

### Skill Directory Structure

```
skills/
├── README.md (installation and usage guide)
├── django-production/
├── frontend-productionize/
├── dependency-security-audit/
├── django-auth-react-native/
├── modern-terminal-setup/
├── skill-creator/
└── [other skills]/
```

### Installation

Copy skills to Claude Code's skills directory:

```bash
cp -r skills/* ~/.claude/skills/
```

## Available Skills

### Production Skills (🚀)

**django-production**
Production-ready Django setup with modern tooling (uv, ruff, pytest, Docker, drf-spectacular).
- **Use when:** Auditing Django codebases, implementing production best practices
- **Triggers:** "productionize Django", "Django production setup", "audit Django"

**frontend-productionize**
Next.js + Django integration with OpenAPI TypeScript codegen for type-safe APIs.
- **Use when:** Starting Next.js projects, setting up CI/CD, type-safe API integration
- **Triggers:** "productionize Next.js", "Next.js production", "setup CI/CD"

---

### Security & Authentication (🔒)

**django-auth-react-native**
Complete Django authentication system for React Native with JWT, email verification, and OTP.
- **Use when:** Building Django + React Native projects, implementing JWT auth, multi-device session management
- **Triggers:** "Django React Native auth", "JWT authentication", "mobile app auth"

**dependency-security-audit**
Comprehensive dependency security auditing and automated fixing (npm, pnpm, yarn, pip, poetry).
- **Use when:** Security audits, checking for CVEs, fixing Dependabot issues, before production deployment
- **Triggers:** "audit security", "check vulnerabilities", "scan dependencies", "fix Dependabot"

---

### Developer Tooling (🛠️)

**modern-terminal-setup**
Modern macOS/Linux terminal with curated CLI tools, fzf-powered keybindings, and beautiful prompt.
- **Tools included:** bat, eza, ripgrep, fzf, zoxide, starship, lazygit, delta
- **Use when:** Setting up development environment, installing modern CLI tools, terminal productivity
- **Triggers:** "setup terminal", "modern CLI tools", "terminal productivity", "dev environment setup"

**skill-creator**
Guide for creating effective Claude Code skills with best practices and templates.
- **Use when:** Creating new skills, updating existing skills, learning skill development
- **Triggers:** "create skill", "skill development", "write skill"

---

### Utilities & Helpers (📝)

**gh_issue** - GitHub issue management and automation

**nano_banana** - Image generation using Gemini 2.5 Flash Image model

**stripe_processing** - Stripe payment processing with one-time payments, subscriptions, and email notifications

**presentation_maker** - Create presentations programmatically

---

### Superpowers Skills (External, Optional)

The following skills are available if you install the Superpowers marketplace separately:

- **agent-organizer** - Expert multi-agent orchestration
- **brainstorm** - Interactive design refinement
- **commit** - Smart git commit workflow
- **debug** - Systematic debugging
- **execplan** - Create execution plans
- **optimize** - Performance optimization
- **refactor** - Safe code refactoring
- **review-pr** - PR review checklist
- **security-audit** - Security vulnerability assessment
- **write-tests** - Test-driven development

---

## Using Skills

Skills are invoked using natural language that matches their triggers:

```bash
# Production skills
"Productionize my Django app"           → django-production
"Set up Next.js with type-safe APIs"    → frontend-productionize

# Security skills
"Audit my dependencies for CVEs"        → dependency-security-audit
"Set up Django auth for React Native"   → django-auth-react-native

# Developer tools
"Set up my terminal with modern tools"  → modern-terminal-setup
"Help me create a new skill"            → skill-creator

# Utilities
"Generate an image with AI"             → nano_banana
"Set up Stripe payments"                → stripe_processing
```

For detailed documentation on each skill's capabilities, implementation, and usage examples, see:
- `skills/README.md` - Installation and overview
- `skills/SKILLS_INVENTORY.md` - Complete inventory with status
- `skills/{skill-name}/SKILL.md` - Individual skill documentation

---

## For Future Claude Code Instances

**Getting oriented:**
1. Start with `README.md` to understand the repository purpose and structure
2. Explore the relevant category (`django/`, `development/`, `review/`, `toolkit/`, or `team/`)
3. Check the category `README.md` (where available: django, development, toolkit) for guide scope
4. Read the specific guide file(s) as needed for your task

**Making changes:**
- Follow the existing markdown style and emoji conventions
- Maintain relative path consistency
- Update both the guide file AND the relevant `README.md` file
- Test that all links and images work after changes

**Common questions:**
- "Where do I add a new guide?" → Create it in the appropriate category folder and update that category's `README.md`
- "Should I create a new guide or update an existing one?" → Check if the existing guide already covers the topic; prefer updating for consistency
- "How do I link between guides?" → Use relative paths: `[Link Text](../other-category/guide.md)`
- "What's the difference between the three Django guides?" → See the `django/README.md` comparison table for quick reference
- "What's in the deployment/ folder?" → Platform-specific deployment guides (Heroku, DigitalOcean), CI/CD setup, and React Native mobile development (4 guides)
- "What's in the development/ folder?" → Complete end-to-end development workflow, CI/CD setup, Claude Code ecosystem tools, and PR review processes (4 guides + 20 visual assets)
- "Are there images/assets to reference?" → Yes, 20 images in `development/assets/` providing visual workflow guidance
- "Is the team/ folder empty?" → Yes, it's currently a placeholder structure with `.gitkeep`, ready for team-specific content when needed
- "Why are there two PR review guides?" → `review/01-pr-review-workflow.md` and `development/01-pr-review-workflow.md` serve different contexts but contain similar content - use whichever fits your workflow
