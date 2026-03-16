---
name: universal-auth
description: Use when adding authentication to any application — mobile, web, SaaS, internal tool, or healthcare system. Triggers on requests for login, signup, 2FA, TOTP, biometric auth, Face ID, fingerprint, JWT, session management, password reset, MFA setup, role-based access, or audit logging. Covers Django, Node/Express, NestJS, Laravel, React Native, Next.js, Flutter. Applies to new projects and retrofitting existing codebases without breaking architecture.
context: fork
---

# Universal Authentication Skill

## Overview

Plug-and-play authentication layer for any application stack. Analyzes the existing codebase, detects architecture, recommends a security mode, generates production-ready auth infrastructure, and integrates without breaking existing code.

**Core principle:** Analyze first, ask if unclear, propose before generating, never overwrite without approval.

**Progress banners:** At the start of every numbered step, output a plain-text banner so the developer always knows where you are:

```
 ──────────────────────────────────────────────────────────
  Step N / 10  ·  STEP NAME
 ──────────────────────────────────────────────────────────
```

Example: `Step 1 / 10  ·  PROJECT INTELLIGENCE ANALYSIS`

---

## Workflow (follow in order)

```
0.  Adaptive Pre-Analysis           →  read past logs, compute stack confidence
1.  Project Intelligence Analysis   →  detect stack, sensitivity, tenancy, auth transport
🎛  (if LOW confidence gaps)        →  AskUserQuestion to fill in unknowns
2.  🎛 Mode selection               →  AskUserQuestion · user picks mode · wait for answer
3.  🎛 Clarifying questions         →  AskUserQuestion · all at once · skip confirmed · wait
4.  🎛 Architecture proposal        →  list files to create/modify · AskUserQuestion to approve
5.  Install dependencies            →  check manifests, skip already-present packages
6.  Generate auth infrastructure    →  backend → frontend → integration
7.  🎛 Mode Upgrade (if applicable) →  AskUserQuestion for target mode · additive only
8.  Security Hardening Pass         →  CSRF + headers + encryption keys + token security
9.  Security Review Summary         →  plain-text terminal output
10. Log integration                 →  append to integrations.jsonl
```

---

## Step 1 — Project Intelligence Analysis

Read these files to infer architecture before writing any code:

| Signal | Files to read |
|--------|--------------|
| Language/framework | `package.json`, `requirements.txt`, `composer.json`, `go.mod`, `pubspec.yaml`, `Podfile`, `build.gradle`, `*.csproj`, `go.sum` |
| Database | ORM config, `settings.py`, `prisma/schema.prisma`, `sequelize.config.js`, `typeorm.config.ts`, `mongoose` imports, migrations folder |
| Existing auth | `models.py`, `schema.prisma`, routes folder, `auth/` directory, `middleware/` directory |
| Env vars | `.env`, `.env.example`, `config/` folder, `appsettings.json` (.NET) |
| Sensitivity signals | Model field names (patient, provider, clinic), payment imports, compliance comments |
| Tenancy | Fields named `tenant_id`, `org_id`, `workspace_id`, team relations |
| Auth type | Cookie-based session vs JWT Bearer — check middleware, response headers, frontend storage |

### Backend Framework Detection

| File/Signal | Detected Framework |
|-------------|-------------------|
| `requirements.txt` + `django` import | Django |
| `requirements.txt` + `flask` import | Flask |
| `package.json` + `express` | Node/Express |
| `package.json` + `@nestjs/core` | NestJS |
| `composer.json` + `laravel/framework` | Laravel |
| `go.mod` + `gin` or `echo` or `fiber` | Go |
| `*.csproj` + `Microsoft.AspNetCore` | .NET / ASP.NET Core |

### Frontend / Mobile Framework Detection

| File/Signal | Detected Framework |
|-------------|-------------------|
| `package.json` + `react-native` | React Native |
| `package.json` + `expo` | Expo (React Native) |
| `package.json` + `next` | Next.js |
| `package.json` + `react` (no next/native) | React |
| `package.json` + `@angular/core` | Angular |
| `package.json` + `vue` | Vue.js |
| `pubspec.yaml` + `flutter` | Flutter |
| `*.xcodeproj` / `AppDelegate.swift` | Swift (iOS native) |
| `build.gradle` + `kotlin` | Kotlin (Android native) |

### ORM / Database Detection

| File/Signal | ORM / DB |
|-------------|----------|
| `prisma/schema.prisma` | Prisma |
| `sequelize.config.js` or `sequelize` in `package.json` | Sequelize |
| `typeorm.config.ts` or `TypeOrmModule` import | TypeORM |
| `mongoose` in `package.json` or `.model.ts` with Schema | Mongoose (MongoDB) |
| `models.py` + Django imports | Django ORM |
| `*.csproj` + `EntityFrameworkCore` | Entity Framework Core |
| `go.mod` + `gorm.io/gorm` | GORM (Go) |
| `Eloquent` model imports | Laravel Eloquent |

### Infer These Values

**Project type:** internal-tool | SaaS | mobile-app | enterprise | healthcare | admin-dashboard | consumer-app | API-service

**Data sensitivity:**
- LOW → internal dashboards, non-user-facing tools
- MEDIUM → SaaS, customer accounts, general user data
- HIGH → healthcare (patient/provider/clinic terms), financial, identity services

**Auth transport:** cookie-session | JWT-bearer | both
- Cookie/session → **CSRF protection required**
- JWT bearer → CSRF not required but secure storage is critical

**Tenancy:** single-tenant | multi-tenant (look for org/workspace/team FK on main models)

**Stack detection results table:**

| Layer | Detected | Confidence |
|-------|----------|------------|
| Backend framework | | |
| Frontend framework | | |
| Database | | |
| ORM | | |
| Auth transport | | |
| Cache/queue | | |
| Existing auth | | |

If confidence is LOW on any row — ask the developer before proceeding.

### Low-Confidence Detection — Use AskUserQuestion

When any layer in the stack detection table has LOW confidence, do not guess — use AskUserQuestion to fill in only the unknown rows. Load with `ToolSearch` → `select:AskUserQuestion` if not already loaded.

Ask up to 4 questions at once (one per unknown layer). Example for backend + database unknown:

```js
AskUserQuestion({
  questions: [
    {
      question: "Which backend framework is this project using?",
      header: "Backend",
      multiSelect: false,
      options: [
        { label: "Django (Recommended)",  description: "Python — detected requirements.txt but no clear framework" },
        { label: "Node / Express",        description: "JavaScript — package.json present" },
        { label: "NestJS",                description: "TypeScript — @nestjs/core" },
        { label: "Laravel",               description: "PHP — composer.json" }
      ]
    },
    {
      question: "Which database are you targeting?",
      header: "Database",
      multiSelect: false,
      options: [
        { label: "PostgreSQL (Recommended)", description: "Full-featured, production-ready" },
        { label: "SQLite",                   description: "File-based, no server needed" },
        { label: "MySQL / MariaDB",          description: "Popular in existing stacks" },
        { label: "MongoDB",                  description: "Document store" }
      ]
    }
  ]
})
```

Only ask about rows with LOW confidence — skip rows that are already confirmed.

---

## Step 2 — Auth Mode Selection

**ALWAYS present all 4 modes as a selection block — never auto-proceed without the user confirming.** Pre-select the recommended mode with `← recommended` based on detected signals, but the user must confirm or choose a different one.

### Recommendation Logic

| Detected signals | Recommend |
|------------------|-----------|
| Internal tool, no user PII | Mode 1 |
| SaaS, general users | Mode 2 |
| Multi-role, organizations, B2B | Mode 3 |
| patient/provider/clinic/ehr terms | Mode 4 |
| Financial + user accounts | Mode 3 minimum |

### Mode Selection — Use AskUserQuestion

First load the tool: `ToolSearch` → `select:AskUserQuestion`

Then call it with **1 question, 4 options, previews enabled**. Put the recommended mode first and append `(Recommended)` to its label. Each option's `preview` shows the feature breakdown so the user can compare before choosing.

```js
AskUserQuestion({
  questions: [{
    question: "Which auth mode do you want to implement?",
    header: "Auth Mode",
    multiSelect: false,
    options: [
      // Put recommended mode first — swap order based on detection
      {
        label: "Mode 2 · Secure Auth (Recommended)",
        description: "Production SaaS, consumer apps with real user data",
        preview:
          "🌐  Web\n" +
          "  · Email/password login\n" +
          "  · TOTP 2FA — scannable QR code, manual key, 8 recovery codes\n" +
          "  · httpOnly JWT cookies · refresh token rotation\n" +
          "  · Replay attack detection · session tracking\n" +
          "  · Email verification · password reset · rate limiting\n\n" +
          "📱  Mobile (adds on top of web)\n" +
          "  · Face ID / Touch ID / device passcode\n" +
          "  · Biometric device tokens (30-day expiry)\n" +
          "  · Secure device fingerprint binding\n" +
          "  · SecureStore / Keychain token storage"
      },
      {
        label: "Mode 1 · Quick Auth",
        description: "MVPs, prototypes, internal tools",
        preview:
          "🌐  Web\n" +
          "  · Email/password login\n" +
          "  · httpOnly JWT cookies · rate limiting\n" +
          "  · Register · login · logout · password reset\n\n" +
          "📱  Mobile (adds on top of web)\n" +
          "  · SecureStore / Keychain token storage"
      },
      {
        label: "Mode 3 · Enterprise Auth",
        description: "Multi-role SaaS, B2B platforms, admin systems",
        preview:
          "🌐  Web (everything in Mode 2, plus)\n" +
          "  · RBAC — roles & permissions middleware\n" +
          "  · Audit logging (login, logout, MFA, permission changes)\n" +
          "  · Active session list · per-session revocation\n" +
          "  · Suspicious login detection & alerts\n\n" +
          "📱  Mobile (adds on top of web)\n" +
          "  · Per-device session management\n" +
          "  · Remote biometric device revocation"
      },
      {
        label: "Mode 4 · HIPAA Secure",
        description: "Healthcare, EHR, telehealth, patient portals",
        preview:
          "🌐  Web (everything in Mode 3, plus)\n" +
          "  · Immutable audit logs (no deletion ever)\n" +
          "  · Enforced MFA for providers — cannot be disabled\n" +
          "  · Token lifetimes: 15 min access / 1 day refresh\n" +
          "  · HIPAA consent timestamps on User model\n" +
          "  · Record-level access traceability\n\n" +
          "📱  Mobile (adds on top of web)\n" +
          "  · Mandatory biometric for providers\n" +
          "  · No passcode-only fallback allowed"
      }
    ]
  }]
})
```

Wait for the user's selection before proceeding to Step 3.

---

## Step 3 — Clarifying Questions

**NEVER ask questions one-by-one in prose.** Present ALL outstanding questions together as a single structured block with labelled options — inline in the chat response. The user ticks/types their answers in one reply.

Skip any question already answered by the codebase analysis (document the assumption inline). Only include questions that are genuinely ambiguous.

### Clarifying Questions — Use AskUserQuestion

First load the tool: `ToolSearch` → `select:AskUserQuestion` (skip if already loaded in this session)

Call it with **up to 4 questions in one shot** — only include questions that are genuinely ambiguous. Remove any question already answered by codebase analysis and note the assumption in plain text before the tool call.

The tool supports 2–4 options per question. The user can also select "Other" to type a custom answer.

```js
AskUserQuestion({
  questions: [
    {
      question: "Which database are you using?",
      header: "Database",
      multiSelect: false,
      options: [
        { label: "PostgreSQL (Recommended)", description: "Best for production — full-featured, widely supported" },
        { label: "SQLite",                   description: "Zero-config, file-based — great for dev / testing" },
        { label: "MySQL / MariaDB",          description: "Popular in existing stacks" },
        { label: "MongoDB",                  description: "Document store — choose if your models are already Mongoose/Motor" }
      ]
    },
    {
      question: "How should auth tokens be transported?",
      header: "Auth Transport",
      multiSelect: false,
      options: [
        { label: "httpOnly Cookie JWT (Recommended)", description: "Most secure for web — XSS-safe, requires CSRF protection" },
        { label: "Bearer Token",                      description: "Authorization header — good for APIs and mobile clients" },
        { label: "Server-side Session",               description: "Session ID in cookie — requires session store (Redis/DB)" }
      ]
    },
    {
      question: "How should the app send emails?",
      header: "Email",
      multiSelect: false,
      options: [
        { label: "Console / Terminal (Recommended)", description: "Prints to terminal — no setup needed, great for dev" },
        { label: "SMTP",                             description: "Provide host + credentials — works with any mail server" },
        { label: "SendGrid / Mailgun / Postmark",    description: "API-based — provide key after setup" },
        { label: "Existing utility",                 description: "You have an email helper already — I'll plug into it" }
      ]
    },
    {
      question: "What should be done with the frontend?",
      header: "Frontend",
      multiSelect: false,
      options: [
        { label: "Build new auth pages",   description: "Generate login, register, MFA, password reset pages from scratch" },
        { label: "Reuse existing pages",   description: "Adapt auth pages from another part of this project" },
        { label: "Backend only",           description: "Skip frontend — I'll wire it up myself" }
      ]
    }
  ]
})
```

**Rules:**
- Only include questions that are actually ambiguous — remove confirmed ones entirely
- Put the recommended option first and append `(Recommended)` to its label
- Before the tool call, print one line for each skipped question: e.g. `✓ Auth transport — assuming httpOnly cookie JWT (detected from existing middleware)`
- Wait for the user's answers before proceeding to Step 4

---

## Step 4 — Architecture Proposal + Approval

Before writing any code, present a clear list of everything that will be created or modified. Then use AskUserQuestion to get explicit approval.

**Format the proposal as plain text** — list files grouped by backend / frontend / config:

```
 ──────────────────────────────────────────────────────────
  📋  ARCHITECTURE PROPOSAL  —  Mode [N] · [Stack]
 ──────────────────────────────────────────────────────────

  Backend  ([framework])
  ├── src/db/schema.[ext]          — database schema + migrations
  ├── src/models/user.[ext]        — User model with auth fields
  ├── src/utils/jwt.[ext]          — token generation + verification
  ├── src/utils/totp.[ext]         — TOTP setup + verification  (Mode 2+)
  ├── src/utils/email.[ext]        — email sending utility
  ├── src/middleware/auth.[ext]    — JWT auth middleware
  ├── src/middleware/csrf.[ext]    — CSRF protection            (cookie JWT only)
  ├── src/middleware/rateLimit.[ext] — rate limiting
  └── src/routes/auth.[ext]        — all auth endpoints

  Frontend  ([framework])
  ├── app/login/page.[ext]         — login page
  ├── app/register/page.[ext]      — registration page
  ├── app/dashboard/page.[ext]     — protected dashboard
  ├── app/verify-email/page.[ext]  — email verification
  ├── app/forgot-password/page.[ext]
  ├── app/reset-password/page.[ext]
  ├── app/mfa/setup/page.[ext]     — TOTP QR setup             (Mode 2+)
  ├── app/mfa/verify/page.[ext]    — MFA login challenge        (Mode 2+)
  ├── lib/auth.[ext]               — auth API functions
  ├── lib/api.[ext]                — API fetch wrapper
  └── context/AuthContext.[ext]    — auth state provider

  Config
  ├── .env                         — environment variables (new file)
  └── .env.example                 — committed placeholder values

 ──────────────────────────────────────────────────────────
  Files that already exist and will be MODIFIED:
  · [list any files from the project that need changes]
  · (none — this is a fresh auth setup)
 ──────────────────────────────────────────────────────────
```

Then call AskUserQuestion:

```js
AskUserQuestion({
  questions: [{
    question: "Ready to generate this auth infrastructure?",
    header: "Proceed?",
    multiSelect: false,
    options: [
      {
        label: "Generate everything (Recommended)",
        description: "Proceed with the full architecture as proposed above"
      },
      {
        label: "Backend only",
        description: "Generate backend files now — I'll handle the frontend separately"
      },
      {
        label: "I have changes first",
        description: "I'll describe what to adjust before you start generating"
      }
    ]
  }]
})
```

**Rules:**
- Always show the file list before the widget — the user needs to see what they're approving
- Adapt the file list to the actual stack detected (rename extensions, paths, frameworks)
- Mark any existing files that will be modified in the MODIFIED section — never silently overwrite
- Wait for the user's answer before writing any code

---

## Step 3b — Dependencies by Stack

### Django (Python)

```bash
pip install pyotp>=2.9.0          # TOTP (Mode 2+)
pip install PyJWT[crypto]>=2.9.0   # JWT tokens
pip install django-redis>=6.0.0   # Rate limiting + sessions
pip install redis>=7.0.0
pip install qrcode[pil]>=7.4.0    # QR code generation (Mode 2+)
```

### Node / Express

```bash
npm install bcryptjs jsonwebtoken speakeasy qrcode
npm install express-rate-limit ioredis
```

### NestJS

```bash
npm install @nestjs/passport @nestjs/jwt passport passport-local
npm install speakeasy qrcode bcryptjs
npm install @nestjs/throttler
```

### React Native (Expo)

```bash
npx expo install expo-local-authentication  # Biometric (Mode 2+)
npx expo install expo-secure-store          # Token storage
npx expo install expo-application           # Device fingerprint
npm install react-native-qrcode-svg         # TOTP QR display (Mode 2+)
```

### Next.js / React Web

```bash
npm install next-auth speakeasy qrcode
# OR custom:
npm install jsonwebtoken bcryptjs speakeasy qrcode
npm install js-cookie    # httpOnly cookies for token storage
```

### Vue.js

```bash
npm install axios speakeasy qrcode
npm install @vueuse/core    # Reactive auth state helpers
```

### Angular

```bash
npm install @angular/common @angular/forms    # usually present
npm install speakeasy qrcode jsonwebtoken
```

### Flask (Python)

```bash
pip install Flask-Login Flask-WTF    # sessions + CSRF
pip install pyotp PyJWT bcrypt
pip install Flask-Limiter redis
```

### Laravel (PHP)

```bash
composer require pragmarx/google2fa-laravel    # TOTP
composer require bacon/bacon-qr-code           # QR codes
composer require laravel/sanctum               # Token auth
# CSRF: built-in via VerifyCsrfToken middleware
```

### Go (Gin / Echo / Fiber)

```bash
go get github.com/pquerna/otp              # TOTP
go get github.com/golang-jwt/jwt/v5        # JWT
go get golang.org/x/crypto/bcrypt          # Password hashing
go get github.com/ulule/limiter/v3         # Rate limiting
```

### .NET / ASP.NET Core

```bash
dotnet add package Microsoft.AspNetCore.Authentication.JwtBearer
dotnet add package OtpNet                  # TOTP
dotnet add package BCrypt.Net-Next         # Password hashing
dotnet add package AspNetCoreRateLimit     # Rate limiting
# CSRF: built-in via AntiForgery middleware
```

### Swift (iOS Native)

```swift
// Use LocalAuthentication framework (built-in, no install)
import LocalAuthentication    // Face ID / Touch ID
import Security               // Keychain storage
// TOTP: add via SPM
// .package(url: "https://github.com/lachlanbell/SwiftOTP", from: "3.0.0")
```

### Kotlin (Android Native)

```kotlin
// build.gradle (app)
implementation("androidx.biometric:biometric:1.2.0-alpha05")
implementation("com.warrenstrange:googleauth:1.5.0")  // TOTP
implementation("androidx.security:security-crypto:1.1.0-alpha06")  // EncryptedSharedPreferences
```

### Flutter

```bash
flutter pub add local_auth flutter_secure_storage
flutter pub add otp base32     # TOTP
flutter pub add qr_flutter     # QR display
```

### Dependency Detection Rule

Before running any install command, check the existing manifest:
- `package.json` → `dependencies` + `devDependencies`
- `requirements.txt` / `pyproject.toml` → installed packages
- `composer.json` → `require` block
- `go.mod` → `require` block
- `pubspec.yaml` → `dependencies`
- `*.csproj` → `PackageReference` items

Only install packages that are **not already present**. Log what was skipped.

### Dependency Confirmation — Use AskUserQuestion

After checking manifests, present what will be installed and get confirmation before running any install commands. Load with `ToolSearch` → `select:AskUserQuestion` if not already loaded.

```js
AskUserQuestion({
  questions: [{
    question: "Ready to install these packages?",
    header: "Install",
    multiSelect: false,
    options: [
      {
        label: "Install all (Recommended)",
        description: "Run the install command now for all missing packages"
      },
      {
        label: "Show me the command first",
        description: "Print the exact install command so I can run it myself"
      },
      {
        label: "Skip — already handled",
        description: "I'll manage dependencies myself, proceed to code generation"
      }
    ]
  }]
})
```

Always list the packages that will be installed (and any skipped ones) in plain text BEFORE showing this widget.

---

## Step 4 — Core Patterns (Reference Implementation)

These patterns are based on production implementations. Adapt to detected stack.

### 4.1 User Model Fields

**All modes:**
```python
# Django example — adapt field types for other ORMs
id = UUIDField(primary_key=True, default=uuid.uuid4)
email = EmailField(unique=True, db_index=True)
email_verified = BooleanField(default=False)
is_active = BooleanField(default=True)
created_at = DateTimeField(auto_now_add=True)
updated_at = DateTimeField(auto_now=True)
```

**Mode 2+ (add to User):**
```python
mfa_enabled = BooleanField(default=False)
mfa_secret = BinaryField(null=True, blank=True)  # Encrypted TOTP secret
mfa_enrolled_at = DateTimeField(null=True)
```

**Mode 4 (add to User):**
```python
hipaa_consent_accepted = BooleanField(default=False)
hipaa_consent_version = CharField(max_length=20, null=True)
hipaa_consent_at = DateTimeField(null=True)
terms_accepted_at = DateTimeField(null=True)
privacy_policy_accepted_at = DateTimeField(null=True)
```

### 4.2 Session Model (Mode 2+)

```python
class UserSession(models.Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    user = ForeignKey(User, on_delete=CASCADE, related_name="sessions")
    session_id = CharField(max_length=255, unique=True, db_index=True)
    refresh_token_hash = CharField(max_length=64)        # SHA-256, never plain
    device_fingerprint = CharField(max_length=255, db_index=True)
    device_name = CharField(max_length=255, blank=True)
    is_biometric = BooleanField(default=False)
    ip_address = GenericIPAddressField(null=True)
    user_agent = TextField(blank=True)
    expires_at = DateTimeField(db_index=True)
    is_active = BooleanField(default=True)
    revoked_at = DateTimeField(null=True)
    last_used_at = DateTimeField(null=True)
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["user", "is_biometric"]),
        ]
```

### 4.3 JWT Token Generation

**Token lifetimes (production defaults):**
```python
ACCESS_TOKEN_LIFETIME_MINUTES = 15      # Short-lived
REFRESH_TOKEN_LIFETIME_DAYS = 7         # Rotated on use
DEVICE_TOKEN_LIFETIME_DAYS = 30         # Biometric only
MFA_PENDING_TOKEN_MINUTES = 5           # During MFA challenge
```

**HIPAA Mode overrides:**
```python
ACCESS_TOKEN_LIFETIME_MINUTES = 15
REFRESH_TOKEN_LIFETIME_DAYS = 1         # Tighter for healthcare
```

**Token payload pattern:**
```python
import jwt, uuid
from django.utils import timezone
from datetime import timedelta

def generate_tokens(user, session, request):
    now = int(timezone.now().timestamp())

    access_payload = {
        "sub": str(user.id),
        "iat": now,
        "exp": now + (ACCESS_TOKEN_LIFETIME_MINUTES * 60),
        "user_id": str(user.id),
        "email": user.email,
        "session_id": session.session_id,  # For revocation check
    }
    # Add roles/permissions for Mode 3+

    refresh_payload = {
        "sub": str(user.id),
        "iat": now,
        "exp": now + (REFRESH_TOKEN_LIFETIME_DAYS * 86400),
        "scope": "offline_access",
        "user_id": str(user.id),
        "jti": str(uuid.uuid4()),           # Unique per token
        "token_type": "refresh",
    }

    return {
        "accessToken": jwt.encode(access_payload, SECRET_KEY, algorithm="HS256"),
        "refreshToken": jwt.encode(refresh_payload, SECRET_KEY, algorithm="HS256"),
        "expiresIn": ACCESS_TOKEN_LIFETIME_MINUTES * 60,
    }
```

### 4.4 TOTP Setup (Mode 2+)

```python
import secrets, base64, pyotp

# Setup endpoint — generates secret + QR URI
def totp_setup(user):
    if not user.mfa_secret:
        raw_secret = secrets.token_bytes(20)     # 20 bytes = 160-bit entropy
        user.mfa_secret = raw_secret              # Store as binary (pgcrypto or encrypted field)
        user.save(update_fields=["mfa_secret"])
    else:
        raw_secret = bytes(user.mfa_secret)

    secret_b32 = base64.b32encode(raw_secret).decode("utf-8").rstrip("=")

    qr_uri = (
        f"otpauth://totp/{APP_NAME}:{user.email}"
        f"?secret={secret_b32}&issuer={APP_NAME}&algorithm=SHA1&digits=6&period=30"
    )

    recovery_codes = [
        f"{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}"
        for _ in range(8)
    ]

    # Generate actual QR code PNG (always include — user must be able to scan, not just copy URI)
    import qrcode, io
    qr = qrcode.QRCode(version=1, box_size=8, border=4)
    qr.add_data(qr_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_image_b64 = base64.b64encode(buf.getvalue()).decode()

    return {
        "secret": secret_b32,
        "qrCodeUri": qr_uri,
        "qrCodeImage": f"data:image/png;base64,{qr_image_b64}",  # Render as <img src={qrCodeImage} />
        "recoveryCodes": recovery_codes,
    }

# Node.js (speakeasy + qrcode):
# const qrCodeImage = await QRCode.toDataURL(qrCodeUri, { width: 256, margin: 2 });
# return { secret, qrCodeUri, qrCodeImage, recoveryCodes };

# Frontend (React/Next.js) — display the scannable QR image:
# <img src={setup.qrCodeImage} alt="Scan with authenticator app" width={200} height={200} />
# Always show manual entry secret as a collapsible fallback beneath the image.


# Verification helper — used on enable and every MFA login
def verify_totp(user, code: str) -> bool:
    if not user.mfa_secret:
        return False
    secret = bytes(user.mfa_secret) if isinstance(user.mfa_secret, memoryview) else user.mfa_secret
    secret_b32 = base64.b32encode(secret).decode("utf-8").rstrip("=")
    totp = pyotp.TOTP(secret_b32)
    return totp.verify(code, valid_window=1)   # ±30 sec tolerance
```

**Recovery code storage (hashed, single-use):**
```python
import hashlib

def store_recovery_codes(user, plain_codes: list[str]):
    MFARecoveryCode.objects.filter(user=user, is_used=False).delete()
    MFARecoveryCode.objects.bulk_create([
        MFARecoveryCode(
            user=user,
            code_hash=hashlib.sha256(code.encode()).hexdigest(),
        )
        for code in plain_codes
    ])

def use_recovery_code(user, plain_code: str) -> bool:
    code_hash = hashlib.sha256(plain_code.encode()).hexdigest()
    recovery = MFARecoveryCode.objects.filter(
        user=user, code_hash=code_hash, is_used=False
    ).first()
    if not recovery:
        return False
    recovery.is_used = True
    recovery.used_at = timezone.now()
    recovery.save()
    return True
```

**MFA login flow — issue partial token, verify, then issue full token:**
```python
# On login if user.mfa_enabled:
mfa_token = jwt.encode({
    "sub": str(user.id),
    "scope": "mfa_pending",
    "exp": int((timezone.now() + timedelta(minutes=5)).timestamp()),
    "session_id": session_id,
}, SECRET_KEY, algorithm="HS256")

return Response({"mfaRequired": True, "mfaToken": mfa_token})

# On /auth/mfa/verify/ with code + mfaToken:
#   1. Decode + validate mfaToken scope == "mfa_pending"
#   2. verify_totp(user, code) OR use_recovery_code(user, code)
#   3. If valid → generate full access + refresh tokens
```

### 4.5 Biometric Auth (Mode 2+, React Native / Flutter)

**Device registration flow:**
```
POST /auth/biometric/register/   (authenticated, valid JWT required)
Body: { deviceFingerprint, deviceName, platform }

Backend:
1. Check max biometric devices per user (default: 3)
2. Generate session_id = f"biometric_{uuid4()}"
3. Create UserSession(is_biometric=True, device_fingerprint=fingerprint, expires_at=now+30days)
4. Return { deviceToken: session_id, expiresAt }

Frontend (React Native):
1. expo-local-authentication.authenticateAsync() → must succeed first
2. expo-secure-store.setItemAsync(BIOMETRIC_TOKEN_KEY, deviceToken)
3. expo-secure-store.setItemAsync(BIOMETRIC_FINGERPRINT_KEY, deviceFingerprint)
```

**Device fingerprint generation (React Native):**
```typescript
import * as Application from 'expo-application';
import { Platform } from 'react-native';

async function getDeviceFingerprint(): Promise<string> {
  if (Platform.OS === 'ios') {
    const vendorId = await Application.getIosIdForVendorAsync();
    return vendorId ?? `ios_${Application.applicationId}`;
  }
  return Application.getAndroidId() ?? `android_${Application.applicationId}`;
}
```

**Biometric login flow:**
```
POST /auth/biometric/login/
Body: { deviceToken, deviceFingerprint }

Backend validation:
1. Find UserSession by session_id = deviceToken
2. Check session.is_active AND session.is_biometric
3. Check session.expires_at > now()
4. Check session.device_fingerprint == deviceFingerprint (CRITICAL binding)
5. If all pass → generate fresh access + refresh tokens
6. Update session.last_used_at

React Native:
1. LocalAuthentication.authenticateAsync({ promptMessage: "Sign in" })
2. On success → retrieve deviceToken + fingerprint from SecureStore
3. POST to /auth/biometric/login/ → receive access + refresh tokens
4. Store tokens in SecureStore (never AsyncStorage for tokens)
```

### 4.6 Rate Limiting

**Redis-based (recommended for all modes):**
```python
from django.core.cache import cache

def check_rate_limit(email: str, max_attempts=5, window_seconds=900) -> bool:
    """Returns True if request is allowed, False if rate limited."""
    cache_key = f"login_attempts:{email.lower()}"
    attempts = cache.get(cache_key, 0)
    if attempts >= max_attempts:
        return False
    return True

def record_failed_attempt(email: str, window_seconds=900):
    cache_key = f"login_attempts:{email.lower()}"
    attempts = cache.get(cache_key, 0)
    cache.set(cache_key, attempts + 1, window_seconds)

def clear_rate_limit(email: str):
    cache.delete(f"login_attempts:{email.lower()}")
```

**Usage in login view:**
```python
if not check_rate_limit(email):
    return Response(
        {"error": "Too many failed attempts. Try again in 15 minutes."},
        status=429,
    )

if not user.check_password(password):
    record_failed_attempt(email)
    return Response({"error": "Invalid credentials."}, status=401)

clear_rate_limit(email)   # Success — reset counter
```

### 4.7 Token Rotation + Replay Detection

```python
def refresh_access_token(refresh_token: str, request):
    payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=["HS256"])

    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    session = UserSession.objects.filter(
        refresh_token_hash=token_hash,
        is_active=True,
    ).first()

    if not session:
        # Possible replay attack — revoke ALL sessions for this user
        user_id = payload.get("user_id")
        if user_id:
            UserSession.objects.filter(user_id=user_id, is_active=True).update(
                is_active=False, revoked_at=timezone.now()
            )
        return Response({"error": "Session revoked."}, status=401)

    # Rotate token
    new_tokens = generate_tokens(session.user, session, request)
    new_hash = hashlib.sha256(new_tokens["refreshToken"].encode()).hexdigest()
    session.refresh_token_hash = new_hash
    session.last_used_at = timezone.now()
    session.save(update_fields=["refresh_token_hash", "last_used_at"])

    return Response(new_tokens)
```

### 4.8 CSRF Protection (cookie/session auth only)

CSRF protection is **only required when using cookie-based sessions or httpOnly cookie JWT**. JWT in Authorization Bearer headers is inherently CSRF-safe.

**Decision rule:**
```
Auth transport == cookie or session  →  CSRF protection REQUIRED
Auth transport == JWT Bearer header  →  CSRF protection NOT needed
```

**Django (built-in middleware):**
```python
# settings.py — already in MIDDLEWARE by default
MIDDLEWARE = [
    ...
    'django.middleware.csrf.CsrfViewMiddleware',   # Add if missing
    ...
]

# For DRF cookie-based auth — enforce CSRF on all non-safe methods
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',  # Enforces CSRF
    ],
}

# Cookie settings
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True          # HTTPS only
SESSION_COOKIE_SAMESITE = 'Lax'       # Prevents CSRF on cross-site requests
CSRF_COOKIE_HTTPONLY = False          # Must be False so JS can read CSRF token
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = 'Lax'
```

**Express / Node:**
```bash
npm install csurf cookie-parser    # csurf depends on cookie-parser
```
```javascript
const csrf = require('csurf');
const cookieParser = require('cookie-parser');

app.use(cookieParser());
app.use(csrf({ cookie: { httpOnly: true, secure: true, sameSite: 'lax' } }));

// Expose token to frontend
app.get('/csrf-token', (req, res) => res.json({ csrfToken: req.csrfToken() }));

// Attach token to all state-changing responses
app.use((req, res, next) => {
    res.cookie('XSRF-TOKEN', req.csrfToken(), { sameSite: 'lax', secure: true });
    next();
});
```

**NestJS:**
```bash
npm install csurf
```
```typescript
import * as csurf from 'csurf';
// In main.ts:
app.use(csurf({ cookie: { httpOnly: true, secure: true, sameSite: 'lax' } }));
```

**Laravel (built-in):**
```php
// Already in Kernel.php web middleware group:
\App\Http\Middleware\VerifyCsrfToken::class

// Cookie settings in config/session.php:
'secure' => env('SESSION_SECURE_COOKIE', true),
'http_only' => true,
'same_site' => 'lax',
```

**.NET / ASP.NET Core:**
```csharp
// Program.cs
builder.Services.AddAntiforgery(options => {
    options.HeaderName = "X-CSRF-TOKEN";
    options.Cookie.HttpOnly = true;
    options.Cookie.SecurePolicy = CookieSecurePolicy.Always;
    options.Cookie.SameSite = SameSiteMode.Lax;
});
app.UseAntiforgery();
```

**SameSite cookie configuration (all frameworks):**
```
SameSite=Lax    → Recommended default. Cookies sent on top-level navigation, blocked on cross-site POST.
SameSite=Strict → Strictest. Cookies not sent on any cross-site request (may break OAuth redirects).
SameSite=None   → Only use with Secure=true and when cross-site cookies are explicitly needed.
```

---

### 4.9 Security Headers (framework-specific)

Apply security headers on **every response**, not just auth endpoints.

**Headers required and their purpose:**
```
Strict-Transport-Security  → Force HTTPS, prevent downgrade attacks
X-Frame-Options            → Prevent clickjacking
X-Content-Type-Options     → Prevent MIME sniffing
Content-Security-Policy    → Restrict resource loading sources
Referrer-Policy            → Control referrer header leakage
Permissions-Policy         → Disable unused browser features
```

**Django:**
```python
# settings.py
SECURE_HSTS_SECONDS = 31536000          # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True      # X-Content-Type-Options: nosniff
X_FRAME_OPTIONS = 'DENY'               # X-Frame-Options: DENY
SECURE_BROWSER_XSS_FILTER = True        # Legacy X-XSS-Protection

# Add django-csp for Content-Security-Policy
pip install django-csp

# settings.py with CSP
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")  # Tighten if possible
CSP_IMG_SRC = ("'self'", "data:")
CSP_FRAME_ANCESTORS = ("'none'",)

MIDDLEWARE = [
    'csp.middleware.CSPMiddleware',
    ...
]

# Referrer-Policy via custom middleware or whitenoise
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
```

**Express / Node:**
```bash
npm install helmet
```
```javascript
const helmet = require('helmet');

app.use(helmet({
    hsts: { maxAge: 31536000, includeSubDomains: true, preload: true },
    frameguard: { action: 'deny' },
    noSniff: true,
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            scriptSrc: ["'self'"],
            styleSrc: ["'self'", "'unsafe-inline'"],
            imgSrc: ["'self'", "data:"],
            frameAncestors: ["'none'"],
        },
    },
    referrerPolicy: { policy: 'strict-origin-when-cross-origin' },
    permissionsPolicy: {
        features: {
            camera: [],
            microphone: [],
            geolocation: [],
        },
    },
}));
```

**NestJS:**
```typescript
// main.ts
import helmet from 'helmet';
app.use(helmet({
    hsts: { maxAge: 31536000, includeSubDomains: true },
    frameguard: { action: 'deny' },
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            frameAncestors: ["'none'"],
        },
    },
}));
```

**Laravel:**
```php
// app/Http/Middleware/SecurityHeaders.php
public function handle($request, Closure $next) {
    $response = $next($request);
    $response->headers->set('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
    $response->headers->set('X-Frame-Options', 'DENY');
    $response->headers->set('X-Content-Type-Options', 'nosniff');
    $response->headers->set('Referrer-Policy', 'strict-origin-when-cross-origin');
    $response->headers->set('Content-Security-Policy', "default-src 'self'");
    $response->headers->set('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');
    return $response;
}

// Register in Kernel.php $middleware array
```

**.NET / ASP.NET Core:**
```csharp
// Program.cs
app.UseHsts();   // Adds HSTS header (configure in AddHsts)
app.Use(async (context, next) => {
    context.Response.Headers.Add("X-Frame-Options", "DENY");
    context.Response.Headers.Add("X-Content-Type-Options", "nosniff");
    context.Response.Headers.Add("Referrer-Policy", "strict-origin-when-cross-origin");
    context.Response.Headers.Add("Content-Security-Policy", "default-src 'self'");
    context.Response.Headers.Add("Permissions-Policy", "camera=(), microphone=()");
    await next();
});

// appsettings.json
builder.Services.AddHsts(options => {
    options.MaxAge = TimeSpan.FromDays(365);
    options.IncludeSubDomains = true;
    options.Preload = true;
});
```

**Go (Gin):**
```go
func SecurityHeaders() gin.HandlerFunc {
    return func(c *gin.Context) {
        c.Header("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        c.Header("X-Frame-Options", "DENY")
        c.Header("X-Content-Type-Options", "nosniff")
        c.Header("Referrer-Policy", "strict-origin-when-cross-origin")
        c.Header("Content-Security-Policy", "default-src 'self'")
        c.Header("Permissions-Policy", "camera=(), microphone=()")
        c.Next()
    }
}

// Register:
router.Use(SecurityHeaders())
```

---

### 4.10 Encryption Key Management

All secrets used for auth (JWT signing key, TOTP encryption key, session secret) must be:
1. Generated securely
2. Stored outside the codebase
3. Never hardcoded or logged

**Key generation (production-safe):**
```bash
# JWT / session secret (32 bytes = 256-bit)
python -c "import secrets; print(secrets.token_hex(32))"
# or
openssl rand -hex 32
# or
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

**Storage tiers (choose based on environment):**

| Environment | Storage Method |
|-------------|---------------|
| Development | `.env` file (never commit) |
| Staging | CI/CD env vars (GitHub Actions secrets, GitLab CI vars) |
| Production (basic) | Platform env vars (Heroku config, Railway, Fly.io secrets) |
| Production (standard) | AWS Parameter Store / GCP Secret Manager / Azure Key Vault |
| Production (enterprise) | HashiCorp Vault / AWS KMS with envelope encryption |

**Loading pattern — detect what the project uses:**

```python
# Django — python-dotenv or os.environ
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.environ["AUTH_SECRET_KEY"]   # Fail loudly if missing

# Never:
SECRET_KEY = "hardcoded-value"
SECRET_KEY = os.environ.get("AUTH_SECRET_KEY", "fallback")  # fallback = silent failure
```

```javascript
// Node — dotenv
require('dotenv').config();
const JWT_SECRET = process.env.JWT_SECRET;
if (!JWT_SECRET) throw new Error('JWT_SECRET is not set');

// Never:
const JWT_SECRET = process.env.JWT_SECRET || 'fallback';
```

**TOTP secret encryption at the application level (if DB-level encryption is unavailable):**
```python
# AES-256 encryption for TOTP secrets (use when pgcrypto not available)
from cryptography.fernet import Fernet
import os, base64

TOTP_ENCRYPTION_KEY = os.environ["TOTP_ENCRYPTION_KEY"]   # 32-byte base64 key
fernet = Fernet(TOTP_ENCRYPTION_KEY)

def encrypt_totp_secret(raw_bytes: bytes) -> bytes:
    return fernet.encrypt(raw_bytes)

def decrypt_totp_secret(encrypted: bytes) -> bytes:
    return fernet.decrypt(encrypted)
```

**Generate TOTP encryption key:**
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())   # Store this as TOTP_ENCRYPTION_KEY
```

**Environment variables to generate (all modes):**
```bash
# Generate and add to .env / secret manager — never commit plain values
AUTH_SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)
TOTP_ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
```

**Key rotation rule:** Rotating `JWT_SECRET` invalidates all active tokens — plan for graceful rotation by supporting multiple valid signing keys simultaneously during the rotation window.

---

### 4.11 RBAC (Mode 3+)

```python
# User model additions
class UserRole(models.TextChoices):
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    VIEWER = "viewer"

# Add to User model:
role = CharField(max_length=50, choices=UserRole.choices, default=UserRole.MEMBER)
# OR for complex permissions:
permissions = ArrayField(CharField(max_length=100), default=list)

# DRF permission class
class HasPermission(BasePermission):
    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return self.required_permission in (request.user.permissions or [])
```

### 4.12 Audit Logging (Mode 3+)

```python
# AuditLog model
class AuditLog(models.Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    user = ForeignKey(User, null=True, on_delete=SET_NULL)
    event_type = CharField(max_length=100, db_index=True)  # USER_LOGIN, MFA_SETUP, etc.
    status = CharField(max_length=20)                       # success | failure
    ip_address = GenericIPAddressField(null=True)
    user_agent = TextField(blank=True)
    error_message = TextField(blank=True)
    details = JSONField(default=dict)
    created_at = DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

# Mode 4: never allow deletion of audit logs
# Add to Meta: def delete(self): raise PermissionError("Audit logs are immutable")

def log_auth_event(event_type: str, user=None, request=None, status="success", **kwargs):
    AuditLog.objects.create(
        user=user,
        event_type=event_type,
        status=status,
        ip_address=get_client_ip(request) if request else None,
        user_agent=request.META.get("HTTP_USER_AGENT", "") if request else "",
        details=kwargs,
    )

# Log these events:
# USER_LOGIN, USER_LOGOUT, LOGIN_FAILED, PASSWORD_CHANGED
# MFA_SETUP, MFA_ENABLED, MFA_DISABLED, MFA_VERIFIED, MFA_FAILED
# BIOMETRIC_REGISTERED, BIOMETRIC_LOGIN, SESSION_REVOKED
# PASSWORD_RESET_REQUESTED, PASSWORD_RESET_COMPLETED
# EMAIL_VERIFIED, ACCOUNT_SUSPENDED (Mode 3+)
```

---

---

## Step 6 — Generate Auth Infrastructure

Generate files in this order: **backend first → get approval → then frontend**.

### 6a. Backend Generation

Generate all backend files based on the detected stack and chosen mode. After generating each file, confirm it was written successfully before moving on.

When all backend files are done, use AskUserQuestion:

```js
AskUserQuestion({
  questions: [{
    question: "Backend auth files generated. What next?",
    header: "Next",
    multiSelect: false,
    options: [
      {
        label: "Generate frontend (Recommended)",
        description: "Build the auth pages — login, register, MFA setup, dashboard"
      },
      {
        label: "Test backend first",
        description: "I'll test the API endpoints before you generate frontend"
      },
      {
        label: "Backend only — done",
        description: "Skip frontend generation entirely"
      }
    ]
  }]
})
```

### 6b. Frontend Generation

Generate auth pages in this order:
1. `lib/api.[ext]` — fetch wrapper with CSRF + token handling
2. `lib/auth.[ext]` — typed auth functions
3. `context/AuthContext.[ext]` — auth state provider
4. `app/login/` → `app/register/` → `app/dashboard/`
5. `app/verify-email/` → `app/forgot-password/` → `app/reset-password/`
6. `app/mfa/setup/` → `app/mfa/verify/` (Mode 2+ only)

---

## Step 5 — Mode Upgrade / Migration Path

When upgrading from one mode to a higher mode, all changes must be **additive and non-breaking**. Never drop columns, delete routes, or change existing field types.

### Upgrade Selection — Use AskUserQuestion

When a developer asks to upgrade, first confirm current mode (from logs or codebase), then ask which target mode they want. Load with `ToolSearch` → `select:AskUserQuestion` if not already loaded.

```js
AskUserQuestion({
  questions: [
    {
      question: "Which mode do you want to upgrade TO?",
      header: "Upgrade To",
      multiSelect: false,
      options: [
        {
          label: "Mode 2 · Secure Auth",
          description: "Add TOTP 2FA, biometric (mobile), refresh token rotation, session tracking",
        },
        {
          label: "Mode 3 · Enterprise Auth",
          description: "Add RBAC roles & permissions, audit logging, per-session revocation",
        },
        {
          label: "Mode 4 · HIPAA Secure",
          description: "Add HIPAA consent, immutable audit logs, enforced MFA for providers",
        }
      ]
    },
    {
      question: "Are you upgrading from a clean Mode N install done by this skill?",
      header: "Source State",
      multiSelect: false,
      options: [
        { label: "Yes — skill-generated codebase", description: "I know exactly what fields and tables exist" },
        { label: "No — existing custom codebase",  description: "Read the existing models before proposing any migrations" }
      ]
    }
  ]
})
```

After getting the answer — follow the relevant upgrade section below, then use the Step 4 architecture proposal + approval widget to show what will change before writing anything.

### Mode 1 → Mode 2 (Add TOTP + Biometric)

**Database migrations (additive only):**
```python
# Django migration — adds MFA fields to existing User table
migrations.AddField('User', 'mfa_enabled', models.BooleanField(default=False))
migrations.AddField('User', 'mfa_secret', models.BinaryField(null=True, blank=True))
migrations.AddField('User', 'mfa_enrolled_at', models.DateTimeField(null=True))
```

**New tables to create:**
- `MFARecoveryCode` — TOTP recovery codes
- `UserSession` — device session tracking (if not already present)

**New endpoints to add (non-breaking):**
```
POST /auth/mfa/setup/        → Generate TOTP secret + QR
POST /auth/mfa/enable/       → Verify first TOTP code, activate
POST /auth/mfa/verify/       → Verify code during login
POST /auth/mfa/disable/      → Disable MFA (non-HIPAA only)
POST /auth/biometric/register/
POST /auth/biometric/login/
```

**Existing login endpoint change:**
- If user has `mfa_enabled=True` → return `mfaRequired: true` + partial token instead of full tokens
- Backwards compatible: users without MFA still get full tokens on login

**Frontend upgrade checklist:**
- [ ] Add MFA setup screen
- [ ] Add TOTP prompt screen on login
- [ ] Add biometric toggle in security settings
- [ ] Add biometric login button on login screen

**New dependencies to install:** `pyotp`, `qrcode[pil]`, `expo-local-authentication`, `react-native-qrcode-svg`

---

### Mode 2 → Mode 3 (Add RBAC + Audit Logs)

**Database migrations:**
```python
# Add role field to User
migrations.AddField('User', 'role', models.CharField(
    max_length=50, default='member',
    choices=[('admin','admin'),('manager','manager'),('member','member'),('viewer','viewer')]
))
# Add permissions array (PostgreSQL)
migrations.AddField('User', 'permissions', ArrayField(
    models.CharField(max_length=100), default=list, blank=True
))
```

**New tables to create:**
- `AuditLog` — auth event log

**New endpoints to add:**
```
GET  /auth/sessions/         → List active sessions
DELETE /auth/sessions/{id}/  → Revoke specific session
GET  /auth/audit-log/        → View auth events (admin only)
```

**Middleware to add:**
- Role/permission check middleware on all protected routes
- Audit logging middleware (wraps all auth endpoints)

**No breaking changes:** existing sessions and tokens remain valid. Role defaults to `member` for all existing users.

---

### Mode 3 → Mode 4 (Add HIPAA Compliance)

**Database changes:**
```python
# Add HIPAA consent fields to User
migrations.AddField('User', 'hipaa_consent_accepted', models.BooleanField(default=False))
migrations.AddField('User', 'hipaa_consent_version', models.CharField(max_length=20, null=True))
migrations.AddField('User', 'hipaa_consent_at', models.DateTimeField(null=True))

# Make AuditLog immutable — add DB-level trigger or override delete()
# Shorten token lifetimes in settings (no migration needed, takes effect on next login)
```

**Token lifetime changes:**
```python
# Update settings — affects new tokens only, existing tokens honored until expiry
REFRESH_TOKEN_LIFETIME_DAYS = 1    # Was 7
```

**Enforcement changes:**
- Add `ProviderMFARequired` permission class: returns 403 if provider has `mfa_enabled=False`
- Add HIPAA consent gate: new users must accept consent before any auth token is issued

**Existing users:** not forced to re-auth. HIPAA consent can be collected on next login via a consent screen — do not invalidate existing sessions.

**AuditLog immutability enforcement:**
```python
class AuditLog(models.Model):
    ...
    def delete(self, *args, **kwargs):
        raise PermissionError("AuditLog records are immutable and cannot be deleted.")

    class Meta:
        # Prevent bulk deletes via queryset
        # Override in admin: readonly_fields = '__all__'
```

---

### Mode Upgrade Summary Table

| Upgrade | New Tables | New Fields on User | Breaking Changes |
|---------|-----------|-------------------|-----------------|
| 1 → 2 | MFARecoveryCode, UserSession | mfa_enabled, mfa_secret, mfa_enrolled_at | None |
| 2 → 3 | AuditLog | role, permissions | None |
| 3 → 4 | None | hipaa_consent_accepted, hipaa_consent_version, hipaa_consent_at | None |

All upgrades are additive. All existing data, sessions, and tokens remain valid.

---

## Step 6 — Security Hardening Pass (run after generation)

After generating all auth code, verify each item:

### Checklist

**Request Validation**
- [ ] Email format validated on all auth endpoints
- [ ] Password strength enforced (min 12 chars, complexity)
- [ ] TOTP code format validated (6 digits, numeric only)
- [ ] All request bodies sanitized

**Rate Limiting**
- [ ] Login endpoint: 5 attempts / 15-min window
- [ ] TOTP verify: 10 attempts / 10-min window
- [ ] Password reset: 3 requests / 60-min window
- [ ] Biometric login: 10 attempts / 15-min window

**Token Security**
- [ ] Refresh tokens stored as SHA-256 hashes only (never plain)
- [ ] Token rotation implemented on every refresh
- [ ] Replay attack detection (revoke all sessions)
- [ ] Biometric device tokens bound to device fingerprint
- [ ] MFA partial tokens expire in 5 minutes

**Session Security**
- [ ] Max sessions per user enforced (default: 5, biometric: 3)
- [ ] Session expiration validated on every request
- [ ] Device fingerprint validated on biometric login

**Password Security**
- [ ] Bcrypt (cost ≥12), Argon2, or PBKDF2 (≥260,000 iterations)
- [ ] Password reset tokens are single-use + expiring (24h)
- [ ] Password reset rate limited
- [ ] Enumeration prevention (same response for unknown email)

**TOTP Security**
- [ ] Secrets stored encrypted (binary field + DB encryption, or app-level AES)
- [ ] Recovery codes hashed (SHA-256), single-use
- [ ] QR URI never logged

**CSRF Protection**
- [ ] Detect auth transport: cookie/session vs JWT Bearer
- [ ] If cookie/session: CSRF middleware installed and active
- [ ] CSRF token exposed via `/csrf-token` endpoint or cookie for SPA
- [ ] `SESSION_COOKIE_SAMESITE = 'Lax'` (or Strict)
- [ ] `SESSION_COOKIE_HTTPONLY = True`
- [ ] `SESSION_COOKIE_SECURE = True`
- [ ] `CSRF_COOKIE_SECURE = True`
- [ ] If JWT Bearer: confirm no CSRF middleware needed (document this explicitly)

**Transport & Cookies**
- [ ] HTTPS enforced in production
- [ ] All auth cookies: httpOnly=True, secure=True, samesite="lax"

**Mobile Storage**
- [ ] Access/refresh tokens in SecureStore (never AsyncStorage)
- [ ] Biometric device token in SecureStore
- [ ] No auth secrets in AsyncStorage or plain files

**Security Headers (web)**
- [ ] `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
- [ ] `X-Frame-Options: DENY`
- [ ] `X-Content-Type-Options: nosniff`
- [ ] `Content-Security-Policy: default-src 'self'` (at minimum)
- [ ] `Referrer-Policy: strict-origin-when-cross-origin`
- [ ] `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- [ ] Framework-specific header middleware installed (helmet / django-csp / SecurityHeaders middleware)

**Encryption Key Security**
- [ ] All secrets loaded from env vars — no hardcoded values anywhere
- [ ] No `os.environ.get("KEY", "fallback")` patterns — fail loudly on missing keys
- [ ] TOTP secrets stored encrypted (binary field + DB encryption or Fernet)
- [ ] JWT secret is ≥256 bits (32 bytes / 64 hex chars)
- [ ] `.env` file is in `.gitignore`
- [ ] `.env.example` committed with placeholder values only

### Hardening Findings — Use AskUserQuestion

After running through the checklist, report findings and ask how to proceed:

First output a plain-text findings report:

```
 ──────────────────────────────────────────────────────────
  🔍  SECURITY HARDENING FINDINGS
 ──────────────────────────────────────────────────────────
  ✓  [N] checks passed
  ⚠  [N] gaps found:
     · [gap 1 — e.g. no HSTS header in production config]
     · [gap 2 — e.g. JWT_SECRET has a fallback value]
     · [gap 3 — ...]
 ──────────────────────────────────────────────────────────
```

Then call AskUserQuestion:

```js
AskUserQuestion({
  questions: [{
    question: "Security hardening found [N] gaps. What would you like to do?",
    header: "Hardening",
    multiSelect: false,
    options: [
      {
        label: "Fix all gaps now (Recommended)",
        description: "Patch each gap automatically before generating the security summary"
      },
      {
        label: "Fix critical gaps only",
        description: "Fix token security + CSRF issues; leave header/key improvements for later"
      },
      {
        label: "Skip fixes — show summary",
        description: "Note gaps in the security review summary but don't modify files"
      }
    ]
  }]
})
```

If no gaps were found, skip the widget and proceed directly to Step 9.

---

## Step 7 — Non-Breaking Integration Rules

Before generating files:
1. Read existing auth files — never assume they don't exist
2. Identify the existing User model — extend it, don't replace it
3. Follow the existing folder/naming conventions
4. List every file that will be created or modified — get approval before overwriting
5. Generate additive migrations, never destructive ones
6. Mark integration points clearly: `# AUTH_INTEGRATION_POINT — add this to your existing file`

If there's an existing auth system, note exactly what changes and why.

---

## Step 8 — Environment Variables

Generate `.env.example` additions — never overwrite existing values:

```bash
# Auth Core
AUTH_SECRET_KEY=generate-with-secrets.token-hex-32
JWT_ALGORITHM=HS256

# TOTP (Mode 2+)
TOTP_ISSUER=YourAppName

# Session limits
MAX_SESSIONS_PER_USER=5
MAX_BIOMETRIC_DEVICES=3
ACCESS_TOKEN_LIFETIME_MINUTES=15
REFRESH_TOKEN_LIFETIME_DAYS=7

# Rate limiting
RATE_LIMIT_LOGIN_ATTEMPTS=5
RATE_LIMIT_WINDOW_SECONDS=900

# Redis (for rate limiting + sessions)
REDIS_URL=redis://localhost:6379/0
```

Detect how the project currently loads env vars (python-dotenv, dotenv npm, Laravel .env, os.environ) and match that pattern.

---

## Step 9 — Security Review Summary

Output this as plain text at the end of every auth generation (fill in all bracketed values):

```
 ──────────────────────────────────────────────────────────
  🔒  SECURITY REVIEW SUMMARY
 ──────────────────────────────────────────────────────────
  Auth Mode  :  [N] — [mode name]
  Stack      :  [backend] + [frontend] + [database]
  Transport  :  [httpOnly cookie JWT | Bearer token | session]
 ──────────────────────────────────────────────────────────

  Protections Implemented
  ✓  [list each protection that was added]

  Vulnerabilities Mitigated
  ✓  Credential stuffing   — rate limiting + account lockout
  ✓  Token replay          — rotation + revocation detection
  ✓  Session hijacking     — token rotation + session_id validation
  ✓  Enumeration           — consistent responses for unknown users
  ✓  TOTP secret theft     — encrypted at-rest storage          (Mode 2+)
  ✓  Biometric bypass      — device fingerprint binding         (Mode 2+ mobile)
  ✓  Clickjacking / MIME   — security headers (helmet / CSP)

  Gaps Found in Existing Code
  ⚠  [any issues discovered — or "none found"]

  Recommended Improvements (out of scope)
  →  [optional enhancements: WebAuthn, hardware keys, anomaly detection]
  →  [or "none — implementation is complete for this mode"]

 ──────────────────────────────────────────────────────────
  Next steps:
  · Set all env vars in .env (see .env.example for keys)
  · Run migrations before starting the server
  · Test: register → verify email → login → MFA setup → recovery codes
 ──────────────────────────────────────────────────────────
```

### After Summary — Use AskUserQuestion

```js
AskUserQuestion({
  questions: [{
    question: "Auth implementation is complete. What would you like to do next?",
    header: "Next Steps",
    multiSelect: true,
    options: [
      {
        label: "Generate .env.example",
        description: "Create a committed placeholder file documenting all required secrets"
      },
      {
        label: "Show test flow",
        description: "Walk me through testing: register → verify → login → MFA → recovery"
      },
      {
        label: "Upgrade to a higher mode",
        description: "Add more security features (RBAC, HIPAA, audit logs)"
      },
      {
        label: "Done — nothing needed",
        description: "Close out the auth implementation"
      }
    ]
  }]
})
```

---

---

## Section 6 — Self-Learning

The goal is **one-shot generation**: after enough integrations, Claude should know your exact preferences, stack, and code style well enough to generate everything in a single pass without asking any questions.

Two files power this:
- `integrations.jsonl` — one record per session (append-only)
- `profile.json` — cumulative preference profile (updated each session)

Both live in `~/.claude/skills/universal-auth/logs/`. Never store secrets, passwords, tokens, connection strings, real paths, or file contents in either file.

---

### 6.1 — Log Entry (append after every integration)

Capture as much as possible. Every field you fill in now reduces a question next time.

```json
{
  "timestamp": "ISO-8601",
  "project_id": "sha256_of_abs_project_path[:8]",

  "stack": {
    "backend": "node-express",
    "frontend": "nextjs",
    "database": "sqlite",
    "orm": "better-sqlite3",
    "auth_transport": "httponly-cookie-jwt",
    "language": "typescript",
    "css_framework": "tailwind"
  },

  "selections": {
    "mode": 2,
    "mode_was_recommended": true,
    "mode_override": false,
    "database": "sqlite",
    "auth_transport": "httponly-cookie-jwt",
    "email": "console",
    "frontend": "build-new",
    "install_preference": "install-all",
    "generation_split": "backend-then-frontend",
    "hardening_choice": "fix-all",
    "post_summary_actions": ["generate-env-example", "show-test-flow"]
  },

  "code_style": {
    "quotes": "double",
    "semicolons": true,
    "indent": "2-spaces",
    "trailing_commas": true,
    "naming_functions": "camelCase",
    "naming_files": "kebab-case",
    "naming_vars": "camelCase",
    "file_extension": ".js",
    "folder_structure": "src/routes src/middleware src/utils src/db"
  },

  "architecture": {
    "approved_as_proposed": true,
    "modifications_requested": [],
    "files_created": [],
    "files_modified_existing": []
  },

  "security": {
    "gaps_found": 0,
    "gaps_fixed": [],
    "gaps_skipped": []
  },

  "fixes_requested_after_generation": [],

  "questions": {
    "asked": ["database"],
    "skipped_with_reason": ["email — console stub detected from existing code"],
    "answers": {
      "database": "sqlite",
      "auth_transport": "httponly-cookie-jwt",
      "email": "console",
      "frontend": "build-new"
    }
  },

  "one_shot_eligible": false,
  "one_shot_blocked_by": ["database question still ambiguous"]
}
```

---

### 6.2 — Profile File (update after every integration)

Read this at Step 0. Write updated version at Step 10. File: `profile.json`.

```json
{
  "last_updated": "ISO-8601",
  "total_integrations": 0,

  "confidence": {
    "mode": "LOW",
    "database": "LOW",
    "auth_transport": "LOW",
    "email": "LOW",
    "frontend_choice": "LOW",
    "install_preference": "LOW",
    "hardening_choice": "LOW",
    "generation_split": "LOW"
  },

  "defaults": {
    "mode": null,
    "database": null,
    "auth_transport": null,
    "email": null,
    "frontend_choice": null,
    "install_preference": null,
    "hardening_choice": null,
    "post_summary_actions": []
  },

  "code_style": {
    "quotes": null,
    "semicolons": null,
    "indent": null,
    "trailing_commas": null,
    "naming_functions": null,
    "naming_files": null,
    "naming_vars": null
  },

  "common_fixes": [],

  "stack_history": {}
}
```

**Confidence thresholds:**

| Consistent answers across N sessions | Confidence | Action |
|--------------------------------------|------------|--------|
| 0 | LOW | Ask the question normally |
| 1–2 | MEDIUM | Ask but pre-select the likely answer |
| 3–4 | HIGH | Skip the widget, note assumption inline |
| 5+ | VERY HIGH | Skip silently, include in one-shot summary |

Update `confidence` field for each key after every session based on how many past sessions gave the same answer.

---

### 6.3 — Step 0: Reading Profile & Applying Learning

At the very start (before Step 1), read both files:

```
1. Read profile.json → load defaults + confidence levels
2. Read integrations.jsonl → compute stack_history for this stack combo

stack_key = backend + "+" + frontend + "+" + database + "+" + auth_transport
```

Then decide which interaction mode to use:

**Normal mode** (< 3 consistent integrations):
- Run all AskUserQuestion widgets as normal
- Pre-select HIGH/VERY HIGH confidence answers but still show the widget

**Accelerated mode** (3–4 consistent integrations):
- Skip LOW-value widgets (install preference, generation split, post-summary)
- Show a single combined summary of what was auto-applied before proceeding
- Still show mode selection and clarifying questions

**One-shot mode** (5+ consistent integrations, `one_shot_eligible: true` in last entry):
- Skip ALL widgets except a single confirmation
- Show this banner instead:

```
 ──────────────────────────────────────────────────────────
  ⚡  ONE-SHOT MODE  —  Based on [N] past integrations
 ──────────────────────────────────────────────────────────
  Auto-applying your preferences:
  · Mode      [N] — [name]
  · Stack     [backend] + [frontend] + [database]
  · Transport [auth_transport]
  · Email     [email]
  · Style     [quotes] quotes · [indent] · [naming]
  · Install   [install_preference]
  · Hardening [hardening_choice]
  · After     [post_summary_actions]
 ──────────────────────────────────────────────────────────
```

Then use ONE confirmation widget:

```js
AskUserQuestion({
  questions: [{
    question: "Everything look right? I'll generate the full auth system now.",
    header: "One-Shot",
    multiSelect: false,
    options: [
      { label: "Go — generate everything", description: "Run the full implementation with these settings" },
      { label: "Adjust a setting",         description: "Change one or more preferences before generating" },
      { label: "Reset to guided mode",     description: "Walk me through each step manually this time" }
    ]
  }]
})
```

---

### 6.4 — What to Capture from Code Style

When running Step 1 (Project Intelligence Analysis), also detect code style from existing files:

| Signal | What to detect |
|--------|----------------|
| Existing `.js`/`.ts` files | quotes (single vs double), semicolons, trailing commas, indent size |
| File names in the project | naming convention (kebab-case, camelCase, snake_case) |
| Function names in existing code | camelCase vs snake_case |
| Folder structure | how src is organized (routes/, controllers/, services/ etc.) |
| `package.json` → `prettier`, `.eslintrc`, `tsconfig.json` | override with explicit config if present |

Save this to both the log entry `code_style` and update `profile.json` `code_style`. Apply these when generating ALL code — variable names, function names, file names, folder structure.

---

### 6.5 — What to Capture from Each Widget Answer

Track every AskUserQuestion answer by key so the profile can learn from them:

| Widget | Key to store |
|--------|-------------|
| Mode selection | `selections.mode`, `mode_was_recommended`, `mode_override` |
| Database | `selections.database` + `questions.answers.database` |
| Auth transport | `selections.auth_transport` |
| Email | `selections.email` |
| Frontend | `selections.frontend_choice` |
| Install preference | `selections.install_preference` |
| Architecture approval | `architecture.approved_as_proposed`, `modifications_requested` |
| Backend/frontend split | `selections.generation_split` |
| Hardening choice | `selections.hardening_choice`, `security.gaps_fixed`, `security.gaps_skipped` |
| Post-summary | `selections.post_summary_actions` |

Also capture anything the user types into "Other" fields — these reveal preferences that aren't in the default options yet.

---

### 6.6 — Capturing Fixes Requested After Generation

If the developer asks for any changes after code is generated (e.g. "change the cookie path", "add rate limit to MFA verify", "use arrow functions instead"), log each as a plain English string in `fixes_requested_after_generation`. After 2+ integrations with the same fix, add it to `profile.json` `common_fixes` and apply it automatically next time (no need to ask).

---

### 6.7 — One-Shot Eligibility

After completing Step 10, compute whether the next integration would be eligible for one-shot mode:

```
one_shot_eligible = true  IF ALL of:
  · total_integrations >= 5
  · same stack_key seen 5+ times
  · all confidence levels for this stack are HIGH or VERY HIGH
  · architecture.approved_as_proposed = true in last 3 sessions
  · no modifications_requested in last 3 sessions
  · common_fixes list has stabilized (same 2+ sessions)
```

Write `one_shot_eligible: true/false` to both the log entry and `profile.json`.

---

### 6.8 — File Setup & Security

```bash
mkdir -p ~/.claude/skills/universal-auth/logs
chmod 700 ~/.claude/skills/universal-auth/logs
touch ~/.claude/skills/universal-auth/logs/integrations.jsonl
touch ~/.claude/skills/universal-auth/logs/profile.json
chmod 600 ~/.claude/skills/universal-auth/logs/integrations.jsonl
chmod 600 ~/.claude/skills/universal-auth/logs/profile.json
```

**Non-negotiable rules:**
- Never log secrets, tokens, passwords, connection strings, file contents, or real project paths
- Never auto-proceed past an AskUserQuestion result without reading the answer
- Never learn to skip a security checklist item — security checks always run
- Never overwrite existing project files without showing the change and getting approval
- All auto-applied preferences are shown in the one-shot summary before any code is written — the developer can always override

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Storing refresh tokens in plain text | Always SHA-256 hash before persisting |
| TOTP secret in char field | Use BinaryField + DB-level encryption or Fernet |
| Biometric tokens not bound to device | Validate `device_fingerprint` on every biometric login |
| AsyncStorage for tokens (React Native) | Use `expo-secure-store` for all auth tokens |
| No replay detection on refresh | On token reuse: revoke ALL user sessions |
| Rate limiting only on IP | Also rate limit on email/username |
| Generic 404 for unknown user at login | Return same error as wrong password (prevent enumeration) |
| MFA token valid forever | MFA partial token must expire (5 min max) |
| Recovery codes stored plain text | SHA-256 hash each code, single-use flag |
| Biometric setup without re-auth | Always require fresh authentication before registering biometric |
| No CSRF on cookie-based auth | Detect auth transport first — install middleware if cookie/session |
| Skipping CSRF for JWT Bearer | JWT Bearer is inherently CSRF-safe — document this, don't add unneeded middleware |
| Security headers missing | Add `helmet` (Node), `django-csp` + `SECURE_*` settings (Django), or per-framework equivalent |
| Hardcoded `SECRET_KEY = "dev-secret"` | Fail loudly on missing env var — never use fallback values for secrets |
| `os.environ.get("KEY", "fallback")` | Use `os.environ["KEY"]` — silent fallback hides misconfiguration |
| Mode upgrade drops columns | All mode upgrades are additive — only add fields/tables, never remove |
| Upgrading mode invalidates all sessions | Token lifetimes only change for new tokens — existing sessions honored until natural expiry |
| No `.env.example` in repo | Always commit `.env.example` with placeholder values to document required secrets |
