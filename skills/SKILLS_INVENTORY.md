# Skills Inventory

All skills tracked in this repo. Install via `bm install` (symlinks to `~/.claude/skills/`).

## Quick Install

```bash
pipx install ./bm && bm install
```

---

## General Skills (55 total)

### 🚀 Production & Deployment

| Skill | Source | Status | Description |
|-------|--------|--------|-------------|
| `django-production` | Locally owned | ✅ Active | Production-ready Django setup (uv, ruff, pytest, Docker, drf-spectacular) |
| `frontend-productionize` | Locally owned | ✅ Active | Next.js + Django with OpenAPI TypeScript codegen for type-safe APIs |
| `productionize-app` | Locally owned | ✅ Active | Full production release-readiness checklist for any app |
| `fastapi-templates` | Marketplace | ✅ Active | Production-ready FastAPI project setup with async patterns |
| `vercel-cli` | Marketplace | ✅ Active | Deploy, manage, and develop projects on Vercel from the CLI |
| `vercel-react-best-practices` | Marketplace | ✅ Active | React/Next.js performance optimization (Vercel Engineering) |

### 🔒 Security & Auth

| Skill | Source | Status | Description |
|-------|--------|--------|-------------|
| `dependency-security-audit` | Locally owned | ✅ Active | Comprehensive CVE auditing for npm, pip, poetry |
| `django-auth-react-native` | Locally owned | ✅ Active | Complete Django auth for React Native (JWT, OTP, email) |
| `audit-trail` | Locally owned | ✅ Active | Add audit logging to API endpoints and database operations |
| `gdpr-compliance` | Locally owned | ✅ Active | GDPR consent management, DSARs, data retention |
| `multi-tenant-guard` | Locally owned | ✅ Active | Multi-tenant isolation audit and implementation |

### 🛠️ Developer Tools & Workflows

| Skill | Source | Status | Description |
|-------|--------|--------|-------------|
| `modern-terminal-setup` | Locally owned | ✅ Active | Modern macOS/Linux terminal (bat, eza, fzf, starship, lazygit) |
| `skill-creator` | Locally owned | ✅ Active | Guide for creating effective Claude Code skills |
| `find-skills` | Marketplace | ✅ Active | Discover and install agent skills |
| `mcp-builder` | Marketplace | ✅ Active | Create MCP servers for LLM tool integration |
| `receiving-code-review` | Marketplace | ✅ Active | Handle code review feedback with technical rigor |
| `django-celery-expert` | Marketplace | ✅ Active | Django + Celery async task processing |
| `qa-plan` | Locally owned | ✅ Active | Generate QA test plans from code changes with blast radius analysis and risk scoring |

### 💳 Payments & Integration

| Skill | Source | Status | Description |
|-------|--------|--------|-------------|
| `stripe-integration` | Marketplace | ✅ Active | Stripe payment processing integration |
| `stripe_processing` | Locally owned | ✅ Active | Stripe one-time payments + subscriptions with email |

### 🌐 SEO & Marketing

| Skill | Source | Status | Description |
|-------|--------|--------|-------------|
| `ai-seo` | Marketplace | ✅ Active | Optimize for AI search engines and LLM citation |
| `seo-audit` | Marketplace | ✅ Active | Diagnose and fix SEO issues |
| `programmatic-seo` | Marketplace | ✅ Active | SEO-driven pages at scale with templates |

### 📄 Data & Documents

| Skill | Source | Status | Description |
|-------|--------|--------|-------------|
| `pdf` | Marketplace | ✅ Active | PDF operations (read, merge, split, create, OCR) |
| `docx` | External | ✅ Active | Create, read, edit Word documents (.docx) with tables, headings, page numbers, images |
| `xlsx` | Marketplace | ✅ Active | Spreadsheet file operations (.xlsx/.csv) |
| `presentation-maker` | Locally owned | ✅ Active | Create presentations programmatically |
| `presentation_maker` | Locally owned | ✅ Active | Enhanced presentation formatter |
| `release-notes` | Marketplace | ✅ Active | Generate user-facing release notes from tickets |
| `tickets` | Locally owned | ✅ Active | Custom GitHub Issue Generator |

### 🎨 Frontend & UI

| Skill | Source | Status | Description |
|-------|--------|--------|-------------|
| `web-design-guidelines` | Marketplace | ✅ Active | Review UI against Web Interface Guidelines |
| `remotion-best-practices` | Marketplace | ✅ Active | Video creation in React with Remotion |
| `minimalist-ui-design` | Locally owned | ✅ Active | Minimalist UI design system (Thor Electric) |
| `modern-floating-ui-design` | Locally owned | ✅ Active | Modern floating UI design system |
| `chatbot_frontend` | Locally owned | ✅ Active | AI chatbot — enterprise website assistant |

### 🔧 Misc / Auth / Mobile

| Skill | Source | Status | Description |
|-------|--------|--------|-------------|
| `universal-auth` | Locally owned | ✅ Active | Authentication for mobile, web, SaaS, healthcare |
| `otp-verification` | Locally owned | ✅ Active | OTP verification implementation |
| `push-notifications-firebase` | Locally owned | ✅ Active | Firebase push notifications |
| `role-based-authentication` | Locally owned | ✅ Active | Role-based auth flow |
| `mailjet-email-service` | Locally owned | ✅ Active | Mailjet email service implementation |
| `imap-smtp-email` | External | ✅ Active | Read and send email via IMAP/SMTP — inbox, search, reply, compose, attachments |
| `video-download` | External | ✅ Active | Download videos from Douyin, Bilibili, YouTube, Instagram, Twitter/X, and 1700+ sites |
| `nano_banana` | Locally owned | ✅ Active | Image generation via Gemini 2.5 Flash |
| `gh_issue` | Locally owned | ✅ Active | GitHub issue management |
| `github-issue-gen` | Locally owned | ✅ Active | GitHub issue generator |
| `creating-user-flows` | Locally owned | ✅ Active | User flow diagrams (Mermaid) for Discovery phase — .md + .html deliverables |
| `project-primer` | Locally owned | ✅ Active | Pre-kickoff project primer for client engagements |
| `realtime-socket-react-query` | Locally owned | ✅ Active | Real-time React Query + WebSockets |

---

## PCS Skills (Project-Scoped, 7 total)

Lives in `skills/pcs/`. Installed flat into `~/.claude/skills/pcs-*`.

| Skill | Status | Description |
|-------|--------|-------------|
| `pcs-add-endpoint` | ✅ Active | Add CRUD endpoints to PCS microservices |
| `pcs-add-kafka-event` | ✅ Active | Add Kafka producer + consumer events |
| `pcs-integration-test` | ✅ Active | Write PCS integration/unit tests |
| `pcs-kong-route` | ✅ Active | Add/modify Kong Gateway routes |
| `pcs-migration` | ✅ Active | Create Alembic database migrations |
| `pcs-new-service` | ✅ Active | Scaffold a complete new PCS microservice |
| `pcs-pr-review` | ✅ Active | Review PRs for PCS architecture compliance |

---

## Maintenance

```bash
bm install          # install/update all symlinks
bm status           # check what's linked vs missing
bm registry sync    # detect externally installed skills
bm skill add <name> --project <p>   # add project-scoped skill
bm skill generalize <name>          # promote to general skill
```

Last updated: 2026-04-04
