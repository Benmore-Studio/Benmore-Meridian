"""
User Model Fields for TOTP 2FA

Add these fields to your custom User model (AbstractUser or AbstractBaseUser).
Then run: python manage.py makemigrations && python manage.py migrate
"""

from django.db import models

# ── Add these fields to your User model ──────────────────────────────────────

# TOTP / Authenticator App (RFC 6238)
totp_enabled = models.BooleanField(
    default=False,
    db_index=True,
    help_text="Whether TOTP authenticator app 2FA is active for this user",
)
totp_secret_encrypted = models.TextField(
    null=True,
    blank=True,
    help_text="Fernet-encrypted TOTP base32 secret — never expose in API responses",
)
totp_backup_codes = models.JSONField(
    default=list,
    blank=True,
    help_text="List of SHA-256 hashed single-use backup codes for TOTP recovery",
)


# ── Example User model ──────────────────────────────────────────────────────

"""
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(unique=True)

    # ... your existing fields ...

    # TOTP 2FA fields
    totp_enabled = models.BooleanField(default=False, db_index=True)
    totp_secret_encrypted = models.TextField(null=True, blank=True)
    totp_backup_codes = models.JSONField(default=list, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
"""


# ── Serializer field (add to your user serializer) ──────────────────────────

"""
# In your UserSerializer or UserDetailSerializer, include:
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "email", "totp_enabled",
            # ... other fields ...
        ]
        # NEVER include totp_secret_encrypted or totp_backup_codes
"""
