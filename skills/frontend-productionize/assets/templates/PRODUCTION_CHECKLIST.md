# Frontend Production Checklist

Complete checklist for productionizing Next.js frontends with strict quality gates.

---

## Quick Installation

```bash
# 1. Install all dev dependencies at once
pnpm add -D \
  prettier \
  @eslint/eslintrc @eslint/js typescript-eslint eslint-config-next \
  vitest @vitejs/plugin-react jsdom @testing-library/react @testing-library/jest-dom \
  @playwright/test \
  openapi-typescript \
  nodemon

# 2. Install runtime dependencies
pnpm add openapi-fetch @tanstack/react-query

# 3. Copy config files from skill templates (or use contents below)
```

---

## Configuration Files

### 1. TypeScript Configuration (`tsconfig.json`)

**Why strict?** Catches bugs at compile time, not runtime. Every `any` is a potential crash.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "ES2022"],
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",

    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "useUnknownInCatchVariables": true,
    "alwaysStrict": true,

    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "noPropertyAccessFromIndexSignature": true,
    "forceConsistentCasingInFileNames": true,

    "noEmit": true,
    "allowSyntheticDefaultImports": true,
    "esModuleInterop": true,
    "skipLibCheck": true,

    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@/api/*": ["./src/api/*"],
      "@/components/*": ["./src/components/*"],
      "@/lib/*": ["./src/lib/*"]
    },

    "incremental": true,
    "plugins": [{ "name": "next" }]
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules", ".next", "out", "coverage", "playwright-report"]
}
```

### 2. Prettier Configuration (`prettier.json`)

**Consistent formatting = no diff noise in PRs.**

```json
{
  "$schema": "https://json.schemastore.org/prettierrc",
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "useTabs": false,
  "trailingComma": "es5",
  "bracketSpacing": true,
  "bracketSameLine": false,
  "arrowParens": "always",
  "printWidth": 100,
  "endOfLine": "lf",
  "quoteProps": "as-needed",
  "jsxSingleQuote": false,
  "proseWrap": "preserve",
  "htmlWhitespaceSensitivity": "css",
  "embeddedLanguageFormatting": "auto",
  "singleAttributePerLine": false,
  "overrides": [
    {
      "files": "*.json",
      "options": {
        "tabWidth": 2,
        "printWidth": 80,
        "trailingComma": "none"
      }
    },
    {
      "files": "*.md",
      "options": {
        "proseWrap": "always",
        "printWidth": 80
      }
    },
    {
      "files": ["*.yml", "*.yaml"],
      "options": {
        "tabWidth": 2,
        "singleQuote": false
      }
    }
  ]
}
```

### 3. ESLint Configuration (`eslint.config.mjs`)

**Zero warnings policy = no broken windows.**

```javascript
import { dirname } from 'path';
import { fileURLToPath } from 'url';
import { FlatCompat } from '@eslint/eslintrc';
import js from '@eslint/js';
import tseslint from 'typescript-eslint';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
  recommendedConfig: js.configs.recommended,
});

export default tseslint.config(
  {
    ignores: [
      '.next/**',
      'node_modules/**',
      'out/**',
      'coverage/**',
      'playwright-report/**',
      '*.config.js',
      '*.config.mjs',
      'src/api/schema.d.ts',
    ],
  },
  js.configs.recommended,
  ...tseslint.configs.strictTypeChecked,
  ...tseslint.configs.stylisticTypeChecked,
  ...compat.extends('next/core-web-vitals'),
  {
    languageOptions: {
      parserOptions: {
        project: true,
        tsconfigRootDir: __dirname,
      },
    },
  },
  {
    rules: {
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
      '@typescript-eslint/no-floating-promises': 'error',
      '@typescript-eslint/no-misused-promises': 'error',
      '@typescript-eslint/await-thenable': 'error',
      '@typescript-eslint/no-unsafe-assignment': 'error',
      '@typescript-eslint/no-unsafe-member-access': 'error',
      '@typescript-eslint/no-unsafe-call': 'error',
      '@typescript-eslint/no-unsafe-return': 'error',
      '@typescript-eslint/require-await': 'error',
      '@typescript-eslint/strict-boolean-expressions': 'error',
      '@typescript-eslint/switch-exhaustiveness-check': 'error',
      '@typescript-eslint/prefer-nullish-coalescing': 'error',
      '@typescript-eslint/prefer-optional-chain': 'error',
      '@typescript-eslint/no-unnecessary-condition': 'error',
      '@typescript-eslint/no-non-null-assertion': 'error',
      '@typescript-eslint/consistent-type-imports': ['error', { prefer: 'type-imports' }],
      'react/jsx-key': ['error', { checkFragmentShorthand: true }],
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'error',
      'no-console': ['warn', { allow: ['warn', 'error'] }],
      eqeqeq: ['error', 'always', { null: 'ignore' }],
      'prefer-const': 'error',
      'no-var': 'error',
    },
  },
  {
    files: ['**/*.test.ts', '**/*.test.tsx', '**/*.spec.ts'],
    rules: {
      '@typescript-eslint/no-unsafe-assignment': 'off',
      '@typescript-eslint/no-explicit-any': 'off',
    },
  }
);
```

### 4. Package Scripts (`package.json`)

**Key: `--max-warnings 0` and build error detection.**

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "build:strict": "NEXT_TELEMETRY_DISABLED=1 next build 2>&1 | tee build.log && ! grep -q 'error' build.log",
    "start": "next start",
    "lint": "next lint --max-warnings 0",
    "lint:fix": "next lint --fix",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "type-check": "tsc --noEmit",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage",
    "test:e2e": "playwright test",
    "validate": "pnpm run lint && pnpm run format:check && pnpm run type-check && pnpm run test",
    "ci": "pnpm run validate && pnpm run build:strict"
  }
}
```

### 5. Next.js Configuration (`next.config.ts`)

**Production hardening.**

```typescript
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // Fail builds on ESLint errors (not just warnings)
  eslint: {
    ignoreDuringBuilds: false,
    dirs: ['src', 'app'],
  },

  // Fail builds on TypeScript errors
  typescript: {
    ignoreBuildErrors: false,
  },

  // Enable strict mode for React
  reactStrictMode: true,

  // Production optimizations
  poweredByHeader: false,
  compress: true,

  // Security headers via middleware or vercel.json
  headers: async () => [
    {
      source: '/:path*',
      headers: [
        { key: 'X-DNS-Prefetch-Control', value: 'on' },
        { key: 'X-XSS-Protection', value: '1; mode=block' },
        { key: 'X-Frame-Options', value: 'SAMEORIGIN' },
        { key: 'X-Content-Type-Options', value: 'nosniff' },
        { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
      ],
    },
  ],

  // Image optimization
  images: {
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048],
    minimumCacheTTL: 60,
  },

  // Experimental features (Next.js 15+)
  experimental: {
    typedRoutes: true,
  },
};

export default nextConfig;
```

---

## Production Checklist

### Build Quality Gates

- [ ] **TypeScript strict mode enabled** (`strict: true` in tsconfig.json)
- [ ] **Build fails on TypeScript errors** (`ignoreBuildErrors: false` in next.config)
- [ ] **Build fails on ESLint errors** (`ignoreDuringBuilds: false` in next.config)
- [ ] **Zero warnings policy** (`--max-warnings 0` in lint script)
- [ ] **No `any` types** (`@typescript-eslint/no-explicit-any: 'error'`)
- [ ] **Unused vars are errors** (`noUnusedLocals` and `noUnusedParameters`)
- [ ] **Strict null checks** (`strictNullChecks: true`)
- [ ] **Unchecked index access** (`noUncheckedIndexedAccess: true`)

### Code Formatting

- [ ] **Prettier installed and configured**
- [ ] **Format check in CI** (`pnpm run format:check`)
- [ ] **Consistent JSON formatting** (2-space indent, no trailing commas)
- [ ] **EditorConfig for consistency** (`.editorconfig` file)

### Testing

- [ ] **Unit tests with Vitest**
- [ ] **E2E tests with Playwright**
- [ ] **Coverage thresholds set** (80%+ recommended)
- [ ] **Tests run in CI**
- [ ] **Tests must pass before merge**

### Security

- [ ] **Gitleaks for secret scanning**
- [ ] **npm audit in CI**
- [ ] **Security headers configured**
- [ ] **Environment variables documented** (`.env.example`)
- [ ] **No secrets in code**

### CI/CD Pipeline

- [ ] **Lint step (zero warnings)**
- [ ] **Format check step**
- [ ] **Type check step**
- [ ] **Unit test step**
- [ ] **Build step (with error detection)**
- [ ] **E2E test step**
- [ ] **Security scan step**
- [ ] **Artifacts uploaded (coverage, playwright report)**

### API Integration

- [ ] **OpenAPI types generated**
- [ ] **Schema committed to Git**
- [ ] **Type-safe API client**
- [ ] **Schema sync check in CI**

### Monitoring (Optional but Recommended)

- [ ] **Sentry error tracking**
- [ ] **Performance monitoring**
- [ ] **Log aggregation**

---

## EditorConfig (`.editorconfig`)

```ini
root = true

[*]
indent_style = space
indent_size = 2
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.md]
trim_trailing_whitespace = false

[Makefile]
indent_style = tab
```

---

## Git Hooks (`.husky/pre-commit`)

```bash
#!/usr/bin/env sh
. "$(dirname -- "$0")/_/husky.sh"

pnpm run lint
pnpm run format:check
pnpm run type-check
```

Install with:
```bash
pnpm add -D husky
pnpm exec husky init
```

---

## VSCode Settings (`.vscode/settings.json`)

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit",
    "source.organizeImports": "explicit"
  },
  "typescript.tsdk": "node_modules/typescript/lib",
  "typescript.enablePromptUseWorkspaceTsdk": true,
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[json]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

---

## Common Errors & Fixes

### "Type 'X' is not assignable to type 'Y'"
- Check if you need `strictNullChecks` handling
- Use `noUncheckedIndexedAccess` to catch array access issues

### "Parameter implicitly has an 'any' type"
- Add explicit type annotations
- Don't use `// @ts-ignore` - fix the type

### ESLint warnings blocking CI
- Fix all warnings (don't disable rules)
- If rule is wrong for your case, configure exception in eslint.config.mjs

### Prettier conflicts with ESLint
- Prettier handles formatting, ESLint handles logic
- Use `eslint-config-prettier` to disable conflicting rules

### Build succeeds locally but fails in CI
- CI uses `--frozen-lockfile` - commit your lockfile
- Check environment variables are set in CI secrets

---

## Quick Commands

```bash
# Run all checks (same as CI)
pnpm run ci

# Auto-fix what can be fixed
pnpm run lint:fix && pnpm run format

# Check everything without fixing
pnpm run validate

# Generate API types
pnpm run generate:api

# Run tests with coverage
pnpm run test:coverage
```
