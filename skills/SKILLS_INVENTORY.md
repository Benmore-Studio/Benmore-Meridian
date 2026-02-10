# Skills Inventory

This document tracks all skills available in the `/Users/arkashjain/Desktop/guides/skills` directory.

## Production Skills

Production-grade skills for Django, Next.js, authentication, security, and developer tooling:

| Skill | Category | Status | Description |
|-------|----------|--------|-------------|
| `django-production` | 🚀 Production | ✅ Active | Production-ready Django setup with modern tooling (uv, ruff, pytest, Docker, drf-spectacular) |
| `frontend-productionize` | 🚀 Production | ✅ Active | Next.js + Django integration with OpenAPI TypeScript codegen for type-safe APIs |
| `dependency-security-audit` | 🔒 Security | ✅ Active | Comprehensive dependency security auditing and automated fixing (npm, pip, poetry) |
| `django-auth-react-native` | 🔒 Security | ✅ Active | Complete Django authentication system for React Native with JWT and OTP |
| `modern-terminal-setup` | 🛠️ DevTools | ✅ Active | Modern macOS/Linux terminal with CLI tools (bat, eza, fzf, starship, lazygit) |
| `skill-creator` | 🛠️ DevTools | ✅ Active | Guide for creating effective Claude Code skills |
| `gh_issue` | 📝 Utilities | ✅ Active | GitHub issue management and automation |
| `nano_banana` | 📝 Utilities | ✅ Active | Image generation using Gemini 2.5 Flash Image model |
| `stripe_processing` | 📝 Utilities | ✅ Active | Stripe payment processing with email notifications |
| `presentation_maker` | 📝 Utilities | ✅ Active | Create presentations programmatically |

## Superpowers Skills (External)

The following superpowers-style skills may be available if installed separately:

- `agent-organizer` - Expert multi-agent orchestration
- `brainstorm` - Interactive design refinement
- `commit` - Smart git commit workflow
- `debug` - Systematic debugging
- `execplan` - Create execution plans
- `optimize` - Performance optimization
- `refactor` - Safe code refactoring
- `review-pr` - PR review checklist
- `security-audit` - Security vulnerability assessment
- `write-tests` - Test-driven development

## Installation Notes

1. **Custom skills** in this directory can be used directly by Claude Code
2. **Managed skills** require symlink setup via the superpowers repository
3. To add managed skills: Clone superpowers and run their installation script
4. Skills are auto-detected by Claude Code when placed in this directory
5. Use `/skill-name` syntax to invoke any skill (e.g., `/agent-organizer`, `/refactor`)

## Maintenance

- **Adding new custom skills**: Place `.md` files directly in this directory
- **Updating skills**: Edit the corresponding `.md` file
- **Removing skills**: Delete the file and update this inventory
- **Version control**: All custom skills are tracked in git

---

Last updated: 2026-02-09
