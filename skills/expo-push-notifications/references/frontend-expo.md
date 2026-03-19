# Frontend: React Native + Expo

## Installation

```bash
npx expo install expo-notifications expo-device expo-constants
```

## App Config

Add to `app.json` (or `app.config.js`):

```jsonc
{
  "expo": {
    "plugins": [
      [
        "expo-notifications",
        {
          "icon": "./assets/notification-icon.png",
          "color": "#ffffff",
          "defaultChannel": "default"
        }
      ]
    ],
    "android": {
      "useNextNotificationsApi": true
    },
    "ios": {
      "infoPlist": {
        "UIBackgroundModes": ["remote-notification"]
      }
    }
  }
}
```

## EAS Credentials Setup

Push credentials are managed via EAS — no manual `.p8` or `google-services.json` on the backend.

```bash
# Configure iOS APNs key (one-time)
eas credentials -p ios

# Configure Android FCM key (one-time)
eas credentials -p android
```

## Push Notifications Hook

```typescript
// hooks/usePushNotifications.ts
import { useEffect, useRef, useState } from 'react';
import { Platform } from 'react-native';
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';

// Foreground notification display behavior
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

export interface PushNotificationState {
  expoPushToken: string | null;
  notification: Notifications.Notification | null;
  error: string | null;
}

export function usePushNotifications(): PushNotificationState {
  const [expoPushToken, setExpoPushToken] = useState<string | null>(null);
  const [notification, setNotification] = useState<Notifications.Notification | null>(null);
  const [error, setError] = useState<string | null>(null);
  const notificationListener = useRef<Notifications.EventSubscription>();
  const responseListener = useRef<Notifications.EventSubscription>();

  useEffect(() => {
    // Android notification channel
    if (Platform.OS === 'android') {
      Notifications.setNotificationChannelAsync('default', {
        name: 'Default',
        importance: Notifications.AndroidImportance.HIGH,
        vibrationPattern: [0, 250, 250, 250],
        sound: 'default',
      });
    }

    // Register
    registerForPushNotifications()
      .then(setExpoPushToken)
      .catch((err) => setError(err.message));

    // Foreground listener
    notificationListener.current = Notifications.addNotificationReceivedListener(
      setNotification,
    );

    // Tap listener (foreground + background)
    responseListener.current = Notifications.addNotificationResponseReceivedListener(
      (response) => {
        const data = response.notification.request.content.data;
        // Navigate based on data — e.g., data.screen, data.id
        console.log('Notification tapped:', data);
      },
    );

    return () => {
      if (notificationListener.current)
        Notifications.removeNotificationSubscription(notificationListener.current);
      if (responseListener.current)
        Notifications.removeNotificationSubscription(responseListener.current);
    };
  }, []);

  return { expoPushToken, notification, error };
}

async function registerForPushNotifications(): Promise<string | null> {
  if (!Device.isDevice) {
    console.warn('Push notifications require a physical device');
    return null;
  }

  const { status: existing } = await Notifications.getPermissionsAsync();
  let finalStatus = existing;

  if (existing !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== 'granted') {
    console.warn('Push permission not granted');
    return null;
  }

  const projectId = Constants.expoConfig?.extra?.eas?.projectId;
  const { data } = await Notifications.getExpoPushTokenAsync({ projectId });
  return data; // "ExponentPushToken[...]"
}
```

## Register Token with Backend

```typescript
// Call after login, when you have both the auth token and push token

import { Platform } from 'react-native';
import * as Device from 'expo-device';
import Constants from 'expo-constants';

async function registerTokenWithBackend(
  expoPushToken: string,
  apiClient: any, // your axios/fetch instance
): Promise<void> {
  await apiClient.post('/devices/register/', {
    expo_push_token: expoPushToken,
    platform: Platform.OS,
    device_model: Device.modelName || '',
    os_version: Device.osVersion || '',
    app_version: Constants.expoConfig?.version || '',
  });
}
```

## Unregister on Logout

```typescript
import * as Notifications from 'expo-notifications';
import Constants from 'expo-constants';

async function unregisterPushToken(apiClient: any): Promise<void> {
  try {
    const projectId = Constants.expoConfig?.extra?.eas?.projectId;
    const { data: token } = await Notifications.getExpoPushTokenAsync({ projectId });
    if (token) {
      await apiClient.delete(`/devices/${encodeURIComponent(token)}/`);
    }
  } catch {
    // Don't block logout if this fails
  }
}
```

## Usage in App Root

```tsx
// App.tsx or layout component
import { usePushNotifications } from './hooks/usePushNotifications';

export default function App() {
  const { expoPushToken, notification, error } = usePushNotifications();

  useEffect(() => {
    if (expoPushToken && isAuthenticated) {
      registerTokenWithBackend(expoPushToken, apiClient);
    }
  }, [expoPushToken, isAuthenticated]);

  // ... rest of app
}
```

## Handle Navigation from Notification Tap

```typescript
// In the response listener callback:
responseListener.current = Notifications.addNotificationResponseReceivedListener(
  (response) => {
    const data = response.notification.request.content.data;

    // Route based on notification data
    if (data.screen) {
      navigation.navigate(data.screen, data.params || {});
    }
  },
);
```

## Check Notification on Cold Start

```typescript
// App was killed, user tapped notification to open it
useEffect(() => {
  Notifications.getLastNotificationResponseAsync().then((response) => {
    if (response) {
      const data = response.notification.request.content.data;
      // Navigate based on data
    }
  });
}, []);
```

## Local Notifications (Optional)

```typescript
// Schedule a local notification (no server needed)
await Notifications.scheduleNotificationAsync({
  content: {
    title: 'Reminder',
    body: 'Your appointment is in 30 minutes',
    data: { screen: 'AppointmentDetail', id: '123' },
    sound: 'default',
  },
  trigger: { seconds: 1800 },
});
```

## Badge Management (iOS)

```typescript
// Set badge count
await Notifications.setBadgeCountAsync(5);

// Clear badge
await Notifications.setBadgeCountAsync(0);

// Get current badge
const count = await Notifications.getBadgeCountAsync();
```

## Testing

Push notifications only work on **physical devices**, not simulators/emulators. Use Expo's push notification tool for quick testing: https://expo.dev/notifications
