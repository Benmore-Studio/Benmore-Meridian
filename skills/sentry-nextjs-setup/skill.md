---
name: sentry-nextjs-setup
description: |
  Set up Sentry error monitoring for Next.js + Django projects deployed on Vercel.
  Covers full integration: SDK install, client/server/edge configs, instrumentation hooks,
  tunnel route, source maps, Vercel env vars, Django CORS, and Sentry project creation.

  Use when: (1) Adding Sentry to a Next.js project, (2) Setting up error monitoring for production,
  (3) Configuring Sentry with Vercel deployment, (4) User says "add Sentry", "error monitoring",
  "production monitoring", or "set up error tracking".
context: fork
---

# Sentry Next.js + Django Setup Skill

Integrate Sentry error monitoring into a Next.js App Router frontend with a Django REST backend, deployed on Vercel. Follows the official `@sentry/nextjs` v10+ patterns with ad-blocker bypass, PII masking, and source map uploads.

## Prerequisites

- Next.js 14+ with App Router
- `pnpm` / `npm` / `yarn` package manager
- Vercel CLI authenticated (`vercel whoami`)
- Sentry account with organization access
- sentry-cli installed (`sentry-cli --version`)

## Phase 1: Sentry Project Setup

### 1.1 Create Sentry Project

```bash
# Check if project exists
sentry-cli projects list --org <ORG_SLUG>

# If not, create via Sentry UI:
# https://sentry.io/organizations/<ORG_SLUG>/projects/new/
# Platform: Next.js
# Note the project slug and DSN
```

> **CLI cannot create projects** — the `sentry-cli projects` command only supports `list`. Create projects via the Sentry web UI or REST API.

### 1.2 Get Project DSN

```bash
# Get DSN via API (requires token with project:read scope)
curl -s https://sentry.io/api/0/projects/<ORG>/<PROJECT>/keys/ \
  -H "Authorization: Bearer <TOKEN>" | jq '.[0].dsn.public'
```

### 1.3 Configure sentry-cli Defaults

```bash
# ~/.sentryclirc
cat >> ~/.sentryclirc << 'EOF'
[defaults]
org=<ORG_SLUG>
project=<PROJECT_SLUG>
EOF
```

> If the existing token only has `org:ci` scope, generate a new one at https://sentry.io/settings/account/api/auth-tokens/ with `project:releases` + `org:read` + `project:read` scopes.

## Phase 2: Install SDK

```bash
# Install @sentry/nextjs
pnpm add @sentry/nextjs

# Approve build scripts (pnpm v10+)
# Add to package.json under pnpm:
```

```json
{
  "pnpm": {
    "onlyBuiltDependencies": [
      "@sentry/cli",
      "esbuild"
    ]
  }
}
```

```bash
# Regenerate lockfile
pnpm install --no-frozen-lockfile
```

## Phase 3: Create Config Files

### 3.1 Client Config — `instrumentation-client.ts`

> **File name matters.** In `@sentry/nextjs` v10+, the client config file is `instrumentation-client.ts` (NOT `sentry.client.config.ts`).

```typescript
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  tracesSampleRate: process.env.NODE_ENV === "development" ? 1.0 : 0.1,
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
  integrations: [
    Sentry.replayIntegration({
      maskAllText: true,
      blockAllMedia: true,
    }),
    Sentry.browserTracingIntegration(),
  ],
  environment: process.env.NODE_ENV,
});

// Capture App Router navigation transitions
Sentry.captureRouterTransitionStart();
```

**Key decisions:**
- `NEXT_PUBLIC_SENTRY_DSN` — must be public for client-side
- `maskAllText: true` — PIPEDA/GDPR safe, no PII in replays
- `replaysOnErrorSampleRate: 1.0` — capture 100% of error sessions
- `captureRouterTransitionStart()` — tracks App Router page navigations

### 3.2 Server Config — `sentry.server.config.ts`

```typescript
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  tracesSampleRate: process.env.NODE_ENV === "development" ? 1.0 : 0.1,
  includeLocalVariables: true,
  environment: process.env.NODE_ENV,
});
```

**Key decisions:**
- `SENTRY_DSN` — server-side only, not exposed to browser
- `includeLocalVariables: true` — captures variable values in stack frames (e.g., `user_id = 42`). Only safe server-side.

### 3.3 Edge Config — `sentry.edge.config.ts`

```typescript
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  tracesSampleRate: process.env.NODE_ENV === "development" ? 1.0 : 0.1,
  environment: process.env.NODE_ENV,
});
```

### 3.4 Instrumentation Hook — `instrumentation.ts`

```typescript
import * as Sentry from "@sentry/nextjs";

export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    await import("./sentry.server.config");
  }

  if (process.env.NEXT_RUNTIME === "edge") {
    await import("./sentry.edge.config");
  }
}

export const onRequestError = Sentry.captureRequestError;
```

> `onRequestError` requires `@sentry/nextjs` >= 8.28.0. It automatically captures unhandled errors in API routes and server actions.

### 3.5 Global Error Boundary — `app/global-error.tsx`

```tsx
"use client";

import * as Sentry from "@sentry/nextjs";
import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    Sentry.captureException(error);
  }, [error]);

  return (
    <html>
      <body>
        <div style={{ padding: "2rem", textAlign: "center" }}>
          <h2>Something went wrong</h2>
          <p style={{ color: "#666", marginTop: "0.5rem" }}>
            An unexpected error occurred. Our team has been notified.
          </p>
          <button
            onClick={reset}
            style={{
              marginTop: "1rem",
              padding: "0.5rem 1rem",
              borderRadius: "0.375rem",
              border: "1px solid #ccc",
              cursor: "pointer",
            }}
          >
            Try again
          </button>
        </div>
      </body>
    </html>
  );
}
```

## Phase 4: Wrap Next.js Config

Edit `next.config.mjs` (or `.js`/`.ts`):

```javascript
import { withSentryConfig } from "@sentry/nextjs";

const nextConfig = {
  // ... existing config
};

export default withSentryConfig(nextConfig, {
  org: "<ORG_SLUG>",
  project: "<PROJECT_SLUG>",
  silent: !process.env.CI,
  // Route events through your domain — bypasses ad blockers
  tunnelRoute: "/monitoring",
  // Upload source maps but don't serve them to browsers
  hideSourceMaps: true,
  // Include more files for better stack traces
  widenClientFileUpload: true,
  disableLogger: true,
});
```

**Why tunnel route?** Ad blockers block requests to `*.sentry.io`. The tunnel proxies events through `/monitoring` on your domain, capturing errors from 100% of users.

**Why hideSourceMaps?** Source maps upload to Sentry during build for readable stack traces, but aren't served to browsers (prevents source code exposure).

## Phase 5: Update Middleware

Exclude the Sentry tunnel route from auth middleware to prevent JWT checks from blocking event ingestion.

In `middleware.ts`, update the matcher:

```typescript
export const config = {
  matcher: [
    // Add "monitoring|" to the exclusion list
    "/((?!monitoring|_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
```

## Phase 6: Vercel Environment Variables

### 6.1 Required Variables

| Variable | Environments | Purpose |
|----------|-------------|---------|
| `SENTRY_DSN` | Production, Development | Server-side Sentry DSN |
| `NEXT_PUBLIC_SENTRY_DSN` | Production, Development | Client-side Sentry DSN (same value) |
| `SENTRY_AUTH_TOKEN` | Production, Development | Source map upload during build |

### 6.2 Set via CLI

```bash
# Add to production
vercel env add SENTRY_DSN production --value "<DSN>" --yes
vercel env add NEXT_PUBLIC_SENTRY_DSN production --value "<DSN>" --yes
vercel env add SENTRY_AUTH_TOKEN production --value "<TOKEN>" --yes

# Add to development
vercel env add SENTRY_DSN development --value "<DSN>" --yes
vercel env add NEXT_PUBLIC_SENTRY_DSN development --value "<DSN>" --yes
vercel env add SENTRY_AUTH_TOKEN development --value "<TOKEN>" --yes

# Preview requires interactive branch selection or dashboard
# Add via Vercel Dashboard: Settings > Environment Variables
```

> **Gotcha:** `vercel env add <name> preview` requires a git branch argument in non-interactive mode. Use the Vercel Dashboard for Preview env vars.

### 6.3 Generate Auth Token

Go to https://sentry.io/settings/account/api/auth-tokens/ and create a token with:
- `project:releases` — upload source maps
- `org:read` — read org info during build

## Phase 7: Vercel Security Headers

Create `vercel.json` with production security headers:

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": "nextjs",
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" },
        { "key": "Permissions-Policy", "value": "camera=(), microphone=(), geolocation=()" },
        { "key": "X-DNS-Prefetch-Control", "value": "on" },
        { "key": "Strict-Transport-Security", "value": "max-age=31536000; includeSubDomains; preload" }
      ]
    },
    {
      "source": "/monitoring(.*)",
      "headers": [
        { "key": "Access-Control-Allow-Origin", "value": "*" }
      ]
    }
  ],
  "functions": {
    "app/api/**/*.ts": {
      "maxDuration": 30
    }
  }
}
```

The CORS header on `/monitoring(.*)` allows the client Sentry SDK to POST events to the tunnel route.

## Phase 8: Django Backend CORS (if applicable)

If the frontend is deployed on a different domain than the backend, add CORS origins:

```python
# core/settings.py
CORS_ALLOWED_ORIGINS = [
    # ... existing origins
    "https://app.yourdomain.com",
    "https://your-project.vercel.app",
]

# Allow Vercel preview deployments
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://your-project.*\.vercel\.app$",
]
```

## Phase 9: Verify

### 9.1 Build Test

```bash
pnpm build
# Should complete without errors
# Source maps upload if SENTRY_AUTH_TOKEN is set
```

### 9.2 Runtime Test

```bash
pnpm dev
# Open browser console:
# Sentry.captureMessage("Test from local dev");
# Check Sentry dashboard for the event
```

### 9.3 Production Test

After Vercel deploy:
1. Open the deployed site
2. Open browser console
3. Run: `Sentry.captureMessage("Production test")`
4. Check Sentry → `propurti_frontend` → Issues

## Checklist

- [ ] Sentry project created (Next.js platform)
- [ ] `@sentry/nextjs` installed
- [ ] `instrumentation-client.ts` created (client config)
- [ ] `sentry.server.config.ts` created (server config)
- [ ] `sentry.edge.config.ts` created (edge config)
- [ ] `instrumentation.ts` created (registration hook + onRequestError)
- [ ] `app/global-error.tsx` created (root error boundary)
- [ ] `next.config.mjs` wrapped with `withSentryConfig`
- [ ] Middleware matcher excludes `/monitoring`
- [ ] `vercel.json` with security headers + Sentry CORS
- [ ] `SENTRY_DSN` set in Vercel (Production + Development)
- [ ] `NEXT_PUBLIC_SENTRY_DSN` set in Vercel (Production + Development)
- [ ] `SENTRY_AUTH_TOKEN` set in Vercel (Production + Development)
- [ ] `~/.sentryclirc` updated with org/project defaults
- [ ] `pnpm.onlyBuiltDependencies` includes `@sentry/cli` + `esbuild`
- [ ] Django CORS updated with production + preview origins
- [ ] Build passes locally
- [ ] Test event visible in Sentry dashboard

## Common Gotchas

| Issue | Cause | Fix |
|-------|-------|-----|
| Source maps not uploading | Missing `SENTRY_AUTH_TOKEN` in Vercel env | Add token with `project:releases` scope |
| Client errors not appearing | Ad blocker blocking `sentry.io` | Tunnel route handles this automatically |
| Middleware blocks `/monitoring` | Auth matcher catches all routes | Add `monitoring\|` to matcher exclusion |
| `sentry-cli projects create` fails | CLI doesn't support project creation | Use Sentry web UI or REST API |
| `pnpm install` warns about build scripts | `@sentry/cli` needs post-install | Add to `pnpm.onlyBuiltDependencies` |
| Preview deploys fail | Env vars only in Production | Add to Preview via Vercel Dashboard |
| `instrumentation.ts` not loaded | Next.js < 14.0.4 | Add `experimental.instrumentationHook: true` to next.config |
| Client config not loading | Wrong filename | Must be `instrumentation-client.ts` in v10+, NOT `sentry.client.config.ts` |

## Separate Frontend vs Backend Projects

Always create **separate Sentry projects** for frontend and backend:
- Different error audiences (UI crashes vs API 500s)
- Independent alert rules (page on-call for backend, batch frontend)
- Cleaner issue triage per team
- Different DSNs prevent cross-contamination

## Environment Variable Reference

| Variable | Where | Purpose |
|----------|-------|---------|
| `SENTRY_DSN` | Vercel env (server) | Server/edge-side event ingestion |
| `NEXT_PUBLIC_SENTRY_DSN` | Vercel env (public) | Client-side event ingestion |
| `SENTRY_AUTH_TOKEN` | Vercel env (build) | Source map upload authentication |
| `SENTRY_ORG` | Optional build env | Alternative to `org` in withSentryConfig |
| `SENTRY_PROJECT` | Optional build env | Alternative to `project` in withSentryConfig |
