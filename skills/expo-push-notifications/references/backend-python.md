# Backend: Python + exponent_server_sdk

## Installation

```bash
uv add exponent_server_sdk
```

Package name on PyPI is `exponent_server_sdk` (underscores, not hyphens).

## SDK API Reference

### Imports

```python
from exponent_server_sdk import (
    DeviceNotRegisteredError,
    InvalidCredentialsError,
    MessageRateExceededError,
    MessageTooBigError,
    PushClient,
    PushMessage,
    PushServerError,
    PushTicketError,
)
```

### Exception Hierarchy

```
PushServerError          — server-level formatting/validation error
PushTicketError          — per-notification error (base class)
├── DeviceNotRegisteredError
├── MessageTooBigError
├── MessageRateExceededError
└── InvalidCredentialsError
```

### PushClient

```python
client = PushClient()
# Optional: custom session with access token
session = requests.Session()
session.headers.update({"Authorization": f"Bearer {access_token}"})
client = PushClient(session=session)

# Constructor params: host, api_url, session, force_fcm_v1
```

**Methods:**
- `PushClient.is_exponent_push_token(token: str) -> bool` — classmethod, validates token format
- `client.publish(push_message) -> PushTicket` — send single message
- `client.publish_multiple(push_messages) -> list[PushTicket]` — send batch, auto-chunks into groups of 100
- `client.check_receipts(push_tickets) -> list[PushReceipt]` — check delivery status
- `client.check_receipts_multiple(push_tickets) -> list[PushReceipt]` — batch receipt check, auto-chunks into groups of 1000

### PushMessage

```python
PushMessage(
    to="ExponentPushToken[xxx]",  # required
    body="Message text",           # required
    title="Title",
    data={"key": "value"},
    sound="default",
    ttl=None,                      # seconds before Expo stops trying to deliver
    expiration=None,               # UNIX timestamp when message expires
    priority="default",            # "default" | "normal" | "high"
    badge=1,                       # iOS badge count
    channel_id="default",          # Android notification channel
    category=None,                 # notification category for actions
    subtitle=None,                 # iOS subtitle
    mutable_content=None,          # iOS mutable-content flag
    display_in_foreground=None,    # deprecated, use notification handler on client
)
```

### PushTicket (returned by publish)

```python
ticket = client.publish(message)
ticket.status          # "ok" | "error"
ticket.id              # ticket ID string (for receipt polling)
ticket.message         # error message if status == "error"
ticket.details         # error details dict
ticket.is_success()    # True if status == "ok"
ticket.validate_response()  # raises DeviceNotRegisteredError, MessageTooBigError, etc.
```

### PushReceipt (returned by check_receipts)

```python
receipts = client.check_receipts(tickets)
for receipt in receipts:
    receipt.status     # "ok" | "error"
    receipt.id         # receipt ID
    receipt.message    # error message
    receipt.details    # {"error": "DeviceNotRegistered"} etc.
    receipt.is_success()
    receipt.validate_response()  # raises exceptions on error
```

---

## Push Utility Module

```python
# push.py
import logging
from typing import Any, Dict, List, Optional

from exponent_server_sdk import (
    DeviceNotRegisteredError,
    MessageRateExceededError,
    MessageTooBigError,
    PushClient,
    PushMessage,
    PushServerError,
    PushTicketError,
)

logger = logging.getLogger(__name__)
_client: Optional[PushClient] = None


def get_push_client() -> PushClient:
    global _client
    if _client is None:
        _client = PushClient()
    return _client


def send_push(
    token: str,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    badge: Optional[int] = None,
    sound: str = "default",
    channel_id: str = "default",
    priority: str = "default",
    ttl: Optional[int] = None,
    subtitle: Optional[str] = None,
) -> Dict[str, Any]:
    """Send a single push notification. Returns {"success", "ticket_id"|"error_code", "token"}."""
    if not PushClient.is_exponent_push_token(token):
        return {"success": False, "error_code": "INVALID_TOKEN", "token": token}
    try:
        ticket = get_push_client().publish(PushMessage(
            to=token, title=title, body=body, data=data,
            sound=sound, badge=badge, channel_id=channel_id,
            priority="high" if priority == "high" else "default",
            ttl=ttl, subtitle=subtitle,
        ))
        ticket.validate_response()
        return {"success": True, "ticket_id": ticket.id, "token": token}
    except DeviceNotRegisteredError:
        return {"success": False, "error_code": "DEVICE_NOT_REGISTERED", "token": token}
    except MessageTooBigError:
        return {"success": False, "error_code": "MESSAGE_TOO_BIG", "token": token}
    except MessageRateExceededError:
        return {"success": False, "error_code": "RATE_EXCEEDED", "token": token, "retryable": True}
    except PushServerError as exc:
        return {"success": False, "error_code": "SERVER_ERROR", "token": token, "retryable": True}
    except PushTicketError as exc:
        return {"success": False, "error_code": "TICKET_ERROR", "token": token}
    except Exception as exc:
        logger.exception("Expo push error")
        return {"success": False, "error_code": "UNKNOWN", "token": token}


def send_push_batch(
    tokens: List[str],
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    badge: Optional[int] = None,
    sound: str = "default",
    channel_id: str = "default",
    priority: str = "default",
) -> Dict[str, Any]:
    """Send to multiple devices. SDK auto-chunks into batches of 100."""
    if not tokens:
        return {"success_count": 0, "failure_count": 0, "results": [], "ticket_ids": []}

    valid = [t for t in tokens if PushClient.is_exponent_push_token(t)]
    invalid = [t for t in tokens if not PushClient.is_exponent_push_token(t)]

    try:
        messages = [
            PushMessage(
                to=t, title=title, body=body, data=data,
                sound=sound, badge=badge, channel_id=channel_id,
                priority="high" if priority == "high" else "default",
            ) for t in valid
        ]
        # publish_multiple auto-chunks into batches of DEFAULT_MAX_MESSAGE_COUNT (100)
        tickets = get_push_client().publish_multiple(messages)

        results, ticket_ids = [], []
        success_count = failure_count = 0
        for idx, ticket in enumerate(tickets):
            try:
                ticket.validate_response()
                ticket_ids.append(ticket.id)
                results.append({"token": valid[idx], "success": True, "ticket_id": ticket.id})
                success_count += 1
            except DeviceNotRegisteredError:
                results.append({"token": valid[idx], "success": False, "error": "DEVICE_NOT_REGISTERED"})
                failure_count += 1
            except PushTicketError as exc:
                results.append({"token": valid[idx], "success": False, "error": str(exc)})
                failure_count += 1

        for t in invalid:
            results.append({"token": t, "success": False, "error": "INVALID_TOKEN"})
            failure_count += 1

        return {"success_count": success_count, "failure_count": failure_count,
                "results": results, "ticket_ids": ticket_ids}
    except PushServerError as exc:
        logger.exception("Expo batch failed: %s", exc)
        return {"success_count": 0, "failure_count": len(tokens),
                "results": [{"token": t, "success": False, "error": str(exc)} for t in tokens],
                "ticket_ids": []}


def check_receipts(tickets: list) -> List[Dict]:
    """
    Poll Expo for delivery receipts. Call 15+ min after sending.
    Pass the PushTicket objects returned by publish/publish_multiple.
    """
    if not tickets:
        return []
    try:
        # check_receipts_multiple auto-chunks into batches of 1000
        receipts = get_push_client().check_receipts_multiple(tickets)
        results = []
        for receipt in receipts:
            if receipt.is_success():
                results.append({"id": receipt.id, "status": "delivered"})
            else:
                error_code = receipt.details.get("error", "UNKNOWN") if receipt.details else "UNKNOWN"
                results.append({
                    "id": receipt.id,
                    "status": "error",
                    "error_code": error_code,
                    "message": receipt.message or "",
                })
        return results
    except Exception:
        logger.exception("Receipt check failed")
        return []
```

---

## Django Integration

### UserDevice Model

```python
import uuid
from django.conf import settings
from django.db import models

class UserDevice(models.Model):
    PLATFORM_CHOICES = [('ios', 'iOS'), ('android', 'Android')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='devices')
    expo_push_token = models.CharField(max_length=255, unique=True, db_index=True)
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES)
    device_model = models.CharField(max_length=100, blank=True, default='')
    app_version = models.CharField(max_length=20, blank=True, default='')
    os_version = models.CharField(max_length=20, blank=True, default='')
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_devices'
        indexes = [models.Index(fields=['user', 'is_active'])]
        ordering = ['-last_used_at']
```

### Device Registration Endpoint (DRF)

```python
# serializers.py
from exponent_server_sdk import PushClient
from rest_framework import serializers

class DeviceRegisterSerializer(serializers.Serializer):
    expo_push_token = serializers.CharField(max_length=255)
    platform = serializers.ChoiceField(choices=['ios', 'android'])
    device_model = serializers.CharField(max_length=100, required=False, default='')
    app_version = serializers.CharField(max_length=20, required=False, default='')
    os_version = serializers.CharField(max_length=20, required=False, default='')

    def validate_expo_push_token(self, value):
        value = value.strip()
        if not PushClient.is_exponent_push_token(value):
            raise serializers.ValidationError("Invalid Expo Push Token format.")
        return value
```

```python
# views.py
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

class DeviceRegisterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DeviceRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Upsert — handles device transfer between users
        existing = UserDevice.objects.filter(expo_push_token=data['expo_push_token']).first()
        if existing:
            existing.user = request.user
            existing.platform = data['platform']
            existing.device_model = data.get('device_model', '')
            existing.app_version = data.get('app_version', '')
            existing.os_version = data.get('os_version', '')
            existing.is_active = True
            existing.save()
            device = existing
        else:
            device = UserDevice.objects.create(user=request.user, **data)

        return Response({"id": str(device.id), "token": device.expo_push_token},
                        status=status.HTTP_201_CREATED)


class DeviceUnregisterView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, token):
        try:
            device = UserDevice.objects.get(user=request.user, expo_push_token=token)
        except UserDevice.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        device.is_active = False
        device.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
```

```python
# urls.py
from django.urls import path

urlpatterns = [
    path('devices/register/', DeviceRegisterView.as_view(), name='device-register'),
    path('devices/<str:token>/', DeviceUnregisterView.as_view(), name='device-unregister'),
]
```

### Celery Async Delivery Task

```python
from celery import shared_task

@shared_task(bind=True, max_retries=3, acks_late=True)
def deliver_push(self, token: str, title: str, body: str, data: dict = None, badge: int = None):
    from .push import send_push

    result = send_push(token=token, title=title, body=body, data=data, badge=badge)

    if result['success']:
        # Store ticket.id for later receipt polling
        return {"status": "delivered", "ticket_id": result['ticket_id']}

    error = result.get('error_code', 'UNKNOWN')

    # Auto-deactivate dead tokens
    if error == 'DEVICE_NOT_REGISTERED':
        UserDevice.objects.filter(expo_push_token=token).update(is_active=False)
        return {"status": "failed", "error": error, "token_deactivated": True}

    # Retry on transient errors
    if result.get('retryable') and self.request.retries < self.max_retries:
        raise self.retry(countdown=[30, 60, 120][min(self.request.retries, 2)])

    return {"status": "failed", "error": error}


@shared_task
def poll_receipts():
    """Run via Celery Beat every 15 min. Pass stored PushTicket objects to check_receipts."""
    from .push import check_receipts
    # Collect tickets from your notification records
    # receipts = check_receipts(tickets)
    # Deactivate devices where error_code == 'DeviceNotRegistered'
    pass
```

## FastAPI Integration

```python
# The push utility module is identical. Only the endpoint layer changes:
from exponent_server_sdk import PushClient
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator

router = APIRouter()

class DeviceRegisterRequest(BaseModel):
    expo_push_token: str
    platform: str  # "ios" | "android"
    device_model: str = ""

    @field_validator("expo_push_token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        v = v.strip()
        if not PushClient.is_exponent_push_token(v):
            raise ValueError("Invalid Expo Push Token format")
        return v

@router.post("/devices/register/", status_code=201)
async def register_device(body: DeviceRegisterRequest, user=Depends(get_current_user)):
    # Upsert logic same as Django version
    ...

@router.delete("/devices/{token}/", status_code=204)
async def unregister_device(token: str, user=Depends(get_current_user)):
    # Deactivate token
    ...
```

## Testing

```python
from unittest.mock import MagicMock, patch
from exponent_server_sdk import PushClient

TOKEN = "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]"


def test_valid_token():
    assert PushClient.is_exponent_push_token(TOKEN) is True
    assert PushClient.is_exponent_push_token("ExpoPushToken[xxx]") is True
    assert PushClient.is_exponent_push_token("raw-fcm-token") is False


@patch('push.get_push_client')
def test_send_success(mock_get_client):
    client = MagicMock()
    ticket = MagicMock()
    ticket.id = "ticket-001"
    ticket.validate_response.return_value = None
    client.publish.return_value = ticket
    mock_get_client.return_value = client

    from push import send_push
    result = send_push(token=TOKEN, title="Hi", body="Hello")
    assert result['success'] is True
    assert result['ticket_id'] == 'ticket-001'


@patch('push.get_push_client')
def test_device_not_registered(mock_get_client):
    from exponent_server_sdk import DeviceNotRegisteredError
    client = MagicMock()
    ticket = MagicMock()
    ticket.validate_response.side_effect = DeviceNotRegisteredError()
    client.publish.return_value = ticket
    mock_get_client.return_value = client

    from push import send_push
    result = send_push(token=TOKEN, title="Hi", body="Hello")
    assert result['success'] is False
    assert result['error_code'] == 'DEVICE_NOT_REGISTERED'
```
