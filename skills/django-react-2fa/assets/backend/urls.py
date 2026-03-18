"""
TOTP 2FA URL patterns.

Add these to your auth URL configuration:
    path("totp/", include("your_app.totp_urls")),

Or merge them directly into your existing auth urls.py.
"""

from django.urls import path

from . import views  # adapt import path

# These assume your auth URLs are mounted at /api/v1/auth/
# Full paths: /api/v1/auth/totp/setup/, /api/v1/auth/totp/enable/, etc.
totp_urlpatterns = [
    path("totp/setup/", views.totp_setup, name="totp-setup"),
    path("totp/backup-codes/regenerate/", views.totp_backup_codes_regenerate, name="totp-backup-codes-regenerate"),
    # totp/<action>/ handles both enable and disable via URL parameter
    path("totp/<str:action>/", views.totp_toggle, name="totp-toggle"),
]
