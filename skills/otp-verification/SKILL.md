---
name: otp-verification
description: OTP Verification Implementation Skill
---

# OTP Verification Implementation Skill

## Purpose

This skill guides Claude Code through implementing and maintaining the OTP (One-Time Password) authentication system for customers in the House Service Pass mobile app and Django backend.

## When to Use This Skill

Use this skill when:
- Implementing the OTP authentication flow from scratch
- Adding OTP to new endpoints or authentication methods
- Debugging OTP delivery or verification issues
- Scaling OTP system for high request volumes
- Modifying rate limiting or security parameters
- Investigating fraud or suspicious authentication attempts
- Adding new OTP purposes (2FA, password reset, etc.)

## Architecture Overview

The OTP system authenticates customers using their phone number without requiring passwords. Three-step flow:

1. **Validate Pass Code**: Customer provides HSP-XXXX-XXXX pass code, backend returns masked phone
2. **Send OTP**: Backend sends 6-digit code via SMS, starts 10-minute countdown
3. **Verify OTP**: Customer enters code, backend validates and issues JWT tokens

Rate limiting operates at two levels: phone-based (10/day) and IP-based (5/hour) to prevent brute force attacks.

## Phase 1: Database Models

### OTPVerification Model

```python
# django-backend/accounts/models.py
# Add to existing models.py file

class OTPVerification(models.Model):
    """
    OTP verification for email verification and password reset
    Implements secure OTP generation and validation
    """

    PURPOSE_CHOICES = [
        ('email_verification', 'Email Verification'),
        ('password_reset', 'Password Reset'),
        ('login_verification', '2FA Login'),
        ('phone_verification', 'Phone Verification'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_verifications')

    # OTP details
    otp_code = models.CharField(max_length=6, db_index=True)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)

    # Security
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=3)
    is_used = models.BooleanField(default=False, db_index=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    # Additional data
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = 'otp_verifications'
        verbose_name = 'OTP Verification'
        verbose_name_plural = 'OTP Verifications'
        indexes = [
            models.Index(fields=['user', 'purpose', 'is_used']),
            models.Index(fields=['otp_code', 'expires_at']),
        ]
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.otp_code:
            self.otp_code = self.generate_otp()
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    @staticmethod
    def generate_otp():
        """Generate a secure 6-digit OTP"""
        return str(secrets.randbelow(900000) + 100000)

    def is_valid(self):
        """Check if OTP is valid"""
        return (
            not self.is_used and
            self.attempts < self.max_attempts and
            timezone.now() < self.expires_at
        )

    def verify(self, otp_input):
        """Verify the OTP input"""
        if not self.is_valid():
            return False

        self.attempts += 1

        if self.otp_code == otp_input:
            self.is_used = True
            self.verified_at = timezone.now()
            self.save()
            return True

        self.save()
        return False

    def __str__(self):
        return f"{self.user.email} - {self.purpose} - {self.otp_code}"
OTPRequestLog Model
# django-backend/accounts/models.py
# Add to existing models.py file

class OTPRequestLog(models.Model):
    """
    Audit log for OTP requests - tracks all OTP request attempts per phone number
    Used for rate limiting enforcement and fraud investigation
    """

    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('rate_limited', 'Rate Limited'),
    ]

    PURPOSE_CHOICES = [
        ('phone_verification', 'Phone Verification'),
        ('login_verification', '2FA Login'),
        ('email_verification', 'Email Verification'),
        ('password_reset', 'Password Reset'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(max_length=20, db_index=True)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'otp_request_logs'
        verbose_name = 'OTP Request Log'
        verbose_name_plural = 'OTP Request Logs'
        indexes = [
            models.Index(fields=['phone_number', 'created_at']),
            models.Index(fields=['phone_number', 'purpose', 'created_at']),
            models.Index(fields=['ip_address', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.phone_number} - {self.purpose} - {self.status} - {self.created_at}"
Phase 2: OTP Service Layer
OTPService Class
# django-backend/accounts/services/otp_service.py

import logging
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from accounts.models import OTPVerification, User, OTPRequestLog
from payments.services.twilio_service import TwilioSMSService

logger = logging.getLogger(__name__)


class OTPService:
    """
    Service to manage OTP generation and verification for customer authentication

    Phone-based rate limiting:
    - Maximum 10 OTP requests per phone number per 24 hours (all purposes combined)
    - Prevents brute force attacks and spam across IP rotation
    - Counts even if SMS delivery fails
    """

    # Phone rate limiting configuration
    PHONE_RATE_LIMIT = 10
    PHONE_RATE_WINDOW = 86400  # 24 hours in seconds

    @staticmethod
    def _get_phone_cache_key(phone_number: str) -> str:
        """
        Generate cache key for phone-based rate limiting

        Args:
            phone_number: User's phone number in E.164 format

        Returns:
            str: Cache key for storing phone rate limit counter
        """
        return f'otp_phone_rate_{phone_number}'

    @staticmethod
    def check_phone_rate_limit(phone_number: str) -> dict | None:
        """
        Check if phone number has exceeded rate limit

        Args:
            phone_number: User's phone number in E.164 format

        Returns:
            None if phone can request OTP
            dict with error details if rate limited
        """
        cache_key = OTPService._get_phone_cache_key(phone_number)
        current_count = cache.get(cache_key, 0)

        if current_count >= OTPService.PHONE_RATE_LIMIT:
            retry_after = OTPService.PHONE_RATE_WINDOW

            logger.warning(
                f"Phone rate limit exceeded for {OTPService.mask_phone(phone_number)}: "
                f"{current_count}/{OTPService.PHONE_RATE_LIMIT} requests"
            )

            return {
                'success': False,
                'error': 'phone_rate_limited',
                'message': 'Too many OTP requests sent to this phone number. Please try again later.',
                'retry_after_seconds': retry_after
            }

        return None

    @staticmethod
    def increment_phone_counter(phone_number: str) -> int:
        """
        Increment phone rate limit counter by 1 using atomic operation
        Sets 24-hour expiry for the counter

        Args:
            phone_number: User's phone number in E.164 format

        Returns:
            int: Updated counter value
        """
        cache_key = OTPService._get_phone_cache_key(phone_number)

        # Use atomic incr() to prevent race conditions
        try:
            new_count = cache.incr(cache_key)
        except ValueError:
            # Key doesn't exist, initialize it
            if cache.add(cache_key, 1, timeout=OTPService.PHONE_RATE_WINDOW):
                new_count = 1
            else:
                # Race condition: another thread created it, increment it
                new_count = cache.incr(cache_key)

        # Update timeout on the key
        cache.touch(cache_key, timeout=OTPService.PHONE_RATE_WINDOW)

        logger.info(
            f"Phone OTP counter incremented for {OTPService.mask_phone(phone_number)}: "
            f"{new_count}/{OTPService.PHONE_RATE_LIMIT}"
        )

        return new_count

    @staticmethod
    def log_otp_request(phone_number: str, purpose: str, status: str, ip_address: str | None = None) -> None:
        """
        Log OTP request for audit trail and fraud investigation

        Args:
            phone_number: User's phone number in E.164 format
            purpose: OTP purpose (phone_verification, login_verification, etc.)
            status: Request status (success, failed, rate_limited)
            ip_address: Client IP address (optional)
        """
        try:
            OTPRequestLog.objects.create(
                phone_number=phone_number,
                purpose=purpose,
                status=status,
                ip_address=ip_address
            )
            logger.info(
                f"OTP request logged: {OTPService.mask_phone(phone_number)} | "
                f"purpose={purpose} | status={status}"
            )
        except Exception as e:
            # Don't let logging failures break the OTP flow
            logger.error(f"Failed to log OTP request: {str(e)}")

    @staticmethod
    def create_and_send_otp(user: User, purpose: str = 'phone_verification', ip_address: str | None = None) -> dict:
        """
        Create OTP and send via SMS

        Args:
            user: User to send OTP to
            purpose: OTP purpose (phone_verification, login_verification, etc.)
            ip_address: Client IP address for audit logging (optional)

        Returns:
            dict: Result with success status and message
        """
        if not user.phone_number:
            logger.warning(f"Cannot send OTP to {user.email}: no phone number")
            return {
                'success': False,
                'error': 'no_phone_number',
                'message': 'No phone number on file'
            }

        # Check phone-based rate limit BEFORE creating OTP
        rate_limit_error = OTPService.check_phone_rate_limit(user.phone_number)
        if rate_limit_error:
            # Log rate limited attempt for audit trail
            OTPService.log_otp_request(user.phone_number, purpose, 'rate_limited', ip_address)
            return rate_limit_error

        # Increment phone counter (counts all purposes together)
        OTPService.increment_phone_counter(user.phone_number)

        # Invalidate any existing unused OTPs for this purpose
        OTPVerification.objects.filter(
            user=user,
            purpose=purpose,
            is_used=False
        ).update(is_used=True)

        # Create new OTP
        otp = OTPVerification.objects.create(
            user=user,
            purpose=purpose,
        )

        # Send SMS (or bypass in development mode)
        message = f"Your House Service Pass verification code is: {otp.otp_code}. Expires in 10 minutes."

        # In development mode, skip actual SMS and log OTP to console
        if settings.DEBUG:
            logger.info(
                f"[DEV MODE] OTP for {user.email}: {otp.otp_code} "
                f"[WARNING: Never log OTP codes in production!]"
            )
            print(f"\n{'='*50}")
            print(f"[DEV MODE] OTP CODE: {otp.otp_code}")
            print(f"User: {user.email}")
            print(f"Phone: {user.phone_number}")
            print(f"[WARNING: This is sensitive information. Never log OTP codes in production!]")
            print(f"{'='*50}\n")
            sms_sent = True
        else:
            sms_sent = TwilioSMSService.send_sms(user.phone_number, message)

        if not sms_sent:
            logger.error(f"Failed to send OTP SMS to {user.phone_number}")
            # Mark OTP as used since we couldn't send it
            otp.is_used = True
            otp.save()
            # Log failed SMS send for audit trail
            OTPService.log_otp_request(user.phone_number, purpose, 'failed', ip_address)
            return {
                'success': False,
                'error': 'sms_failed',
                'message': 'Failed to send verification code'
            }

        logger.info(f"OTP sent to {user.email} ({OTPService.mask_phone(user.phone_number)})")

        # Log successful OTP send for audit trail
        OTPService.log_otp_request(user.phone_number, purpose, 'success', ip_address)

        return {
            'success': True,
            'phone_masked': OTPService.mask_phone(user.phone_number),
            'expires_in': 600  # 10 minutes in seconds
        }

    @staticmethod
    def verify_otp(user: User, otp_code: str, purpose: str = 'phone_verification') -> dict:
        """
        Verify OTP code

        Args:
            user: User to verify OTP for
            otp_code: OTP code to verify
            purpose: OTP purpose to match

        Returns:
            dict: Result with success status
        """
        # Find the most recent valid OTP for this user/purpose
        try:
            otp = OTPVerification.objects.filter(
                user=user,
                purpose=purpose,
                is_used=False,
                expires_at__gt=timezone.now()
            ).order_by('-created_at').first()
        except OTPVerification.DoesNotExist:
            otp = None

        if not otp:
            logger.warning(f"No valid OTP found for {user.email}")
            return {
                'success': False,
                'error': 'otp_expired',
                'message': 'Verification code expired or not found. Please request a new code.'
            }

        # Check max attempts
        if otp.attempts >= otp.max_attempts:
            logger.warning(f"Max OTP attempts reached for {user.email}")
            otp.is_used = True
            otp.save()
            return {
                'success': False,
                'error': 'too_many_attempts',
                'message': 'Too many attempts. Please request a new code.'
            }

        # Verify the OTP
        if otp.verify(otp_code):
            logger.info(f"OTP verified successfully for {user.email}")
            return {
                'success': True,
                'message': 'Verification successful'
            }
        else:
            remaining_attempts = otp.max_attempts - otp.attempts
            logger.warning(f"Invalid OTP for {user.email}. {remaining_attempts} attempts remaining.")
            return {
                'success': False,
                'error': 'invalid_otp',
                'message': f'Invalid code. {remaining_attempts} attempts remaining.',
                'attempts_remaining': remaining_attempts
            }

    @staticmethod
    def mask_phone(phone_number: str) -> str:
        """
        Mask phone number for display (e.g., +18015551234 → ***-***-1234)

        Args:
            phone_number: Full phone number

        Returns:
            str: Masked phone number
        """
        if not phone_number or len(phone_number) < 4:
            return '***-***-****'

        # Get last 4 digits
        last_four = phone_number[-4:]
        return f'***-***-{last_four}'
Phase 3: API Views & Endpoints
IP Extraction Utility
# django-backend/accounts/views.py
# Add at the top of views.py file

def get_client_ip(request):
    """
    Safely extract client IP address from request.
    Validates IP format and handles X-Forwarded-For headers.

    Args:
        request: Django HTTP request object

    Returns:
        str: Valid IPv4/IPv6 address or None if invalid
    """
    import ipaddress

    # Try X-Forwarded-For header first (for proxies)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # X-Forwarded-For can contain multiple IPs: client, proxy1, proxy2
        # Get the first (client) IP
        ips = x_forwarded_for.split(',')
        for ip in ips:
            ip = ip.strip()
            try:
                # Validate IP format
                ipaddress.ip_address(ip)
                return ip
            except ValueError:
                # Invalid IP, try next
                continue

    # Fallback to REMOTE_ADDR
    remote_addr = request.META.get('REMOTE_ADDR')
    if remote_addr:
        try:
            ipaddress.ip_address(remote_addr)
            return remote_addr
        except ValueError:
            pass

    # No valid IP found
    return None
Rate Throttle Configuration
# django-backend/accounts/views.py
# Add near the top with other imports and classes

from rest_framework.throttling import AnonRateThrottle


class OTPRateThrottle(AnonRateThrottle):
    """Rate limiting for OTP endpoints: 5 requests per hour per IP"""
    rate = '5/hour'
Customer Validate Pass Endpoint
# django-backend/accounts/views.py
# Add in the customer authentication section

@api_view(['POST'])
@permission_classes([AllowAny])
def customer_validate_pass(request):
    """
    Validate a pass code and return masked phone number for verification.

    Request body:
    {
        "pass_code": "HSP-1234-5678"
    }

    Returns:
        200: Pass is valid with masked phone number
        400: Invalid pass code format or pass not found/not paid
    """
    pass_code = request.data.get('pass_code', '').strip().upper()

    if not pass_code:
        return Response(
            {'valid': False, 'error': 'pass_code_required', 'message': 'Pass code is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate format
    import re
    if not re.match(r'^HSP-\d{4}-\d{4}$', pass_code):
        return Response(
            {'valid': False, 'error': 'invalid_format', 'message': 'Invalid pass code format'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        pass_purchase = PassPurchase.objects.select_related('user').get(pass_code=pass_code)
    except PassPurchase.DoesNotExist:
        logger.info(f"Pass code not found: {pass_code}")
        return Response({
            'valid': False,
            'error': 'pass_not_found',
            'message': 'Pass code not found'
        }, status=status.HTTP_200_OK)

    # Check payment status
    if pass_purchase.payment_status != 'paid':
        logger.info(f"Pass code not paid: {pass_code}")
        return Response({
            'valid': False,
            'error': 'pass_not_paid',
            'message': 'This pass has not been activated yet. Please complete your purchase first.'
        }, status=status.HTTP_200_OK)

    # Get user
    user = pass_purchase.user

    if not user.phone_number:
        logger.warning(f"User {user.email} has no phone number for pass {pass_code}")
        return Response(
            {'valid': False, 'error': 'no_phone', 'message': 'No phone number on file. Please contact support.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Mask phone number
    phone_masked = OTPService.mask_phone(user.phone_number)

    logger.info(f"Pass code validated: {pass_code} for user {user.email}")

    return Response({
        'valid': True,
        'phone_masked': phone_masked,
    }, status=status.HTTP_200_OK)
Customer Send OTP Endpoint
# django-backend/accounts/views.py
# Add in the customer authentication section

@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([OTPRateThrottle])
def customer_send_otp(request):
    """
    Send OTP to customer's phone number for verification.

    Rate limited: 5 requests per hour per IP address.

    Request body:
    {
        "pass_code": "HSP-1234-5678"
    }

    Returns:
        200: OTP sent successfully
        400: Invalid pass code or failed to send
        429: Too many requests (rate limited)
    """
    pass_code = request.data.get('pass_code', '').strip().upper()

    if not pass_code:
        return Response(
            {'sent': False, 'error': 'pass_code_required', 'message': 'Pass code is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        pass_purchase = PassPurchase.objects.select_related('user').get(
            pass_code=pass_code,
            payment_status='paid'
        )
    except PassPurchase.DoesNotExist:
        return Response(
            {'sent': False, 'error': 'invalid_pass', 'message': 'Invalid or inactive pass code'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = pass_purchase.user

    # Extract and validate client IP address for audit logging
    ip_address = get_client_ip(request)

    # Send OTP
    result = OTPService.create_and_send_otp(user, purpose='phone_verification', ip_address=ip_address)

    if result.get('success'):
        return Response({
            'sent': True,
            'phone_masked': result.get('phone_masked'),
            'expires_in': result.get('expires_in', 600)
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'sent': False,
            'error': result.get('error'),
            'message': result.get('message')
        }, status=status.HTTP_400_BAD_REQUEST)
Customer Verify OTP Endpoint
# django-backend/accounts/views.py
# Add in the customer authentication section

@api_view(['POST'])
@permission_classes([AllowAny])
def customer_verify_otp(request):
    """
    Verify OTP and issue JWT tokens for customer authentication.

    Request body:
    {
        "pass_code": "HSP-1234-5678",
        "otp": "123456"
    }

    Returns:
        200: Verification successful with JWT tokens and user data
        400: Invalid OTP or pass code
        401: OTP expired or too many attempts
    """
    pass_code = request.data.get('pass_code', '').strip().upper()
    otp_code = request.data.get('otp', '').strip()

    if not pass_code or not otp_code:
        return Response(
            {'success': False, 'error': 'missing_fields', 'message': 'Pass code and OTP are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        pass_purchase = PassPurchase.objects.select_related('user', 'plan').get(
            pass_code=pass_code,
            payment_status='paid'
        )
    except PassPurchase.DoesNotExist:
        return Response(
            {'success': False, 'error': 'invalid_pass', 'message': 'Invalid or inactive pass code'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = pass_purchase.user

    # Verify OTP
    result = OTPService.verify_otp(user, otp_code, purpose='phone_verification')

    if not result.get('success'):
        # Always use 400 for OTP errors (not 401) to avoid confusing
        # the mobile app's token refresh interceptor
        return Response({
            'success': False,
            'error': result.get('error'),
            'message': result.get('message'),
            'attempts_remaining': result.get('attempts_remaining')
        }, status=status.HTTP_400_BAD_REQUEST)

    # Mark user as verified
    user.is_verified = True
    user.save()

    # Generate JWT tokens
    refresh = CustomTokenObtainPairSerializer.get_token(user)
    access = refresh.access_token

    # Check pass expiration
    is_expired = False
    days_until_expiry = None

    if pass_purchase.expires_at:
        if pass_purchase.expires_at < timezone.now():
            is_expired = True
            pass_purchase.pass_status = 'expired'
            pass_purchase.save()
        else:
            days_until_expiry = (pass_purchase.expires_at - timezone.now()).days

    logger.info(f"Customer authenticated via OTP: {user.email}")

    return Response({
        'success': True,
        'access_token': str(access),
        'refresh_token': str(refresh),
        'user': {
            'id': str(user.id),
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone_number': user.phone_number,
        },
        'pass': {
            'pass_code': pass_purchase.pass_code,
            'status': pass_purchase.pass_status,
            'plan_name': pass_purchase.plan.name,
            'expires_at': pass_purchase.expires_at.isoformat() if pass_purchase.expires_at else None,
            'days_until_expiry': days_until_expiry,
            'is_expired': is_expired
        }
    }, status=status.HTTP_200_OK)
Phase 4: URL Configuration
# django-backend/accounts/urls.py
# Add these routes to the urlpatterns list

urlpatterns = [
    # ... existing routes ...
    
    # Customer authentication (phone + OTP)
    path('customer/validate-pass/', views.customer_validate_pass, name='customer_validate_pass'),
    path('customer/send-otp/', views.customer_send_otp, name='customer_send_otp'),
    path('customer/verify-otp/', views.customer_verify_otp, name='customer_verify_otp'),
]
Phase 5: Mobile App Integration
AuthContext Implementation
// mobile-app/src/context/AuthContext.tsx
// Add OTP-related functions to the existing AuthContext

import { sendOTP, verifyOTP, validatePassCode } from '../services/auth';
import type { SendOTPResponse, VerifyOTPResponse } from '../types/auth';

export function AuthProvider({ children, onAuthStateReady }: AuthProviderProps) {
  // ... existing state ...
  const [otpPhoneMasked, setOtpPhoneMasked] = useState<string | null>(null);
  const [otpExpiration, setOtpExpiration] = useState<number | null>(null);

  const requestOTP = useCallback(async (passCode: string) => {
    try {
      const response = await sendOTP(passCode);
      if (response.sent) {
        setOtpPhoneMasked(response.phone_masked);
        setOtpExpiration(response.expires_in);
        return { success: true, phoneMasked: response.phone_masked };
      } else {
        return { 
          success: false, 
          error: response.error, 
          message: response.message 
        };
      }
    } catch (error) {
      logger.error('Failed to send OTP:', error);
      return { 
        success: false, 
        error: 'network_error',
        message: 'Network error. Please try again.' 
      };
    }
  }, []);

  const submitOTP = useCallback(async (passCode: string, otp: string) => {
    try {
      const response = await verifyOTP(passCode, otp);
      if (response.success) {
        // Login successful - store tokens and user data
        await login(
          response.access_token,
          response.refresh_token,
          response.user,
          response.pass
        );
        setOtpPhoneMasked(null);
        setOtpExpiration(null);
        return { success: true };
      } else {
        return {
          success: false,
          error: response.error,
          message: response.message,
          attemptsRemaining: response.attempts_remaining
        };
      }
    } catch (error) {
      logger.error('Failed to verify OTP:', error);
      return {
        success: false,
        error: 'network_error',
        message: 'Network error. Please try again.'
      };
    }
  }, [login]);

  const value: AuthContextValue = {
    // ... existing values ...
    otpPhoneMasked,
    otpExpiration,
    requestOTP,
    submitOTP,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}
OTP Verification Screen
// mobile-app/src/screens/OTPVerificationScreen.tsx

import { useState, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet } from 'react-native';
import { useAuth } from '../context/AuthContext';
import { colors } from '../constants/colors';

export function OTPVerificationScreen({ route, navigation }: Props) {
  const { passCode } = route.params;
  const { submitOTP, otpPhoneMasked } = useAuth();
  
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [attemptsRemaining, setAttemptsRemaining] = useState(3);

  const handleVerifyOTP = async () => {
    if (otp.length !== 6) {
      setError('Please enter a 6-digit code');
      return;
    }

    setLoading(true);
    setError(null);

    const result = await submitOTP(passCode, otp);

    if (result.success) {
      // Authentication successful, navigate to dashboard
      navigation.reset({
        index: 0,
        routes: [{ name: 'Dashboard' }],
      });
    } else {
      setError(result.message);
      if (result.attemptsRemaining !== undefined) {
        setAttemptsRemaining(result.attemptsRemaining);
      }
    }

    setLoading(false);
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Enter Verification Code</Text>
      <Text style={styles.subtitle}>We sent a code to {otpPhoneMasked}</Text>

      <TextInput
        style={styles.input}
        placeholder="000000"
        placeholderTextColor={colors.text.muted}
        maxLength={6}
        keyboardType="numeric"
        value={otp}
        onChangeText={setOtp}
        editable={!loading}
      />

      {error && (
        <Text style={styles.error}>{error}</Text>
      )}

      {attemptsRemaining < 3 && (
        <Text style={styles.attemptsRemaining}>
          {attemptsRemaining} attempts remaining
        </Text>
      )}

      <TouchableOpacity 
        style={[styles.button, loading && styles.buttonDisabled]}
        onPress={handleVerifyOTP}
        disabled={loading}
      >
        <Text style={styles.buttonText}>
          {loading ? 'Verifying...' : 'Verify Code'}
        </Text>
      </TouchableOpacity>

      <TouchableOpacity onPress={() => navigation.goBack()}>
        <Text style={styles.backLink}>Enter a different pass code</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: colors.background,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.text.primary,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: colors.text.secondary,
    marginBottom: 24,
  },
  input: {
    borderWidth: 2,
    borderColor: colors.border,
    borderRadius: 8,
    padding: 16,
    fontSize: 24,
    textAlign: 'center',
    letterSpacing: 4,
    marginBottom: 16,
    color: colors.text.primary,
  },
  error: {
    color: colors.status.error,
    fontSize: 14,
    marginBottom: 16,
  },
  attemptsRemaining: {
    color: colors.status.warning,
    fontSize: 12,
    marginBottom: 16,
  },
  button: {
    backgroundColor: colors.primary,
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
    marginTop: 24,
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  buttonText: {
    color: colors.white,
    fontSize: 16,
    fontWeight: '600',
  },
  backLink: {
    color: colors.primary,
    fontSize: 14,
    textAlign: 'center',
    marginTop: 16,
  },
});
Testing Checklist
 OTPVerification model creates 6-digit code automatically
 OTP expires after 10 minutes
 Max 3 attempts per OTP enforced
 After 3 attempts, OTP marked as used
 Phone rate limit: max 10 requests per 24 hours per phone
 IP rate limit: max 5 requests per hour per IP
 Rate limit counter incremented atomically (no race conditions)
 Old OTPs invalidated when new one requested
 SMS sent successfully and OTP delivered
 SMS failures logged and OTP marked as unusable
 OTP verification succeeds with correct code
 OTP verification fails with incorrect code
 Remaining attempts returned in error response
 Pass code validation works (format, exists, paid)
 Phone number masked correctly in responses
 IP address extracted correctly from headers
 Development mode logs OTP instead of sending SMS
 User marked as verified after successful OTP
 JWT tokens issued correctly
 Pass expiration status checked and returned
 Audit log created for every OTP request
Security Guidelines
Never Log OTP Codes in Production: Only log in DEBUG mode
Always Mask Phone Numbers: Never expose full phone in responses
Rate Limit at Two Levels: Phone + IP prevents multiple attack vectors
Atomic Counter Operations: Use cache.incr() to prevent race conditions
Invalidate Previous OTPs: Only one valid OTP per purpose per user
Set Proper Expiration: 10 minutes is sufficient for security + UX
Log All Attempts: Audit trail helps detect fraud
Validate IP Format: Prevent header injection attacks
Use 400 Not 401 for OTP Errors: Prevents breaking mobile token refresh
Handle SMS Failures Gracefully: Mark OTP unusable if SMS fails
Common Issues & Fixes
Issue: "Too many OTP requests" immediately on first try
Check Redis is running and accessible
Check CACHES configuration in settings.py
Verify phone number format is E.164
Issue: SMS not being sent in production
Verify Twilio credentials in environment variables
Check phone number format is E.164 international
Review Twilio logs for delivery failures
Issue: OTP expires too quickly/slowly
OTP model's save() method sets expires_at to now + 10 minutes
Adjust timedelta(minutes=10) to change expiration window
Remember to update frontend timeout display to match
Issue: Rate limit seems inconsistent
Redis may not be persisting correctly
Check cache.touch() is being called to reset TTL
Review cache backend configuration
Files to Create/Modify
Create:
django-backend/accounts/services/otp_service.py - Complete OTPService class
mobile-app/src/screens/OTPVerificationScreen.tsx - OTP entry screen
Modify:
django-backend/accounts/models.py - Add OTPVerification, OTPRequestLog models
django-backend/accounts/views.py - Add 3 customer OTP endpoints, IP extractor, throttle class
django-backend/accounts/urls.py - Register OTP endpoints
django-backend/accounts/migrations/ - Create migration for OTP models
django-backend/settings.py - Ensure CACHES (Redis) configured
mobile-app/src/context/AuthContext.tsx - Add requestOTP, submitOTP functions
mobile-app/src/services/auth.ts - Ensure sendOTP, verifyOTP exported

Key Design Patterns
1. Service Layer Pattern: OTPService encapsulates all OTP logic, views are thin 2. Atomic Counter Pattern: cache.incr() for thread-safe rate limiting 3. Result Dictionary Pattern: Methods return {success, error, message} dicts 4. Audit Logging Pattern: Every action logged to OTPRequestLog 5. Development Bypass Pattern: DEBUG mode skips Twilio for testing 6. Graceful Failure Pattern: SMS failure marks OTP unusable but doesn't break flow
