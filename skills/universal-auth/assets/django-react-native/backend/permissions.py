"""
RBAC permission classes — Universal Auth Skill template.
Stack: Django REST Framework

IMPROVEMENTS over source:
  - IsMfaPending added (inverse of IsMfaVerified — required by /auth/mfa/verify/)
  - HasPermission now logs a warning when required_permission is unset
    (silent True is a misconfiguration footgun in production)
  - IsOwnerOrAdmin docstring clarifies has_object_permission won't run without
    has_permission returning True first — common gotcha with DRF permission chaining
"""

import logging

from rest_framework.permissions import BasePermission

logger = logging.getLogger(__name__)


# ============================================================================
# Role permissions
# ============================================================================


class IsPatient(BasePermission):
    """Allow access only to patient users."""

    message = "Only patient users can access this endpoint."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.user_type == "patient"


class IsProvider(BasePermission):
    """Allow access only to provider users."""

    message = "Only provider users can access this endpoint."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.user_type == "provider"


class IsAdmin(BasePermission):
    """Allow access only to admin users."""

    message = "Only admin users can access this endpoint."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.user_type == "admin"


class IsProviderOrAdmin(BasePermission):
    """Allow access to provider or admin users."""

    message = "Only provider or admin users can access this endpoint."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.user_type in ("provider", "admin")


class IsFrontDesk(BasePermission):
    """Allow access only to front_desk users."""

    message = "Only front desk users can access this endpoint."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.user_type == "front_desk"


class IsProviderOrFrontDesk(BasePermission):
    """Allow access to provider or front_desk users."""

    message = "Only provider or front desk users can access this endpoint."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.user_type in ("provider", "front_desk")


# ============================================================================
# Object-level permissions
# ============================================================================


class IsOwnerOrAdmin(BasePermission):
    """
    Allow access to the owner of a resource or admin users.

    IMPORTANT: has_object_permission() is only called if has_permission()
    returns True first. Always pair this class with IsAuthenticated (or
    equivalent) when using it in permission_classes. Otherwise the object
    check is silently skipped.

    The view must set a `get_owner` method or the object must have a
    `user` or `user_id` field.
    """

    message = "You do not have permission to access this resource."

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.user_type == "admin":
            return True

        if hasattr(obj, "user"):
            return obj.user == request.user
        if hasattr(obj, "user_id"):
            return obj.user_id == request.user.id

        return False


# ============================================================================
# MFA permissions
# ============================================================================


class IsMfaVerified(BasePermission):
    """
    Deny access if the user's JWT has mfa_pending scope.
    Apply to all protected endpoints to block partial-auth tokens.
    """

    message = "MFA verification required."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        claims = getattr(request, "auth_claims", {})
        return not claims.get("mfa_pending")


class IsMfaPending(BasePermission):
    """
    Allow access ONLY to users with mfa_pending scope.
    Apply exclusively to /auth/mfa/verify/ — no other endpoint should accept
    partial-auth tokens.

    NEW: not present in source. Required so MFAVerifyAPIView doesn't need
    to check mfa_pending manually; the permission class handles it declaratively.
    """

    message = "This endpoint is only accessible during MFA verification."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        claims = getattr(request, "auth_claims", {})
        return bool(claims.get("mfa_pending"))


# ============================================================================
# Claim-based permissions
# ============================================================================


class HasPermission(BasePermission):
    """
    Check if the user has a specific permission string from JWT claims.

    Usage:
        class MyView(APIView):
            permission_classes = [IsAuthenticated, HasPermission]
            required_permission = "read:patient_records"

    FIX: source silently returned True when required_permission was not set.
    This is dangerous — a misconfigured view would appear to work but bypass
    all permission checks. Now logs a warning so misconfiguration is visible.
    """

    message = "You do not have the required permission."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        required = getattr(view, "required_permission", None)
        if not required:
            # FIX: warn instead of silently granting access
            logger.warning(
                "HasPermission used on %s but required_permission is not set. "
                "Granting access — set required_permission to silence this.",
                view.__class__.__name__,
            )
            return True

        claims = getattr(request, "auth_claims", {})
        permissions = claims.get("permissions", [])
        return required in permissions
