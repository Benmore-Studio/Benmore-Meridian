"""
JWT token generation utilities — Universal Auth Skill template.
Stack: Django + PyJWT

IMPROVEMENTS over source:
  - session_id embedded in access token payload for revocation checking
  - generate_token_pair() accepts optional session parameter
  - Token namespace is configurable via APP_CLAIM_NAMESPACE setting
  - Removed Auth0-specific namespace (optional — re-add if using Auth0)
  - hash_token() and generate_refresh_token() consolidated here
"""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from django.conf import settings


# ============================================================================
# Settings (add these to your settings.py)
# ============================================================================
#
# JWT_SECRET_KEY = env("JWT_SECRET_KEY")          # Required — 256-bit minimum
# ACCESS_TOKEN_LIFETIME_MINUTES = 15
# REFRESH_TOKEN_LIFETIME_DAYS = 7
# DEVICE_TOKEN_LIFETIME_DAYS = 30
# APP_CLAIM_NAMESPACE = "https://yourapp.com"     # Used for custom JWT claims
# JWT_AUDIENCE = env("JWT_AUDIENCE", default="https://api.yourapp.com")
# JWT_ISSUER = env("JWT_ISSUER", default="https://yourapp.com/")


def _secret() -> str:
    """Prefer dedicated JWT secret; fall back to Django SECRET_KEY."""
    return getattr(settings, "JWT_SECRET_KEY", settings.SECRET_KEY)


def _namespace() -> str:
    return getattr(settings, "APP_CLAIM_NAMESPACE", "https://app.example.com")


def _audience() -> str:
    return getattr(settings, "JWT_AUDIENCE", "https://api.example.com")


def _issuer() -> str:
    return getattr(settings, "JWT_ISSUER", "https://example.com/")


# ============================================================================
# Token Generation
# ============================================================================


def generate_token_pair(user, session=None) -> dict[str, Any]:
    """
    Generate access + refresh token pair.

    Args:
        user: Django User instance
        session: UserSession instance (optional — embeds session_id for revocation)

    Returns:
        {"accessToken": str, "refreshToken": str, "expiresIn": int}
    """
    now = datetime.now(tz=UTC)
    ns = _namespace()

    access_payload: dict[str, Any] = {
        "sub": str(user.id),
        "iss": _issuer(),
        "aud": _audience(),
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_LIFETIME_MINUTES),
        f"{ns}/user_id": str(user.id),
        f"{ns}/user_type": user.user_type,
        "email": user.email,
        "email_verified": user.email_verified,
    }

    # Embed session_id so middleware can check for revocation
    if session is not None:
        access_payload["session_id"] = session.session_id

    # Add role/permissions for Mode 3+
    permissions = get_user_permissions(user)
    if permissions:
        access_payload[f"{ns}/permissions"] = permissions

    refresh_payload: dict[str, Any] = {
        "sub": str(user.id),
        "iss": _issuer(),
        "aud": _audience(),
        "iat": now,
        "exp": now + timedelta(days=settings.REFRESH_TOKEN_LIFETIME_DAYS),
        "scope": "offline_access",
        f"{ns}/user_id": str(user.id),
        "token_type": "refresh",
        "jti": str(uuid.uuid4()),
    }

    access_token = jwt.encode(access_payload, _secret(), algorithm="HS256")
    refresh_token = generate_refresh_token_string()

    return {
        "accessToken": access_token,
        "refreshToken": refresh_token,
        "expiresIn": settings.ACCESS_TOKEN_LIFETIME_MINUTES * 60,
    }


def generate_mfa_partial_token(user) -> str:
    """
    Short-lived token (5 min) with scope=mfa_pending.
    Accepted only by /auth/mfa/verify/ — blocks all other endpoints.
    """
    now = datetime.now(tz=UTC)
    ns = _namespace()

    payload = {
        "sub": str(user.id),
        "iss": _issuer(),
        "aud": _audience(),
        "iat": now,
        "exp": now + timedelta(minutes=5),
        "scope": "mfa_pending",
        f"{ns}/user_id": str(user.id),
    }
    return jwt.encode(payload, _secret(), algorithm="HS256")


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT. Raises jwt.PyJWTError on invalid/expired tokens.
    In production, swap _secret() for RS256 public key validation.
    """
    return jwt.decode(
        token,
        _secret(),
        algorithms=["HS256"],
        audience=_audience(),
        options={"verify_iss": False},  # Set True and add issuer= in production
    )


# ============================================================================
# Refresh Token String
# ============================================================================


def generate_refresh_token_string() -> str:
    """
    Generate a high-entropy opaque refresh token string.
    This is NOT a JWT — it is hashed before storage.
    """
    return f"refresh_{uuid.uuid4().hex}{secrets.token_hex(16)}"


# ============================================================================
# Hashing
# ============================================================================


def hash_token(token: str) -> str:
    """SHA-256 hash for secure token storage. Never store plain tokens in DB."""
    return hashlib.sha256(token.encode()).hexdigest()


# ============================================================================
# Permissions (Mode 3+)
# ============================================================================


def get_user_permissions(user) -> list[str]:
    """
    Build permission list from user role.
    Extend/replace with your own permission model for Mode 3+.
    """
    base: dict[str, list[str]] = {
        "patient": [
            "read:own_profile",
            "write:own_profile",
            "read:own_records",
        ],
        "provider": [
            "read:patient_records",
            "write:patient_records",
            "read:own_profile",
            "write:own_profile",
        ],
        "admin": [
            "read:all_users",
            "write:all_users",
            "read:patient_records",
            "write:patient_records",
            "manage:system",
            "read:audit_logs",
        ],
    }
    return base.get(getattr(user, "user_type", ""), [])
