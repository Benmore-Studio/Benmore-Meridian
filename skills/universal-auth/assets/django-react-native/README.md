# Django + React Native Auth Template

Production-ready authentication templates for Django REST Framework + React Native (Expo).
Based on a real HIPAA-grade EHR system with fixes and improvements documented below.

## File Map

```
backend/
  managers.py      — ActiveUserManager, UserSessionManager
  models.py        — User, UserSession, EmailVerificationToken, PasswordResetToken, MFARecoveryCode
  tokens.py        — JWT generation, refresh token strings, permission helpers
  middleware.py    — JWTAuthentication (DRF BaseAuthentication)
  permissions.py   — RBAC: IsPatient, IsProvider, IsAdmin, IsMfaVerified, IsMfaPending, HasPermission
  utils.py         — Recovery code helpers, get_client_ip
  urls.py          — 20 auth endpoints
  auth_views.py    — All view implementations

frontend/
  services/
    storage.ts          — SecureStore + AsyncStorage wrappers
    biometric.ts        — Face ID / Touch ID service
    api/auth.ts         — Auth API calls
  context/
    AuthContext.tsx     — Auth state (useReducer), session restoration, all actions
```

## Improvements Over Source

### Backend

| File | Fix | Why it matters |
|------|-----|----------------|
| `models.py` | `UserSession.revoke()` now sets `revoked_at` | Without timestamp, audit logs can't show when a session was revoked |
| `models.py` | Added `user,is_active` composite index on UserSession | N+1 on active session queries |
| `managers.py` | `UserSessionManager.active_sessions()` implemented (was `pass`) | Source was a stub — calling it returned `None` |
| `managers.py` | Added `active_for_device()` | BiometricLoginAPIView needs to look up session by fingerprint |
| `utils.py` | Added `verify_and_consume_recovery_code()` — atomic UPDATE | Original two-step verify+mark had a TOCTOU race condition; two concurrent requests could both pass verify before either marks it used |
| `utils.py` | `get_client_ip()` extracted to utils | Was duplicated inline in every rate-limited view |
| `permissions.py` | Added `IsMfaPending` | Without it, MFAVerifyAPIView had to manually check `auth_claims` — now declarative |
| `permissions.py` | `HasPermission` logs warning when `required_permission` unset | Silently returning `True` on misconfiguration was a security footgun |
| `tokens.py` | Auth0-agnostic — no JWKS, no external dependency | Dropped Auth0 management client; everything self-hosted |
| `tokens.py` | `generate_token_pair()` embeds `session_id` for revocation | Without `session_id` in the token, middleware can't check per-session revocation |
| `middleware.py` | Auto-detects claim namespace from token | Works with both custom-namespaced and plain tokens |
| `middleware.py` | `.only("is_active")` on session revocation check | Prevents loading full session row just to check one boolean |
| `auth_views.py` | Removed 6 debug `print()` statements | PHI was being printed to stdout/logs |
| `auth_views.py` | MFA setup generates 8 recovery codes (was 3) | 3 codes is unusably few; NIST recommends 8-10 |
| `auth_views.py` | `MFADisableAPIView` revokes all sessions (was commented out) | Disabling MFA without revoking sessions lets existing tokens bypass the removed protection |
| `auth_views.py` | `create_user_session()` passes all device fields | `os`, `os_version`, `app_version`, `device_id` were being silently dropped |
| `auth_views.py` | `TokenRefreshAPIView` sets `revoked_at` on replay attack | Revoked sessions had no timestamp — audit trail was incomplete |
| `auth_views.py` | `BiometricLoginAPIView` has rate limiting (was missing) | Biometric endpoint was wide open to brute force |
| `auth_views.py` | Consistent `{"code": str, "message": str}` error shape | Mixed error shapes across endpoints broke client error handling |

### Frontend

| File | Fix | Why it matters |
|------|-----|----------------|
| `storage.ts` | Error wrapping on `secureStorage.setItem` | expo-secure-store throws silently on Android when device lock is removed; surfacing context makes debugging possible |
| `storage.ts` | `clearAll()` on both stores | Single call to clear all auth state on logout/account deletion |
| `storage.ts` | `APP_PREFIX` constant | Prevents key collisions when multiple apps share a device |
| `biometric.ts` | `getSupportStatus()` separates "no hardware" from "not enrolled" | Allows showing "enable in Settings" vs "not supported" messages |
| `biometric.ts` | `authenticate()` adds `fallbackLabel` | Android shows PIN fallback option; iOS ignores it |
| `biometric.ts` | `getDeviceFingerprint()` has stable fallback | Source could return `null` on some devices — now always returns a string |
| `api/auth.ts` | Removed mock infrastructure | Mock layer was baked in; template shouldn't carry dev-only code |
| `api/auth.ts` | `refreshToken()` guards against null stored token | Source would send `null` to backend, getting a confusing 400 error |
| `api/auth.ts` | `logout()` accepts `clearBiometric` option | Source never cleared biometric credentials on logout — now explicit |
| `AuthContext.tsx` | Session restoration validates token expiry | Source restored any stored session without checking if it was expired |
| `AuthContext.tsx` | `verifyMFA` reads `mfaToken` via ref | Avoids stale closure — `useCallback` with deps could read old value in some React Native batching scenarios |
| `AuthContext.tsx` | `biometricLogin` checks HTTP status for credential clearing | String-matching on error messages is fragile; 401/403 status is reliable |

## Settings Required (Django)

```python
# settings.py
JWT_SECRET_KEY = env("JWT_SECRET_KEY")          # 256-bit minimum, never share
ACCESS_TOKEN_LIFETIME_MINUTES = 15
REFRESH_TOKEN_LIFETIME_DAYS = 7
DEVICE_TOKEN_LIFETIME_DAYS = 30
APP_CLAIM_NAMESPACE = "https://yourapp.com"     # Used for custom JWT claims
JWT_AUDIENCE = env("JWT_AUDIENCE")
JWT_ISSUER = env("JWT_ISSUER")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "accounts.middleware.JWTAuthentication",
    ],
}
```

## Auth Flow

```
Register → Email OTP verify → Login → [MFA verify] → Access API
                                  ↓
                           Biometric register
                                  ↓
                      Next login → Biometric prompt → Access API
```

## Mode Upgrade Path

This template implements Mode 2 (Secure) out of the box:
- JWT + refresh token rotation
- Email verification
- Session management with device binding
- Biometric login

To reach Mode 3 (Enterprise), add: RBAC permissions on protected endpoints
To reach Mode 4 (HIPAA), add: enforced MFA for providers, consent tracking, audit logs
