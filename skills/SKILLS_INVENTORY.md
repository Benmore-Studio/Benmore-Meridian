# Skills Inventory

This document tracks all skills available in the `/Users/arkashjain/Desktop/guides/skills` directory.

## Custom Skills Included

These skills are directly included in this repository (not symlinked):

| Skill | Status | Added | Description |
|-------|--------|-------|-------------|
| `agent-organizer` | ✅ Active | 2026-02-09 | Expert multi-agent orchestration and team coordination |
| `brainstorm` | ✅ Active | 2026-02-09 | Interactive design refinement with iterative feedback |
| `commit` | ✅ Active | 2026-02-09 | Smart git commit workflow with context analysis |
| `debug` | ✅ Active | 2026-02-09 | Systematic debugging with root cause analysis |
| `execplan` | ✅ Active | 2026-02-09 | Create and manage detailed execution plans |
| `optimize` | ✅ Active | 2026-02-09 | Performance optimization with measurable improvements |
| `refactor` | ✅ Active | 2026-02-09 | Safe code refactoring with test preservation |
| `review-pr` | ✅ Active | 2026-02-09 | Comprehensive pull request review checklist |
| `security-audit` | ✅ Active | 2026-02-09 | Security vulnerability assessment and remediation |
| `write-tests` | ✅ Active | 2026-02-09 | Test-driven development with comprehensive coverage |

## Managed Skills (Not Included)

The following skills are managed via symlinks to the main superpowers repository and are **not included** in this skills directory:

- `api-design` - RESTful API design patterns
- `debug-cicd` - CI/CD pipeline debugging
- `deploy` - Deployment automation
- `docker-optimize` - Container optimization
- `docs` - Documentation generation
- `explore` - Codebase exploration
- `extract` - Code extraction and modularization
- `fix-types` - TypeScript type error resolution
- `migrate-db` - Database migration management
- `onboard` - New developer onboarding
- `perf-profile` - Performance profiling
- `quick-fix` - Fast bug fixes
- `research` - Technical research
- `scaffold` - Project scaffolding
- `schema-design` - Database schema design
- `setup-project` - New project setup
- `tech-debt` - Technical debt tracking
- `upgrade-deps` - Dependency upgrades

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
