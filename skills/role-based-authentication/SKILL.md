---
name: role-based-authentication
description: Authentication Flow in House Service Pass Web-Frontend
---

# Authentication Flow in House Service Pass Web-Frontend

This skill documents the complete authentication flow in the House Service Pass web-frontend application, including login, logout, token refresh, route protection, and state management.

## Overview

The authentication system uses:
- **React Context API** for state management (`AuthProvider` + `useAuth()` hook)
- **HttpOnly Cookies** for secure token storage (backend-set, not accessible to JavaScript)
- **Automatic Token Refresh** via axios interceptor
- **localStorage** for instant UI on page reload (user profile only, not tokens)
- **Role-Based Route Protection** (three tiers: admin, provider, customer)

**Key Insight:** Tokens are always in HttpOnly cookies (XSS-safe). User profile is cached in localStorage for instant UI. All requests automatically include cookies via `credentials: "include"`.

---

## 1. Login Flow (Complete End-to-End)

### User Journey:
```
1. User navigates to /auth/admin or /auth/provider
2. AuthLoginForm component renders with email/password fields
3. User enters credentials and clicks "Sign In"
4. Form submits → handleSubmit() calls useAuth().signIn()
5. signIn() calls appropriate backend endpoint:
   - POST /api/accounts/admin/login/ (for admin)
   - POST /api/accounts/provider/login/ (for provider)
6. Backend validates credentials → sets HttpOnly cookies:
   - access_token (short-lived)
   - refresh_token (long-lived)
7. signIn() calls getCurrentUser() → GET /accounts/me/
8. Backend reads cookies, returns user profile
9. setUser(user) stores in React state AND localStorage
10. Router.push() redirects to appropriate dashboard:
    - /admin (for admins)
    - /provider (for providers)
11. Route guards verify user has permission to access dashboard
12. Dashboard renders successfully
```

### Code Example (AuthLoginForm):
```typescript
// File: /web-frontend/components/auth-login-form.tsx
const handleLogin = async () => {
  try {
    // Call auth context function
    await signIn(email, password, userRole)

    // AuthContext handles:
    // 1. Login API call → POST /api/accounts/{role}/login/
    // 2. Backend sets HttpOnly cookies
    // 3. Fetch user → GET /api/accounts/me/
    // 4. Store in state and localStorage
    // 5. Redirect to dashboard (handled by router)
  } catch (error) {
    toast.error("Invalid credentials. Please try again.")
  }
}
```

### Code Example (Auth Context signIn):
```typescript
// File: /web-frontend/lib/contexts/auth-context.tsx (lines 149-163)
const signIn = async (email: string, password: string, role: "admin" | "provider") => {
  // 1. Call login endpoint based on role
  const loginFn = role === "admin" ? adminLogin : providerLogin
  await loginFn(email, password)
  // Backend response: { access_token, refresh_token } in HttpOnly cookies

  // 2. Fetch current user
  const user = await getCurrentUser()
  // Backend: reads cookies, validates, returns user profile

  // 3. Store in state and localStorage
  setUser(user)

  // 4. Redirect to dashboard
  const redirectPath = getRedirectPath(role)
  router.push(redirectPath)
}
```

---

## 2. Logout Flow

### User Journey:
```
1. User clicks logout button in DemoNav
2. handleLogout() called
3. useAuth().logout() executes:
   - POST /api/accounts/logout/ (backend clears its session)
   - setUser(null) clears React state
   - localStorage.removeItem("user") clears cached profile
4. Router redirects based on current path:
   - Was in /admin → go to /auth/admin
   - Was in /provider → go to /auth/provider
   - Otherwise → go to /
5. User is now unauthenticated
```

### Code Example:
```typescript
// File: /web-frontend/lib/contexts/auth-context.tsx (lines 166-185)
const logout = async () => {
  try {
    await apiService.post("/accounts/logout/", {})
  } catch (error) {
    logger.warn("Logout API failed (user still logged out locally)")
  } finally {
    // Clear local state regardless of API result
    setUser(null)

    // Redirect based on previous path
    if (pathname.startsWith("/admin")) {
      router.push("/auth/admin")
    } else if (pathname.startsWith("/provider")) {
      router.push("/auth/provider")
    } else {
      router.push("/")
    }
  }
}
```

---

## 3. Token Refresh (Automatic)

### How It Works:

When user's `access_token` expires, axios interceptor handles refresh automatically:

```
1. User makes API request with expired access_token
2. Backend responds with HTTP 401 Unauthorized
3. Axios interceptor catches 401 (lines 13-63 in axios.ts)
4. Interceptor checks if on auth page (/auth/admin or /auth/provider)
   - If on auth page: reject error (let form handle it)
   - If on protected page: attempt refresh
5. Refresh endpoint: POST /api/accounts/refresh/
6. Backend validates refresh_token (in cookie), issues new access_token
7. Backend sets new access_token in cookie
8. Interceptor retries original request with new token
9. If successful: user never notices token expiry
10. If refresh fails: user redirected to login
```

### Code Example (Axios Interceptor):
```typescript
// File: /web-frontend/lib/api/axios.ts (lines 13-63)
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    // On 401, attempt one token refresh
    if (error.response?.status === 401) {
      const currentPath = window.location.pathname

      // Don't redirect on auth pages - let form handle errors
      const authPages = ['/auth/admin', '/auth/provider']
      if (authPages.some(page => currentPath.startsWith(page))) {
        return Promise.reject(error)
      }

      // Attempt refresh
      try {
        await POST /accounts/refresh/
        // New access_token now in cookie
        return apiClient(error.config) // Retry original request
      } catch (refreshError) {
        // Refresh failed - redirect to login
        router.push(getLoginPath(currentPath))
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)
```

### Code Example (Manual Refresh in Auth Context):
```typescript
// File: /web-frontend/lib/contexts/auth-context.tsx (lines 80-146)
const refreshUser = async () => {
  try {
    // Attempt to fetch user (validates session)
    const user = await getCurrentUser() // GET /accounts/me/
    setUser(user)
  } catch (error) {
    // If 401, try one refresh
    if (error?.response?.status === 401) {
      try {
        await refreshAccessToken() // POST /accounts/refresh/
        const user = await getCurrentUser() // Retry with new token
        setUser(user)
      } catch {
        // Still failed - clear session
        setUser(null)
        throw error
      }
    } else {
      throw error
    }
  }
}
```

---

## 4. Route Protection (Two-Layer System)

### Layer 1: Initial Auth Load (useEffect #1)

Runs when app first loads to establish auth state:

```typescript
// File: /web-frontend/lib/contexts/auth-context.tsx (lines 188-236)
useEffect(() => {
  const initAuth = async () => {
    setIsLoading(true)

    try {
      // 1. Check localStorage for cached user
      const storedUser = localStorage.getItem("user")
      if (storedUser) {
        setUserState(JSON.parse(storedUser))
      }

      // 2. For protected routes, validate with backend
      const isPublicRoute = PUBLIC_ROUTES.includes(pathname)
      if (!isPublicRoute) {
        // Call GET /accounts/me/ to validate and refresh
        const user = await getCurrentUser()
        setUser(user)
      }

      setIsLoaded(true)
    } catch (error) {
      // Session invalid - clear everything
      setUser(null)
      setIsLoaded(true)
    } finally {
      setIsLoading(false)
    }
  }

  initAuth()
}, [pathname])
```

**Public Routes (No Auth Required):**
```typescript
const PUBLIC_ROUTES = [
  "/",                    // Landing page
  "/auth/admin",         // Admin login
  "/auth/provider",      // Provider login
  "/activate",           // Provider activation
  "/customer",           // Customer onboarding
  "/partners",           // Partners page
  "/purchase-success",
  "/purchase-cancelled"
]
```

### Layer 2: Route Guards (useEffect #2)

Enforces role-based access after auth is loaded:

```typescript
// File: /web-frontend/lib/contexts/auth-context.tsx (lines 239-315)
useEffect(() => {
  // Wait for initial auth check to complete
  if (isLoading) return

  // If not loaded, show loading screen
  if (!isLoaded) {
    setShowLoadingScreen(true)
    return
  }

  setShowLoadingScreen(false)

  // Check access rules
  const isPublicRoute = PUBLIC_ROUTES.includes(pathname)

  if (!isPublicRoute && !isAuthenticated) {
    // Trying to access protected route without auth
    router.push(getLoginPath(pathname))
    return
  }

  if (pathname.startsWith("/admin")) {
    // Admin route - only admins can access
    if (user?.role !== "admin") {
      router.push(user?.role === "provider" ? "/provider" : "/")
    }
  }

  if (pathname.startsWith("/provider")) {
    // Provider route - only providers and admins can access
    if (user?.role !== "provider" && user?.role !== "admin") {
      router.push("/")
    }
  }
}, [isLoading, isLoaded, isAuthenticated, user?.role, pathname])
```

**Access Rules:**
| Route | Admin? | Provider? | Customer? |
|-------|--------|-----------|-----------|
| /admin/* | ✓ | → /provider | → / |
| /provider/* | ✓ | ✓ | → / |
| /auth/* | ✓ (allowed) | ✓ (allowed) | ✓ (allowed) |
| / | ✓ | ✓ | ✓ |

---

## 5. State Management

### Auth Context State:
```typescript
// File: /web-frontend/lib/contexts/auth-context.tsx
type User = {
  user_id: string
  email: string
  first_name: string
  last_name: string
  phone_number: string
  role: "admin" | "provider" | "customer"
  is_verified: boolean
  is_active: boolean
}

type AuthContextType = {
  user: User | null
  isLoading: boolean      // Initial auth check in progress
  isLoaded: boolean       // Initial auth check completed
  isAuthenticated: boolean // Shorthand for !!user
  signIn: (email: string, password: string, role: string) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
  setUser: (user: User | null) => void
}
```

### Storage Locations:

| Data | Where | Accessible by JS? | Purpose |
|------|-------|-------------------|---------|
| access_token | HttpOnly Cookie | NO ✓ | Authentication |
| refresh_token | HttpOnly Cookie | NO ✓ | Token refresh |
| User profile | React State | YES | Current auth state |
| User profile | localStorage | YES | Instant UI on reload |

---

## 6. API Endpoints and Services

### Auth Endpoints:
```typescript
// File: /web-frontend/services/auth.ts

// Login
POST /api/accounts/admin/login/
  Request: { email: string, password: string }
  Response: { access_token, refresh_token } in HttpOnly cookies

// Login
POST /api/accounts/provider/login/
  Request: { email: string, password: string }
  Response: { access_token, refresh_token } in HttpOnly cookies

// Get current user
GET /api/accounts/me/
  Headers: Cookies included automatically
  Response: User profile

// Token refresh
POST /api/accounts/refresh/
  Cookies: refresh_token included automatically
  Response: New access_token in cookie

// Logout
POST /api/accounts/logout/
  Cookies: access_token and refresh_token sent
  Response: Clears server-side session
```

### API Service Setup:
```typescript
// File: /web-frontend/lib/api/api-service.ts
export const apiService = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
  withCredentials: true  // Send cookies with all requests
})

// Requests are made like:
apiService.get('/accounts/me/')        // GET with cookies
apiService.post('/accounts/logout/', {})  // POST with cookies
```

---

## 7. Component Integration

### Using Auth in Components:

```typescript
"use client"

import { useAuth } from "@/lib/contexts/auth-context"

export default function Dashboard() {
  const { user, isLoading, signIn, logout } = useAuth()

  if (isLoading) return <LoadingScreen />

  if (!user) return <Redirect to="/auth/provider" />

  return (
    <div>
      <h1>Welcome, {user.business_name}</h1>
      <button onClick={logout}>Sign Out</button>
    </div>
  )
}
```

### Components Using Auth:
| Component | Location | Purpose |
|-----------|----------|---------|
| AuthLoginForm | /components/auth-login-form.tsx | Login UI, calls signIn() |
| DemoNav | /components/demo-nav.tsx | Logout button |
| AdminPage | /app/admin/page.tsx | Protected admin dashboard |
| ProviderPage | /app/provider/page.tsx | Protected provider dashboard |
| ActivatePage | /app/activate/page.tsx | Account activation (public) |

---

## 8. Provider Hierarchy

```
RootLayout (app/layout.tsx)
  ├─ QueryProvider (React Query)
  │   └─ AuthProvider (Auth Context)
  │       └─ {children}
  │           ├─ Toaster (Sonner notifications)
  │           ├─ Protected Routes (admin, provider)
  │           ├─ Public Routes (auth, home)
  │           └─ ...all pages
```

**AuthProvider exports:**
```typescript
export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider")
  }
  return context
}
```

---

## 9. Security Features

### ✓ HttpOnly Cookies
Tokens stored in browser cookies set by backend only (not accessible to JavaScript):
- Prevents XSS attacks from stealing tokens
- Browser sends automatically with `credentials: "include"`

### ✓ Automatic Token Refresh
Seamless token renewal without user interruption:
- Axios interceptor detects 401 responses
- Automatically calls refresh endpoint
- Retries original request with new token
- User-transparent (unless refresh also fails)

### ✓ Role-Based Access Control
Three-tier hierarchy enforced:
- Admin: Full access to /admin, /provider, public routes
- Provider: Access to /provider and public routes only
- Customer: Access to public routes only
- Unauthenticated: Access to public routes only

### ✓ Privilege Loss Detection
If user permissions change between page loads:
- Auth context detects role mismatch
- Shows warning toast
- Redirects to appropriate page
- Example: Admin loses admin role → redirected from /admin

### ✓ Route Whitelist
Only specified public routes accessible without authentication:
- Prevents unauthorized access to protected routes
- Redirects to login if trying to access protected route

---

## 10. Error Handling

### Login Errors:
```typescript
// Caught in AuthLoginForm.handleSubmit()
try {
  await signIn(email, password, role)
} catch (error) {
  toast.error("Invalid email or password")
}
```

### Token Refresh Failures:
```typescript
// In axios interceptor
try {
  await POST /accounts/refresh/
} catch (error) {
  // Refresh failed - clear session and redirect
  router.push(getLoginPath())
}
```

### Permission Changes:
```typescript
// Detected during route guard check
if (user.role changed) {
  toast.info("Your permissions have changed")
  router.push(appropriate_page)
}
```

---

## 11. Session Initialization on Page Load

**Timeline of what happens when user visits app after closing browser:**

```
1. Browser loads https://app.example.com (React app loads)
2. AuthProvider useEffect #1 runs
3. Check localStorage for cached user
   ✓ Found: setUserState(storedUser) → instant UI
4. For protected routes: call GET /accounts/me/
   - Browser sends refresh_token in cookie
   - Backend validates, returns user profile
   - If token expired: backend issues new access_token
5. setUser(user) updates state and localStorage
6. setIsLoaded(true) triggers useEffect #2
7. Route guards run - verify user has access to current route
8. If all valid: dashboard renders with user data
9. If invalid: redirect to login
```

**Result:** User sees dashboard instantly (cached from localStorage) with fresh data from backend.

---

## 12. Troubleshooting Guide

### User stays logged out after refresh
- Check: localStorage for "user" key
- Check: HttpOnly cookies in DevTools (Application tab)
- Check: Network tab - is GET /accounts/me/ being called?
- Check: Is POST /accounts/refresh/ being called on 401?

### Logout button doesn't clear authentication
- Check: localStorage.removeItem("user") is called
- Check: POST /accounts/logout/ response code is 200
- Check: Browser cookies cleared (Application tab)

### User can access /admin even though not admin
- Check: Route guard checks user.role === "admin"
- Check: GET /accounts/me/ returns correct role
- Check: Backend authentication is validating role correctly

### Login form shows "Invalid credentials" for correct password
- Check: Backend /accounts/admin/login/ response status
- Check: Network tab shows 401 or 400?
- Check: User exists in database
- Check: Password hash matches

### Token refresh not working
- Check: POST /accounts/refresh/ response status
- Check: refresh_token cookie exists and valid
- Check: Axios interceptor running (check console)
- Check: NEXT_PUBLIC_API_URL configured correctly

---

## 13. File Quick Reference

| File | What It Does |
|------|--------------|
| auth-context.tsx | Main auth state, signIn/logout logic, route protection |
| auth.ts | API functions: adminLogin, providerLogin, getCurrentUser, logout |
| axios.ts | Axios setup, token refresh interceptor, error handling |
| api-service.ts | Generic wrapper around axios for type-safe API calls |
| auth-login-form.tsx | Login form UI, calls useAuth().signIn() |
| demo-nav.tsx | Navigation, logout button calls useAuth().logout() |
| layout.tsx | Root layout, wraps app with AuthProvider |

---

## 14. Implementation Checklist

Use this when implementing similar auth in other projects:

- [ ] Create auth context with signIn, logout, refreshUser methods
- [ ] Create auth service with login, logout, getCurrentUser APIs
- [ ] Set up axios with credentials: true and interceptor for 401 handling
- [ ] Create login form component calling useAuth().signIn()
- [ ] Define PUBLIC_ROUTES constant for route guards
- [ ] Implement two useEffects in auth context:
  - [ ] First: Load cached user + validate with backend
  - [ ] Second: Enforce role-based access after auth loaded
- [ ] Wrap app root with AuthProvider
- [ ] Create login pages at /auth/admin, /auth/provider
- [ ] Create protected pages at /admin, /provider
- [ ] Test: Login, logout, page refresh, token expiry, role changes
