# Troubleshooting Guide

Common issues and solutions for Next.js + Django frontend productionization.

## Table of Contents

- [Backend Connectivity Issues](#backend-connectivity-issues)
  - [Backend Unreachable During Type Generation](#backend-unreachable-during-type-generation)
  - [Schema Endpoint Returns 404](#schema-endpoint-returns-404)
  - [Authentication Required for Schema](#authentication-required-for-schema)
- [Type Errors](#type-errors)
  - [Type Errors After Schema Update](#type-errors-after-schema-update)
  - [Generated Types Have Errors](#generated-types-have-errors)
- [Build Errors](#build-errors)
  - [Build Fails Due to Missing Environment Variables](#build-fails-due-to-missing-environment-variables)
  - [Build Fails on Type Check](#build-fails-on-type-check)
- [CI/CD Issues](#cicd-issues)
  - [CI Fails on Schema Generation](#ci-fails-on-schema-generation)
  - [Gitleaks Blocks Commit](#gitleaks-blocks-commit)
  - [ESLint Errors Block CI](#eslint-errors-block-ci)
- [Runtime Errors](#runtime-errors)
  - [API Calls Return CORS Errors](#api-calls-return-cors-errors)
  - [Sentry Not Capturing Errors](#sentry-not-capturing-errors)
- [Performance Issues](#performance-issues)
  - [Slow Type Checking](#slow-type-checking)
  - [Large Bundle Size](#large-bundle-size)

## Backend Connectivity Issues

### Backend Unreachable During Type Generation

**Symptom:**
```bash
$ npm run generate:api
❌ Backend unreachable at http://localhost:8000/api/schema/
```

**Solutions:**

1. **Start Django backend:**
   ```bash
   cd backend
   python manage.py runserver
   ```

2. **Check backend URL is correct:**
   ```bash
   echo $API_SCHEMA_URL
   # Should match Django server address
   ```

3. **Use cached schema (if exists):**
   ```bash
   # Check if cached schema exists
   ls src/api/schema.d.ts
   # If yes, you can continue development
   ```

4. **Commit schema.d.ts to Git (recommended):**
   ```bash
   git add src/api/schema.d.ts
   git commit -m "chore: update API schema"
   # Now CI/CD doesn't need backend access
   ```

### Schema Endpoint Returns 404

**Symptom:**
```bash
$ curl http://localhost:8000/api/schema/
404 Not Found
```

**Solutions:**

1. **Install drf-spectacular:**
   ```bash
   pip install drf-spectacular
   ```

2. **Add to INSTALLED_APPS:**
   ```python
   # backend/settings.py
   INSTALLED_APPS = [
       # ...
       'drf_spectacular',
   ]
   ```

3. **Configure schema URL:**
   ```python
   # backend/urls.py
   from drf_spectacular.views import SpectacularAPIView

   urlpatterns = [
       path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
   ]
   ```

4. **Restart Django server:**
   ```bash
   python manage.py runserver
   ```

### Authentication Required for Schema

**Symptom:**
```bash
$ npm run generate:api
❌ 401 Unauthorized
```

**Solutions:**

1. **Create service account token:**
   ```python
   # Django admin or shell
   from rest_framework.authtoken.models import Token
   token = Token.objects.create(user=service_account_user)
   print(token.key)
   ```

2. **Add token to environment:**
   ```bash
   # .env.local
   API_SCHEMA_TOKEN=your_service_account_token_here
   ```

3. **Update codegen config:**
   ```typescript
   // openapi-ts.config.ts
   export default defineConfig({
     input: process.env.API_SCHEMA_URL,
     auth: `Bearer ${process.env.API_SCHEMA_TOKEN}`,
     output: './src/api/schema.d.ts',
   });
   ```

## Type Errors

### Type Errors After Schema Update

**Symptom:**
```typescript
// src/components/UserList.tsx
const { data } = useUsers();
// Error: Property 'username' does not exist on type 'User'
```

**Cause:** Backend renamed field from `username` to `user_name`.

**Solutions:**

1. **Check schema diff:**
   ```bash
   git diff src/api/schema.d.ts
   ```

2. **Update component to match new types:**
   ```typescript
   // Change from:
   <div>{user.username}</div>

   // To:
   <div>{user.user_name}</div>
   ```

3. **Ask backend team to revert if breaking change:**
   ```bash
   # Backend should version API or use field aliases
   # backend/serializers.py
   class UserSerializer(serializers.ModelSerializer):
       username = serializers.CharField(source='user_name')  # Alias
   ```

### Generated Types Have Errors

**Symptom:**
```bash
$ npm run type-check
src/api/schema.d.ts:42:5 - error TS1005: ';' expected.
```

**Solutions:**

1. **Regenerate types:**
   ```bash
   npm run generate:api
   ```

2. **Check openapi-typescript version:**
   ```bash
   npm list openapi-typescript
   # Should be v7.0.0 or later
   npm install --save-dev openapi-typescript@latest
   ```

3. **Check backend schema is valid:**
   ```bash
   curl http://localhost:8000/api/schema/ | python -m json.tool
   # Should be valid JSON without errors
   ```

## Build Errors

### Build Fails Due to Missing Environment Variables

**Symptom:**
```bash
$ npm run build
Error: NEXT_PUBLIC_API_BASE_URL is not defined
```

**Solutions:**

1. **Add to `.env.production`:**
   ```bash
   NEXT_PUBLIC_API_BASE_URL=https://api.production.com
   ```

2. **Set in Vercel/hosting dashboard:**
   - Go to Project Settings → Environment Variables
   - Add `NEXT_PUBLIC_API_BASE_URL`
   - Redeploy

3. **Provide default in code:**
   ```typescript
   // src/api/client.ts
   const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
   ```

### Build Fails on Type Check

**Symptom:**
```bash
$ npm run build
Type error: src/app/page.tsx:12:5 - error TS2741
```

**Solutions:**

1. **Fix type errors locally first:**
   ```bash
   npm run type-check
   # Fix all errors before building
   ```

2. **Temporary workaround (NOT recommended for production):**
   ```javascript
   // next.config.js
   module.exports = {
     typescript: {
       ignoreBuildErrors: process.env.VERCEL_ENV === 'preview', // Only for previews
     },
   };
   ```

## CI/CD Issues

### CI Fails on Schema Generation

**Symptom:**
```bash
# GitHub Actions
❌ Backend unreachable during npm run generate:api
```

**Solutions:**

1. **Commit `schema.d.ts` to Git (recommended):**
   ```bash
   git add src/api/schema.d.ts
   git commit -m "chore: commit generated API types for CI"
   ```

2. **Use cached schema in CI:**
   ```yaml
   # .github/workflows/ci.yml
   - name: Generate API types
     run: npm run generate:api
     continue-on-error: true  # Don't fail if backend unreachable
   ```

3. **Run backend in CI (advanced):**
   ```yaml
   # .github/workflows/ci.yml
   services:
     backend:
       image: your-django-backend:latest
       ports:
         - 8000:8000
   ```

### Gitleaks Blocks Commit

**Symptom:**
```bash
$ git commit -m "add feature"
❌ Gitleaks detected: potential secret in file X
```

**Solutions:**

1. **Remove actual secrets:**
   ```bash
   # Remove hardcoded API key
   # Replace with environment variable
   ```

2. **Add false positive to .gitleaksignore:**
   ```
   # .gitleaksignore
   tests/fixtures/fake-api-key.ts:*
   ```

3. **Whitelist test patterns:**
   ```toml
   # gitleaks.toml
   [allowlist]
   regexes = [
     '''test_[a-zA-Z0-9_]+''',
     '''mock_[a-zA-Z0-9_]+''',
   ]
   ```

### ESLint Errors Block CI

**Symptom:**
```bash
$ npm run lint
✖ 23 problems (12 errors, 11 warnings)
```

**Solutions:**

1. **Auto-fix safe issues:**
   ```bash
   npm run lint -- --fix
   ```

2. **Fix remaining errors manually:**
   ```bash
   npm run lint
   # Address each error one by one
   ```

3. **Temporarily downgrade errors to warnings (NOT recommended):**
   ```json
   // .eslintrc.json
   {
     "rules": {
       "no-console": "warn"  // Changed from "error"
     }
   }
   ```

## Runtime Errors

### API Calls Return CORS Errors

**Symptom:**
```
Access to fetch at 'http://localhost:8000/api/users/' has been blocked by CORS policy
```

**Solutions:**

1. **Configure Django CORS:**
   ```bash
   pip install django-cors-headers
   ```

   ```python
   # backend/settings.py
   INSTALLED_APPS = [
       'corsheaders',
       # ...
   ]

   MIDDLEWARE = [
       'corsheaders.middleware.CorsMiddleware',
       # ...
   ]

   CORS_ALLOWED_ORIGINS = [
       'http://localhost:3000',  # Next.js dev server
   ]
   ```

### Sentry Not Capturing Errors

**Symptom:** Errors not appearing in Sentry dashboard.

**Solutions:**

1. **Check DSN is set:**
   ```bash
   echo $NEXT_PUBLIC_SENTRY_DSN
   # Should show your Sentry DSN
   ```

2. **Verify Sentry is initialized:**
   ```typescript
   // Check sentry.client.config.ts exists
   // and is imported in app layout
   ```

3. **Test with manual error:**
   ```typescript
   // Add to a page
   <button onClick={() => { throw new Error('Test Sentry'); }}>
     Test Error
   </button>
   ```

4. **Check environment filter:**
   ```typescript
   // sentry.client.config.ts
   Sentry.init({
     dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
     environment: process.env.NODE_ENV,
     // Make sure you want this environment
   });
   ```

## Performance Issues

### Slow Type Checking

**Symptom:** `npm run type-check` takes >60 seconds.

**Solutions:**

1. **Exclude `node_modules` from tsconfig:**
   ```json
   // tsconfig.json
   {
     "exclude": ["node_modules", ".next", "out"]
   }
   ```

2. **Use incremental builds:**
   ```json
   // tsconfig.json
   {
     "compilerOptions": {
       "incremental": true
     }
   }
   ```

3. **Split large type files:**
   ```bash
   # If schema.d.ts is huge (>10MB), consider:
   # - Backend: Split API into multiple apps
   # - Frontend: Generate types per module
   ```

### Large Bundle Size

**Symptom:** Next.js build shows bundle >500KB.

**Solutions:**

1. **Analyze bundle:**
   ```bash
   npm install --save-dev @next/bundle-analyzer
   ```

   ```javascript
   // next.config.js
   const withBundleAnalyzer = require('@next/bundle-analyzer')({
     enabled: process.env.ANALYZE === 'true',
   });
   module.exports = withBundleAnalyzer({});
   ```

   ```bash
   ANALYZE=true npm run build
   ```

2. **Use dynamic imports:**
   ```typescript
   // Instead of:
   import HeavyComponent from './HeavyComponent';

   // Use:
   const HeavyComponent = dynamic(() => import('./HeavyComponent'));
   ```

3. **Check for duplicate dependencies:**
   ```bash
   npm dedupe
   ```

## Need More Help?

- **OpenAPI Integration**: See [openapi-integration.md](./openapi-integration.md)
- **Development Checklist**: See [dev-checklist.md](./dev-checklist.md)
- **Report Issues**: [GitHub Issues](https://github.com/your-org/your-project/issues)
