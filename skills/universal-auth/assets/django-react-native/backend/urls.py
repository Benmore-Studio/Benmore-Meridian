"""
URL routing for auth app — Universal Auth Skill template.
Stack: Django

IMPROVEMENTS over source:
  - Removed project-specific stub import (PatientMeAPIView from stubs)
  - Relative imports instead of absolute (portable across project renames)
  - Grouped comments align with auth flow stages for readability
"""

from django.urls import path

from .views.auth import (
    BiometricLoginAPIView,
    BiometricRegisterAPIView,
    BiometricRevokeAPIView,
    EmailResendVerificationAPIView,
    EmailVerifyAPIView,
    ForgotPasswordAPIView,
    LoginAPIView,
    LogoutAllAPIView,
    LogoutAPIView,
    MeAPIView,
    MFADisableAPIView,
    MFAEnableAPIView,
    MFASetupAPIView,
    MFAVerifyAPIView,
    ProfileAPIView,
    RegisterAPIView,
    ResetPasswordAPIView,
    SessionsListAPIView,
    TokenRefreshAPIView,
)

app_name = "accounts"

urlpatterns = [
    # ── Core auth ─────────────────────────────────────────────────────────────
    path("auth/login/", LoginAPIView.as_view(), name="login"),
    path("auth/register/", RegisterAPIView.as_view(), name="register"),
    path("auth/logout/", LogoutAPIView.as_view(), name="logout"),
    path("auth/logout/all/", LogoutAllAPIView.as_view(), name="logout-all"),

    # ── Token management ──────────────────────────────────────────────────────
    path("auth/token/refresh/", TokenRefreshAPIView.as_view(), name="token-refresh"),

    # ── Email verification ────────────────────────────────────────────────────
    path("auth/email/verify/", EmailVerifyAPIView.as_view(), name="email-verify"),
    path(
        "auth/email/resend-verification/",
        EmailResendVerificationAPIView.as_view(),
        name="email-resend-verification",
    ),

    # ── MFA (TOTP) ────────────────────────────────────────────────────────────
    path("auth/mfa/verify/", MFAVerifyAPIView.as_view(), name="mfa-verify"),
    path("auth/mfa/setup/", MFASetupAPIView.as_view(), name="mfa-setup"),
    path("auth/mfa/enable/", MFAEnableAPIView.as_view(), name="mfa-enable"),
    path("auth/mfa/disable/", MFADisableAPIView.as_view(), name="mfa-disable"),

    # ── User profile ──────────────────────────────────────────────────────────
    path("auth/me/", MeAPIView.as_view(), name="me"),
    path("auth/profile/", ProfileAPIView.as_view(), name="profile"),

    # ── Sessions ──────────────────────────────────────────────────────────────
    path("auth/sessions/", SessionsListAPIView.as_view(), name="sessions"),

    # ── Password reset ────────────────────────────────────────────────────────
    path("auth/password/forgot/", ForgotPasswordAPIView.as_view(), name="password-forgot"),
    path("auth/password/reset/", ResetPasswordAPIView.as_view(), name="password-reset"),

    # ── Biometric ─────────────────────────────────────────────────────────────
    path("auth/biometric/register/", BiometricRegisterAPIView.as_view(), name="biometric-register"),
    path("auth/biometric/login/", BiometricLoginAPIView.as_view(), name="biometric-login"),
    path("auth/biometric/revoke/", BiometricRevokeAPIView.as_view(), name="biometric-revoke"),
]
