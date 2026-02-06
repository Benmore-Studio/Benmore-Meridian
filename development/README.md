# Development Guides

Master the full development workflow — from meeting notes to CI/CD automation to AI-powered tools.

---

## 📋 Guide Contents

**[00-developer-workflow.md](./00-developer-workflow.md)**

End-to-end developer workflow:
- ✅ Accessing client meeting transcripts
- ✅ Extracting requirements with Gemini
- ✅ Building implementation plans with Claude Code
- ✅ Executing plans with skills & subagents

**[01-pr-review-workflow.md](./01-pr-review-workflow.md)**

PR review & project management:
- ✅ GitHub integration setup
- ✅ Project management with GitHub Projects
- ✅ AI-assisted PR review process
- ✅ Automated checks and verification

**[02-ci-cd-bots-setup.md](./02-ci-cd-bots-setup.md)**

CI/CD bots & automated checks:
- ✅ Sentry Bot — runtime error tracking
- ✅ Vercel Bot — preview deployments
- ✅ GitHub Actions — lints, formatting, tests
- ✅ Claude Bot — AI-powered code review (`/install-github-app`)

**[03-claude-code-ecosystem.md](./03-claude-code-ecosystem.md)**

Claude Code tools & ecosystem:
- ✅ MCP Servers (Context7, Hyperbrowser, Agent Browser)
- ✅ Plugins & Marketplaces (Superpowers, Double Shot Latte)
- ✅ Skills (skills.sh, Superpowers skills, custom skills)
- ✅ Subagents & Agent Teams

---

## 🎯 Workflow Phases

### Phase 1: Initial Setup
- Install and configure Claude GitHub app
- Add team members to GitHub organization
- Setup Sentry for error monitoring

### Phase 2: Project Management
- Create GitHub Projects to visualize roadmap
- Assign projects to repositories
- Create issues and milestones
- Link tickets to development work

### Phase 3: PR Review Workflow
- Use Claude for hyper-critical analysis
- Review code changes in detail
- Verify acceptance criteria
- Post feedback and comments

### Phase 4: Final Checks
- Verify GitHub Actions (CI/CD)
- Check Vercel deployment status
- Confirm Sentry integration
- Complete automated review

---

## 📸 Included Assets

Visual guides for each phase:
- `install_claude_github.png` - GitHub app installation
- `Github_project.png` - Creating GitHub Projects
- `add_project.png` - Assigning projects to repos
- `link_tickets.png` - Linking tickets to PRs
- `prompt.png` - Claude analysis strategy
- `claude result.png` - Review analysis results
- `pr_review.png` - PR feedback process

---

## ✅ PR Review Checklist

### Setup Phase
- [ ] GitHub App installed and configured?
- [ ] All developers added to GitHub?
- [ ] Sentry onboarding complete?

### Project Management
- [ ] GitHub Project created?
- [ ] Project assigned to repository?
- [ ] Issues and milestones created?
- [ ] Timeline updated?
- [ ] Tickets linked to project?

### PR Review
- [ ] AI analysis completed?
- [ ] Code changes verified?
- [ ] Feedback posted on PR?
- [ ] GitHub Actions passed?
- [ ] Vercel deployment successful?
- [ ] Sentry checks green?
- [ ] Claude review passed?

---

## 🔗 Related Resources

- **GitHub Documentation** - https://docs.github.com/
- **GitHub Projects** - https://github.com/features/project-management
- **Claude for GitHub** - https://github.com/apps/claude
- **Sentry Integration** - https://sentry.io/
- **Vercel Deployment** - https://vercel.com/

---

## 💡 Key Principles

1. **Automation First** - Let tools handle repetitive checks
2. **Human Review** - Focus human effort on critical decisions
3. **Clear Feedback** - Provide actionable comments
4. **Verification** - Check acceptance criteria explicitly
5. **Transparency** - Link tickets and document decisions

---

**New developer?** Start here:
1. [Developer Workflow](./00-developer-workflow.md) — How we build features
2. [CI/CD Bots](./02-ci-cd-bots-setup.md) — Set up your repo's automated checks
3. [Claude Code Ecosystem](./03-claude-code-ecosystem.md) — Set up your AI tools
4. [PR Review Workflow](./01-pr-review-workflow.md) — How to review PRs
