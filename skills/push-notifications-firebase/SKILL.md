# Push Notifications Implementation Skill

## Purpose

This skill guides Claude Code through implementing Firebase Cloud Messaging push notifications for the House Service Pass mobile app and Django backend. Includes code snippets for all major components.

## When to Use This Skill

Use this skill when:
- Implementing the full push notification feature from scratch
- Adding push notification support to new booking state transitions
- Debugging push notification delivery issues
- Scaling push notification system for more users

## Architecture Overview

Push notifications follow this flow:

1. **Device Registration**: Mobile app registers Firebase token with backend after login
2. **Event Emission**: When booking state changes, backend emits notification event
3. **Async Delivery**: Celery task sends push via Firebase in background (non-blocking)
4. **User Preferences**: Customer can toggle notification types on/off
5. **Token Cleanup**: Expired/invalid tokens are pruned automatically

## Phase 1: Database Models

### DeviceToken Model

```python
# django-backend/accounts/models.py
# Add to the models.py file after existing models

class DeviceToken(models.Model):
    """
    Store Firebase Cloud Messaging tokens for push notifications.
    Each device (phone, tablet) has a unique token.
    """
    
    PLATFORM_CHOICES = [
        ('ios', 'iOS'),
        ('android', 'Android'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='device_tokens')
    
    # Firebase token - unique per device
    token = models.TextField(db_index=True, unique=True, help_text='Firebase Cloud Messaging token')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, help_text='Mobile platform')
    device_name = models.CharField(max_length=255, blank=True, help_text='User-visible device name')
    
    # Status tracking
    is_active = models.BooleanField(default=True, db_index=True, help_text='False if token expired or revoked')
    last_used = models.DateTimeField(auto_now=True, help_text='Last successful push to this device')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'device_tokens'
        verbose_name = 'Device Token'
        verbose_name_plural = 'Device Tokens'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['token']),
        ]
        unique_together = [['user', 'token']]
        ordering = ['-last_used']
    
    def __str__(self):
        return f"{self.user.email} - {self.device_name or self.platform}"


class PushNotificationPreference(models.Model):
    """
    User-controlled preferences for push notifications.
    Allows customers to toggle specific notification types.
    """
    
    NOTIFICATION_TYPES = [
        ('booking_scheduled', 'Booking Scheduled'),
        ('booking_completed', 'Booking Completed'),
        ('booking_cancelled', 'Booking Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_notification_preferences')
    
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    enabled = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'push_notification_preferences'
        verbose_name = 'Push Notification Preference'
        verbose_name_plural = 'Push Notification Preferences'
        unique_together = [['user', 'notification_type']]
        indexes = [
            models.Index(fields=['user', 'notification_type']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.notification_type}: {self.enabled}"
Migrations
# django-backend/accounts/migrations/0015_device_token.py

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0014_add_stripe_customer_id_to_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='DeviceToken',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('token', models.TextField(db_index=True, help_text='Firebase Cloud Messaging token', unique=True)),
                ('platform', models.CharField(choices=[('ios', 'iOS'), ('android', 'Android')], help_text='Mobile platform', max_length=20)),
                ('device_name', models.CharField(blank=True, help_text='User-visible device name', max_length=255)),
                ('is_active', models.BooleanField(db_index=True, default=True, help_text='False if token expired or revoked')),
                ('last_used', models.DateTimeField(auto_now=True, help_text='Last successful push to this device')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='device_tokens', to='accounts.user')),
            ],
            options={
                'verbose_name': 'Device Token',
                'verbose_name_plural': 'Device Tokens',
                'db_table': 'device_tokens',
            },
        ),
        migrations.AddIndex(
            model_name='devicetoken',
            index=models.Index(fields=['user', 'is_active'], name='accounts_devicetoken_user_is_active_idx'),
        ),
        migrations.AddIndex(
            model_name='devicetoken',
            index=models.Index(fields=['token'], name='accounts_devicetoken_token_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='devicetoken',
            unique_together={('user', 'token')},
        ),
    ]
# django-backend/accounts/migrations/0016_push_notification_preference.py

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0015_device_token'),
    ]

    operations = [
        migrations.CreateModel(
            name='PushNotificationPreference',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('notification_type', models.CharField(choices=[('booking_scheduled', 'Booking Scheduled'), ('booking_completed', 'Booking Completed'), ('booking_cancelled', 'Booking Cancelled')], max_length=50)),
                ('enabled', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='push_notification_preferences', to='accounts.user')),
            ],
            options={
                'verbose_name': 'Push Notification Preference',
                'verbose_name_plural': 'Push Notification Preferences',
                'db_table': 'push_notification_preferences',
            },
        ),
        migrations.AddIndex(
            model_name='pushnotificationpreference',
            index=models.Index(fields=['user', 'notification_type'], name='accounts_pushnotificationpreference_user_notification_type_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='pushnotificationpreference',
            unique_together={('user', 'notification_type')},
        ),
    ]
Phase 2: Backend Endpoints
Serializers
# django-backend/notifications/serializers.py

from rest_framework import serializers
from accounts.models import DeviceToken, PushNotificationPreference


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ['id', 'token', 'platform', 'device_name', 'is_active', 'created_at']
        read_only_fields = ['id', 'is_active', 'created_at']


class PushNotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushNotificationPreference
        fields = ['notification_type', 'enabled']


class PushNotificationPreferencesListSerializer(serializers.Serializer):
    """Serializer for bulk preference operations"""
    preferences = PushNotificationPreferenceSerializer(many=True)
Views
# django-backend/notifications/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from accounts.models import DeviceToken, PushNotificationPreference
from .serializers import DeviceTokenSerializer, PushNotificationPreferenceSerializer
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_device_token(request):
    """
    Register a device token for push notifications.
    Called by mobile app after successful login.
    
    Request body:
    {
        "token": "firebase-device-token-here",
        "platform": "ios" or "android",
        "device_name": "John's iPhone" (optional)
    }
    """
    token = request.data.get('token', '').strip()
    platform = request.data.get('platform', '').lower()
    device_name = request.data.get('device_name', '')
    
    # Validate
    if not token:
        return Response(
            {'error': 'token field is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if platform not in ['ios', 'android']:
        return Response(
            {'error': 'platform must be "ios" or "android"'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create or update device token
    device_token, created = DeviceToken.objects.update_or_create(
        user=request.user,
        token=token,
        defaults={
            'platform': platform,
            'device_name': device_name,
            'is_active': True,
            'last_used': timezone.now()
        }
    )
    
    logger.info(f"Device token registered for user {request.user.email}: {platform}")
    
    return Response(
        DeviceTokenSerializer(device_token).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unregister_device_token(request):
    """
    Unregister a device token (called on logout).
    Marks token as inactive so no more pushes are sent.
    
    Request body:
    {
        "token": "firebase-device-token-here"
    }
    """
    token = request.data.get('token', '').strip()
    
    if not token:
        return Response(
            {'error': 'token field is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Mark as inactive (soft delete)
    device_token = DeviceToken.objects.filter(
        user=request.user,
        token=token
    ).first()
    
    if device_token:
        device_token.is_active = False
        device_token.save()
        logger.info(f"Device token unregistered for user {request.user.email}")
    
    return Response(
        {'message': 'Device token unregistered'},
        status=status.HTTP_200_OK
    )


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def push_notification_preferences(request):
    """
    Get or update push notification preferences for user.
    
    GET: Returns all preference types with current enabled status
    PUT: Update preferences
    
    PUT Request body:
    {
        "preferences": [
            {"notification_type": "booking_scheduled", "enabled": true},
            {"notification_type": "booking_completed", "enabled": false},
            {"notification_type": "booking_cancelled", "enabled": true}
        ]
    }
    """
    if request.method == 'GET':
        preferences = PushNotificationPreference.objects.filter(
            user=request.user
        ).all()
        
        serializer = PushNotificationPreferenceSerializer(preferences, many=True)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        preferences_data = request.data.get('preferences', [])
        
        for pref_data in preferences_data:
            notification_type = pref_data.get('notification_type')
            enabled = pref_data.get('enabled', True)
            
            if not notification_type:
                continue
            
            # Create or update preference
            PushNotificationPreference.objects.update_or_create(
                user=request.user,
                notification_type=notification_type,
                defaults={'enabled': enabled}
            )
        
        logger.info(f"Push notification preferences updated for user {request.user.email}")
        
        # Return updated preferences
        preferences = PushNotificationPreference.objects.filter(
            user=request.user
        ).all()
        
        serializer = PushNotificationPreferenceSerializer(preferences, many=True)
        return Response(serializer.data)
URL Configuration
# django-backend/notifications/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('devices/register/', views.register_device_token, name='register_device_token'),
    path('devices/unregister/', views.unregister_device_token, name='unregister_device_token'),
    path('preferences/', views.push_notification_preferences, name='push_notification_preferences'),
]
Add to main URLs
# django-backend/config/urls.py (or main project urls.py)
# Add this line in the urlpatterns list:

path('api/notifications/', include('notifications.urls')),
Phase 3: Celery Task Setup
Celery Configuration
# django-backend/settings.py
# Add or update these settings

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Celery task routing
CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_QUEUES = (
    Queue('default', routing_key='default'),
    Queue('notifications', routing_key='notifications'),
)

# Task configuration
CELERY_TASK_MAX_RETRIES = 3
CELERY_TASK_DEFAULT_RETRY_DELAY = 60  # 1 minute

# Firebase configuration
FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH', '')
Celery Task
# django-backend/bookings/tasks.py

from celery import shared_task
from django.utils import timezone
from django.conf import settings
import firebase_admin
from firebase_admin import credentials, messaging
import logging
import os

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
if not firebase_admin.get_app(_DEFAULT_APP_NAME=None):
    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)


@shared_task(bind=True, max_retries=3)
def send_booking_notification(self, booking_id, event_type):
    """
    Send push notification to customer about booking status change.
    
    Args:
        booking_id: UUID of the booking
        event_type: Type of event (booking_scheduled, booking_completed, booking_cancelled)
    
    Retries with exponential backoff on failure.
    """
    from bookings.models import Booking
    from accounts.models import DeviceToken, PushNotificationPreference
    
    try:
        # Fetch booking
        booking = Booking.objects.get(id=booking_id)
        customer = booking.customer
        
        # Check if customer has enabled this notification type
        preference = PushNotificationPreference.objects.filter(
            user=customer,
            notification_type=event_type,
            enabled=True
        ).first()
        
        if not preference:
            logger.info(f"Push notification disabled for user {customer.email}: {event_type}")
            return {'status': 'skipped', 'reason': 'preference_disabled'}
        
        # Fetch active device tokens
        device_tokens = DeviceToken.objects.filter(
            user=customer,
            is_active=True
        ).all()
        
        if not device_tokens:
            logger.warning(f"No active device tokens for user {customer.email}")
            return {'status': 'failed', 'reason': 'no_devices'}
        
        # Build notification payload
        title, body = _get_notification_content(booking, event_type)
        
        message_data = {
            'booking_id': str(booking.id),
            'event_type': event_type,
            'action': 'open_booking_detail'
        }
        
        # Send to all devices
        success_count = 0
        failure_count = 0
        
        for device_token in device_tokens:
            try:
                # Build message
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=title,
                        body=body
                    ),
                    data=message_data,
                    token=device_token.token
                )
                
                # Send via Firebase
                response = messaging.send(message)
                
                # Update last_used timestamp
                device_token.last_used = timezone.now()
                device_token.save()
                
                success_count += 1
                logger.info(f"Push sent to {device_token.platform}: {device_token.device_name}")
                
            except messaging.UnregisteredError:
                # Token is invalid/expired
                device_token.is_active = False
                device_token.save()
                failure_count += 1
                logger.warning(f"Device token invalid, marked inactive: {device_token.token[:20]}...")
                
            except messaging.InvalidArgumentError as e:
                # Malformed message
                failure_count += 1
                logger.error(f"Invalid Firebase message: {str(e)}")
                
            except Exception as e:
                # Network/service error - will retry
                failure_count += 1
                logger.error(f"Firebase error: {str(e)}")
                raise
        
        result = {
            'status': 'success',
            'sent': success_count,
            'failed': failure_count
        }
        
        logger.info(f"Booking notification sent: {event_type} to user {customer.email} - {result}")
        return result
        
    except Booking.DoesNotExist:
        logger.error(f"Booking not found: {booking_id}")
        return {'status': 'failed', 'reason': 'booking_not_found'}
        
    except Exception as exc:
        # Exponential backoff retry
        retry_delay = (2 ** self.request.retries) * 60  # 60s, 120s, 240s
        logger.exception(f"Error sending notification, retrying in {retry_delay}s")
        raise self.retry(exc=exc, countdown=retry_delay)


def _get_notification_content(booking, event_type):
    """Generate notification title and body based on event type"""
    
    scheduled_date = booking.scheduled_at.strftime('%A, %B %d') if booking.scheduled_at else 'TBD'
    scheduled_time = booking.scheduled_at.strftime('%I:%M %p') if booking.scheduled_at else 'TBD'
    
    if event_type == 'booking_scheduled':
        title = 'Booking Scheduled'
        body = f'Your {booking.service.name} is scheduled for {scheduled_date} at {scheduled_time}'
        
    elif event_type == 'booking_completed':
        body_text = booking.provider_notes or 'Your service has been completed'
        title = 'Service Completed'
        body = f'{booking.service.name} completed. {body_text[:50]}...'
        
    elif event_type == 'booking_cancelled':
        title = 'Booking Cancelled'
        body = f'Your {booking.service.name} booking has been cancelled'
        
    else:
        title = 'House Service Pass'
        body = 'Booking update'
    
    return title, body
Django Signal Handler
# django-backend/bookings/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
from bookings.models import Booking
from bookings.tasks import send_booking_notification
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Booking)
def booking_status_changed(sender, instance, created, **kwargs):
    """
    Emit notification event when booking status changes.
    Queues async task to send push notification.
    """
    
    # Don't send notification for newly created bookings (PENDING status)
    if created:
        return
    
    # Map status to notification event type
    event_mapping = {
        'SCHEDULED': 'booking_scheduled',
        'COMPLETED': 'booking_completed',
        'CANCELLED': 'booking_cancelled'
    }
    
    event_type = event_mapping.get(instance.status)
    
    if event_type:
        # Queue notification task
        send_booking_notification.apply_async(
            args=[str(instance.id), event_type],
            queue='notifications'
        )
        
        logger.info(f"Notification task queued for booking {instance.id}: {event_type}")


# Register signal in apps.py ready() method
def setup_signals():
    """Call this in BookingsConfig.ready()"""
    from . import signals  # noqa
Register Signal in Apps
# django-backend/bookings/apps.py

from django.apps import AppConfig


class BookingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bookings'
    
    def ready(self):
        from .signals import setup_signals
        setup_signals()
Phase 4: Mobile App Integration
AuthContext Update
// mobile-app/src/context/AuthContext.tsx

import messaging from '@react-native-firebase/messaging';

interface AuthContextValue extends AuthState {
  login: (accessToken: string, refreshToken: string, user: User, pass: Pass) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<boolean>;
  updatePassStatus: (pass: Pass) => void;
}

export function AuthProvider({ children, onAuthStateReady }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [pass, setPass] = useState<Pass | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isPassExpired, setIsPassExpired] = useState(false);

  const login = useCallback(async (
    accessToken: string,
    refreshToken: string,
    userData: User,
    passData: Pass
  ) => {
    await saveTokens({ accessToken, refreshToken });
    await saveUserData(userData);
    await savePassData(passData);
    setUser(userData);
    setPass(passData);
    setIsAuthenticated(true);
    setIsPassExpired(passData.is_expired);
    
    // Register device token for push notifications
    try {
      const token = await messaging().getToken();
      if (token) {
        const platform = Platform.OS; // 'ios' or 'android'
        await api.post('/notifications/devices/register/', {
          token,
          platform,
          device_name: `${Platform.OS} Device`
        });
      }
    } catch (error) {
      console.warn('Failed to register device token:', error);
      // Don't fail login if push registration fails
    }
  }, []);

  const logout = useCallback(async () => {
    // Unregister device token on logout
    try {
      const token = await messaging().getToken();
      if (token) {
        await api.post('/notifications/devices/unregister/', { token });
      }
    } catch (error) {
      console.warn('Failed to unregister device token:', error);
    }
    
    await clearAllData();
    setUser(null);
    setPass(null);
    setIsAuthenticated(false);
    setIsPassExpired(false);
  }, []);

  // ... rest of AuthProvider code
}
Root App Component Push Listener
// mobile-app/src/App.tsx

import messaging from '@react-native-firebase/messaging';
import { useEffect } from 'react';
import { Platform } from 'react-native';

export function App() {
  useEffect(() => {
    // Request notification permission (iOS only)
    if (Platform.OS === 'ios') {
      messaging().requestPermission();
    }
    
    // Handle foreground notifications
    const unsubscribeForeground = messaging().onMessage(async (remoteMessage) => {
      const bookingId = remoteMessage.data?.booking_id;
      const action = remoteMessage.data?.action;
      
      if (action === 'open_booking_detail' && bookingId) {
        // Navigate to booking detail screen
        navigationRef.navigate('BookingDetail', { id: bookingId });
      }
    });
    
    // Handle background notification tap
    const unsubscribeBackground = messaging().onNotificationOpenedApp((remoteMessage) => {
      const bookingId = remoteMessage?.data?.booking_id;
      const action = remoteMessage?.data?.action;
      
      if (action === 'open_booking_detail' && bookingId) {
        navigationRef.navigate('BookingDetail', { id: bookingId });
      }
    });
    
    return () => {
      unsubscribeForeground();
      unsubscribeBackground();
    };
  }, []);
  
  return (
    // ... app content
  );
}
ProfileScreen Notification Preferences
// mobile-app/src/screens/ProfileScreen.tsx
// Add this to the existing ProfileScreen component

import { Switch } from 'react-native';

const NotificationPreferencesSection = () => {
  const [preferences, setPreferences] = useState({
    booking_scheduled: true,
    booking_completed: true,
    booking_cancelled: true
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Fetch current preferences
    const fetchPreferences = async () => {
      try {
        const response = await api.get('/notifications/preferences/');
        const prefMap = {};
        response.data.forEach((pref: any) => {
          prefMap[pref.notification_type] = pref.enabled;
        });
        setPreferences(prefMap);
      } catch (error) {
        console.error('Failed to fetch preferences:', error);
      }
    };
    
    fetchPreferences();
  }, []);

  const handleToggle = async (notificationType: string) => {
    try {
      setLoading(true);
      const updated = {
        ...preferences,
        [notificationType]: !preferences[notificationType]
      };
      
      await api.put('/notifications/preferences/', {
        preferences: Object.entries(updated).map(([type, enabled]) => ({
          notification_type: type,
          enabled
        }))
      });
      
      setPreferences(updated);
    } catch (error) {
      console.error('Failed to update preferences:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.preferencesSection}>
      <Text style={styles.sectionTitle}>Notification Settings</Text>
      
      <View style={styles.preferenceItem}>
        <Text style={styles.preferenceName}>Booking Scheduled</Text>
        <Switch
          value={preferences.booking_scheduled}
          onValueChange={() => handleToggle('booking_scheduled')}
          disabled={loading}
        />
      </View>
      
      <View style={styles.preferenceItem}>
        <Text style={styles.preferenceName}>Booking Completed</Text>
        <Switch
          value={preferences.booking_completed}
          onValueChange={() => handleToggle('booking_completed')}
          disabled={loading}
        />
      </View>
      
      <View style={styles.preferenceItem}>
        <Text style={styles.preferenceName}>Booking Cancelled</Text>
        <Switch
          value={preferences.booking_cancelled}
          onValueChange={() => handleToggle('booking_cancelled')}
          disabled={loading}
        />
      </View>
    </View>
  );
};
Firebase Setup Checklist
 Create Firebase project at https://console.firebase.google.com
 Download service account JSON credentials
 Add credentials to environment variable: FIREBASE_CREDENTIALS_PATH
 Enable Cloud Messaging in Firebase Console
 Add Firebase to mobile app via google-services.json (Android) and GoogleService-Info.plist (iOS)
 Test with Firebase Emulator Suite before production
Testing Checklist
 Device token created when registering
 Device token marked inactive when unregistering
 Preferences default to enabled for new users
 Preferences can be toggled via API
 Celery task queued when booking status changes
 Firebase receives push with correct payload
 Dead tokens (404) marked as inactive
 Notification skipped if preference disabled
 Mobile app receives push in foreground
 Mobile app receives push in background
 Notification tap navigates to booking detail
 Token cleanup removes old inactive tokens
Key Files Summary
Create:
django-backend/accounts/migrations/0015_device_token.py
django-backend/accounts/migrations/0016_push_notification_preference.py
django-backend/notifications/views.py
django-backend/notifications/serializers.py
django-backend/notifications/urls.py
django-backend/bookings/tasks.py
django-backend/bookings/signals.py
Modify:
django-backend/accounts/models.py - Add DeviceToken, PushNotificationPreference models
django-backend/settings.py - Add Celery config
django-backend/config/urls.py - Register notifications app
django-backend/bookings/apps.py - Register signal handlers
mobile-app/src/context/AuthContext.tsx - Add Firebase token registration
mobile-app/src/App.tsx - Add push listeners
mobile-app/src/screens/ProfileScreen.tsx - Add preference toggles
Deployment Notes
Ensure Redis is running and accessible at CELERY_BROKER_URL
Start Celery worker: celery -A django_backend worker -l info -Q default,notifications
Test push delivery with Firebase emulator first
Monitor Celery task queue for failures: celery -A django_backend events
Set up log aggregation to track push delivery metrics

---

This comprehensive skill includes:
- Complete model definitions with docstrings
- Full migration code ready to copy
- Serializers and views with request/response examples
- Celery task implementation with Firebase integration
- Django signal handlers
- Mobile app code for AuthContext, App root, and ProfileScreen
- Firebase setup checklist
- Testing checklist
- File summary

