# Security Policy

## Supported Versions

Security fixes target the latest released `benmore-bm` version and the current
`main` branch.

## Reporting a Vulnerability

Do not open a public issue for a suspected vulnerability.

Report security issues privately to the maintainers with:

- Affected skill or package path.
- Steps to reproduce.
- Impact and any known exploitability.
- Suggested mitigation, if known.

Maintainers will acknowledge reports as soon as practical, investigate, and
coordinate a fix or disclosure plan.

## Skill Safety

Skills in this repository are plain files and scripts. Before publishing or
installing externally sourced skills:

- Review `SKILL.md` instructions for unsafe behavior.
- Inspect bundled scripts before running them.
- Prefer dry-run commands where available.
- Use `bm uninstall --all` to remove bm-managed installed skills from the local
  agent skill directory without deleting source files.
