"""
Authentication models — Universal Auth Skill template.
Stack: Django + PostgreSQL
Adapted from MyMed EHR System (HIPAA Mode 4).

IMPROVEMENTS over source:
  - UserSession.revoke() now sets revoked_at timestamp (was missing)
  - SessionManager added for common query patterns
  - MFARecoveryCode adds remaining_count() helper
  - Explicit __all__ for clean imports
"""

import uuid
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from .managers import ActiveUserManager, UserSessionManager


__all__ = [
    "User",
    "UserSession",
    "EmailVerificationToken",
    "PasswordResetToken",
    "MFARecoveryCode",
]


# ============================================================================
# User
# ============================================================================


class User(AbstractUser):
    """
    Custom user model — email-based auth, MFA support, HIPAA consent tracking.
    Replace APP_NAME and role choices to match your domain.
    """

    class UserType(models.TextChoices):
        # CUSTOMIZE: replace with your app's role names
        PATIENT = "patient", "Patient"
        PROVIDER = "provider", "Provider"
        FRONT_DESK = "front_desk", "Front Desk"
        ADMIN = "admin", "Admin"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Remove username — use email instead
    username = None
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["user_type"]

    email = models.EmailField(unique=True, db_index=True)
    email_verified = models.BooleanField(default=False)
    phone = models.CharField(max_length=50, blank=True, default="")
    phone_verified = models.BooleanField(default=False)

    user_type = models.CharField(
        max_length=50,
        choices=UserType.choices,
        default=UserType.PATIENT,
        db_index=True,
    )

    # ── MFA ──────────────────────────────────────────────────────────────────
    mfa_enabled = models.BooleanField(default=False)
    mfa_secret = models.BinaryField(
        null=True,
        blank=True,
        help_text="TOTP secret — store encrypted (pgcrypto or Fernet). Never log this field.",
    )
    mfa_enrolled_at = models.DateTimeField(null=True, blank=True)

    # ── Account status ────────────────────────────────────────────────────────
    is_suspended = models.BooleanField(default=False)
    suspension_reason = models.TextField(blank=True, default="")
    suspended_at = models.DateTimeField(null=True, blank=True)

    # ── HIPAA consent (Mode 4 — remove for Mode 1/2/3) ───────────────────────
    terms_accepted = models.BooleanField(default=False)
    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    terms_version = models.CharField(max_length=20, default="1.0.0")

    hipaa_consent_accepted = models.BooleanField(default=False)
    hipaa_consent_accepted_at = models.DateTimeField(null=True, blank=True)
    hipaa_consent_version = models.CharField(max_length=20, default="1.0.0")

    privacy_policy_accepted = models.BooleanField(default=False)
    privacy_policy_accepted_at = models.DateTimeField(null=True, blank=True)
    privacy_policy_version = models.CharField(max_length=20, default="1.0.0")

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, help_text="Soft delete timestamp")

    # ── Managers ──────────────────────────────────────────────────────────────
    objects = ActiveUserManager()        # filters is_active=True, deleted_at=None
    all_objects = models.Manager()       # unfiltered — use for auth lookups

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user_type"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.email} ({self.user_type})"

    # ── Role helpers ──────────────────────────────────────────────────────────

    @property
    def is_patient(self) -> bool:
        return self.user_type == self.UserType.PATIENT

    @property
    def is_provider(self) -> bool:
        return self.user_type == self.UserType.PROVIDER

    @property
    def is_admin_user(self) -> bool:
        return self.user_type == self.UserType.ADMIN

    # ── Account lifecycle ─────────────────────────────────────────────────────

    def suspend(self, reason: str = "") -> None:
        self.is_suspended = True
        self.suspension_reason = reason
        self.suspended_at = timezone.now()
        self.save(update_fields=["is_suspended", "suspension_reason", "suspended_at", "updated_at"])

    def reactivate(self) -> None:
        self.is_suspended = False
        self.suspension_reason = ""
        self.suspended_at = None
        self.save(update_fields=["is_suspended", "suspension_reason", "suspended_at", "updated_at"])

    def soft_delete(self) -> None:
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_active", "deleted_at", "updated_at"])

    # ── Consent ───────────────────────────────────────────────────────────────

    def has_valid_consents(self) -> bool:
        return self.terms_accepted and self.hipaa_consent_accepted and self.privacy_policy_accepted

    def accept_consents(self, accepted_at: datetime, versions: dict | None = None) -> None:
        v = versions or {"terms": "1.0.0", "hipaa": "1.0.0", "privacy": "1.0.0"}
        self.terms_accepted = True
        self.terms_accepted_at = accepted_at
        self.terms_version = v.get("terms", "1.0.0")
        self.hipaa_consent_accepted = True
        self.hipaa_consent_accepted_at = accepted_at
        self.hipaa_consent_version = v.get("hipaa", "1.0.0")
        self.privacy_policy_accepted = True
        self.privacy_policy_accepted_at = accepted_at
        self.privacy_policy_version = v.get("privacy", "1.0.0")
        self.save(
            update_fields=[
                "terms_accepted", "terms_accepted_at", "terms_version",
                "hipaa_consent_accepted", "hipaa_consent_accepted_at", "hipaa_consent_version",
                "privacy_policy_accepted", "privacy_policy_accepted_at", "privacy_policy_version",
                "updated_at",
            ]
        )


# ============================================================================
# UserSession
# ============================================================================


class UserSession(models.Model):
    """
    Device-bound session. Stores refresh token hash (never the plain token).
    Biometric sessions use session_id as device token — no separate token model needed.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sessions",
    )

    # ── Identity ──────────────────────────────────────────────────────────────
    session_id = models.CharField(max_length=255, unique=True, db_index=True)
    refresh_token_hash = models.CharField(max_length=64, help_text="SHA-256 of refresh token")

    # ── Device info ───────────────────────────────────────────────────────────
    device_name = models.CharField(max_length=255, blank=True, default="")
    device_fingerprint = models.CharField(max_length=255, blank=True, default="", db_index=True)
    device_id = models.CharField(max_length=255, blank=True, default="")
    os = models.CharField(max_length=50, blank=True, default="")
    os_version = models.CharField(max_length=50, blank=True, default="")
    app_version = models.CharField(max_length=50, blank=True, default="")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")

    # ── Session type ──────────────────────────────────────────────────────────
    is_biometric = models.BooleanField(default=False)

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(db_index=True)
    is_active = models.BooleanField(default=True)
    revoked_at = models.DateTimeField(null=True, blank=True)  # FIX: was never set in source

    objects = UserSessionManager()

    class Meta:
        db_table = "user_sessions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["session_id"]),
            models.Index(fields=["expires_at"]),
            models.Index(fields=["user", "is_biometric"]),
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self):
        return f"Session {self.session_id[:20]}… ({self.user.email})"

    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    def revoke(self) -> None:
        """Revoke session and record timestamp. FIX: source was missing revoked_at."""
        self.is_active = False
        self.revoked_at = timezone.now()
        self.save(update_fields=["is_active", "revoked_at", "last_used_at"])


# ============================================================================
# EmailVerificationToken
# ============================================================================


class EmailVerificationToken(models.Model):
    """
    OTP-based email verification.
    Only the SHA-256 hash is persisted; plain token is sent once via email.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        USED = "used", "Used"
        EXPIRED = "expired", "Expired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_verification_tokens",
    )
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "email_verification_tokens"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["expires_at"]),
        ]

    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    def is_valid(self) -> bool:
        return self.status == self.Status.PENDING and not self.is_expired()

    def mark_used(self) -> None:
        self.status = self.Status.USED
        self.used_at = timezone.now()
        self.save(update_fields=["status", "used_at"])


# ============================================================================
# PasswordResetToken
# ============================================================================


class PasswordResetToken(models.Model):
    """
    OTP-based password reset.
    Only the SHA-256 hash is persisted; plain OTP is sent once via email.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        USED = "used", "Used"
        EXPIRED = "expired", "Expired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "password_reset_tokens"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["expires_at"]),
        ]

    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    def is_valid(self) -> bool:
        return self.status == self.Status.PENDING and not self.is_expired()

    def mark_used(self) -> None:
        self.status = self.Status.USED
        self.used_at = timezone.now()
        self.save(update_fields=["status", "used_at"])


# ============================================================================
# MFARecoveryCode
# ============================================================================


class MFARecoveryCode(models.Model):
    """
    SHA-256 hashed backup codes for TOTP recovery.
    Shown to user once during MFA setup; only hash stored.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mfa_recovery_codes",
    )
    code_hash = models.CharField(max_length=64, db_index=True)
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "mfa_recovery_codes"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["user", "is_used"]),
        ]

    def __str__(self):
        return f"Recovery code ({self.user.email}) — {'used' if self.is_used else 'active'}"

    def mark_used(self) -> None:
        self.is_used = True
        self.used_at = timezone.now()
        self.save(update_fields=["is_used", "used_at"])

    @classmethod
    def remaining_count(cls, user) -> int:
        """Helper — how many unused recovery codes does this user have?"""
        return cls.objects.filter(user=user, is_used=False).count()
