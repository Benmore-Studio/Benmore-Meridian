---
name: stripe-processing
description: Stripe processing skill for onetime payment and subscription with email notification.
license: Stripe
---

## Overview
Core Stripe payment integration in Python supporting one-time payments and subscriptions with webhook handling and email notifications.

## Use Cases
- Accept one-time payments
- Create subscription-based billing
- Handle payment webhooks
- Send payment confirmation emails
- Manage payment lifecycle

---

## Phase 1: Setup & Configuration

### 1.1 Install Dependencies
```bash
pip install stripe python-decouple
```

### 1.2 Environment Variables
```env
# .env
STRIPE_SECRET_KEY=sk_test_51...
STRIPE_PUBLISHABLE_KEY=pk_test_51...
STRIPE_WEBHOOK_SECRET=whsec_...

# Email settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@yourcompany.com
```

### 1.3 Django Settings (if using Django)
```python
# settings.py
from decouple import config

STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET')

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool)
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')
```

---

## Phase 2: Stripe Service Layer

### 2.1 Payment Service
```python
# services/stripe_service.py
import stripe
from decimal import Decimal
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class StripePaymentService:
    """
    Core Stripe payment service for one-time payments and subscriptions.
    """

    def __init__(self, api_key: str):
        stripe.api_key = api_key
        self.stripe = stripe

    # ============= ONE-TIME PAYMENTS =============

    def create_payment_intent(
        self,
        amount: Decimal,
        currency: str = 'usd',
        customer_email: Optional[str] = None,
        metadata: Optional[Dict] = None,
        description: Optional[str] = None,
    ) -> Dict:
        """
        Create a payment intent for one-time payment.

        Args:
            amount: Amount in dollars (will be converted to cents)
            currency: Currency code (default: 'usd')
            customer_email: Customer's email for receipt
            metadata: Additional metadata (max 50 keys)
            description: Payment description

        Returns:
            dict: {
                'payment_intent_id': 'pi_...',
                'client_secret': 'pi_..._secret_...',
                'amount': 2500,
                'status': 'requires_payment_method'
            }

        Raises:
            stripe.error.StripeError: If payment intent creation fails
        """
        try:
            amount_in_cents = int(amount * 100)

            intent = self.stripe.PaymentIntent.create(
                amount=amount_in_cents,
                currency=currency,
                metadata=metadata or {},
                description=description,
                receipt_email=customer_email,
                automatic_payment_methods={'enabled': True},
            )

            logger.info(f"Payment intent created: {intent.id}")

            return {
                'payment_intent_id': intent.id,
                'client_secret': intent.client_secret,
                'amount': intent.amount,
                'status': intent.status,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            raise

    def retrieve_payment_intent(self, payment_intent_id: str) -> Dict:
        """
        Retrieve payment intent details.

        Args:
            payment_intent_id: Payment intent ID

        Returns:
            dict: Payment intent data
        """
        try:
            intent = self.stripe.PaymentIntent.retrieve(payment_intent_id)
            return {
                'id': intent.id,
                'amount': intent.amount,
                'currency': intent.currency,
                'status': intent.status,
                'customer_email': intent.receipt_email,
                'metadata': intent.metadata,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving payment intent: {str(e)}")
            raise

    def cancel_payment_intent(self, payment_intent_id: str) -> Dict:
        """
        Cancel a payment intent.

        Args:
            payment_intent_id: Payment intent ID

        Returns:
            dict: Cancelled payment intent data
        """
        try:
            intent = self.stripe.PaymentIntent.cancel(payment_intent_id)
            logger.info(f"Payment intent cancelled: {intent.id}")
            return {'id': intent.id, 'status': intent.status}
        except stripe.error.StripeError as e:
            logger.error(f"Error cancelling payment intent: {str(e)}")
            raise

    # ============= SUBSCRIPTIONS =============

    def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        Create a Stripe customer for subscriptions.

        Args:
            email: Customer email
            name: Customer name
            metadata: Additional metadata

        Returns:
            dict: {
                'customer_id': 'cus_...',
                'email': 'customer@example.com',
                'name': 'John Doe'
            }
        """
        try:
            customer = self.stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {},
            )

            logger.info(f"Customer created: {customer.id}")

            return {
                'customer_id': customer.id,
                'email': customer.email,
                'name': customer.name,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error creating customer: {str(e)}")
            raise

    def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        metadata: Optional[Dict] = None,
        trial_period_days: Optional[int] = None,
    ) -> Dict:
        """
        Create a subscription for a customer.

        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID (e.g., 'price_...')
            metadata: Additional metadata
            trial_period_days: Number of trial days (optional)

        Returns:
            dict: {
                'subscription_id': 'sub_...',
                'client_secret': 'seti_..._secret_...',
                'status': 'active',
                'current_period_end': 1234567890
            }
        """
        try:
            subscription_params = {
                'customer': customer_id,
                'items': [{'price': price_id}],
                'metadata': metadata or {},
                'payment_behavior': 'default_incomplete',
                'payment_settings': {
                    'save_default_payment_method': 'on_subscription'
                },
                'expand': ['latest_invoice.payment_intent'],
            }

            if trial_period_days:
                subscription_params['trial_period_days'] = trial_period_days

            subscription = self.stripe.Subscription.create(**subscription_params)

            logger.info(f"Subscription created: {subscription.id}")

            return {
                'subscription_id': subscription.id,
                'client_secret': subscription.latest_invoice.payment_intent.client_secret,
                'status': subscription.status,
                'current_period_end': subscription.current_period_end,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error creating subscription: {str(e)}")
            raise

    def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = True
    ) -> Dict:
        """
        Cancel a subscription.

        Args:
            subscription_id: Subscription ID
            at_period_end: If True, cancel at end of billing period

        Returns:
            dict: Cancelled subscription data
        """
        try:
            if at_period_end:
                subscription = self.stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                subscription = self.stripe.Subscription.delete(subscription_id)

            logger.info(f"Subscription cancelled: {subscription_id}")

            return {
                'subscription_id': subscription.id,
                'status': subscription.status,
                'cancel_at_period_end': subscription.cancel_at_period_end,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error cancelling subscription: {str(e)}")
            raise

    def retrieve_subscription(self, subscription_id: str) -> Dict:
        """
        Retrieve subscription details.

        Args:
            subscription_id: Subscription ID

        Returns:
            dict: Subscription data
        """
        try:
            subscription = self.stripe.Subscription.retrieve(subscription_id)
            return {
                'id': subscription.id,
                'customer': subscription.customer,
                'status': subscription.status,
                'current_period_start': subscription.current_period_start,
                'current_period_end': subscription.current_period_end,
                'cancel_at_period_end': subscription.cancel_at_period_end,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving subscription: {str(e)}")
            raise

    # ============= WEBHOOKS =============

    def verify_webhook_signature(
        self,
        payload: bytes,
        sig_header: str,
        webhook_secret: str
    ) -> Dict:
        """
        Verify webhook signature and construct event.

        Args:
            payload: Raw request body as bytes
            sig_header: Stripe-Signature header value
            webhook_secret: Webhook signing secret

        Returns:
            dict: Stripe event object

        Raises:
            stripe.error.SignatureVerificationError: If signature invalid
        """
        try:
            event = self.stripe.Webhook.construct_event(
                payload,
                sig_header,
                webhook_secret
            )
            logger.info(f"Webhook verified: {event['type']}")
            return event

        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {str(e)}")
            raise

    def handle_webhook_event(self, event: Dict) -> None:
        """
        Route webhook events to appropriate handlers.

        Args:
            event: Stripe event object
        """
        event_type = event['type']
        event_data = event['data']['object']

        handlers = {
            'payment_intent.succeeded': self._handle_payment_succeeded,
            'payment_intent.payment_failed': self._handle_payment_failed,
            'customer.subscription.created': self._handle_subscription_created,
            'customer.subscription.updated': self._handle_subscription_updated,
            'customer.subscription.deleted': self._handle_subscription_deleted,
            'invoice.payment_succeeded': self._handle_invoice_paid,
            'invoice.payment_failed': self._handle_invoice_failed,
        }

        handler = handlers.get(event_type)
        if handler:
            handler(event_data)
        else:
            logger.info(f"Unhandled webhook event: {event_type}")

    # ============= WEBHOOK HANDLERS =============

    def _handle_payment_succeeded(self, payment_intent: Dict) -> None:
        """Handle successful payment intent."""
        payment_intent_id = payment_intent['id']
        amount = Decimal(payment_intent['amount']) / 100
        customer_email = payment_intent.get('receipt_email')
        metadata = payment_intent.get('metadata', {})

        logger.info(f"Payment succeeded: {payment_intent_id}, Amount: ${amount}")

        # TODO: Update your database
        # Example: Mark transaction as paid, fulfill order, etc.

        # Send confirmation email
        if customer_email:
            from .email_service import send_payment_confirmation_email
            send_payment_confirmation_email(
                email=customer_email,
                amount=amount,
                payment_id=payment_intent_id,
                metadata=metadata
            )

    def _handle_payment_failed(self, payment_intent: Dict) -> None:
        """Handle failed payment intent."""
        payment_intent_id = payment_intent['id']
        logger.warning(f"Payment failed: {payment_intent_id}")

        # TODO: Update your database
        # Example: Mark transaction as failed, notify customer, etc.

    def _handle_subscription_created(self, subscription: Dict) -> None:
        """Handle new subscription creation."""
        subscription_id = subscription['id']
        customer_id = subscription['customer']
        logger.info(f"Subscription created: {subscription_id} for customer {customer_id}")

        # TODO: Update your database
        # Example: Store subscription details, activate features, etc.

    def _handle_subscription_updated(self, subscription: Dict) -> None:
        """Handle subscription updates."""
        subscription_id = subscription['id']
        status = subscription['status']
        logger.info(f"Subscription updated: {subscription_id}, Status: {status}")

        # TODO: Update your database
        # Example: Update subscription status, adjust features, etc.

    def _handle_subscription_deleted(self, subscription: Dict) -> None:
        """Handle subscription cancellation."""
        subscription_id = subscription['id']
        logger.info(f"Subscription deleted: {subscription_id}")

        # TODO: Update your database
        # Example: Deactivate features, archive data, etc.

    def _handle_invoice_paid(self, invoice: Dict) -> None:
        """Handle successful invoice payment."""
        invoice_id = invoice['id']
        subscription_id = invoice.get('subscription')
        customer_email = invoice.get('customer_email')
        amount_paid = Decimal(invoice['amount_paid']) / 100

        logger.info(f"Invoice paid: {invoice_id}, Amount: ${amount_paid}")

        # Send subscription confirmation email
        if customer_email:
            from .email_service import send_subscription_confirmation_email
            send_subscription_confirmation_email(
                email=customer_email,
                amount=amount_paid,
                invoice_id=invoice_id,
                subscription_id=subscription_id
            )

    def _handle_invoice_failed(self, invoice: Dict) -> None:
        """Handle failed invoice payment."""
        invoice_id = invoice['id']
        subscription_id = invoice.get('subscription')
        logger.warning(f"Invoice payment failed: {invoice_id}")

        # TODO: Handle failed payment
        # Example: Notify customer, retry payment, suspend subscription, etc.

    # ============= REFUNDS =============

    def create_refund(
        self,
        payment_intent_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None
    ) -> Dict:
        """
        Create a refund for a payment.

        Args:
            payment_intent_id: Payment intent ID
            amount: Amount to refund in dollars (None for full refund)
            reason: Refund reason ('duplicate', 'fraudulent', 'requested_by_customer')

        Returns:
            dict: Refund data
        """
        try:
            refund_params = {'payment_intent': payment_intent_id}

            if amount:
                refund_params['amount'] = int(amount * 100)

            if reason:
                refund_params['reason'] = reason

            refund = self.stripe.Refund.create(**refund_params)

            logger.info(f"Refund created: {refund.id} for {payment_intent_id}")

            return {
                'refund_id': refund.id,
                'amount': Decimal(refund.amount) / 100,
                'status': refund.status,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error creating refund: {str(e)}")
            raise
```

---

## Phase 3: Email Notification Service

### 3.1 Email Service
```python
# services/email_service.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from decimal import Decimal
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


def send_payment_confirmation_email(
    email: str,
    amount: Decimal,
    payment_id: str,
    metadata: Optional[Dict] = None
) -> None:
    """
    Send payment confirmation email for one-time payments.

    Args:
        email: Customer email
        amount: Payment amount
        payment_id: Stripe payment intent ID
        metadata: Additional payment metadata
    """
    try:
        subject = 'Payment Confirmation'
        from_email = settings.DEFAULT_FROM_EMAIL

        context = {
            'amount': amount,
            'payment_id': payment_id,
            'metadata': metadata or {},
        }

        html_content = render_to_string('emails/payment_confirmation.html', context)
        text_content = f"Your payment of ${amount} has been successfully processed. Payment ID: {payment_id}"

        email_message = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[email],
        )

        email_message.attach_alternative(html_content, "text/html")
        email_message.send()

        logger.info(f"Payment confirmation email sent to {email}")

    except Exception as e:
        logger.error(f"Failed to send payment confirmation email: {str(e)}")


def send_subscription_confirmation_email(
    email: str,
    amount: Decimal,
    invoice_id: str,
    subscription_id: Optional[str] = None
) -> None:
    """
    Send subscription confirmation email.

    Args:
        email: Customer email
        amount: Subscription amount
        invoice_id: Stripe invoice ID
        subscription_id: Stripe subscription ID
    """
    try:
        subject = 'Subscription Confirmation'
        from_email = settings.DEFAULT_FROM_EMAIL

        context = {
            'amount': amount,
            'invoice_id': invoice_id,
            'subscription_id': subscription_id,
        }

        html_content = render_to_string('emails/subscription_confirmation.html', context)
        text_content = f"Your subscription payment of ${amount} has been processed. Invoice ID: {invoice_id}"

        email_message = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[email],
        )

        email_message.attach_alternative(html_content, "text/html")
        email_message.send()

        logger.info(f"Subscription confirmation email sent to {email}")

    except Exception as e:
        logger.error(f"Failed to send subscription confirmation email: {str(e)}")
```

### 3.2 Payment Confirmation Email Template
```html
<!-- templates/emails/payment_confirmation.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Payment Confirmation</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        .container {
            background-color: #f9f9f9;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            padding-bottom: 20px;
            border-bottom: 2px solid #4F46E5;
        }
        .header h1 {
            color: #4F46E5;
            margin: 0;
        }
        .content {
            padding: 20px 0;
        }
        .success-icon {
            text-align: center;
            font-size: 48px;
            color: #10B981;
            margin: 20px 0;
        }
        .amount {
            font-size: 36px;
            font-weight: bold;
            text-align: center;
            color: #4F46E5;
            margin: 20px 0;
        }
        .details {
            background-color: #fff;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .details-row {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #e5e7eb;
        }
        .details-row:last-child {
            border-bottom: none;
        }
        .label {
            font-weight: bold;
            color: #6B7280;
        }
        .value {
            color: #111827;
        }
        .footer {
            text-align: center;
            padding-top: 20px;
            border-top: 2px solid #e5e7eb;
            color: #6B7280;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Payment Successful</h1>
        </div>

        <div class="content">
            <div class="success-icon">✓</div>

            <p style="text-align: center; font-size: 18px;">
                Thank you! Your payment has been processed successfully.
            </p>

            <div class="amount">${{ amount }}</div>

            <div class="details">
                <div class="details-row">
                    <span class="label">Payment ID:</span>
                    <span class="value">{{ payment_id }}</span>
                </div>
                <div class="details-row">
                    <span class="label">Amount:</span>
                    <span class="value">${{ amount }}</span>
                </div>
                <div class="details-row">
                    <span class="label">Status:</span>
                    <span class="value" style="color: #10B981;">Completed</span>
                </div>
            </div>

            {% if metadata %}
            <div class="details">
                <h3 style="margin-top: 0;">Additional Details</h3>
                {% for key, value in metadata.items %}
                <div class="details-row">
                    <span class="label">{{ key|title }}:</span>
                    <span class="value">{{ value }}</span>
                </div>
                {% endfor %}
            </div>
            {% endif %}
        </div>

        <div class="footer">
            <p>If you have any questions, please contact our support team.</p>
            <p>support@yourcompany.com</p>
        </div>
    </div>
</body>
</html>
```

### 3.3 Subscription Confirmation Email Template
```html
<!-- templates/emails/subscription_confirmation.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Subscription Confirmation</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        .container {
            background-color: #f9f9f9;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            padding-bottom: 20px;
            border-bottom: 2px solid #8B5CF6;
        }
        .header h1 {
            color: #8B5CF6;
            margin: 0;
        }
        .content {
            padding: 20px 0;
        }
        .success-icon {
            text-align: center;
            font-size: 48px;
            color: #10B981;
            margin: 20px 0;
        }
        .amount {
            font-size: 36px;
            font-weight: bold;
            text-align: center;
            color: #8B5CF6;
            margin: 20px 0;
        }
        .subscription-badge {
            background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
            color: white;
            padding: 10px 20px;
            border-radius: 20px;
            text-align: center;
            font-weight: bold;
            margin: 20px 0;
        }
        .details {
            background-color: #fff;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .details-row {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #e5e7eb;
        }
        .details-row:last-child {
            border-bottom: none;
        }
        .label {
            font-weight: bold;
            color: #6B7280;
        }
        .value {
            color: #111827;
        }
        .benefits {
            background-color: #F3F4F6;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .benefits ul {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        .benefits li {
            padding: 8px 0;
            padding-left: 30px;
            position: relative;
        }
        .benefits li:before {
            content: "✓";
            position: absolute;
            left: 0;
            color: #10B981;
            font-weight: bold;
            font-size: 18px;
        }
        .footer {
            text-align: center;
            padding-top: 20px;
            border-top: 2px solid #e5e7eb;
            color: #6B7280;
            font-size: 14px;
        }
        .button {
            display: inline-block;
            padding: 12px 30px;
            background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
            color: white;
            text-decoration: none;
            border-radius: 6px;
            margin: 20px 0;
            font-weight: bold;
        }
        .button:hover {
            opacity: 0.9;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Subscription Active</h1>
        </div>

        <div class="content">
            <div class="success-icon">🎉</div>

            <div class="subscription-badge">
                PREMIUM SUBSCRIPTION
            </div>

            <p style="text-align: center; font-size: 18px;">
                Welcome! Your subscription is now active and ready to use.
            </p>

            <div class="amount">${{ amount }}/month</div>

            <div class="details">
                <div class="details-row">
                    <span class="label">Subscription ID:</span>
                    <span class="value">{{ subscription_id }}</span>
                </div>
                <div class="details-row">
                    <span class="label">Invoice ID:</span>
                    <span class="value">{{ invoice_id }}</span>
                </div>
                <div class="details-row">
                    <span class="label">Amount:</span>
                    <span class="value">${{ amount }}</span>
                </div>
                <div class="details-row">
                    <span class="label">Status:</span>
                    <span class="value" style="color: #10B981;">Active</span>
                </div>
                <div class="details-row">
                    <span class="label">Billing Cycle:</span>
                    <span class="value">Monthly</span>
                </div>
            </div>

            <div class="benefits">
                <h3 style="margin-top: 0; color: #8B5CF6;">Your Subscription Benefits:</h3>
                <ul>
                    <li>Full access to all premium features</li>
                    <li>Priority customer support</li>
                    <li>Exclusive content and updates</li>
                    <li>Cancel anytime, no questions asked</li>
                </ul>
            </div>

            <div style="text-align: center;">
                <a href="#" class="button">Manage Subscription</a>
            </div>
        </div>

        <div class="footer">
            <p><strong>Need help?</strong> Contact our support team anytime.</p>
            <p>support@yourcompany.com</p>
            <p style="font-size: 12px; color: #9CA3AF; margin-top: 20px;">
                You can cancel your subscription at any time from your account settings.
                Your card will be charged ${{ amount }} automatically every month.
            </p>
        </div>
    </div>
</body>
</html>
```

---

## Phase 4: API Implementation Examples

### 4.1 Flask Example
```python
# app.py (Flask)
from flask import Flask, request, jsonify
from services.stripe_service import StripePaymentService
from decouple import config

app = Flask(__name__)
stripe_service = StripePaymentService(config('STRIPE_SECRET_KEY'))


@app.route('/create-payment-intent', methods=['POST'])
def create_payment_intent():
    """Create payment intent for one-time payment."""
    try:
        data = request.json
        amount = data.get('amount')
        email = data.get('email')
        metadata = data.get('metadata', {})

        result = stripe_service.create_payment_intent(
            amount=amount,
            customer_email=email,
            metadata=metadata
        )

        return jsonify({
            'success': True,
            'clientSecret': result['client_secret'],
            'paymentIntentId': result['payment_intent_id']
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/create-subscription', methods=['POST'])
def create_subscription():
    """Create subscription for customer."""
    try:
        data = request.json
        email = data.get('email')
        name = data.get('name')
        price_id = data.get('priceId')

        # Create customer
        customer = stripe_service.create_customer(email=email, name=name)

        # Create subscription
        subscription = stripe_service.create_subscription(
            customer_id=customer['customer_id'],
            price_id=price_id
        )

        return jsonify({
            'success': True,
            'clientSecret': subscription['client_secret'],
            'subscriptionId': subscription['subscription_id']
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks."""
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe_service.verify_webhook_signature(
            payload=payload,
            sig_header=sig_header,
            webhook_secret=config('STRIPE_WEBHOOK_SECRET')
        )

        # Handle event
        stripe_service.handle_webhook_event(event)

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True)
```

### 4.2 Django Example
```python
# views.py (Django)
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings
from services.stripe_service import StripePaymentService
from decimal import Decimal

stripe_service = StripePaymentService(settings.STRIPE_SECRET_KEY)


@api_view(['POST'])
def create_payment_intent(request):
    """Create payment intent for one-time payment."""
    try:
        amount = Decimal(request.data.get('amount'))
        email = request.data.get('email')
        metadata = request.data.get('metadata', {})

        result = stripe_service.create_payment_intent(
            amount=amount,
            customer_email=email,
            metadata=metadata
        )

        return Response({
            'success': True,
            'clientSecret': result['client_secret'],
            'paymentIntentId': result['payment_intent_id']
        })

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def create_subscription(request):
    """Create subscription for customer."""
    try:
        email = request.data.get('email')
        name = request.data.get('name')
        price_id = request.data.get('priceId')

        # Create customer
        customer = stripe_service.create_customer(email=email, name=name)

        # Create subscription
        subscription = stripe_service.create_subscription(
            customer_id=customer['customer_id'],
            price_id=price_id
        )

        return Response({
            'success': True,
            'clientSecret': subscription['client_secret'],
            'subscriptionId': subscription['subscription_id']
        })

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['POST'])
def stripe_webhook(request):
    """Handle Stripe webhooks."""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe_service.verify_webhook_signature(
            payload=payload,
            sig_header=sig_header,
            webhook_secret=settings.STRIPE_WEBHOOK_SECRET
        )

        # Handle event
        stripe_service.handle_webhook_event(event)

        return HttpResponse(status=200)

    except Exception as e:
        return HttpResponse(status=400)
```

---

## Phase 5: Testing & Deployment

### 5.1 Local Testing with Stripe CLI
```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login
stripe login

# Forward webhooks to local server
stripe listen --forward-to localhost:5000/webhook

# Test webhook events
stripe trigger payment_intent.succeeded
stripe trigger customer.subscription.created
```

### 5.2 Test Cards
```
# Successful payment
4242 4242 4242 4242

# Payment requires authentication
4000 0025 0000 3155

# Payment declined
4000 0000 0000 9995
```

### 5.3 Production Checklist
- [ ] Replace test keys with live keys
- [ ] Configure production webhook URL
- [ ] Enable HTTPS for webhook endpoint
- [ ] Set up error monitoring (Sentry)
- [ ] Configure email service for production
- [ ] Add rate limiting to endpoints
- [ ] Set up database backups
- [ ] Test webhook signature verification
- [ ] Document API endpoints
- [ ] Set up logging and monitoring

---

## Usage Examples

### One-Time Payment
```python
from services.stripe_service import StripePaymentService
from decimal import Decimal

service = StripePaymentService(api_key='sk_test_...')

# Create payment intent
result = service.create_payment_intent(
    amount=Decimal('29.99'),
    customer_email='customer@example.com',
    metadata={'product_id': '123'},
    description='Product purchase'
)

# Get client secret for frontend
client_secret = result['client_secret']
```

### Subscription
```python
# Create customer
customer = service.create_customer(
    email='customer@example.com',
    name='John Doe'
)

# Create subscription
subscription = service.create_subscription(
    customer_id=customer['customer_id'],
    price_id='price_1234567890',
    trial_period_days=14
)

# Get client secret for frontend
client_secret = subscription['client_secret']
```

### Process Refund
```python
# Full refund
refund = service.create_refund(
    payment_intent_id='pi_...',
    reason='requested_by_customer'
)

# Partial refund
refund = service.create_refund(
    payment_intent_id='pi_...',
    amount=Decimal('10.00')
)
```

---

## Common Issues & Solutions

### Issue 1: Webhook Signature Verification Failed
**Solution**: Use raw request body (bytes), not parsed JSON. Ensure webhook secret is correct.

### Issue 2: Amount Mismatch
**Solution**: Always convert dollars to cents: `int(amount * 100)`

### Issue 3: Email Not Sending
**Solution**: Check email backend configuration and SMTP credentials.

### Issue 4: Customer Already Exists
**Solution**: Check if customer exists before creating, or use `email` to search.

---

## Security Best Practices

1. **Never expose secret key** in frontend code
2. **Always verify webhook signatures** before processing
3. **Use HTTPS** for all webhook endpoints
4. **Store sensitive data securely** (use environment variables)
5. **Implement rate limiting** on payment endpoints
6. **Log all payment activities** for audit trail
7. **Validate input** before creating payment intents
8. **Handle errors gracefully** without exposing sensitive info

---

## Resources

- **Stripe Documentation**: https://stripe.com/docs
- **Test Cards**: https://stripe.com/docs/testing
- **Webhook Events**: https://stripe.com/docs/api/events/types
- **Python SDK**: https://stripe.com/docs/api/python

---

**Last Updated**: January 2025
**Version**: 1.0.0
**Focus**: Core Stripe Integration (Payments + Subscriptions)
