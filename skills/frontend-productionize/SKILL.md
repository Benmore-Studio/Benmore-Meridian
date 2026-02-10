---
name: frontend-productionize
description: |
  Productionize Next.js frontends with Django backends using OpenAPI TypeScript codegen for type-safe API integration.

  Use when: (1) Starting development on Next.js project, (2) Before staging/production deployment, (3) Fresh Next.js + Django setup, (4) Quarterly health checks, (5) User asks to "productionize", "make production-ready", "audit", or "set up CI/CD" for Next.js.

  Performs audits, auto-fixes safe issues, reports complex issues. Generates Markdown report with checklist.

  Capabilities: OpenAPI TypeScript integration, code quality audits (ESLint/TS/Prettier), security scanning (secrets/Gitleaks), testing setup (Vitest/Playwright), CI/CD (GitHub Actions), monitoring (Sentry), production configs.
---

# Frontend Productionization Skill

Transform Next.js frontends into production-ready applications with type-safe Django backend integration.

## Overview

This skill audits and productionizes Next.js 14+ projects that connect to Django backends using DRF Spectacular for OpenAPI schema generation. It establishes production-ready foundations, generates comprehensive audit reports, and auto-fixes safe issues while flagging complex problems for manual review.

**Execution Model**: This skill provides **step-by-step prescriptive guidance**. Each phase includes explicit commands to execute, files to copy, and checks to perform. Follow the phases sequentially, executing each command and verifying results before proceeding.

## Prerequisites

Before running this skill, ensure:

- Project is a Next.js 13+ application
- `package.json` exists in current directory
- Django backend with DRF Spectacular is available (or will be during setup)
- Required tools installed: `node`, `npm`/`pnpm`/`yarn`, `curl`, `git`
- Optional tools for full functionality: `ripgrep` (`rg`), `jq`

## Execution Phases

### Phase 1: Project Detection

**Execute these checks in order:**

1. **Verify Next.js project**:
   ```bash
   test -f package.json && grep -q '"next"' package.json || echo "ERROR: Not a Next.js project"
   ```

2. **Detect package manager**:
   ```bash
   if [ -f pnpm-lock.yaml ]; then PKG_MANAGER="pnpm"
   elif [ -f yarn.lock ]; then PKG_MANAGER="yarn"
   else PKG_MANAGER="npm"; fi
   echo "Package manager: $PKG_MANAGER"
   ```

3. **Check Next.js version**:
   ```bash
   grep '"next"' package.json | head -1
   ```

4. **Identify router type**:
   ```bash
   if [ -d app ]; then echo "Router: App Router"
   elif [ -d pages ]; then echo "Router: Pages Router"
   else echo "Router: Unknown"; fi
   ```

5. **Check existing configs**:
   ```bash
   ls -la | grep -E "eslint|prettier|tsconfig"
   ```

**Store results** for use in later phases (package manager, router type, existing configs).

### Phase 2: Production Configuration Setup

**Step 1: Copy TypeScript configuration**

```bash
cp [skill-directory]/assets/templates/tsconfig.json ./tsconfig.json
```

**Key strict settings enforced:**
- `strict: true` - All strict type checking
- `noUnusedLocals: true` - Error on unused variables
- `noUncheckedIndexedAccess: true` - Array access returns `T | undefined`
- `noImplicitReturns: true` - All code paths must return

**Step 2: Copy Prettier configuration**

```bash
cp [skill-directory]/assets/templates/prettier.json ./.prettierrc.json
cp [skill-directory]/assets/templates/.prettierignore ./.prettierignore
```

**Step 3: Copy ESLint configuration**

```bash
cp [skill-directory]/assets/templates/eslint.config.mjs ./eslint.config.mjs
```

**Step 4: Copy Next.js configuration**

```bash
cp [skill-directory]/assets/templates/next.config.ts ./next.config.ts
```

**Critical settings that prevent ignored build errors:**
```typescript
eslint: { ignoreDuringBuilds: false }
typescript: { ignoreBuildErrors: false }
```

**Step 5: Copy EditorConfig**

```bash
cp [skill-directory]/assets/templates/.editorconfig ./.editorconfig
```

**Step 6: Install dev dependencies**

```bash
$PKG_MANAGER add -D prettier @eslint/eslintrc @eslint/js typescript-eslint eslint-config-next
```

**Step 7: Verify configurations work**

```bash
$PKG_MANAGER run lint
$PKG_MANAGER run format:check
$PKG_MANAGER run type-check
```

### Phase 3: Quality Audits (Parallel Execution)

**Execute the audit script:**

```bash
cd [skill-directory]/scripts
./run-quality-audits.sh .productionization
```

**Wait for completion**, then **read and analyze** the reports:

```bash
cat .productionization/eslint-report.txt
cat .productionization/typescript-report.txt
cat .productionization/security-report.txt
```

**Parse results** and categorize issues by severity:
- 🔴 **Critical**: Exposed secrets, critical vulnerabilities
- 🟡 **Warning**: ESLint errors, TypeScript errors
- 🔵 **Info**: Warnings, missing configs

**Store results** for final report generation.

### Phase 4: OpenAPI Integration ⭐ CRITICAL

**Step 1: Ask user for backend URL**

Use AskUserQuestion:
```
Question: "What's your Django backend URL?"
Options:
  - http://localhost:8000 (Development - Recommended)
  - https://staging.api.example.com (Staging)
  - https://api.example.com (Production)
  - Custom URL
```

**Step 2: Test backend connectivity**

```bash
cd [skill-directory]/scripts
./check-backend-connectivity.sh [BACKEND_URL] /api/schema/
```

If fails: Ask user to start backend or use cached schema.

**Step 3: Install dependencies**

```bash
$PKG_MANAGER add openapi-fetch
$PKG_MANAGER add -D openapi-typescript
```

**Step 4: Copy config template**

```bash
cp [skill-directory]/assets/templates/openapi-ts.config.ts ./openapi-ts.config.ts
```

**Step 5: Generate types**

```bash
cd [skill-directory]/scripts
API_SCHEMA_URL=[BACKEND_URL]/api/schema/ ./generate-api-types.sh
```

**Step 6: Copy API client files**

```bash
mkdir -p src/api src/lib
cp [skill-directory]/assets/api/client.ts src/api/
cp [skill-directory]/assets/api/hooks.ts src/api/
cp [skill-directory]/assets/api/query-client.ts src/lib/
cp [skill-directory]/assets/api/providers.tsx src/api/
```

**Step 7: Add npm scripts**

Read `assets/templates/package-scripts.json` and merge into project's `package.json`.

**Step 8: Create .env.example**

```bash
cp [skill-directory]/assets/templates/.env.example ./.env.example
```

**Step 9: Ask user about committing schema**

Use AskUserQuestion:
```
Question: "Commit src/api/schema.d.ts to Git?"
Options:
  - Yes (Recommended - enables CI/CD without backend access)
  - No (Generate locally only)
```

If yes: `git add src/api/schema.d.ts`

**Reference:** For detailed setup, read `references/openapi-integration.md`

### Phase 5: Testing Infrastructure

**Step 1: Install dependencies**

```bash
$PKG_MANAGER add -D vitest @vitejs/plugin-react jsdom @testing-library/react @testing-library/jest-dom
$PKG_MANAGER add -D @playwright/test
```

**Step 2: Copy config files**

```bash
cp [skill-directory]/assets/templates/vitest.config.ts ./
cp [skill-directory]/assets/templates/vitest.setup.ts ./
cp [skill-directory]/assets/templates/playwright.config.ts ./
```

**Step 3: Create test directories and examples**

```bash
mkdir -p src/__tests__ e2e
cp [skill-directory]/assets/testing/api-client.test.ts src/__tests__/
cp [skill-directory]/assets/testing/example.spec.ts e2e/
```

**Step 4: Install Playwright browsers**

```bash
npx playwright install
```

**Step 5: Verify test scripts in package.json**

Ensure these scripts exist (add if missing):
```json
{
  "test": "vitest",
  "test:ui": "vitest --ui",
  "test:e2e": "playwright test"
}
```

### Phase 6: Monitoring Setup (Optional)

**Step 1: Ask user about Sentry**

Use AskUserQuestion:
```
Question: "Set up Sentry error tracking?"
Options:
  - Yes (Recommended for production)
  - No (Skip for now)
```

**If YES:**

**Step 2: Run Sentry wizard**

```bash
npx @sentry/wizard@latest -i nextjs
```

**Step 3: Verify setup**

```bash
test -f sentry.client.config.ts && echo "Client config: ✓"
test -f sentry.server.config.ts && echo "Server config: ✓"
grep -q "SENTRY_DSN" .env.local && echo "DSN configured: ✓"
```

**Step 4: Create test error page** (if using App Router)

```bash
mkdir -p app/sentry-example-page
cat > app/sentry-example-page/page.tsx << 'EOF'
'use client';

export default function SentryTestPage() {
  return (
    <button onClick={() => { throw new Error('Sentry Test Error'); }}>
      Trigger Test Error
    </button>
  );
}
EOF
```

**If wizard fails:** Add "Configure Sentry manually" to manual steps checklist.

**If NO:** Add "Consider Sentry setup" to report recommendations.

### Phase 7: CI/CD Pipeline

**Step 1: Create GitHub Actions workflow**

```bash
mkdir -p .github/workflows
cp [skill-directory]/assets/templates/ci.yml .github/workflows/
```

**IMPORTANT:** Edit `.github/workflows/ci.yml` to match detected package manager:
- If npm: Change `pnpm` → `npm` and remove pnpm setup step
- If yarn: Change `pnpm` → `yarn` and use yarn setup

**Step 2: Copy Gitleaks config**

```bash
cp [skill-directory]/assets/templates/gitleaks.toml ./
cp [skill-directory]/assets/templates/.gitleaksignore ./
```

**Step 3: Copy Makefile**

```bash
cp [skill-directory]/assets/templates/Makefile ./
```

**Edit Makefile** to match package manager (replace `pnpm` with detected manager).

**Step 4: Copy security headers config**

```bash
cp [skill-directory]/assets/templates/vercel.json ./
```

**Step 5: Test CI locally**

```bash
make ci
```

If fails, note errors for manual steps section.

### Phase 8: Final Report Generation

**Step 1: Read report template**

```bash
cat [skill-directory]/assets/templates/report-template.md
```

**Step 2: Fill in template variables**

Replace these placeholders with actual values:
- `{{PROJECT_NAME}}`: From package.json
- `{{DATE}}`: Current date
- `{{DURATION}}`: Time from Phase 1 to Phase 7
- `{{NEXTJS_VERSION}}`: From Phase 1
- `{{PACKAGE_MANAGER}}`: From Phase 1
- `{{COMPLETED_ITEMS}}`: List of completed phases
- `{{CRITICAL_ISSUES}}`: From Phase 2 security audit
- `{{WARNING_ISSUES}}`: ESLint + TypeScript errors
- `{{INFO_ISSUES}}`: Warnings, missing configs
- `{{ESLINT_ERRORS}}`, `{{TS_ERRORS}}`: From Phase 2
- `{{SECRETS_COUNT}}`: From security audit
- `{{VULN_CRITICAL}}`, `{{VULN_HIGH}}`: From npm audit
- `{{MANUAL_CHECKLIST}}`: Collected manual steps
- `{{IMMEDIATE_ACTIONS}}`: Critical fixes needed
- `{{CONFIG_FILES}}`, `{{SOURCE_FILES}}`, `{{CICD_FILES}}`: Lists of created files

**Step 3: Write report**

```bash
Write filled template to: PRODUCTIONIZATION_REPORT.md
```

**Step 4: Display summary**

Show to user:
- Total issues found (by severity)
- Files created count
- Next steps
- Path to full report

## Usage

### Basic Usage

Navigate to your Next.js project directory and invoke this skill:

```bash
cd /path/to/nextjs-project
# Then run: /frontend-productionize
```

**The skill will guide you through 8 phases:**
1. ✅ Detect project structure and validate
2. ⚙️ Set up production configs (tsconfig, prettier, eslint, next.config)
3. 🔍 Run quality audits (ESLint, TypeScript, Security) in parallel
4. ⭐ Set up OpenAPI TypeScript integration (THE critical piece)
5. 🧪 Configure testing infrastructure (Vitest, Playwright)
6. 📊 Set up monitoring (Sentry - optional)
7. 🚀 Generate CI/CD pipeline (GitHub Actions, Gitleaks, Makefile)
8. 📋 Generate comprehensive report with actionable checklist

**Each phase** includes:
- Clear commands to execute
- Files to copy from skill templates
- Verification steps
- Error handling guidance

**Note**: Replace `[skill-directory]` in commands with the actual path to this skill's directory, or use Read tool to access templates directly.

### Advanced Usage

**Skip Sentry setup:**
```
When prompted "Set up Sentry?", choose "No"
```

**Use custom backend URL:**
```
When prompted "Backend URL?", enter your custom URL
```

**Review before applying:**
The skill auto-fixes safe issues (formatting, configs) but reports complex issues for review.

## Key Files Generated

### Configuration
- `tsconfig.json` - Strict TypeScript config (build errors enforced)
- `.prettierrc.json` - Prettier formatting rules (JSON included)
- `.prettierignore` - Files to skip formatting
- `eslint.config.mjs` - ESLint flat config (zero warnings policy)
- `next.config.ts` - Next.js config (build errors not ignored)
- `.editorconfig` - Editor consistency settings
- `openapi-ts.config.ts` - OpenAPI codegen config
- `vitest.config.ts` - Unit test config
- `playwright.config.ts` - E2E test config
- `gitleaks.toml` - Secret scanning rules
- `vercel.json` - Security headers
- `Makefile` - Dev commands
- `.env.example` - Environment template

### Source Code
- `src/api/schema.d.ts` - Generated TypeScript types (🤖 AUTO-GENERATED)
- `src/api/client.ts` - API client wrapper
- `src/api/hooks.ts` - React Query hooks templates
- `src/lib/query-client.ts` - React Query setup

### CI/CD
- `.github/workflows/ci.yml` - GitHub Actions pipeline

### Reports
- `PRODUCTIONIZATION_REPORT.md` - Audit results and checklist

## Error Handling

### Backend Unreachable
- Attempts to use cached `schema.d.ts` if exists
- Creates minimal mock schema as fallback
- Provides clear instructions to start backend

### ESLint Config Conflicts
- Merges new rules with existing (existing takes precedence)
- Shows diff before applying
- Preserves custom configurations

### TypeScript Strict Mode Issues
- Reports errors without enabling strict mode
- Recommends gradual migration approach
- Doesn't break existing working code

### Sentry Setup Fails
- Doesn't abort entire skill
- Adds manual setup guide to checklist
- Continues with remaining phases

## Reference Documents

**For detailed guides, see:**

1. **`assets/templates/PRODUCTION_CHECKLIST.md`**
   - Complete production checklist with checkboxes
   - Installation instructions for all dependencies
   - Full configuration file contents (copy-paste ready)
   - Common errors and fixes
   - Quick commands reference

2. **`references/openapi-integration.md`**
   - Comprehensive OpenAPI + TypeScript integration guide
   - Tool comparison (why openapi-typescript + openapi-fetch)
   - Step-by-step backend and frontend setup
   - Advanced topics (versioning, auth, environments)
   - Code examples and best practices

3. **`references/dev-checklist.md`**
   - Pre-flight checklist for developers
   - Required checks before deployment
   - Git workflow best practices
   - Deployment checklist

4. **`references/troubleshooting.md`**
   - Common issues and solutions
   - Backend connectivity problems
   - Type errors after schema updates
   - CI/CD failures
   - Runtime errors (CORS, Sentry, performance)

**When to read references:**
- Before running skill: Read `dev-checklist.md` to understand requirements
- After setup: Read `openapi-integration.md` for comprehensive API integration guide
- When errors occur: Read `troubleshooting.md` for solutions

## Scripts

### `scripts/check-backend-connectivity.sh`
Test Django backend reachability and schema endpoint availability.

Usage:
```bash
./scripts/check-backend-connectivity.sh http://localhost:8000 /api/schema/
```

### `scripts/generate-api-types.sh`
Generate TypeScript types from Django OpenAPI schema.

Usage:
```bash
API_SCHEMA_URL=http://localhost:8000/api/schema/ ./scripts/generate-api-types.sh
```

### `scripts/run-quality-audits.sh`
Run parallel quality audits (ESLint, TypeScript, Security).

Usage:
```bash
./scripts/run-quality-audits.sh .productionization
```

## Configuration Parameters

**Detected automatically:**
- Package manager (pnpm/yarn/npm)
- Next.js version and router type
- Existing tooling (ESLint, Prettier, testing)

**User-provided:**
- Backend URL (default: `http://localhost:8000`)
- Backend schema path (default: `/api/schema/`)
- Enable Sentry (default: yes)
- Commit schema types (default: yes)

## Success Criteria

✅ Skill succeeds when:
- All 8 phases complete without fatal errors
- `PRODUCTIONIZATION_REPORT.md` generated
- OpenAPI types generated successfully
- CI/CD pipeline configured
- No breaking changes to existing code

⚠️ Partial success when:
- Backend unreachable (uses cached/mock schema)
- Sentry setup fails (adds to manual checklist)
- Some quality audits find issues (reported, not blocking)

## Philosophy

**Audit > Auto-Fix:**
- Report issues with severity levels
- Auto-fix only safe changes (formatting, config generation)
- Let developers fix complex issues manually

**Production-Ready:**
- Full type safety end-to-end
- Security by default (headers, secret scanning)
- Testing infrastructure included
- CI/CD ready from day one

**Developer-Friendly:**
- Clear error messages
- Graceful degradation
- Comprehensive troubleshooting guide
- Educational insights in report

## Related Skills

- `django-productionize` - Productionize Django backend (future)
- `fullstack-productionize` - Coordinate both frontend + backend (future)

## Support

**Issues?**
- Check `references/troubleshooting.md` first
- Review `PRODUCTIONIZATION_REPORT.md` for specific issues
- Consult `references/openapi-integration.md` for API integration help
