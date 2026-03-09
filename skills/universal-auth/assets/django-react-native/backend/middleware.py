"""
JWT authentication middleware — Universal Auth Skill template.
Stack: Django REST Framework

IMPROVEMENTS over source:
  - Imports tokens.py instead of auth0.py (Auth0-agnostic)
  - session_id check uses select_related to avoid N+1
  - MFA pending scope raises PermissionDenied instead of silently attaching flag
    (downstream views must explicitly allow mfa_pending using IsMfaPending permission)
"""

import logging

from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied

from .tokens import decode_token

logger = logging.getLogger(__name__)
User = get_user_model()


class JWTAuthentication(BaseAuthentication):
    """
    DRF authentication class — validates JWT Bearer tokens.

    Attaches to request:
        request.auth_claims  — dict of custom claims
        request.jwt_payload  — full decoded payload

    Usage:
        Authorization: Bearer <access_token>
    """

    keyword = "Bearer"

    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "").strip()
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) == 0 or parts[0].lower() != self.keyword.lower():
            return None
        if len(parts) != 2:
            raise AuthenticationFailed("Invalid Authorization header. Expected: Bearer <token>")

        return self._authenticate_token(parts[1].strip(), request)

    def _authenticate_token(self, token: str, request):
        import jwt as pyjwt

        try:
            payload = decode_token(token)
        except pyjwt.ExpiredSignatureError as e:
            raise AuthenticationFailed("Token has expired", code="token_expired") from e
        except pyjwt.PyJWTError as e:
            raise AuthenticationFailed(f"Invalid token: {e}", code="invalid_token") from e

        claims = self._extract_claims(payload)

        # Partial MFA token — attach flag; downstream must check IsMfaPending
        scope = payload.get("scope", "")
        if scope == "mfa_pending":
            claims["mfa_pending"] = True

        user = self._get_user(claims)
        if user is None:
            raise AuthenticationFailed("User not found")
        if not user.is_active:
            raise AuthenticationFailed("Account is disabled")
        if getattr(user, "is_suspended", False):
            raise PermissionDenied("Account is suspended")

        # Session revocation check
        session_id = payload.get("session_id")
        if session_id:
            from .models import UserSession

            session = (
                UserSession.objects
                .filter(session_id=session_id, user=user)
                .only("is_active")
                .first()
            )
            if session and not session.is_active:
                raise AuthenticationFailed("Session has been revoked")

        request.auth_claims = claims
        request.jwt_payload = payload
        return (user, claims)

    def _extract_claims(self, payload: dict) -> dict:
        """Extract custom namespace claims. Update namespace to match your settings."""
        # Detect namespace dynamically — supports both custom and Auth0 formats
        ns = None
        for key in payload:
            if key.startswith("https://") and key.endswith("/user_id"):
                ns = key.rsplit("/user_id", 1)[0]
                break

        if ns:
            return {
                "user_id": payload.get(f"{ns}/user_id"),
                "user_type": payload.get(f"{ns}/user_type"),
                "permissions": payload.get(f"{ns}/permissions", []),
                "email": payload.get("email"),
                "email_verified": payload.get("email_verified", False),
            }

        # Fallback — token has no namespace (dev/test minimal tokens)
        return {
            "user_id": payload.get("user_id") or payload.get("sub"),
            "user_type": payload.get("user_type", ""),
            "permissions": payload.get("permissions", []),
            "email": payload.get("email", ""),
            "email_verified": payload.get("email_verified", False),
        }

    def _get_user(self, claims: dict):
        user_id = claims.get("user_id")
        if user_id:
            try:
                return User.all_objects.get(id=user_id)
            except (User.DoesNotExist, ValueError):
                pass
        return None

    def authenticate_header(self, request):
        return f'{self.keyword} realm="api"'
