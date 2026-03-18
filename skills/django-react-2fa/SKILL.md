---
name: django-react-2fa
description: Complete TOTP two-factor authentication for Django + React/Next.js applications. Use when implementing authenticator app 2FA (Google Authenticator, Authy), backup codes, QR code enrollment, two-phase login with TOTP priority, email/phone OTP fallback for locked-out users, channel switching on resend, login resend throttling, or adding a 2FA settings UI. Covers the full stack — backend (pyotp, Fernet encryption, Redis pending secrets, DRF views, throttles) and frontend (React Query hooks, 7 UI components, TypeScript types). Works with any Django REST Framework + React/Next.js stack using JWT auth.
context: fork
---

# Django + React Two-Factor Authentication (TOTP)

Production-ready RFC 6238 TOTP 2FA for Django + React/Next.js. Full-stack implementation with authenticator app enrollment, encrypted secret storage, backup codes, multi-channel login fallback, and 7 ready-to-use React components.

## When to Use

- Adding authenticator app 2FA to any Django + React/Next.js project
- Implementing two-phase login (credentials → OTP/TOTP verification)
- Building 2FA settings UI (enable, disable, regenerate backup codes)
- Adding email/phone OTP fallback for users locked out of authenticator
- Implementing backup code recovery for TOTP users
- Adding login resend with channel switching (phone ↔ email)
- Setting up rate limiting for login OTP resend endpoints

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ TOTP Enrollment (Settings Page)                                 │
│                                                                 │
│ POST /auth/totp/setup/     → Secret + QR in Redis (10 min TTL) │
│ POST /auth/totp/enable/    → Verify code → encrypt to DB       │
│ POST /auth/totp/disable/   → Verify code → wipe TOTP data      │
│ POST /auth/totp/backup-codes/regenerate/ → Fresh codes          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Two-Phase Login                                                 │
│                                                                 │
│ POST /auth/login/          → Credentials OK → determine channel │
│   ├─ totp_enabled → otp_channel="totp" (no OTP sent)           │
│   ├─ phone exists → otp_channel="phone" (SMS sent)             │
│   └─ else         → otp_channel="email" (email sent)           │
│                                                                 │
│ POST /auth/login/verify/   → 3-tier verification:               │
│   1. Authenticator code (TOTP)                                  │
│   2. Backup code (XXXXX-XXXXX)                                  │
│   3. Phone/email OTP fallback                                   │
│                                                                 │
│ POST /auth/login/resend/   → Send OTP via phone or email        │
│   ├─ channel="phone" → force phone                              │
│   ├─ channel="email" → force email                              │
│   └─ (omitted)       → phone-first, email fallback              │
│   Returns: { otp_channel, phone_masked, has_phone }             │
└─────────────────────────────────────────────────────────────────┘
```

## Dependencies

```bash
# Backend
pip install pyotp>=2.9.0 "qrcode[pil]>=7.4" cryptography>=41.0

# Frontend (or equivalent OTP input component)
npm install input-otp
```

## Asset Files

### Backend (`assets/backend/`) — Copyable Templates

Backend files are concrete Python code. Copy and adapt imports to your project.

| File | Purpose |
|------|---------|
| `model_fields.py` | User model fields: `totp_enabled`, `totp_secret_encrypted`, `totp_backup_codes` |
| `totp_service.py` | Core TOTP service: encryption, QR generation, code verification, backup codes |
| `views.py` | DRF API views: setup, enable/disable, backup code regeneration |
| `urls.py` | URL patterns for TOTP endpoints |
| `throttles.py` | `LoginOTPResendThrottle` — separate generous throttle for login resend |
| `login_integration.py` | Integration patterns: login flow, OTP verification, resend with channel switching |

### Frontend (`assets/frontend/`) — Types, Services & Algorithms

- **`types.ts`** and **`service.ts`** are concrete TypeScript — copy and adapt API paths.
- **`hooks.ts`** is concrete React Query code — adapt store/query key imports.
- **`components/*.tsx`** are **algorithms and state machines**, NOT UI templates. They describe the state, transitions, data flow, and business logic for each component. Implement using whatever UI framework your project uses (shadcn/ui, MUI, Ant Design, Mantine, plain HTML, full pages, modals, etc.).

| File | Algorithm |
|------|-----------|
| `components/setup-totp-modal.tsx` | 3-step enrollment state machine: QR → verify → backup codes |
| `components/backup-codes-display.tsx` | Copy/download/confirm logic for backup code display |
| `components/security-settings-card.tsx` | 2FA settings: enable/disable/regenerate state + confirmation flows |
| `components/totp-code-confirm-dialog.tsx` | Reusable TOTP/backup code confirmation with input formatting |
| `components/totp-verification-view.tsx` | Login verification: 3-tier fallback state machine with channel switching |
| `components/backup-code-entry.tsx` | Backup code input formatting and validation |
| `components/totp-nudge-banner.tsx` | Dismissible banner visibility rules and localStorage persistence |

## Implementation Order

### Step 1: User Model

Add three fields to your User model (see `assets/backend/model_fields.py`):

```python
totp_enabled = models.BooleanField(default=False, db_index=True)
totp_secret_encrypted = models.TextField(null=True, blank=True)
totp_backup_codes = models.JSONField(default=list, blank=True)
```

Add `totp_enabled` to your user serializer response. **Never** expose the other two fields.

Run: `python manage.py makemigrations && python manage.py migrate`

### Step 2: TOTP Service

Copy `assets/backend/totp_service.py` to your project. Configure:

```python
# settings.py
TOTP_ISSUER_NAME = "Your App Name"  # Shown in authenticator apps
```

Key functions: `encrypt_totp_secret`, `decrypt_totp_secret`, `generate_totp_secret`, `build_provisioning_uri`, `generate_qr_code_data_uri`, `verify_totp_code`, `generate_backup_codes`, `verify_backup_code`.

### Step 3: TOTP API Endpoints

Copy `assets/backend/views.py` and `assets/backend/urls.py`. Add to your auth URL config:

```python
# In your auth urls.py
from your_app.totp_views import totp_setup, totp_toggle, totp_backup_codes_regenerate

urlpatterns += [
    path("totp/setup/", totp_setup, name="totp-setup"),
    path("totp/backup-codes/regenerate/", totp_backup_codes_regenerate, name="totp-backup-codes-regenerate"),
    path("totp/<str:action>/", totp_toggle, name="totp-toggle"),
]
```

### Step 4: Login Flow Integration

Modify your existing login service (see `assets/backend/login_integration.py` for full examples):

**Send OTP (login view):** Check `user.totp_enabled` first. If true, return `otp_channel="totp"` without sending any code. Otherwise send via phone or email.

**Verify OTP:** For TOTP users, try 3 tiers in order: authenticator code → backup code → phone/email OTP fallback. Non-TOTP users go directly to phone/email verification.

**Resend OTP:** Accept optional `channel` parameter ("phone" or "email"). Return `otp_channel`, `phone_masked`, and `has_phone` in response so the frontend can show channel switching options.

### Step 5: Login Resend Throttle

Copy `assets/backend/throttles.py`. This provides `LoginOTPResendThrottle` with scope `login_otp_resend`.

**Why a separate throttle?** The general OTP resend throttle (typically 3/hour) is too strict for login fallback because switching channels (phone → email) counts as a resend. Users hit the limit after just 2-3 actions and get locked out for ~45 minutes.

```python
# settings.py — add to REST_FRAMEWORK
"DEFAULT_THROTTLE_RATES": {
    # ... existing rates ...
    "otp_resend": "3/hour",           # Registration resends (strict)
    "login_otp_resend": "6/hour",     # Login resends (generous for channel switching)
}
```

Apply to your login resend view:

```python
from your_app.throttles import LoginOTPResendThrottle

@throttle_classes([LoginOTPResendThrottle])
def login_resend_otp(request):
    ...
```

### Step 6: Frontend Types & Hooks

Copy `assets/frontend/types.ts`, `assets/frontend/service.ts`, `assets/frontend/hooks.ts`.

Add query keys to your query key factory:

```typescript
totpSetup: () => ["totpSetup"],
totpEnable: () => ["totpEnable"],
totpDisable: () => ["totpDisable"],
totpRegenerateBackupCodes: () => ["totpRegenerateBackupCodes"],
loginResendOTP: () => ["loginResendOTP"],
```

The `useEnableTOTP` and `useDisableTOTP` hooks auto-update your auth store's `totp_enabled` field on success.

### Step 7: Frontend Components

Read the algorithm files in `assets/frontend/components/` and implement each one using your project's UI framework. Each file documents:

- **State machine** — states, transitions, and what triggers them
- **Business logic** — validation, formatting, API calls, error handling
- **Data flow** — which hooks to call, what to read from auth store

Implement these using whatever UI fits your project (modals, full pages, inline forms, etc.):

**Settings page:** Implement the SecuritySettingsCard algorithm — 2FA enable/disable/regenerate.

**Login flow:** When `otp_channel === "totp"`, implement the TOTPVerificationView algorithm — 3-tier fallback with channel switching.

**Dashboard:** Implement the TOTPNudgeBanner algorithm — dismissible prompt with localStorage persistence.

### Step 8: Staging/Development Mode

For local development where SMS delivery is unavailable:

```python
# Backend — expose via your configurations endpoint
SMS_VERIFICATION_BYPASS = settings.DEBUG or os.getenv("SMS_VERIFICATION_BYPASS") == "true"
```

The `TOTPVerificationView` component has a commented-out staging hint that shows phone number digits when bypass is active. Uncomment and wire to your config system.

## Security Checklist

- [ ] TOTP secrets encrypted with Fernet before DB storage
- [ ] Secrets only shown once during enrollment (never in API responses after)
- [ ] Pending secrets in Redis with 10-minute TTL (not written to DB until verified)
- [ ] Backup codes SHA-256 hashed (irreversible) — plaintext shown once
- [ ] Backup codes consumed on use (single-use, remaining saved to DB)
- [ ] Disable 2FA requires authenticator code OR backup code
- [ ] Regenerate backup codes requires live TOTP code (backup codes NOT accepted)
- [ ] Login resend uses separate throttle (6/hour vs 3/hour)
- [ ] `totp_secret_encrypted` and `totp_backup_codes` excluded from all serializers
- [ ] Security-sensitive actions logged (TOTP_ENABLED, TOTP_DISABLED, TOTP_BACKUP_REGENERATED)

## Component Dependency Graph

```
SecuritySettingsCard
  ├── SetupTOTPModal
  │     └── BackupCodesDisplay
  ├── TOTPCodeConfirmDialog (disable)
  ├── TOTPCodeConfirmDialog (regenerate)
  └── BackupCodesDisplay (new codes dialog)

TOTPVerificationView (login)
  ├── BackupCodeEntry
  └── (fallback OTP view — built-in)

TOTPNudgeBanner (dashboard — standalone)
```

## Testing

Test these flows end-to-end:

1. **Enrollment:** Setup → scan QR → enter code → receive backup codes → confirm saved → 2FA enabled
2. **Login with TOTP:** Credentials → TOTP entry → verified → JWT tokens
3. **Login with backup code:** Credentials → TOTP entry → "Use backup code" → verified
4. **Login with fallback:** Credentials → TOTP entry → "Send to email/phone" → code sent → verified
5. **Channel switching:** Fallback phone → "send to email instead" → verified via email
6. **Disable 2FA:** Settings → disable → enter code → TOTP wiped
7. **Regenerate codes:** Settings → regenerate → enter code → old codes invalidated, new codes shown
8. **Throttle:** Resend 7 times in an hour → 429 after 6th request
9. **Nudge banner:** Shown when `totp_enabled=false`, dismissed persists in localStorage
