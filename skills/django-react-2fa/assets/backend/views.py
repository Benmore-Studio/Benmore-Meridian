"""
TOTP 2FA API Views

Provides endpoints for TOTP enrollment, enable, disable, and backup code regeneration.
Designed to integrate with an existing Django REST Framework authentication system.

Prerequisites:
- User model with totp_enabled, totp_secret_encrypted, totp_backup_codes fields
- totp_service.py in your project
- Redis available for pending secret storage
- Your project's ApiResponse and authentication classes

Adapt imports to match your project structure.
"""

import logging

from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

# ── Adapt these imports to your project ──────────────────────────────────────
from your_app.models import User  # noqa: F401 — adapt import path
from your_app.totp_service import (
    TOTP_PENDING_SECRET_TTL,
    build_provisioning_uri,
    decrypt_totp_secret,
    encrypt_totp_secret,
    generate_backup_codes,
    generate_qr_code_data_uri,
    generate_totp_secret,
    verify_backup_code,
    verify_totp_code,
)
from lib.response import ApiResponse  # adapt to your response utility

logger = logging.getLogger(__name__)
security_logger = logging.getLogger("security")


# ── Redis helpers for pending TOTP secrets ───────────────────────────────────

def _totp_pending_key(user_id: int) -> str:
    return f"totp_pending:{user_id}"


def _get_redis_client():
    """Get your Redis client. Adapt to your project's Redis utility."""
    import redis
    return redis.from_url(getattr(settings, "REDIS_URL", "redis://localhost:6379/0"))


# ── TOTP Setup (Step 1: Generate QR Code) ───────────────────────────────────

@extend_schema(
    tags=["Authentication"],
    summary="Start TOTP setup",
    description="Generate a TOTP secret and QR code for authenticator app enrollment.",
    responses={
        200: OpenApiResponse(description="QR code and secret returned"),
        400: OpenApiResponse(description="TOTP already enabled"),
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def totp_setup(request):
    """
    Begin TOTP enrollment: generate secret + QR code.
    Secret is held in Redis for TOTP_PENDING_SECRET_TTL seconds.
    NOT written to DB until /totp/enable/ confirms a valid code.
    """
    user = request.user

    if user.totp_enabled:
        return ApiResponse.error(
            message="TOTP is already enabled. Disable it first before re-enrolling.",
            status=status.HTTP_400_BAD_REQUEST,
        )

    secret = generate_totp_secret()
    provisioning_uri = build_provisioning_uri(secret, user.email)
    qr_code_uri = generate_qr_code_data_uri(provisioning_uri)

    # Store plain secret in Redis pending confirmation
    redis_client = _get_redis_client()
    try:
        redis_client.setex(_totp_pending_key(user.id), TOTP_PENDING_SECRET_TTL, secret)
    except Exception:
        logger.exception(f"Failed to store TOTP pending secret for user {user.id}")
        return ApiResponse.error(
            message="Failed to initiate TOTP setup. Please try again.",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return ApiResponse.success(
        data={
            "secret": secret,
            "provisioning_uri": provisioning_uri,
            "qr_code_uri": qr_code_uri,
        },
        message="Scan the QR code with your authenticator app, then enter the 6-digit code to confirm.",
    )


# ── TOTP Enable / Disable (Step 2) ──────────────────────────────────────────

@extend_schema(
    tags=["Authentication"],
    summary="Enable or disable TOTP",
    description="Enable TOTP by verifying a code from the authenticator app, or disable by providing a TOTP/backup code.",
    responses={
        200: OpenApiResponse(description="TOTP toggled successfully"),
        400: OpenApiResponse(description="Invalid code or no pending setup"),
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def totp_toggle(request, action):
    """Enable or disable TOTP based on the URL action parameter ('enable' | 'disable')."""
    if action not in ("enable", "disable"):
        return ApiResponse.error(
            message="Invalid action. Use 'enable' or 'disable'.",
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = request.user
    code = str(request.data.get("code", "")).strip()

    if not code:
        msg = (
            "A 6-digit code from your authenticator app is required."
            if action == "enable"
            else "Provide the 6-digit authenticator code or a backup code to confirm."
        )
        return ApiResponse.error(message=msg, status=status.HTTP_400_BAD_REQUEST)

    if action == "enable":
        return _totp_enable(user, code)
    return _totp_disable(user, code)


def _totp_enable(user, code):
    """Verify pending TOTP code and persist encrypted secret to DB."""
    redis_client = _get_redis_client()
    pending_key = _totp_pending_key(user.id)

    try:
        raw = redis_client.get(pending_key)
    except Exception:
        logger.exception(f"Redis error reading TOTP pending secret for user {user.id}")
        raw = None

    if not raw:
        return ApiResponse.error(
            message="No pending TOTP setup found. Please start over from /auth/totp/setup/.",
            status=status.HTTP_400_BAD_REQUEST,
        )

    secret = raw.decode() if isinstance(raw, bytes) else raw

    if not verify_totp_code(secret, code):
        return ApiResponse.error(
            message="Invalid code. Check your authenticator app and try again.",
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Code valid — persist encrypted secret and enable TOTP
    plaintext_codes, hashed_codes = generate_backup_codes()
    user.totp_secret_encrypted = encrypt_totp_secret(secret)
    user.totp_backup_codes = hashed_codes
    user.totp_enabled = True
    user.save(update_fields=["totp_secret_encrypted", "totp_backup_codes", "totp_enabled", "updated_at"])

    # Clean up pending key
    try:
        redis_client.delete(pending_key)
    except Exception:
        pass  # Non-fatal; TTL will expire it

    security_logger.info(f"TOTP_ENABLED | User ID: {user.id} | Email: {user.email}")

    return ApiResponse.success(
        data={"backup_codes": plaintext_codes},
        message="Authenticator app enabled. Store your backup codes in a safe place.",
    )


def _totp_disable(user, code):
    """Disable TOTP after verifying authenticator code or backup code."""
    if not user.totp_enabled:
        return ApiResponse.error(
            message="TOTP is not enabled on this account.",
            status=status.HTTP_400_BAD_REQUEST,
        )

    plain_secret = decrypt_totp_secret(user.totp_secret_encrypted or "")
    confirmed = False

    # Try authenticator code
    if plain_secret and verify_totp_code(plain_secret, code):
        confirmed = True
    else:
        # Try backup code
        valid, _ = verify_backup_code(code, user.totp_backup_codes or [])
        confirmed = valid

    if not confirmed:
        security_logger.warning(f"TOTP_DISABLE_FAILED | User ID: {user.id} | Email: {user.email}")
        return ApiResponse.error(
            message="Invalid code. Provide a valid authenticator code or backup code.",
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Wipe all TOTP data
    user.totp_enabled = False
    user.totp_secret_encrypted = None
    user.totp_backup_codes = []
    user.save(update_fields=["totp_enabled", "totp_secret_encrypted", "totp_backup_codes", "updated_at"])

    security_logger.info(f"TOTP_DISABLED | User ID: {user.id} | Email: {user.email}")

    return ApiResponse.success(message="Authenticator app 2FA has been disabled.")


# ── Backup Code Regeneration ─────────────────────────────────────────────────

@extend_schema(
    tags=["Authentication"],
    summary="Regenerate TOTP backup codes",
    description="Generate a fresh set of backup codes, replacing all existing ones. Requires a valid TOTP code.",
    responses={
        200: OpenApiResponse(description="New backup codes returned"),
        400: OpenApiResponse(description="Invalid TOTP code or TOTP not enabled"),
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def totp_backup_codes_regenerate(request):
    """Regenerate backup codes. Requires a live TOTP code to confirm identity."""
    user = request.user
    code = str(request.data.get("code", "")).strip()

    if not user.totp_enabled:
        return ApiResponse.error(
            message="TOTP is not enabled on this account.",
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not code:
        return ApiResponse.error(
            message="Provide your current 6-digit authenticator code to regenerate backup codes.",
            status=status.HTTP_400_BAD_REQUEST,
        )

    plain_secret = decrypt_totp_secret(user.totp_secret_encrypted or "")
    if not plain_secret or not verify_totp_code(plain_secret, code):
        security_logger.warning(f"TOTP_BACKUP_REGEN_FAILED | User ID: {user.id} | Email: {user.email}")
        return ApiResponse.error(
            message="Invalid authenticator code.",
            status=status.HTTP_400_BAD_REQUEST,
        )

    plaintext_codes, hashed_codes = generate_backup_codes()
    user.totp_backup_codes = hashed_codes
    user.save(update_fields=["totp_backup_codes", "updated_at"])

    security_logger.info(f"TOTP_BACKUP_REGENERATED | User ID: {user.id} | Email: {user.email}")

    return ApiResponse.success(
        data={"backup_codes": plaintext_codes},
        message="New backup codes generated. Previous codes are no longer valid.",
    )
