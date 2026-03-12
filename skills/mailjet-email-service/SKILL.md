---
name: mailjet-email-service
description: Mailjet Email Service Implementation Skill
---

# Mailjet Email Service Implementation Skill

## Purpose

This skill provides a complete, reusable implementation for setting up transactional email notifications using Mailjet REST API v3 in a Django application. It includes:

- Core email service class with retry logic
- Pre-built email templates for common workflows (purchase confirmation, provider activation, booking notifications, etc.)
- Integration patterns for sending emails from views and business logic
- Error handling and logging strategies
- HTML + plain text email fallbacks

**User Outcome**: After following this skill, users will have:
- A production-grade email service with automatic retries
- Consistent, branded HTML email templates
- Easy integration points in Django views
- Comprehensive error handling and logging
- Support for multiple email types (purchase, activation, notifications, reports)

## When to Use This Skill

Use this skill when:
- You need transactional emails in a Django REST API application
- You want to use Mailjet for email delivery
- You need professionally designed, branded HTML email templates
- You want automatic retry logic for failed email sends
- You need to send different types of emails (confirmations, notifications, alerts)
- You want proper fallback plain text versions

## Prerequisites Checklist

Before starting, verify your project has:

- [ ] Django REST Framework configured
- [ ] Mailjet account with API credentials (API_KEY, SECRET_KEY)
- [ ] Django settings file configured for environment variables (using `decouple` or similar)
- [ ] Logging configured in Django settings
- [ ] Requests library installed (`pip install requests`)
- [ ] Email templates directory structure (optional, for template rendering)
- [ ] Models for entities you want to email about (PassPurchase, User, Booking, etc.)
- [ ] Basic understanding of Django views and models

**Time Estimate**: 2-3 hours total

## Architecture Overview

### Email Service Flow

```
Trigger event (purchase, activation, booking)
    ↓
Call MailjetEmailService method
    ↓
Build email context/content
    ↓
Render HTML template (if using templates)
    ↓
Generate plain text fallback
    ↓
Call _send_email() with retry logic
    ↓
POST to Mailjet API v3 with Basic Auth
    ↓
Handle response (success/retry/failure)
    ↓
Log results with MessageID
    ↓
Return success status to caller
```

### Core Components

- **MailjetEmailService**: Main class with methods for each email type
- **_send_email()**: Low-level method with retry logic (3 attempts)
- **_render_template()**: Renders Django templates for HTML emails
- **_build_context()**: Builds template context from model instances
- **Public methods**: send_purchase_confirmation(), send_provider_activation_email(), etc.

## Phase 1: Django Configuration

### Step 1: Add Mailjet to Requirements

```bash
pip install requests  # If not already installed
```

(Note: requests is likely already a dependency of Django or other packages)

Update `requirements.txt`:
```
requests>=2.10.0
```

### Step 2: Configure Django Settings

**File**: `django-backend/config/settings.py` (or your settings file)

Add Mailjet configuration (after other service configurations like Stripe, Twilio):

```python
# Mailjet Configuration
MAILJET_API_KEY = config('MAILJET_API_KEY', default='')
MAILJET_SECRET_KEY = config('MAILJET_SECRET_KEY', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@yourapp.com')
DEFAULT_FROM_NAME = config('DEFAULT_FROM_NAME', default='Your App Name')
```

### Step 3: Add Environment Credentials

**File**: `django-backend/.env`

```bash
# Mailjet Configuration
MAILJET_API_KEY=your_mailjet_api_key_here
MAILJET_SECRET_KEY=your_mailjet_secret_key_here
DEFAULT_FROM_EMAIL=noreply@yourapp.com
DEFAULT_FROM_NAME=Your App Name
```

Get credentials from [Mailjet Dashboard](https://app.mailjet.com/account):
1. Go to Account Settings
2. Click "API Key Management"
3. Copy API Key and Secret Key

### Step 4: Configure Logging (Optional but Recommended)

Add to LOGGING configuration in settings.py to capture email service logs:

```python
LOGGING = {
    # ... existing config ...
    'loggers': {
        # ... existing loggers ...
        'payments.services.mailjet_service': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

## Phase 2: Create Email Service

### Step 1: Create Service File

**File**: `django-backend/payments/services/mailjet_service.py` (NEW FILE)

```python
"""
Mailjet Email Service for transactional emails.
Handles confirmation emails, notifications, and alerts via Mailjet REST API v3.
"""
from django.conf import settings
import requests
import logging


logger = logging.getLogger(__name__)


class MailjetEmailService:
    """
    Email service for Mailjet REST API v3 transactional emails.
    Handles various notification types with retry logic and template rendering.

    Documentation: https://dev.mailjet.com/email/guides/send-api-v3/
    """

    def __init__(self):
        """Initialize Mailjet email service with API credentials"""
        self.api_key = settings.MAILJET_API_KEY
        self.api_secret = settings.MAILJET_SECRET_KEY
        self.api_url = 'https://api.mailjet.com/v3/send'
        self.from_email = settings.DEFAULT_FROM_EMAIL
        self.from_name = getattr(settings, 'DEFAULT_FROM_NAME', 'App Name')
        self.logger = logging.getLogger(__name__)

    def send_email(self, subject: str, to_email: str, to_name: str,
                   html_content: str, text_content: str) -> bool:
        """
        Send email via Mailjet REST API v3 with retry logic.

        Args:
            subject: Email subject
            to_email: Recipient email address
            to_name: Recipient name
            html_content: HTML email content
            text_content: Plain text email content

        Returns:
            bool: True if sent successfully, False otherwise
        """
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                # Prepare API payload according to Mailjet v3 documentation
                payload = {
                    'FromEmail': self.from_email,
                    'FromName': self.from_name,
                    'Subject': subject,
                    'Text-part': text_content,
                    'Recipients': [
                        {
                            'Email': to_email,
                            'Name': to_name
                        }
                    ]
                }

                # Add HTML part if available
                if html_content:
                    payload['Html-part'] = html_content

                # Make API request with Basic Auth
                response = requests.post(
                    self.api_url,
                    auth=(self.api_key, self.api_secret),
                    json=payload,
                    timeout=10
                )

                # Check response status - Mailjet returns 200 or 201 for success
                if response.status_code in [200, 201]:
                    # Email was sent successfully by Mailjet
                    try:
                        response_data = response.json()
                        sent_info = response_data.get('Sent', [])

                        if sent_info:
                            message_id = sent_info[0].get('MessageID')
                            message_uuid = sent_info[0].get('MessageUUID')
                            self.logger.info(
                                f"Email sent successfully via Mailjet API (attempt {retry_count + 1}/{max_retries}). "
                                f"MessageID: {message_id}, MessageUUID: {message_uuid}"
                            )
                            return True
                        else:
                            # Status 200/201 means email was sent, even if no Sent info
                            self.logger.warning(
                                f"Mailjet API returned {response.status_code} (success) but no Sent info in response. "
                                f"Email was likely sent to {to_email}"
                            )
                            return True
                    except ValueError as json_error:
                        # JSON parsing failed but status was 200/201, so email was sent
                        self.logger.warning(
                            f"Email sent successfully (status {response.status_code}) but failed to parse response JSON: {str(json_error)}. "
                            f"Email was delivered to {to_email}"
                        )
                        return True

                # Handle rate limiting gracefully
                elif response.status_code == 429:
                    self.logger.warning(
                        f"Mailjet rate limit reached for {to_email} (attempt {retry_count + 1}/{max_retries}). "
                        f"Failing gracefully."
                    )
                    # Don't retry on rate limit, fail gracefully
                    return False

                else:
                    error_message = response.text
                    self.logger.error(
                        f"Mailjet API error (Status {response.status_code}, attempt {retry_count + 1}/{max_retries}): {error_message}"
                    )
                    retry_count += 1
                    continue

            except requests.exceptions.Timeout:
                retry_count += 1
                self.logger.error(f"Mailjet API request timeout for {to_email} (attempt {retry_count}/{max_retries})")
                if retry_count >= max_retries:
                    return False
                continue

            except requests.exceptions.RequestException as e:
                retry_count += 1
                self.logger.error(
                    f"Mailjet API request failed for {to_email} (attempt {retry_count}/{max_retries}): {str(e)}"
                )
                if retry_count >= max_retries:
                    return False
                continue

            except Exception as e:
                retry_count += 1
                self.logger.error(
                    f"Failed to send email to {to_email} (attempt {retry_count}/{max_retries}): {str(e)}"
                )
                if retry_count >= max_retries:
                    return False
                continue

        # All retries exhausted
        self.logger.error(f"Failed to send email to {to_email} after {max_retries} attempts")
        return False

    def _render_template(self, template_name: str, context: dict) -> tuple:
        """
        Render HTML and text email templates.

        Args:
            template_name: Path to HTML template (e.g., 'emails/purchase_confirmation.html')
            context: Template context dictionary

        Returns:
            tuple: (html_content, text_content)
        """
        from django.template.loader import render_to_string

        # Try to render HTML template
        try:
            html_content = render_to_string(template_name, context)
        except Exception as e:
            self.logger.warning(f"Failed to render HTML template: {str(e)}")
            html_content = None

        # Generate plain text fallback
        text_content = f"""
Thank you for using our service!

If you have any questions, contact our support team.

---
© 2025 All rights reserved
        """

        return html_content, text_content
```

### Step 2: Create Service Module Init File

**File**: `django-backend/payments/services/__init__.py`

```python
from .mailjet_service import MailjetEmailService

__all__ = ['MailjetEmailService']
```

## Phase 3: Add Email Methods

Add these methods to the `MailjetEmailService` class in `mailjet_service.py`. Each method handles a specific email type:

### Purchase Confirmation Email

```python
def send_purchase_confirmation(self, user_email: str, user_name: str,
                               plan_name: str, amount: str, pass_code: str) -> bool:
    """
    Send purchase confirmation email.

    Args:
        user_email: Customer email
        user_name: Customer name
        plan_name: Name of pass/plan purchased
        amount: Amount paid
        pass_code: Unique pass code for customer

    Returns:
        bool: True if sent successfully
    """
    try:
        subject = f"Purchase Confirmation - {plan_name}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #1A4C8B 0%, #1e40af 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
                .details {{ background: white; border-left: 4px solid #00A896; padding: 15px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; font-size: 12px; color: #6b7280; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">Purchase Confirmation</h1>
                </div>
                <div class="content">
                    <h2 style="color: #1A4C8B; margin-top: 0;">Thank you, {user_name}!</h2>
                    <p>Your purchase has been confirmed. Here are your details:</p>

                    <div class="details">
                        <p><strong>Plan:</strong> {plan_name}</p>
                        <p><strong>Amount Paid:</strong> ${amount}</p>
                        <p><strong>Pass Code:</strong> {pass_code}</p>
                    </div>

                    <p>You can now start using your {plan_name}. Keep your pass code safe!</p>

                    <p style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                        <strong>Need help?</strong><br>
                        Contact our support team
                    </p>
                </div>
                <div class="footer">
                    <p>&copy; 2025 All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
Thank you for purchasing {plan_name}!

Plan: {plan_name}
Amount Paid: ${amount}
Pass Code: {pass_code}

You can now start using your {plan_name}. Keep your pass code safe!

If you have any questions, contact our support team.

---
© 2025 All rights reserved
        """

        return self.send_email(
            subject=subject,
            to_email=user_email,
            to_name=user_name,
            html_content=html_content,
            text_content=text_content
        )

    except Exception as e:
        self.logger.error(f"Failed to send purchase confirmation email: {str(e)}")
        return False
```

### Provider Activation Email

```python
def send_provider_activation_email(self, user_email: str, user_name: str,
                                   activation_link: str) -> bool:
    """
    Send provider account activation email with password setup link.

    Args:
        user_email: Provider email address
        user_name: Provider business name
        activation_link: URL to set up password and activate account

    Returns:
        bool: True if sent successfully
    """
    try:
        subject = "Welcome - Activate Your Provider Account"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #1A4C8B 0%, #1e40af 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
                .button {{ display: inline-block; background: #00A896; color: white; padding: 14px 30px; text-decoration: none; border-radius: 6px; font-weight: bold; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; font-size: 12px; color: #6b7280; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">Provider Portal</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px;">Account Created</p>
                </div>
                <div class="content">
                    <h2 style="color: #1A4C8B; margin-top: 0;">Welcome, {user_name}!</h2>
                    <p>Your provider account has been created successfully. You're one step away from accessing the Provider Portal.</p>

                    <p><strong>To activate your account:</strong></p>
                    <ol>
                        <li>Click the button below to set up your password</li>
                        <li>Create a secure password for your account</li>
                        <li>Log in to the Provider Portal</li>
                    </ol>

                    <div style="text-align: center;">
                        <a href="{activation_link}" class="button">Activate Account & Set Password</a>
                    </div>

                    <p style="margin-top: 30px; font-size: 14px; color: #6b7280;">
                        If the button doesn't work, copy and paste this link into your browser:<br>
                        <span style="word-break: break-all; color: #1A4C8B;">{activation_link}</span>
                    </p>

                    <p style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                        This activation link is valid for 3 days. If you need assistance, contact us.
                    </p>
                </div>
                <div class="footer">
                    <p>&copy; 2025 All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
Welcome to the Provider Portal, {user_name}!

Your provider account has been created successfully. To activate your account and set up your password, please visit:

{activation_link}

Once activated, you'll be able to:
- Access the Provider Portal
- Manage bookings and appointments
- Track your earnings

This activation link is valid for 3 days. If you need assistance, contact us.

Thank you for joining!

---
© 2025 All rights reserved
        """

        return self.send_email(
            subject=subject,
            to_email=user_email,
            to_name=user_name,
            html_content=html_content,
            text_content=text_content
        )

    except Exception as e:
        self.logger.error(f"Failed to send provider activation email: {str(e)}")
        return False
```

## Phase 4: Integration in Views

### Step 1: Import Email Service

**File**: `django-backend/payments/services/stripe_service.py` (or your relevant view file)

```python
from payments.services.mailjet_service import MailjetEmailService

# ... rest of imports ...
```

### Step 2: Call Email Service from Views

Add email sending after successful payment processing:

```python
def handle_successful_payment(pass_purchase):
    """Example: Send confirmation after payment success"""
    try:
        mailjet = MailjetEmailService()
        mailjet.send_purchase_confirmation(
            user_email=pass_purchase.user.email,
            user_name=pass_purchase.user.full_name,
            plan_name=pass_purchase.plan.name,
            amount=str(pass_purchase.amount_paid),
            pass_code=pass_purchase.pass_code
        )
    except Exception as e:
        logger.error(f"Failed to send confirmation email: {str(e)}")
        # Don't fail the purchase if email fails - log and continue
```

Add email sending after provider creation:

```python
def create_provider_account(user, activation_link):
    """Example: Send activation email after provider creation"""
    try:
        mailjet = MailjetEmailService()
        mailjet.send_provider_activation_email(
            user_email=user.email,
            user_name=user.full_name,
            activation_link=activation_link
        )
    except Exception as e:
        logger.error(f"Failed to send activation email: {str(e)}")
        # Don't fail account creation if email fails
```

## Testing Your Implementation

### Test 1: Verify Credentials

```bash
# Start Django shell
python manage.py shell

# Test credentials are loaded
from django.conf import settings
print(settings.MAILJET_API_KEY)
print(settings.DEFAULT_FROM_EMAIL)
```

### Test 2: Send Test Email

```bash
python manage.py shell

from payments.services import MailjetEmailService

email_service = MailjetEmailService()
result = email_service.send_email(
    subject="Test Email",
    to_email="your-test-email@example.com",
    to_name="Test User",
    html_content="<h1>This is a test</h1>",
    text_content="This is a test"
)

print(f"Email sent: {result}")
```

### Test 3: Monitor Logs

```bash
# In another terminal, monitor Django logs
tail -f logs/django.log

# Look for "Email sent successfully" messages
# Or look for error messages if email fails
```

### Test 4: Check Mailjet Dashboard

1. Go to [Mailjet Dashboard](https://app.mailjet.com/mailbox)
2. You should see your test email in the "Sent Emails" section
3. Check for delivery status, opens, clicks

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'requests'"

**Solution**:
```bash
pip install requests
pip freeze > requirements.txt
```

### Issue: "Mailjet API error (Status 400)"

**Possible causes**:
- Invalid API credentials
- Malformed JSON payload
- Invalid email address
- FromEmail doesn't match Mailjet account sender

**Solution**:
1. Verify API credentials in Mailjet dashboard
2. Check FromEmail is registered in Mailjet
3. Verify email addresses are valid
4. Check logs for exact error message

### Issue: "Mailjet rate limit reached (Status 429)"

**Cause**: Too many emails sent too quickly

**Solution**:
- Implement message queue (Celery) for batch sending
- Throttle email sending
- Contact Mailjet to increase rate limits

### Issue: Email not received

**Debug steps**:
1. Check Django logs for "Email sent successfully" message
2. Go to Mailjet dashboard - is it showing as sent?
3. Check spam folder in test email account
4. Verify recipient email is correct
5. Check Mailjet bounce reports

### Issue: "Authentication failed"

**Solution**:
```bash
python manage.py shell
from django.conf import settings
print(f"Key: {settings.MAILJET_API_KEY}")
print(f"Secret: {settings.MAILJET_SECRET_KEY}")
# Both should be non-empty
```

## Best Practices

1. **Always catch exceptions** - Email failures shouldn't break your app
2. **Log everything** - Use logger for debugging
3. **Test with real emails** - Test SMTP integration fully before deploying
4. **Use retry logic** - The service already has 3 retries built in
5. **Monitor Mailjet dashboard** - Check delivery rates and bounces
6. **Set up sender addresses** - Register sender addresses in Mailjet account
7. **Use HTML + plain text** - Provide both formats for best compatibility
8. **Test from views** - Verify email sending in actual workflow

## Common Email Types to Implement

1. **Purchase Confirmations** - After payment
2. **Activation Emails** - Account creation with reset link
3. **Booking Notifications** - Provider notification of new booking
4. **Status Updates** - Booking status changes
5. **Alerts** - Issues, problems, urgent notifications
6. **Receipts** - Transaction receipts
7. **Password Resets** - Account recovery
8. **Reminders** - Upcoming appointments, renewals

## Advanced: Using Django Templates

For more complex emails, use Django template rendering:

```python
def send_with_template(self, user_email, user_name, context):
    """Send email using Django template"""
    html_content, text_content = self._render_template(
        'emails/purchase_confirmation.html',
        context
    )

    return self.send_email(
        subject="Purchase Confirmation",
        to_email=user_email,
        to_name=user_name,
        html_content=html_content,
        text_content=text_content
    )
```

Create template file: `django-backend/templates/emails/purchase_confirmation.html`

```html
<!DOCTYPE html>
<html>
<body>
    <h1>Purchase Confirmation</h1>
    <p>Thank you, {{ user_name }}!</p>

    <p>Your purchase details:</p>
    <ul>
        <li>Plan: {{ plan_name }}</li>
        <li>Amount: ${{ amount }}</li>
        <li>Pass Code: {{ pass_code }}</li>
    </ul>

    <p>Thank you for your purchase!</p>
</body>
</html>
```

## File Structure Summary

```
django-backend/
├── config/
│   ├── settings.py          # MAILJET_API_KEY, etc.
│   └── .env                 # MAILJET_API_KEY=...
├── payments/
│   ├── services/
│   │   ├── __init__.py      # Export MailjetEmailService
│   │   ├── mailjet_service.py  # NEW - Main email service
│   │   └── stripe_service.py   # Import and use email service
│   ├── views.py             # Call email service after payment
│   └── services.py          # Call email service after pass creation
├── accounts/
│   └── views.py             # Call email service after provider activation
├── bookings/
│   └── views.py             # Call email service for booking notifications
└── templates/
    └── emails/
        ├── purchase_confirmation.html
        ├── provider_activation.html
        └── booking_notification.html
```

## Support & Resources

- [Mailjet API Documentation](https://dev.mailjet.com/email/guides/send-api-v3/)
- [Mailjet REST API v3 Reference](https://app.mailjet.com/docs/api/send/post)
- [Mailjet Python SDK](https://github.com/mailjet/mailjet-apiv3-python) (Alternative)
- [Django Email Documentation](https://docs.djangoproject.com/en/stable/topics/email/)
- [Mailjet Dashboard](https://app.mailjet.com/)
