# Frontend Productionization Checklist

This checklist ensures your Next.js frontend is production-ready before deployment. Use this before starting new features, deploying to staging/production, or during quarterly health checks.

## ✅ Required Before Deployment

### 1. Code Quality

- [ ] **ESLint**: All errors fixed, warnings reviewed
  ```bash
  npm run lint
  ```
- [ ] **TypeScript**: No type errors
  ```bash
  npm run type-check
  ```
- [ ] **Prettier**: Code formatted consistently
  ```bash
  npx prettier --check .
  ```

### 2. API Integration

- [ ] **OpenAPI Types Generated**: Types are up-to-date with backend schema
  ```bash
  npm run generate:api
  ```
- [ ] **Backend Connectivity**: Backend is reachable from frontend
  ```bash
  curl -sf $NEXT_PUBLIC_API_BASE_URL/api/schema/
  ```
- [ ] **Schema Committed**: `src/api/schema.d.ts` committed to Git (for CI/CD)
- [ ] **API Client Configured**: Auth tokens, base URL, error handling set up
- [ ] **React Query Setup**: Query client configured with appropriate cache/retry settings

### 3. Testing

- [ ] **Unit Tests**: Critical components and utilities have tests
  ```bash
  npm test
  ```
- [ ] **E2E Tests**: Happy paths and critical flows covered
  ```bash
  npm run test:e2e
  ```
- [ ] **Test Coverage**: Minimum 70% on critical paths (auth, payments, data processing)
  ```bash
  npm run test -- --coverage
  ```

### 4. Security

- [ ] **No Exposed Secrets**: No API keys, tokens, or passwords in client code
  ```bash
  rg -i "PRIVATE_KEY|SECRET_KEY|PASSWORD|API_KEY" src/
  ```
- [ ] **Environment Variables**: All secrets in `.env.local`, not committed to Git
- [ ] **Gitleaks Configured**: `.gitleaks.toml` and `.gitleaksignore` set up
- [ ] **Security Headers**: `vercel.json` configured with X-Frame-Options, CSP, etc.
- [ ] **Dependency Audit**: No critical vulnerabilities
  ```bash
  npm audit --audit-level=critical
  ```

### 5. Build & Performance

- [ ] **Production Build Succeeds**: No build errors
  ```bash
  npm run build
  ```
- [ ] **Bundle Size**: Within budget (check Next.js build output)
- [ ] **Image Optimization**: Using Next.js `<Image>` component, not `<img>`
- [ ] **No Console Logs**: Remove debug logs from production code

### 6. Monitoring & Error Tracking

- [ ] **Sentry Configured**: DSN set in environment variables
- [ ] **Test Error Reporting**: Trigger test error, verify in Sentry dashboard
- [ ] **Environment Detection**: Sentry distinguishes dev/staging/prod

### 7. CI/CD

- [ ] **GitHub Actions Workflow**: `.github/workflows/ci.yml` exists and passes
- [ ] **Required Secrets Set**: `NEXT_PUBLIC_API_BASE_URL`, `SENTRY_AUTH_TOKEN`, etc.
- [ ] **Makefile**: Local `make ci` passes

### 8. Documentation

- [ ] **Environment Template**: `.env.example` lists all required variables
- [ ] **README Updated**: Setup instructions current (if project has README)
- [ ] **API Documentation**: Endpoints documented or Swagger UI available

## ⚠️ Strongly Recommended

- [ ] **Error Boundaries**: Global and route-level error.tsx files
- [ ] **Loading States**: Skeleton loaders or spinners for async operations
- [ ] **Accessibility**: ARIA labels, keyboard navigation, color contrast
- [ ] **Mobile Responsive**: Test on mobile devices or browser DevTools
- [ ] **SEO**: Meta tags, Open Graph, structured data (next-seo)

## 🎯 Optional (Nice to Have)

- [ ] **Lighthouse Score**: 90+ on Performance, Accessibility, Best Practices
- [ ] **Storybook**: Component library documentation (if using design system)
- [ ] **Bundle Analyzer**: Check for duplicate dependencies or bloat
- [ ] **Feature Flags**: LaunchDarkly or Vercel Edge Config for gradual rollouts
- [ ] **Analytics**: PostHog, GA4, or Mixpanel integrated
- [ ] **Rate Limiting**: API routes protected from abuse

## 📋 Deployment Checklist

Before deploying to production:

1. [ ] Run full CI pipeline locally: `make ci`
2. [ ] Deploy to staging first, smoke test
3. [ ] Verify environment variables in Vercel/hosting dashboard
4. [ ] Check Sentry for errors after staging deployment
5. [ ] Test OpenAPI client with live backend
6. [ ] Monitor logs and metrics for 24 hours post-deployment

## Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature

# Make changes, ensure checklist passes
make ci

# Commit with descriptive message
git commit -m "feat: add user authentication"

# Push and create PR
git push origin feature/your-feature
gh pr create --title "Add user authentication"
```

## Need Help?

- **Backend unreachable**: See [troubleshooting.md](./troubleshooting.md#backend-unreachable)
- **Type errors after schema update**: See [troubleshooting.md](./troubleshooting.md#type-errors)
- **CI/CD failing**: See [troubleshooting.md](./troubleshooting.md#cicd-failures)
