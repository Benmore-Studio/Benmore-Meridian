---
name: expo-push-notifications
description: Implement Expo Push Notifications for React Native (Expo) frontend and Python backend. Use when adding push notifications to an Expo app, registering device tokens, sending push from a Python backend (Django, FastAPI), setting up expo-notifications on the frontend, handling foreground/background notification listeners, or debugging push delivery. Triggers on "push notifications", "expo notifications", "expo push token", "send push notification", "notification listener", "expo-notifications", "expo-server-sdk", "ExponentPushToken", "device token registration", "notification channel", "badge count", or "push receipt". Covers both iOS (APNs) and Android (FCM) via Expo's unified push service. No Firebase Admin SDK or raw APNs setup needed.
---

# Expo Push Notifications

Expo Push provides unified iOS + Android push delivery. One token format (`ExponentPushToken[...]`), one API, automatic APNs/FCM routing.

## Architecture

```
Frontend (Expo)                    Backend (Python)                 Expo Push Service
─────────────────                  ────────────────                 ─────────────────
1. Request permission
2. Get ExponentPushToken ──POST──> 3. Store token in DB
                                   4. Send push via expo-server-sdk ──> 5. Route to APNs/FCM
6. Receive notification <──────────────────────────────────────────────
7. Handle tap → navigate
                                   8. Poll receipts (15 min later)  <── 9. Delivery confirmation
```

## Quick Start

### Frontend

```bash
npx expo install expo-notifications expo-device expo-constants
```

Create `usePushNotifications` hook, register token after login, handle notification taps.

See [references/frontend-expo.md](references/frontend-expo.md) for complete hook, registration, logout cleanup, cold start handling, badge management, and local notifications.

### Backend

```bash
uv add exponent_server_sdk
```

Create push utility module, validate tokens, send via `PushClient`, handle errors, poll receipts.

See [references/backend-python.md](references/backend-python.md) for complete push module, Django/FastAPI integration, device model, registration endpoint, Celery delivery task, and tests.

## Key Patterns

### Token Validation

Use the SDK's built-in classmethod — reject raw FCM/APNs tokens:

```python
from exponent_server_sdk import PushClient

PushClient.is_exponent_push_token("ExponentPushToken[xxx]")  # True
PushClient.is_exponent_push_token("raw-fcm-token")           # False
```

### Error Handling

| Error | Action |
|-------|--------|
| `DeviceNotRegisteredError` | Deactivate token in DB, do not retry |
| `MessageTooBigError` | Reduce payload, do not retry |
| `MessageRateExceededError` | Retry with backoff |
| `PushServerError` | Retry with backoff |

### Dead Token Cleanup

Deactivate tokens on `DEVICE_NOT_REGISTERED` errors (from send or receipts):

```python
if error_code == 'DEVICE_NOT_REGISTERED':
    UserDevice.objects.filter(expo_push_token=token).update(is_active=False)
```

### Receipt Polling

Poll 15+ minutes after sending to confirm delivery:

```python
from push import check_receipts
receipts = check_receipts(ticket_ids)
# Deactivate devices where receipt says DeviceNotRegistered
```

## Checklist

- [ ] `expo-notifications` + `expo-device` installed in frontend
- [ ] Android notification channel configured
- [ ] iOS `remote-notification` background mode in app.json
- [ ] EAS credentials configured (`eas credentials -p ios` and `-p android`)
- [ ] `usePushNotifications` hook created and used in app root
- [ ] Token registered with backend after login
- [ ] Token deactivated on logout
- [ ] `exponent_server_sdk` installed on backend (`uv add exponent_server_sdk`)
- [ ] Token format validated before sending
- [ ] `DeviceNotRegisteredError` deactivates tokens
- [ ] Retry logic for transient errors
- [ ] Receipt polling scheduled (every 15 min)
- [ ] Tested on physical device (push does not work on simulators)
