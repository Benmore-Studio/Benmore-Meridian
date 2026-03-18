"""
TOTP Service — RFC 6238 Time-based One-Time Password Authentication

Implements authenticator app support (Google Authenticator, Authy, Microsoft Authenticator)
with Fernet-encrypted secret storage and SHA-256 hashed backup codes.

Security model:
- TOTP secrets are encrypted with Fernet (AES-128-CBC + HMAC-SHA256) before DB storage
- Encryption key derived from DJANGO_SECRET_KEY (never stored separately)
- Secrets displayed exactly once (during enrollment) then encrypted
- 30-second windows with +-1 window drift tolerance (90-second validation window)
- Backup codes are SHA-256 hashed before storage (irreversible)

Dependencies:
    pip install pyotp qrcode[pil] cryptography
"""

import base64
import hashlib
import io
import logging
import secrets
import string

import pyotp
import qrcode
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────────────
BACKUP_CODE_COUNT = 10
BACKUP_CODE_LENGTH = 10
# TOTP_ISSUER_NAME is displayed in the user's authenticator app.
# Override via Django settings: TOTP_ISSUER_NAME = "Your App Name"
TOTP_ISSUER_NAME = getattr(settings, "TOTP_ISSUER_NAME", "MyApp")
# TTL for pending TOTP secret in Redis (seconds). User must complete setup within this window.
TOTP_PENDING_SECRET_TTL = 600  # 10 minutes


# ── Encryption ───────────────────────────────────────────────────────────────

def _get_fernet() -> Fernet:
    """
    Build a Fernet cipher from the Django secret key.

    Derives a 32-byte URL-safe base64 key from SECRET_KEY so
    the encryption key is never stored separately.
    """
    raw = settings.SECRET_KEY.encode()
    key_bytes = raw[:32].ljust(32, b"0")
    encoded_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(encoded_key)


def encrypt_totp_secret(plain_secret: str) -> str:
    """Encrypt a TOTP base32 secret for database storage."""
    fernet = _get_fernet()
    return fernet.encrypt(plain_secret.encode()).decode()


def decrypt_totp_secret(encrypted_secret: str) -> str | None:
    """
    Decrypt a stored TOTP secret.
    Returns None if the ciphertext is invalid (key rotation, corruption).
    """
    try:
        fernet = _get_fernet()
        return fernet.decrypt(encrypted_secret.encode()).decode()
    except (InvalidToken, Exception):
        logger.error("Failed to decrypt TOTP secret — key mismatch or corruption")
        return None


# ── TOTP Generation & Verification ──────────────────────────────────────────

def generate_totp_secret() -> str:
    """Generate a random base32 TOTP secret (RFC 6238 compatible)."""
    return pyotp.random_base32()


def build_provisioning_uri(secret: str, email: str, issuer: str | None = None) -> str:
    """
    Build the otpauth:// URI used to populate QR codes.
    Format: otpauth://totp/{issuer}:{email}?secret={secret}&issuer={issuer}
    """
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=issuer or TOTP_ISSUER_NAME)


def generate_qr_code_data_uri(provisioning_uri: str) -> str:
    """
    Generate a QR code and return it as a data:image/png;base64,... URI
    ready for <img src="..."> embedding.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(provisioning_uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    b64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def verify_totp_code(secret: str, code: str, valid_window: int = 1) -> bool:
    """
    Verify a 6-digit TOTP code.

    Args:
        secret: Raw (decrypted) base32 TOTP secret
        code: 6-digit string from the authenticator app
        valid_window: Number of 30-second windows to allow on either side
                      (default 1 = +-30 seconds = 90-second validation window)
    """
    if not secret or not code:
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=valid_window)


# ── Backup Codes ─────────────────────────────────────────────────────────────

def generate_backup_codes() -> tuple[list[str], list[str]]:
    """
    Generate BACKUP_CODE_COUNT single-use backup codes.

    Returns:
        (plaintext_codes, hashed_codes) — store hashed in DB,
        display plaintext to user exactly once.
    """
    alphabet = string.ascii_uppercase + string.digits
    plaintext_codes = [
        "".join(secrets.choice(alphabet) for _ in range(BACKUP_CODE_LENGTH))
        for _ in range(BACKUP_CODE_COUNT)
    ]
    # Format as XXXXX-XXXXX for readability
    formatted = [f"{c[:5]}-{c[5:]}" for c in plaintext_codes]
    hashed = [hashlib.sha256(c.encode()).hexdigest() for c in formatted]
    return formatted, hashed


def verify_backup_code(provided_code: str, stored_hashes: list[str]) -> tuple[bool, list[str]]:
    """
    Verify a backup code against stored SHA-256 hashes.
    Removes the matched hash (single-use).

    Returns:
        (is_valid, remaining_hashes)
    """
    code = provided_code.upper().replace(" ", "").strip()
    h = hashlib.sha256(code.encode()).hexdigest()
    if h in stored_hashes:
        remaining = [x for x in stored_hashes if x != h]
        return True, remaining
    return False, stored_hashes
