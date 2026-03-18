"""
Login OTP Resend Throttle

Separate throttle for login OTP resend endpoint. More generous than
the general OTP resend throttle because users may need to switch
channels (phone -> email or vice versa) during the login fallback flow.

Usage:
    from .throttles import LoginOTPResendThrottle

    @throttle_classes([LoginOTPResendThrottle])
    def login_resend_otp(request):
        ...

Settings (add to REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]):
    "login_otp_resend": "6/hour",
"""

from rest_framework.throttling import SimpleRateThrottle


class LoginOTPResendThrottle(SimpleRateThrottle):
    """
    Throttle for login OTP resend endpoint.

    More generous than the general OTPResendThrottle (typically 3/hour)
    because channel switching (phone -> email -> resend) is a legitimate
    user action during the TOTP fallback flow.

    Limits: 6 resends per hour per IP address.
    Applies to: login_resend_otp only.
    """

    scope = "login_otp_resend"

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}
