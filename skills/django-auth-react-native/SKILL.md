---
name: django-auth-react-native
description: Complete, production-ready Django authentication system for React Native applications. This skill should be used when building a new Django + React Native project that needs authentication, implementing JWT-based authentication with refresh tokens, adding email verification and OTP functionality, setting up password reset workflows, implementing multi-device session management, building multi-tenant SaaS applications, or migrating from session-based to token-based authentication. Provides complete backend and frontend templates with security best practices built-in.
---

# Django Authentication for React Native

## Overview

This skill provides a comprehensive, production-ready authentication system for Django backend + React Native frontend applications. It includes complete implementations for user registration, login, email verification, password reset, session management, and optional multi-tenant support.

## Quick Start Workflow

### Step 1: Choose Implementation Approach

**Option A: Full Implementation** (Recommended for new projects)
- Use all template files to set up complete authentication system
- Includes user model, views, serializers, services, and React Native integration
- Best for: New projects starting from scratch

**Option B: Partial Implementation** (For existing projects)
- Pick specific components you need (e.g., just OTP service or JWT setup)
- Integrate with existing user model and authentication
- Best for: Adding features to existing authentication system

### Step 2: Install Dependencies

**Backend Requirements:**
```bash
pip install django==5.2.6
pip install djangorestframework==3.14.0
pip install djangorestframework-simplejwt==5.5.1
pip install django-cors-headers==4.3.1
pip install django-allauth==0.57.0
pip install celery==5.5.3
pip install redis==7.0.0
```

**Frontend Requirements:**
```bash
npm install @react-native-async-storage/async-storage
npm install expo-secure-store expo-device expo-constants
```

### Step 3: Set Up Django Backend

1. **Create accounts app**: `python manage.py startapp accounts`

2. **Copy template files** from `assets/django_templates/`:
   - `models.py.template` → `accounts/models.py`
   - `views.py.template` → `accounts/views.py`
   - `serializers.py.template` → `accounts/serializers.py`
   - `middleware.py.template` → `accounts/middleware.py`
   - `urls.py.template` → `accounts/urls.py`
   - `services/otp_service.py.template` → `accounts/services/otp_service.py`
   - `services/email_service.py.template` → `accounts/services/email_service.py`

3. **Update settings.py** with JWT configuration, CORS headers, and custom user model

4. **Run migrations**: `python manage.py migrate`

### Step 4: Set Up React Native Frontend

1. **Copy auth service**: `assets/react_native_templates/authService.js.template` → `services/authService.js`

2. **Update API URL** in authService.js for your backend

3. **Create Auth Context** for state management

4. **Implement auth screens** using the auth service

## Core Features

### 1. Custom User Model with Email Authentication
- UUID primary keys for security
- Email-based authentication (no username)
- Role-based access control (admin, manager, employee, customer)
- Profile fields (name, phone, profile picture)
- Optional multi-tenant organization support

### 2. JWT Token Management
- Access tokens (1 hour default)
- Refresh tokens (7 days default)
- Automatic token rotation on refresh
- Token blacklisting on logout
- Secure storage (SecureStore on mobile, AsyncStorage on web)

### 3. OTP Verification System
- 6-digit secure OTP generation
- Email verification flow
- Password reset flow (3-step process)
- Rate limiting (5 per hour per user, 10 per IP)
- Resend cooldown (2 minutes)
- Maximum 3 attempts per OTP

### 4. Session Management
- Track multiple devices per user
- Device fingerprinting (platform, model, version)
- Remote session revocation
- IP address and user agent tracking
- Active session listing

### 5. Security Features
- CORS configuration with platform headers
- Rate limiting middleware
- Security headers (XSS, clickjacking protection)
- Audit logging for important actions
- Password strength validation
- User enumeration prevention

## API Endpoints

### Authentication Core
- `POST /api/auth/register/` - New user registration
- `POST /api/auth/login/` - User login with JWT
- `POST /api/auth/refresh/` - Refresh access token
- `POST /api/auth/logout/` - Logout and blacklist token
- `GET /api/auth/verify/` - Verify token validity

### Email Verification
- `POST /api/auth/verify-otp/` - Verify email with OTP (auto-login after verification)
- `POST /api/auth/resend-otp/` - Resend verification code

### Password Reset (3-Step Process)
- `POST /api/auth/password-reset/request/` - Step 1: Request reset (sends OTP)
- `POST /api/auth/password-reset/verify-otp/` - Step 2: Verify OTP
- `POST /api/auth/password-reset/confirm/` - Step 3: Set new password

### Profile Management
- `GET /api/auth/profile/` - Get current user profile
- `PUT /api/auth/profile/update/` - Update profile information
- `POST /api/auth/profile/change-password/` - Change password (requires current password)
- `DELETE /api/auth/profile/delete/` - Delete account (soft or hard delete)

### Session Management
- `GET /api/auth/sessions/` - List all active sessions
- `POST /api/auth/sessions/{id}/revoke/` - Revoke specific session

## React Native Integration

### Using the Auth Service

```javascript
import authService from './services/authService';

// Registration
const userData = {
  email: 'user@example.com',
  password: 'SecurePass123!',
  password_confirm: 'SecurePass123!',
  first_name: 'John',
  last_name: 'Doe'
};
const result = await authService.register(userData);

// Login
const loginResult = await authService.login(email, password);

// Check authentication
const isAuthenticated = await authService.isAuthenticated();

// Authenticated API calls (automatic token refresh)
const response = await authService.authenticatedFetch('/api/protected-endpoint/');

// Logout
await authService.logout();
```

### Platform-Specific Considerations

**iOS:**
- Uses SecureStore for encrypted token storage
- Requires keychain sharing for app groups

**Android:**
- Uses SecureStore with Android Keystore
- Emulator uses 10.0.2.2 for localhost

**Web:**
- Uses AsyncStorage (consider localStorage for production)
- Ensure CORS is properly configured

## Customization Guide

### Adding Social Authentication

Enable social providers in Django settings:
```python
INSTALLED_APPS += [
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.apple',
]

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': 'your-client-id',
            'secret': 'your-secret',
        }
    }
}
```

### Customizing OTP Settings

In `otp_service.py`:
```python
OTP_LENGTH = 6  # Change to 8 for more security
OTP_EXPIRY_MINUTES = 10  # Adjust expiry time
MAX_ATTEMPTS = 3  # Change max verification attempts
RESEND_COOLDOWN_SECONDS = 120  # Adjust cooldown period
```

### Adding Two-Factor Authentication

1. Add TOTP fields to User model
2. Implement TOTP setup endpoint
3. Verify TOTP on login
4. Use pyotp library for TOTP generation

## Troubleshooting

### Common Issues and Solutions

**CORS Errors:**
- Add `x-platform` to CORS_ALLOW_HEADERS
- Include frontend URL in CORS_ALLOWED_ORIGINS

**Token Refresh Failures:**
- Check refresh token expiry settings
- Ensure refresh token is stored correctly
- Verify token rotation is enabled

**Email Not Sending:**
- Check EMAIL_BACKEND configuration
- Use app-specific passwords for Gmail
- Verify SMTP settings

**Rate Limiting Issues:**
- Adjust limits in RateLimitService
- Clear cache for specific users
- Check Redis connection

## Security Checklist

### Production Deployment

**Backend:**
- [ ] Set DEBUG = False
- [ ] Use environment variables for secrets
- [ ] Configure production database
- [ ] Set up Redis for caching
- [ ] Enable HTTPS only
- [ ] Configure secure CORS origins
- [ ] Set up monitoring (Sentry)
- [ ] Enable audit logging

**Frontend:**
- [ ] Update API_BASE_URL to production
- [ ] Remove console.log statements
- [ ] Enable code obfuscation
- [ ] Test on real devices
- [ ] Set up crash reporting
- [ ] Configure certificate pinning

## Resources

### Template Files

**Django Templates** (`assets/django_templates/`):
- **models.py.template** - Complete user model with sessions and OTP
- **views.py.template** - All authentication endpoints
- **serializers.py.template** - Request/response serializers
- **middleware.py.template** - JWT and security middleware
- **urls.py.template** - URL routing configuration
- **services/otp_service.py.template** - OTP generation and validation
- **services/email_service.py.template** - Email sending with templates

**React Native Templates** (`assets/react_native_templates/`):
- **authService.js.template** - Complete auth service with token management
- **authContext.js.template** - React context for auth state
- **screens/** - Login, Register, and OTP verification screens

### Scripts

**Initialization Scripts** (`scripts/`):
- **init_auth.py** - Initialize auth system in existing Django project
- **generate_models.py** - Generate custom user model code
- **setup_jwt.py** - Configure JWT settings automatically

### Reference Documentation

**API Reference** (`references/`):
- **api_endpoints.md** - Complete API documentation
- **security_best_practices.md** - Security guidelines
- **jwt_configuration.md** - JWT setup details
- **email_templates.md** - Email template examples
