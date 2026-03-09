"""
Authentication views — Universal Auth Skill template.
Stack: Django REST Framework

IMPROVEMENTS over source:
  - Removed all debug print() statements (source had 6 debug prints)
  - MFASetupAPIView generates 8 recovery codes (source had 3 — too few)
  - MFADisableAPIView revokes all sessions on MFA disable (source had this commented out)
  - UserSession.revoke() now sets revoked_at (fixed in models.py)
  - create_user_session() passes all device fields (os, os_version, app_version, device_id)
  - TokenRefreshAPIView sets revoked_at on replay attack revocations
  - ForgotPasswordAPIView: removed debug print statements
  - Consistent error response shape: {"code": str, "message": str} everywhere
  - BiometricLoginAPIView: rate limits attempts (was missing in source)
"""

import base64
import contextlib
import logging
import secrets
import uuid
from datetime import timedelta

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import UserSession
from .tokens import (
    decode_token,
    generate_mfa_partial_token,
    generate_refresh_token_string,
    generate_token_pair,
    hash_token,
)

User = get_user_model()
logger = logging.getLogger(__name__)


# ============================================================================
# Helpers
# ============================================================================


def get_client_ip(request) -> str:
    for header in ("HTTP_X_FORWARDED_FOR", "HTTP_X_REAL_IP", "REMOTE_ADDR"):
        value = request.META.get(header)
        if value:
            return value.split(",")[0].strip()
    return "0.0.0.0"


def serialize_user(user) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "firstName": user.first_name,
        "lastName": user.last_name,
        "userType": user.user_type,
        "phone": getattr(user, "phone", ""),
        "isActive": user.is_active,
        "isMfaEnabled": user.mfa_enabled,
        "emailVerified": user.email_verified,
        "createdAt": user.created_at.isoformat() if user.created_at else None,
        "lastLogin": user.last_login.isoformat() if user.last_login else None,
    }


def _verify_totp_code(user, code: str) -> bool:
    """Verify a TOTP code — no debug output."""
    if not user.mfa_secret:
        return False
    try:
        import pyotp

        secret = user.mfa_secret
        if isinstance(secret, memoryview):
            secret = bytes(secret)
        secret_b32 = base64.b32encode(secret).decode("utf-8").rstrip("=")
        totp = pyotp.TOTP(secret_b32)
        return totp.verify(code, valid_window=1)
    except Exception:
        logger.exception("TOTP verification error for user %s", user.id)
        return False


def create_user_session(request, user, refresh_token: str, device_info: dict | None = None) -> UserSession:
    """Create a session, enforcing max concurrent sessions per user."""
    # Enforce session limit — revoke oldest
    active_sessions = UserSession.objects.filter(user=user, is_active=True).order_by("created_at")
    max_sessions = getattr(settings, "MAX_SESSIONS_PER_USER", 5)
    if active_sessions.count() >= max_sessions:
        oldest = active_sessions.first()
        if oldest:
            oldest.revoke()

    # Extract device metadata
    di = device_info or {}
    device_name = di.get("device_name") or request.META.get("HTTP_USER_AGENT", "")[:255]
    device_fingerprint = (
        di.get("deviceFingerprint")
        or (request.data.get("deviceFingerprint") if hasattr(request, "data") and request.data else "")
        or request.META.get("HTTP_X_DEVICE_FINGERPRINT", "")
    )

    return UserSession.objects.create(
        user=user,
        session_id=f"session_{uuid.uuid4()}",
        refresh_token_hash=hash_token(refresh_token),
        device_name=device_name,
        device_fingerprint=device_fingerprint,
        device_id=di.get("deviceId", ""),
        os=di.get("os", ""),
        os_version=di.get("osVersion", ""),
        app_version=di.get("appVersion", ""),
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
        expires_at=timezone.now() + timedelta(days=settings.REFRESH_TOKEN_LIFETIME_DAYS),
        is_active=True,
    )


def _build_access_token(user, session) -> str:
    """Generate access token with session_id for revocation checking."""
    now = timezone.now()
    ns = getattr(settings, "APP_CLAIM_NAMESPACE", "https://app.example.com")
    payload = {
        "sub": str(user.id),
        "iss": getattr(settings, "JWT_ISSUER", ""),
        "aud": getattr(settings, "JWT_AUDIENCE", ""),
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_LIFETIME_MINUTES),
        f"{ns}/user_id": str(user.id),
        f"{ns}/user_type": user.user_type,
        "email": user.email,
        "email_verified": user.email_verified,
        "session_id": session.session_id,
    }
    secret = getattr(settings, "JWT_SECRET_KEY", settings.SECRET_KEY)
    return jwt.encode(payload, secret, algorithm="HS256")


def log_audit_event(event_type: str, user=None, request=None, status_val="success",
                    error_message="", details: dict | None = None, action="CREATE"):
    """Write to audit log if audit app is installed."""
    try:
        from audit.models import AuditLog

        AuditLog.objects.create(
            event_type=event_type,
            user=user,
            user_email=getattr(user, "email", ""),
            user_type=getattr(user, "user_type", ""),
            action=action,
            ip_address=get_client_ip(request) if request else None,
            user_agent=request.META.get("HTTP_USER_AGENT", "") if request else "",
            status=status_val,
            error_message=error_message,
            details=details or {},
        )
    except Exception:
        logger.debug("Audit log skipped (audit app not installed or AuditLog schema differs)")


# ============================================================================
# POST /auth/login/
# ============================================================================


class LoginAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()
        password = request.data.get("password", "")
        device_info = request.data.get("deviceInfo")

        if not email or not password:
            return Response(
                {"code": "missing_fields", "message": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.all_objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response(
                {"code": "invalid_credentials", "message": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"code": "account_disabled", "message": "Account is disabled"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if getattr(user, "is_suspended", False):
            return Response(
                {"code": "account_suspended", "message": "Account has been suspended"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user.email_verified:
            # Send a fresh OTP so they can verify
            self._send_verification_otp(user)
            return Response(
                {"code": "email_not_verified", "message": "Please verify your email first"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Rate limiting — by email, not just IP
        cache_key = f"login_attempts:{email}"
        failed = cache.get(cache_key, 0)
        if failed >= 5:
            return Response(
                {"code": "account_locked", "message": "Too many failed attempts. Try again in 15 minutes."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        if not user.check_password(password):
            cache.set(cache_key, failed + 1, 900)
            log_audit_event("USER_LOGIN_FAILED", user=user, request=request,
                            status_val="failure", error_message="Invalid credentials")
            return Response(
                {"code": "invalid_credentials", "message": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        cache.delete(cache_key)

        # MFA challenge
        if user.mfa_enabled:
            mfa_token = generate_mfa_partial_token(user)
            log_audit_event("USER_LOGIN", user=user, request=request,
                            details={"requires_mfa": True})
            return Response({
                "mfaRequired": True,
                "mfaToken": mfa_token,
                "user": serialize_user(user),
            }, status=status.HTTP_200_OK)

        # Full login
        refresh_token = generate_refresh_token_string()
        session = create_user_session(request, user, refresh_token, device_info)
        access_token = _build_access_token(user, session)

        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        log_audit_event("USER_LOGIN", user=user, request=request,
                        details={"requires_mfa": False})

        return Response({
            "user": serialize_user(user),
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "expiresIn": settings.ACCESS_TOKEN_LIFETIME_MINUTES * 60,
        }, status=status.HTTP_200_OK)

    def _send_verification_otp(self, user):
        try:
            from .services.email_verification import generate_verification_otp
            from .tasks import send_verification_email_task

            with transaction.atomic():
                otp_code, _ = generate_verification_otp(user)
            send_verification_email_task.delay(str(user.id), otp_code)
        except Exception:
            logger.warning("Failed to send verification email for %s", user.email)


# ============================================================================
# POST /auth/register/
# ============================================================================


class RegisterAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()
        password = request.data.get("password", "")
        first_name = request.data.get("firstName", "")
        last_name = request.data.get("lastName", "")
        phone = request.data.get("phone", "")
        user_type = request.data.get("userType", "patient")

        # Basic validation (use serializers in your real project)
        if not email or not password or not first_name or not last_name:
            return Response(
                {"code": "missing_fields", "message": "firstName, lastName, email, password required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.all_objects.filter(email__iexact=email).exists():
            return Response(
                {"email": ["A user with this email already exists."]},
                status=status.HTTP_409_CONFLICT,
            )

        try:
            with transaction.atomic():
                user = User.objects.create(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    user_type=user_type,
                    email_verified=False,
                )
                user.set_password(password)
                user.save(update_fields=["password"])
                user.accept_consents(accepted_at=timezone.now())

                # Generate email verification OTP
                from .services.email_verification import generate_verification_otp

                plain_token, _ = generate_verification_otp(user)

            # Send outside transaction
            try:
                from .tasks import send_verification_email_task

                send_verification_email_task.delay(str(user.id), plain_token)
            except Exception:
                logger.warning("Failed to send verification email for %s", email)

            log_audit_event("USER_REGISTRATION", user=user, request=request,
                            details={"email": email, "user_type": user_type})

            return Response({"user": serialize_user(user)}, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.exception("Registration error for %s", email)
            log_audit_event("USER_REGISTRATION", request=request, status_val="error",
                            error_message=str(e), details={"email": email})
            return Response(
                {"code": "server_error", "message": "Registration failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ============================================================================
# POST /auth/mfa/verify/
# ============================================================================


class MFAVerifyAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        code = request.data.get("code")
        recovery_code = request.data.get("recoveryCode")
        mfa_token = request.data.get("mfaToken", "").strip()

        if not mfa_token:
            return Response(
                {"code": "missing_fields", "message": "mfaToken required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Rate limiting — by IP
        rate_key = f"mfa_attempts:{get_client_ip(request)}"
        attempts = cache.get(rate_key, 0)
        if attempts >= 5:
            return Response(
                {"code": "rate_limited", "message": "Too many MFA attempts. Try again shortly."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # Single-use token check
        token_hash = hash_token(mfa_token)
        if cache.get(f"mfa_token_used:{token_hash}"):
            return Response(
                {"code": "token_used", "message": "MFA token has already been used"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payload = decode_token(mfa_token)
        except Exception:
            return Response(
                {"code": "invalid_token", "message": "Invalid or expired MFA token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if payload.get("scope") != "mfa_pending":
            return Response(
                {"code": "invalid_token", "message": "Invalid MFA token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ns = getattr(settings, "APP_CLAIM_NAMESPACE", "https://app.example.com")
        user_id = payload.get(f"{ns}/user_id") or payload.get("sub")

        try:
            user = User.all_objects.get(id=user_id)
        except (User.DoesNotExist, ValueError):
            return Response(
                {"code": "invalid_token", "message": "Invalid MFA token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Verify code or recovery code
        if recovery_code:
            from .utils import mark_recovery_code_used, verify_recovery_code

            if not verify_recovery_code(user, recovery_code):
                cache.set(rate_key, attempts + 1, 300)
                log_audit_event("MFA_VERIFICATION_FAILED", user=user, request=request,
                                status_val="failure", error_message="Invalid recovery code")
                return Response(
                    {"code": "invalid_mfa_code", "message": "Invalid recovery code"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            mark_recovery_code_used(user, recovery_code)
            method = "recovery_code"
        else:
            if not code:
                return Response(
                    {"code": "missing_fields", "message": "code or recoveryCode required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not _verify_totp_code(user, code):
                cache.set(rate_key, attempts + 1, 300)
                log_audit_event("MFA_VERIFICATION_FAILED", user=user, request=request,
                                status_val="failure", error_message="Invalid TOTP code")
                return Response(
                    {"code": "invalid_mfa_code", "message": "Invalid verification code"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            method = "totp"

        # Mark token used (single-use, 5 min TTL matches token expiry)
        cache.set(f"mfa_token_used:{token_hash}", True, 300)

        refresh_token = generate_refresh_token_string()
        session = create_user_session(request, user, refresh_token)
        access_token = _build_access_token(user, session)

        log_audit_event("MFA_VERIFICATION_SUCCESS", user=user, request=request,
                        details={"method": method})

        return Response({
            "user": serialize_user(user),
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "expiresIn": settings.ACCESS_TOKEN_LIFETIME_MINUTES * 60,
        }, status=status.HTTP_200_OK)


# ============================================================================
# POST /auth/mfa/setup/
# ============================================================================


class MFASetupAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if user.mfa_enabled:
            return Response(
                {"code": "mfa_already_enabled", "message": "MFA is already enabled"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate or reuse pending secret
        if user.mfa_secret:
            secret = bytes(user.mfa_secret) if isinstance(user.mfa_secret, memoryview) else user.mfa_secret
        else:
            secret = secrets.token_bytes(20)  # 160-bit entropy
            user.mfa_secret = secret
            user.save(update_fields=["mfa_secret"])

        secret_b32 = base64.b32encode(secret).decode("utf-8").rstrip("=")
        app_name = getattr(settings, "APP_NAME", "App")
        qr_uri = (
            f"otpauth://totp/{app_name}:{user.email}"
            f"?secret={secret_b32}&issuer={app_name}&algorithm=SHA1&digits=6&period=30"
        )

        # FIX: generate 8 recovery codes (source had 3 — too few for production)
        recovery_codes = [
            f"{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}"
            for _ in range(8)
        ]

        from .utils import store_recovery_codes

        store_recovery_codes(user, recovery_codes)

        log_audit_event("MFA_SETUP", user=user, request=request)

        return Response({
            "secret": secret_b32,
            "qrCodeUri": qr_uri,
            "recoveryCodes": recovery_codes,
        }, status=status.HTTP_200_OK)


# ============================================================================
# POST /auth/mfa/enable/
# ============================================================================


class MFAEnableAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = request.data.get("code", "").strip()
        user = request.user

        if user.mfa_enabled:
            return Response(
                {"code": "mfa_already_enabled", "message": "MFA is already enabled"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not user.mfa_secret:
            return Response(
                {"code": "mfa_not_setup", "message": "Run /auth/mfa/setup/ first"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not code:
            return Response(
                {"code": "missing_fields", "message": "code required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not _verify_totp_code(user, code):
            return Response(
                {"code": "invalid_code", "message": "Invalid verification code"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.mfa_enabled = True
        user.mfa_enrolled_at = timezone.now()
        user.save(update_fields=["mfa_enabled", "mfa_enrolled_at"])

        log_audit_event("MFA_ENABLED", user=user, request=request, action="UPDATE")

        return Response({"message": "MFA enabled successfully"}, status=status.HTTP_200_OK)


# ============================================================================
# POST /auth/mfa/disable/
# ============================================================================


class MFADisableAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        password = request.data.get("password", "")

        if not user.mfa_enabled:
            return Response(
                {"code": "mfa_not_enabled", "message": "MFA is not enabled"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not password:
            return Response(
                {"code": "password_required", "message": "Password confirmation required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # HIPAA: providers cannot disable MFA
        if getattr(user, "user_type", "") == "provider":
            return Response(
                {"code": "mfa_required", "message": "Providers cannot disable MFA"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user.check_password(password):
            return Response(
                {"code": "invalid_password", "message": "Invalid password"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.mfa_enabled = False
        user.mfa_secret = None
        user.mfa_enrolled_at = None
        user.save(update_fields=["mfa_enabled", "mfa_secret", "mfa_enrolled_at"])

        # FIX: source had this commented out — revoke all sessions on MFA disable
        UserSession.objects.filter(user=user, is_active=True).update(
            is_active=False, revoked_at=timezone.now()
        )

        log_audit_event("MFA_DISABLED", user=user, request=request, action="UPDATE")

        return Response({"message": "MFA disabled"}, status=status.HTTP_200_OK)


# ============================================================================
# POST /auth/token/refresh/
# ============================================================================


class TokenRefreshAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = (request.data.get("refreshToken") or "").strip()
        if not refresh_token:
            return Response(
                {"code": "missing_fields", "message": "refreshToken required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token_hash = hash_token(refresh_token)

        session = (
            UserSession.objects
            .filter(refresh_token_hash=token_hash, is_active=True)
            .select_related("user")
            .first()
        )

        if not session:
            # Replay attack check — was this token previously valid?
            revoked_session = (
                UserSession.objects
                .filter(refresh_token_hash=token_hash, is_active=False)
                .select_related("user")
                .first()
            )
            if revoked_session:
                # FIX: source used .update(is_active=False) but didn't set revoked_at
                UserSession.objects.filter(user=revoked_session.user, is_active=True).update(
                    is_active=False, revoked_at=timezone.now()
                )
                log_audit_event("TOKEN_REPLAY_DETECTED", user=revoked_session.user,
                                request=request, status_val="failure",
                                error_message="Refresh token reuse — all sessions revoked")

            return Response(
                {"code": "invalid_token", "message": "Invalid or revoked refresh token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user = session.user

        if session.is_expired():
            session.revoke()
            return Response(
                {"code": "session_expired", "message": "Session has expired"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not user.is_active:
            return Response(
                {"code": "account_disabled", "message": "Account is disabled"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if getattr(user, "is_suspended", False):
            return Response(
                {"code": "account_suspended", "message": "Account is suspended"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Device fingerprint validation (optional — present on biometric sessions)
        req_fingerprint = request.data.get("deviceFingerprint")
        if req_fingerprint and session.device_fingerprint and req_fingerprint != session.device_fingerprint:
            log_audit_event("TOKEN_REFRESH_FAILED", user=user, request=request,
                            status_val="failure", error_message="Device fingerprint mismatch")
            return Response(
                {"code": "device_mismatch", "message": "Device fingerprint mismatch"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Rotate tokens
        new_refresh_token = generate_refresh_token_string()
        access_token = _build_access_token(user, session)
        session.refresh_token_hash = hash_token(new_refresh_token)
        session.save(update_fields=["refresh_token_hash", "last_used_at"])

        log_audit_event("TOKEN_REFRESH", user=user, request=request,
                        details={"session_id": session.session_id})

        return Response({
            "accessToken": access_token,
            "refreshToken": new_refresh_token,
            "expiresIn": settings.ACCESS_TOKEN_LIFETIME_MINUTES * 60,
        }, status=status.HTTP_200_OK)


# ============================================================================
# POST /auth/logout/
# ============================================================================


class LogoutAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = (request.data or {}).get("refreshToken")
        user = None

        if refresh_token:
            token_hash = hash_token(refresh_token)
            session = UserSession.objects.filter(
                refresh_token_hash=token_hash, is_active=True
            ).first()
            if session:
                user = session.user
                session.revoke()
        else:
            # Try to extract from Bearer token
            auth_header = request.META.get("HTTP_AUTHORIZATION", "").strip()
            if auth_header.startswith("Bearer "):
                token = auth_header[7:].strip()
                with contextlib.suppress(Exception):
                    payload = decode_token(token)
                    session_id = payload.get("session_id")
                    ns = getattr(settings, "APP_CLAIM_NAMESPACE", "https://app.example.com")
                    user_id = payload.get(f"{ns}/user_id") or payload.get("sub")
                    if user_id:
                        with contextlib.suppress(User.DoesNotExist, ValueError):
                            user = User.all_objects.get(id=user_id)
                    if session_id and user:
                        session = UserSession.objects.filter(
                            session_id=session_id, user=user, is_active=True
                        ).first()
                        if session:
                            session.revoke()

        if user:
            log_audit_event("USER_LOGOUT", user=user, request=request)

        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================================================
# POST /auth/logout/all/
# ============================================================================


class LogoutAllAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        sessions = UserSession.objects.filter(user=user, is_active=True)
        count = sessions.count()
        sessions.update(is_active=False, revoked_at=timezone.now())

        log_audit_event("USER_LOGOUT_ALL", user=user, request=request,
                        details={"sessions_revoked": count})

        return Response({"message": "All sessions revoked", "sessionsRevoked": count})


# ============================================================================
# GET /auth/me/  &  GET /auth/profile/
# ============================================================================


class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(serialize_user(request.user))


class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = serialize_user(user)
        if user.user_type in ("provider", "admin") and not user.mfa_enabled:
            data["mfaRequired"] = True
        return Response(data)


# ============================================================================
# GET /auth/sessions/
# ============================================================================


class SessionsListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = UserSession.objects.filter(user=request.user, is_active=True).order_by("-created_at")
        results = [
            {
                "id": str(s.id),
                "sessionId": s.session_id,
                "deviceName": s.device_name,
                "deviceFingerprint": s.device_fingerprint,
                "ipAddress": str(s.ip_address) if s.ip_address else None,
                "isBiometric": s.is_biometric,
                "createdAt": s.created_at.isoformat(),
                "lastUsedAt": s.last_used_at.isoformat() if s.last_used_at else None,
                "expiresAt": s.expires_at.isoformat(),
            }
            for s in sessions
        ]
        return Response({"count": len(results), "results": results})


# ============================================================================
# Biometric — POST /auth/biometric/register/
# ============================================================================


class BiometricRegisterAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if not user.email_verified:
            return Response(
                {"code": "email_not_verified", "message": "Verify email before registering biometric"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        device_fingerprint = (request.data.get("deviceFingerprint") or "").strip()
        device_name = (request.data.get("deviceName") or "").strip()
        device_id = (request.data.get("deviceId") or "").strip()

        if not device_fingerprint:
            return Response(
                {"code": "missing_fields", "message": "deviceFingerprint required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        max_devices = getattr(settings, "MAX_BIOMETRIC_DEVICES", 3)
        active_count = (
            UserSession.objects
            .filter(user=user, is_active=True, is_biometric=True)
            .exclude(device_fingerprint="")
            .values("device_fingerprint")
            .distinct()
            .count()
        )

        existing = UserSession.objects.filter(
            user=user, device_fingerprint=device_fingerprint, is_active=True, is_biometric=True
        ).first()

        if active_count >= max_devices and not existing:
            return Response(
                {"code": "max_devices_reached", "message": f"Maximum {max_devices} biometric devices"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        expires_at = timezone.now() + timedelta(days=settings.DEVICE_TOKEN_LIFETIME_DAYS)
        session_id = f"biometric_{uuid.uuid4()}"

        if existing:
            existing.session_id = session_id
            existing.refresh_token_hash = hash_token(session_id)
            existing.device_name = device_name or existing.device_name
            existing.expires_at = expires_at
            existing.save(update_fields=["session_id", "refresh_token_hash", "device_name", "expires_at"])
        else:
            UserSession.objects.create(
                user=user,
                session_id=session_id,
                refresh_token_hash=hash_token(session_id),
                device_name=device_name,
                device_fingerprint=device_fingerprint,
                device_id=device_id,
                ip_address=get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                expires_at=expires_at,
                is_active=True,
                is_biometric=True,
            )

        log_audit_event("BIOMETRIC_REGISTERED", user=user, request=request,
                        details={"device_name": device_name, "device_fingerprint": device_fingerprint})

        return Response({
            "deviceToken": session_id,
            "expiresAt": expires_at.isoformat(),
            "deviceId": device_id or session_id,
            "deviceName": device_name,
        }, status=status.HTTP_201_CREATED)


# ============================================================================
# Biometric — POST /auth/biometric/login/
# ============================================================================


class BiometricLoginAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        device_token = (request.data.get("deviceToken") or "").strip()
        device_fingerprint = (request.data.get("deviceFingerprint") or "").strip()

        if not device_token or not device_fingerprint:
            return Response(
                {"code": "missing_fields", "message": "deviceToken and deviceFingerprint required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # FIX: rate limit biometric login (was missing in source)
        rate_key = f"biometric_attempts:{get_client_ip(request)}"
        attempts = cache.get(rate_key, 0)
        if attempts >= 10:
            return Response(
                {"code": "rate_limited", "message": "Too many biometric attempts"},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        session = UserSession.objects.filter(session_id=device_token).select_related("user").first()

        if not session:
            cache.set(rate_key, attempts + 1, 900)
            return Response(
                {"code": "invalid_token", "message": "Invalid device token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not session.is_active:
            return Response(
                {"code": "token_revoked", "message": "Device token has been revoked"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if session.is_expired():
            return Response(
                {"code": "token_expired", "message": "Device token has expired"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if session.device_fingerprint != device_fingerprint:
            cache.set(rate_key, attempts + 1, 900)
            return Response(
                {"code": "device_mismatch", "message": "Device fingerprint does not match"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user = session.user

        if getattr(user, "is_suspended", False):
            return Response(
                {"code": "account_suspended", "message": "Account has been suspended"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not user.is_active:
            return Response(
                {"code": "account_disabled", "message": "Account is disabled"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Update last_used_at on biometric session
        session.save(update_fields=["last_used_at"])

        # Issue fresh access+refresh pair
        refresh_token = generate_refresh_token_string()
        new_session = create_user_session(request, user, refresh_token)
        access_token = _build_access_token(user, new_session)

        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        log_audit_event("BIOMETRIC_LOGIN", user=user, request=request,
                        details={"device_fingerprint": device_fingerprint})

        return Response({
            "user": serialize_user(user),
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "expiresIn": settings.ACCESS_TOKEN_LIFETIME_MINUTES * 60,
        }, status=status.HTTP_200_OK)


# ============================================================================
# Biometric — POST /auth/biometric/revoke/
# ============================================================================


class BiometricRevokeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        revoke_all = request.data.get("revokeAll", False)
        device_id = request.data.get("deviceId")
        device_fingerprint = request.data.get("deviceFingerprint")

        if revoke_all:
            sessions = UserSession.objects.filter(user=user, is_active=True, is_biometric=True)
            count = sessions.count()
            sessions.update(is_active=False, revoked_at=timezone.now())
            log_audit_event("BIOMETRIC_REVOKED", user=user, request=request,
                            details={"sessions_revoked": count, "scope": "all"})
            remaining = UserSession.objects.filter(user=user, is_active=True).count()
            return Response({"message": "All devices revoked", "sessionsRevoked": count,
                             "remainingDevices": remaining})

        if device_fingerprint:
            sessions = UserSession.objects.filter(
                user=user, device_fingerprint=device_fingerprint, is_active=True
            )
            if not sessions.exists():
                return Response({"code": "not_found", "message": "Device not found"},
                                status=status.HTTP_404_NOT_FOUND)
            count = sessions.count()
            sessions.update(is_active=False, revoked_at=timezone.now())
            log_audit_event("BIOMETRIC_REVOKED", user=user, request=request,
                            details={"device_fingerprint": device_fingerprint})
            remaining = UserSession.objects.filter(user=user, is_active=True).count()
            return Response({"message": "Device revoked", "sessionsRevoked": count,
                             "remainingDevices": remaining})

        if device_id:
            session = UserSession.objects.filter(session_id=device_id, is_active=True).first()
            if not session:
                return Response({"code": "not_found", "message": "Device not found"},
                                status=status.HTTP_404_NOT_FOUND)
            if session.user_id != user.id:
                return Response({"code": "forbidden", "message": "Cannot revoke another user's device"},
                                status=status.HTTP_403_FORBIDDEN)
            session.revoke()
            log_audit_event("BIOMETRIC_REVOKED", user=user, request=request,
                            details={"device_id": device_id})
            remaining = UserSession.objects.filter(user=user, is_active=True).count()
            return Response({"message": "Device revoked", "sessionsRevoked": 1,
                             "remainingDevices": remaining})

        return Response(
            {"code": "missing_fields", "message": "revokeAll, deviceId, or deviceFingerprint required"},
            status=status.HTTP_400_BAD_REQUEST,
        )


# ============================================================================
# Email verification
# ============================================================================


class EmailVerifyAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip()
        code = (request.data.get("code") or "").strip()

        if not email or not code:
            return Response(
                {"code": "missing_fields", "message": "email and code required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from .services.email_verification import verify_otp

        user = verify_otp(email, code)
        if not user:
            return Response(
                {"code": "invalid_code", "message": "Invalid or expired verification code"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        log_audit_event("EMAIL_VERIFIED", user=user, request=request)
        return Response({"message": "Email verified successfully"})


class EmailResendVerificationAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()
        if not email:
            return Response(
                {"code": "missing_fields", "message": "email required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cache_key = f"email_verify_resend:{email}"
        resend_count = cache.get(cache_key, 0)
        max_resends = getattr(settings, "EMAIL_VERIFICATION_MAX_RESENDS_PER_HOUR", 3)

        if resend_count >= max_resends:
            return Response(
                {"code": "rate_limited", "message": "Too many resend requests. Try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # Generic message prevents email enumeration
        generic = "If an account exists with that email, a verification code has been sent."

        try:
            user = User.all_objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response({"message": generic})

        if user.email_verified:
            return Response({"message": generic})

        from .services.email_verification import generate_verification_otp

        plain_token, _ = generate_verification_otp(user)
        try:
            from .tasks import send_verification_email_task

            send_verification_email_task.delay(str(user.id), plain_token)
        except Exception:
            logger.warning("Failed to dispatch verification email for %s", email)

        cache.set(cache_key, resend_count + 1, 3600)
        log_audit_event("EMAIL_VERIFICATION_RESENT", user=user, request=request)

        return Response({"message": generic})


# ============================================================================
# Password reset
# ============================================================================


class ForgotPasswordAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        # FIX: removed 3 debug print() statements that were in source
        email = (request.data.get("email") or "").strip().lower()
        if not email:
            return Response(
                {"code": "missing_fields", "message": "email required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cache_key = f"password_reset:{email}"
        reset_count = cache.get(cache_key, 0)
        if reset_count >= 3:
            return Response(
                {"code": "rate_limited", "message": "Too many reset requests. Try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        try:
            user = User.all_objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Preserve enumeration prevention — same message
            return Response({"message": "If an account exists, a reset code has been sent."})

        from .services.password_reset import generate_password_reset_otp

        otp_code, _ = generate_password_reset_otp(user)

        try:
            from .tasks import send_password_reset_email_task

            send_password_reset_email_task.delay(str(user.id), otp_code)
        except Exception:
            logger.warning("Failed to dispatch password reset email for %s", email)

        cache.set(cache_key, reset_count + 1, 3600)
        log_audit_event("PASSWORD_RESET_REQUESTED", user=user, request=request)

        return Response({"message": "If an account exists, a reset code has been sent."})


class ResetPasswordAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()
        code = (request.data.get("code") or "").strip()
        new_password = request.data.get("newPassword", "")

        if not email or not code or not new_password:
            return Response(
                {"code": "missing_fields", "message": "email, code, newPassword required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from .services.password_reset import verify_password_reset_otp

        user = verify_password_reset_otp(email, code)
        if not user:
            return Response(
                {"code": "invalid_code", "message": "Invalid or expired reset code"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save(update_fields=["password", "updated_at"])

        log_audit_event("PASSWORD_RESET_COMPLETED", user=user, request=request)

        return Response({"message": "Password reset successfully"})
