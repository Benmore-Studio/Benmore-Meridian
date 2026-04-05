# Audit Dimensions

Each parallel exploration agent focuses on one dimension. Below are the default dimensions with specific audit instructions per agent.

## 1. Frontend UX

Audit scope: component structure, user flows, form validation, loading states, error handling, responsive design, empty states, micro-interactions.

Check for:
- Missing loading/skeleton states on async data
- Forms without inline validation or error messages
- Buttons without disabled states during submission
- Missing empty states (no data, no results, first-time user)
- Hardcoded strings that should be dynamic
- Inconsistent spacing, alignment, or typography
- Broken responsive layouts at common breakpoints (375px, 768px, 1024px, 1440px)
- Missing keyboard navigation or focus traps in modals
- Toast/notification patterns that are inconsistent

Output format per finding:
```
FILE: <path>
ISSUE: <one-line description>
SEVERITY: critical | high | medium | low
EFFORT: trivial (<30min) | small (1-2h) | medium (half day) | large (1+ day)
FIX: <concrete fix description>
```

## 2. Backend API

Audit scope: endpoint consistency, error responses, N+1 queries, missing indexes, serializer efficiency, permission gaps, rate limiting.

Check for:
- N+1 queries (loop accessing related objects without select_related/prefetch_related)
- Missing database indexes on frequently filtered/sorted fields
- Inconsistent error response shapes across endpoints
- Endpoints missing permission classes
- Serializers exposing internal fields (IDs, timestamps) unnecessarily
- Missing pagination on list endpoints
- Endpoints without rate limiting
- Unapplied or conflicting migrations

Output format: same as Frontend UX.

## 3. SEO & Metadata

Audit scope: meta tags, Open Graph, structured data, sitemap, robots.txt, canonical URLs, page titles, heading hierarchy.

Check for:
- Pages missing `<title>` or with generic titles
- Missing or incomplete Open Graph tags (og:title, og:description, og:image)
- Missing structured data (JSON-LD) for key pages
- No sitemap.xml or incomplete sitemap
- Missing or misconfigured robots.txt
- Heading hierarchy violations (skipping h2, multiple h1s)
- Missing canonical URLs on duplicate content
- Images without alt text
- Missing meta description on key landing pages

Output format: same as Frontend UX.

## 4. Accessibility (a11y)

Audit scope: WCAG 2.1 AA compliance, ARIA labels, color contrast, keyboard navigation, screen reader compatibility.

Check for:
- Interactive elements without ARIA labels
- Color contrast below 4.5:1 (text) or 3:1 (large text)
- Missing focus indicators on interactive elements
- Images without alt attributes
- Form inputs without associated labels
- Missing skip-to-content links
- Non-semantic HTML (div soup instead of nav, main, section, article)
- Dynamic content changes not announced to screen readers
- Click handlers on non-interactive elements (div, span) without role="button"

Output format: same as Frontend UX.

## 5. Conversion & Growth

Audit scope: CTAs, onboarding friction, checkout flow, trust signals, social proof, value proposition clarity.

Check for:
- Primary CTAs that are unclear, hidden, or use weak copy
- Checkout/signup flows with unnecessary steps
- Missing trust signals (testimonials, security badges, guarantees)
- Price presentation that lacks anchoring or comparison
- Missing or broken referral/sharing mechanisms
- Onboarding flows without progress indicators
- Abandon points with no recovery mechanism (exit intent, save draft)
- Missing urgency/scarcity signals where appropriate

Output format: same as Frontend UX.

## 6. Performance

Audit scope: bundle size, image optimization, lazy loading, caching, Core Web Vitals, unnecessary re-renders.

Check for:
- Large unoptimized images (no next/image, no srcset, no lazy loading)
- Bundle bloat (importing entire libraries for single functions)
- Missing code splitting on routes
- Components re-rendering unnecessarily (missing memo, useMemo, useCallback)
- API calls without caching (no TanStack Query staleTime, no SWR)
- Missing preconnect/preload for critical resources
- Synchronous operations blocking the main thread
- Missing compression (gzip/brotli) headers

Output format: same as Frontend UX.

## 7. Emails & Notifications

Audit scope: transactional email templates, notification triggers, copy quality, delivery reliability, opt-out compliance.

Check for:
- Email templates with hardcoded values instead of dynamic fields
- Missing notification triggers for key user events
- Notification copy that is generic or unclear
- Missing unsubscribe/opt-out mechanisms
- SMS messages exceeding segment limits (160 chars GSM-7)
- Missing notification preferences UI
- Error notifications that expose internal details
- Missing confirmation emails for critical actions (purchase, cancellation)

Output format: same as Frontend UX.

## Custom Dimensions

Add project-specific dimensions as needed. Common additions:
- **Security**: auth flows, CSRF, XSS, injection, secrets management
- **DevOps**: CI/CD, monitoring, logging, alerting
- **Data integrity**: validation, constraints, migration safety
- **Internationalization**: hardcoded strings, locale handling, RTL support
