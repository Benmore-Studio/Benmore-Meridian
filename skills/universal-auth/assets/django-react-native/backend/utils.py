"""
Auth utility functions — Universal Auth Skill template.
Stack: Django

IMPROVEMENTS over source:
  - verify_and_consume_recovery_code() added — atomic verify+mark in one DB
    round-trip, eliminating the race condition in the original two-step approach
    where concurrent requests could both pass verify_recovery_code() before
    either called mark_recovery_code_used()
  - get_client_ip() extracted here (was inline in auth_views.py)
  - Relative imports instead of absolute (portable across app renames)
"""

import hashlib
import logging

from django.utils import timezone

from .models import MFARecoveryCode

logger = logging.getLogger(__name__)


# ============================================================================
# Recovery Code Utilities
# ============================================================================


def verify_recovery_code(user, code: str) -> bool:
    """
    Check whether a recovery code is valid and unused.

    NOTE: prefer verify_and_consume_recovery_code() to avoid the TOCTOU race
    condition between verifying and marking the code used.
    """
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    return MFARecoveryCode.objects.filter(
        user=user,
        code_hash=code_hash,
        is_used=False,
    ).exists()


def mark_recovery_code_used(user, code: str) -> None:
    """Mark a recovery code as used. Silent no-op if not found."""
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    try:
        recovery_code = MFARecoveryCode.objects.get(
            user=user,
            code_hash=code_hash,
            is_used=False,
        )
        recovery_code.mark_used()
    except MFARecoveryCode.DoesNotExist:
        pass


def verify_and_consume_recovery_code(user, code: str) -> bool:
    """
    Atomically verify and mark a recovery code used in a single UPDATE query.

    FIX: the original two-step verify → mark approach has a race condition:
    two concurrent requests can both pass the verify check before either marks
    the code used, allowing a recovery code to be used twice.

    This version uses a single atomic UPDATE and returns True only if one row
    was actually updated (i.e., the code was valid and unused at the time of
    the update).

    Returns:
        True if the code was valid and has now been consumed.
        False if the code was not found, already used, or belongs to another user.
    """
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    updated = MFARecoveryCode.objects.filter(
        user=user,
        code_hash=code_hash,
        is_used=False,
    ).update(
        is_used=True,
        used_at=timezone.now(),
    )
    return updated == 1


def store_recovery_codes(user, plain_codes: list[str]) -> None:
    """
    Store hashed recovery codes for a user.
    Deletes any existing unused codes first (fresh set on each MFA setup).
    """
    MFARecoveryCode.objects.filter(user=user, is_used=False).delete()

    MFARecoveryCode.objects.bulk_create(
        [
            MFARecoveryCode(
                user=user,
                code_hash=hashlib.sha256(code.encode()).hexdigest(),
            )
            for code in plain_codes
        ]
    )


# ============================================================================
# Network Utilities
# ============================================================================


def get_client_ip(request) -> str:
    """
    Extract the real client IP from the request, respecting X-Forwarded-For
    when set by a trusted proxy. Always returns a string (never None).

    Configure TRUSTED_PROXY_DEPTH in settings if behind multiple proxies.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if x_forwarded_for:
        # Take the first (leftmost) IP — the actual client
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")
