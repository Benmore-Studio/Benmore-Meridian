---
name: dependency-security-audit
description: Comprehensive dependency security auditing and automated fixing for npm, pnpm, yarn, pip, poetry projects. Scans for CVEs, explains vulnerability business impact, applies safe fixes automatically, uses parallel Explore agents for deep codebase analysis, and generates detailed security reports. Use when (1) User asks to "audit security", "check for vulnerabilities", "fix Dependabot issues", "scan dependencies", "security audit"; (2) Before production deployment; (3) After major dependency updates; (4) Quarterly security reviews; (5) When Dependabot alerts are found; (6) User mentions CVEs, security patches, or outdated packages.
---

# Dependency Security Audit

Automated security auditing and fixing for dependency vulnerabilities across multiple package managers.

## Quick Start

### Audit Only
```bash
# Check GitHub Dependabot alerts
gh api repos/:owner/:repo/dependabot/alerts?state=open

# Or use package manager audits
pnpm audit  # for pnpm
npm audit   # for npm
pip-audit   # for Python
```

### Audit + Automatic Fix
The skill handles: scanning, prioritization, business impact explanation, automatic fixes, and PR creation.

## Core Workflow

### Phase 1: Discovery & Scanning

1. **Detect package manager**:
   - Look for `package.json`, `pnpm-lock.yaml`, `requirements.txt`
   - Identify: npm/pnpm/yarn/pip/poetry

2. **Scan vulnerabilities**:
   ```bash
   gh api repos/:owner/:repo/dependabot/alerts?state=open
   ```

3. **Use Explore agent** for deep analysis (when needed):
   ```
   Task(subagent_type="Explore",
        prompt="Find all locations where [vulnerable-package] is used.
                Search for imports, requires, transitive dependencies.
                Thoroughness: very thorough")
   ```

### Phase 2: Analysis & Prioritization

1. **Group by severity**: HIGH → MODERATE → LOW

2. **Explain each vulnerability** using `references/vulnerability-types.md`:
   - What it is
   - How it's exploited
   - Business impact
   - Real attack scenarios

### Phase 3: Automated Fixing

**Direct dependencies** (in package.json):
```bash
pnpm update next@15.5.10
npm install next@15.5.10
```

**Transitive dependencies** (via parent):

Option 1 - Upgrade parent:
```bash
pnpm info recharts versions
pnpm update recharts
```

Option 2 - Use overrides (if parent doesn't update):
```json
// package.json
{
  "pnpm": {
    "overrides": {
      "lodash": "^4.17.23"
    }
  }
}
```

**Verify fixes**:
```bash
pnpm install
pnpm why [package]  # Check version
pnpm build          # Test no breaking changes
gh api repos/:owner/:repo/dependabot/alerts?state=open  # Should show fewer alerts
```

### Phase 4: Documentation & PR

1. Generate report using `assets/report-template.md`

2. Create PR:
   ```bash
   git commit -m "fix: upgrade [package] to fix [CVE]"
   gh pr create --title "Security: Fix [N] vulnerabilities" \
                --body "[Detailed explanation]"
   ```

## Parallel Agent Strategy

For complex audits, use parallel agents:

```
Task(subagent_type="general-purpose",
     prompt="Fix all Next.js vulnerabilities (alerts #1-8)")

Task(subagent_type="general-purpose",
     prompt="Fix lodash via recharts override (alert #17)")

Task(subagent_type="Explore",
     prompt="Find direct usage of vulnerable functions: _.unset, _.omit")
```

## Common Patterns

### Pattern 1: Framework Major Version Upgrade
Example: Next.js 14 → 15
- Check breaking changes
- Upgrade: `pnpm update next@15.5.10`
- Update related packages (React)
- Test build

### Pattern 2: Transitive Dependency Override
Example: lodash via recharts
- Identify parent: `pnpm why lodash`
- Check parent updates: `pnpm info recharts versions`
- If no update: Add override to package.json
- Verify: `pnpm why lodash`

### Pattern 3: Multiple Related Vulnerabilities
Example: Next.js with 18 CVEs
- Group by package
- Single upgrade fixes all
- Test thoroughly
- Document all CVEs in PR

## Framework-Specific Guidance

### Next.js
Common: Image optimization DoS, Middleware SSRF, Server Components DoS
- Upgrade to latest stable
- Test `next build`
- Check dynamic route warnings (normal for auth pages)

### React
Common: Dangerous innerHTML (XSS), client-side routing (open redirects)
- Upgrade React + React-DOM together
- Check hook breaking changes

### Django
Common: Pickle deserialization, SQL injection, CSRF bypass
```bash
pip install --upgrade django
python manage.py check --deploy
```

### Python (pip/poetry)
Common: Deserialization attacks, command injection
```bash
pip-audit --fix  # or poetry update
```

## Resources

### scripts/scan_vulnerabilities.sh
Auto-detects package manager and scans for vulnerabilities across npm/pnpm/yarn/pip/poetry. Outputs JSON with all findings.

### references/vulnerability-types.md
Comprehensive guide to vulnerability types (DoS, SSRF, RCE, Prototype Pollution, XSS, etc.) with business impact explanations and real-world attack scenarios.

### assets/report-template.md
Security audit report template with sections for executive summary, vulnerability details, remediation steps, compliance impact, and recommendations.
