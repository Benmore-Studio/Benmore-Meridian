"""
Custom model managers — Universal Auth Skill template.
Stack: Django

IMPROVEMENTS over source:
  - UserSessionManager.active_sessions() implemented (source had `pass`)
  - UserSessionManager.active_for_device() added — needed by biometric login
    to check whether a fingerprint already has a live session
"""

from django.contrib.auth.models import UserManager as DjangoUserManager
from django.db import models
from django.utils import timezone


class ActiveUserManager(DjangoUserManager):
    """
    Default manager for User model.
    Excludes soft-deleted users (deleted_at is set) and inactive accounts.
    Use User.all_objects for auth lookups that must see all users.
    """

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True, is_active=True)

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class UserSessionManager(models.Manager):
    """Manager for UserSession with common query patterns."""

    def active_for_user(self, user):
        """
        Return all non-expired active sessions for a user.
        FIX: source had `pass` — now implemented.
        """
        return self.filter(
            user=user,
            is_active=True,
            expires_at__gt=timezone.now(),
        )

    def active_biometric_for_user(self, user):
        """Return all active biometric sessions for a user."""
        return self.active_for_user(user).filter(is_biometric=True)

    def active_for_device(self, user, device_fingerprint: str):
        """
        Return the active session bound to a specific device fingerprint.
        Used by BiometricLoginAPIView to validate a device token.
        NEW: not in source.
        """
        return self.active_for_user(user).filter(
            device_fingerprint=device_fingerprint
        ).first()
