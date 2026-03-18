"""
Login Flow Integration for TOTP 2FA

This file shows how to integrate TOTP into your existing two-phase login flow.
These are NOT standalone views — adapt them into your existing login/verify views.

Two-Phase Login Architecture:
    Phase 1: POST /auth/login/       → Validate credentials, determine OTP channel
    Phase 2: POST /auth/login/verify/ → Verify OTP code, issue JWT tokens
             POST /auth/login/resend/ → Resend OTP (with optional channel switching)
"""


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 1: Modify your send_login_otp service method
# ══════════════════════════════════════════════════════════════════════════════

def send_login_otp_example(user, ip_address=None):
    """
    Determine OTP channel and send code.
    TOTP takes priority: if enabled, skip delivery — user enters code from app.

    Returns:
        dict with: success, login_token, otp_channel, phone_masked, message
    """
    import uuid

    login_token = str(uuid.uuid4())

    # Store login_token -> user_id in Redis (10 min TTL)
    # store_login_token(login_token, user.id)  # Your Redis utility

    # TOTP takes priority
    if user.totp_enabled:
        return {
            "success": True,
            "login_token": login_token,
            "otp_channel": "totp",
            "phone_masked": None,
            "message": "Enter the 6-digit code from your authenticator app.",
        }

    # Phone-first, email fallback
    if user.phone_number:
        # send_phone_otp(user.phone_number, user)  # Your SMS service
        # Mask phone for frontend display
        digits = user.phone_number[-6:] if len(user.phone_number) >= 6 else user.phone_number
        phone_masked = f"***-*{digits[0:2]}-{digits[2:]}" if len(digits) >= 6 else f"***{digits}"
        return {
            "success": True,
            "login_token": login_token,
            "otp_channel": "phone",
            "phone_masked": phone_masked,
            "message": "Verification code sent to your phone.",
        }
    else:
        # send_email_otp(user.email)  # Your email service
        return {
            "success": True,
            "login_token": login_token,
            "otp_channel": "email",
            "phone_masked": None,
            "message": "Verification code sent to your email.",
        }


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2: Modify your verify_login_otp service method
# ══════════════════════════════════════════════════════════════════════════════

def verify_login_otp_example(user, otp):
    """
    Verify login OTP with 3-tier fallback for TOTP users:
        1. Try authenticator app code (TOTP)
        2. Try backup code (XXXXX-XXXXX format)
        3. Try phone/email OTP (sent via resend endpoint as fallback)

    For non-TOTP users, verify directly via phone or email.

    Returns:
        tuple: (success: bool, message: str)
    """
    from your_app.totp_service import decrypt_totp_secret, verify_backup_code, verify_totp_code

    if user.totp_enabled:
        # Tier 1: Try authenticator app code
        plain_secret = decrypt_totp_secret(user.totp_secret_encrypted or "")
        if plain_secret and verify_totp_code(plain_secret, otp):
            return True, "Login verified via authenticator app."

        # Tier 2: Try backup code (format: XXXXX-XXXXX)
        valid, remaining = verify_backup_code(otp, user.totp_backup_codes or [])
        if valid:
            user.totp_backup_codes = remaining
            user.save(update_fields=["totp_backup_codes"])
            return True, "Login verified via backup code."

        # Tier 3: Try phone/email OTP fallback
        # (user requested this via the resend endpoint when locked out of authenticator)
        if user.phone_number:
            success, message = verify_phone_otp(user.phone_number, otp)  # noqa: F821
            if success:
                return True, "Login verified via phone."
        else:
            success, message = verify_email_otp(user.email, otp)  # noqa: F821
            if success:
                return True, "Login verified via email."

        return False, "Invalid code. Please check and try again."

    # Non-TOTP users: direct phone/email verification
    if user.phone_number:
        return verify_phone_otp(user.phone_number, otp)  # noqa: F821
    else:
        return verify_email_otp(user.email, otp)  # noqa: F821


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 3: Login resend with channel switching
# ══════════════════════════════════════════════════════════════════════════════

def login_resend_otp_view_example(request):
    """
    Resend login OTP with optional channel preference.

    Request body:
        login_token: str (required)
        channel: "phone" | "email" (optional — defaults to phone-first)

    Response data:
        otp_channel: "phone" | "email"
        phone_masked: str | null
        has_phone: bool  (so frontend knows if channel switching is available)

    IMPORTANT: Use LoginOTPResendThrottle (6/hour), NOT the general
    OTPResendThrottle (3/hour). Channel switching is a legitimate action
    that would otherwise hit the stricter limit too quickly.
    """
    # serializer validation, login_token lookup, user fetch...
    # user = User.objects.get(id=user_id_from_token)

    preferred_channel = request.data.get("channel")  # "phone", "email", or None
    phone_masked = None

    if preferred_channel == "email":
        # Force email even if phone is available
        # send_email_otp(user.email)
        channel = "email"
    elif preferred_channel == "phone" and hasattr(request, '_user') and request._user.phone_number:
        # send_phone_otp(user.phone_number, user)
        channel = "phone"
    elif hasattr(request, '_user') and request._user.phone_number:
        # Default: phone-first
        # send_phone_otp(user.phone_number, user)
        channel = "phone"
    else:
        # send_email_otp(user.email)
        channel = "email"

    # Build masked phone for display
    # if channel == "phone" and user.phone_number:
    #     digits = user.phone_number[-6:]
    #     phone_masked = f"***-*{digits[0:2]}-{digits[2:]}"

    return {
        "otp_channel": channel,
        "phone_masked": phone_masked,
        "has_phone": True,  # bool(user.phone_number)
    }


# ══════════════════════════════════════════════════════════════════════════════
# SERIALIZER: Add channel field to your login resend serializer
# ══════════════════════════════════════════════════════════════════════════════

"""
class LoginOTPResendSerializer(serializers.Serializer):
    login_token = serializers.CharField(required=True)
    channel = serializers.ChoiceField(
        choices=["phone", "email"],
        required=False,
        help_text="Preferred delivery channel. If omitted, phone is used when available.",
    )
"""


# ══════════════════════════════════════════════════════════════════════════════
# SETTINGS: Add throttle rate for login resend
# ══════════════════════════════════════════════════════════════════════════════

"""
# In your REST_FRAMEWORK settings:
"DEFAULT_THROTTLE_RATES": {
    # ... existing rates ...
    "login_otp_resend": "6/hour",  # Generous for channel switching
}
"""
