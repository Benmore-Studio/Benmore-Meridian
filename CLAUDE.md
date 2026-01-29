# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

This repository contains a comprehensive collection of **developer onboarding guides and checklists** organized by topic. It's a knowledge base for teams to standardize development practices, from initial environment setup through production deployment.

**Key Focus Areas:**
- Django production readiness and best practices
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
├── django/
│   ├── README.md                     # Guide selector with comparisons
│   ├── 01-simple-checklist.md        # Pure checkbox format (95 items)
│   ├── 02-detailed-checklist.md      # Step-by-step implementation (45-60 min)
│   └── 03-comprehensive-guide.md     # Deep reference with full explanations
├── review/
│   ├── README.md                     # Workflow overview
│   ├── 01-pr-review-workflow.md      # Complete PR review & GitHub setup
│   └── assets/                       # 7 supporting images
├── toolkit/
│   ├── README.md                     # Toolkit overview
│   └── 01-toolkit-checklist.md       # Development environment setup
└── team/
    ├── README.md                     # Team guides index
    └── jacobs_devs/
        └── ore.md                    # Team-specific documentation
```

### File Naming Convention

- **Django guides:** `01-simple-checklist.md`, `02-detailed-checklist.md`, `03-comprehensive-guide.md`
- **Review guides:** `01-pr-review-workflow.md`
- **Toolkit guides:** `01-toolkit-checklist.md`
- **Category indexes:** `README.md` in each directory
- **Team guides:** `team_name/name.md` structure

---

## Guide Purposes and Use Cases

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

### PR Review & Project Management

**File:** `review/01-pr-review-workflow.md`

Complete workflow for collaborative development:
- GitHub integration and configuration
- Project management setup with GitHub Projects
- AI-assisted PR review process
- Automated checks and verification
- Includes 7 supporting images for visual guidance

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

### Team Guides

**File:** `team/` (expandable)

Team-specific onboarding and process documentation:
- Currently contains: `jacobs_devs/ore.md`
- Extensible structure for adding new teams: `team/team_name/guides.md`

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
- `django/README.md` - Guide selector with feature comparison
- `review/README.md` - PR workflow overview
- `toolkit/README.md` - Toolkit setup overview
- `team/README.md` - Team guides index

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

## For Future Claude Code Instances

**Getting oriented:**
1. Start with `README.md` to understand the repository purpose
2. Explore the relevant category (`django/`, `review/`, `toolkit/`, or `team/`)
3. Check the category `README.md` to understand guide scope and differences
4. Read the specific guide file(s) as needed

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
