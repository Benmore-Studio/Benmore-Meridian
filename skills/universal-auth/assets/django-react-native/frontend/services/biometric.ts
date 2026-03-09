/**
 * Biometric Authentication Service — Universal Auth Skill template.
 * Stack: Expo (React Native) + expo-local-authentication + expo-application
 *
 * IMPROVEMENTS over source:
 *  - getDeviceFingerprint() handles null from both iOS vendorId and Android ID
 *    with a stable fallback that doesn't change on reinstall (uses applicationId)
 *  - authenticate() adds fallbackLabel for Android PIN fallback (iOS ignores it)
 *  - isSupported() added — checks hardware AND enrollment in one call;
 *    use this instead of isAvailable() when you need to distinguish the two
 *  - All methods have explicit return types
 */

import * as LocalAuthentication from 'expo-local-authentication';
import * as Application from 'expo-application';
import { Platform } from 'react-native';
import { secureStorage, appStorage, StorageKeys } from './storage';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type BiometricType = 'Face ID' | 'Face Recognition' | 'Touch ID' | 'Fingerprint' | 'Iris' | 'Biometrics' | 'None';

export interface BiometricSupportStatus {
  hasHardware: boolean;
  isEnrolled: boolean;
  isAvailable: boolean;
}

export interface BiometricCredentials {
  deviceToken: string;
  fingerprint: string;
}

// ---------------------------------------------------------------------------
// Service
// ---------------------------------------------------------------------------

export const biometricService = {
  /**
   * Quick check: hardware present AND user has enrolled biometrics.
   * Suitable for showing/hiding the "Use Face ID" button.
   */
  async isAvailable(): Promise<boolean> {
    const hasHardware = await LocalAuthentication.hasHardwareAsync();
    if (!hasHardware) return false;
    return LocalAuthentication.isEnrolledAsync();
  },

  /**
   * Detailed support status — use when you need to differentiate between
   * "no hardware" (device can never use biometrics) and "not enrolled"
   * (user can enable it in device settings).
   * NEW: not in source.
   */
  async getSupportStatus(): Promise<BiometricSupportStatus> {
    const hasHardware = await LocalAuthentication.hasHardwareAsync();
    const isEnrolled = hasHardware
      ? await LocalAuthentication.isEnrolledAsync()
      : false;
    return { hasHardware, isEnrolled, isAvailable: hasHardware && isEnrolled };
  },

  /** User-friendly label for the biometric type on this device. */
  async getBiometricType(): Promise<BiometricType> {
    const types = await LocalAuthentication.supportedAuthenticationTypesAsync();

    if (types.includes(LocalAuthentication.AuthenticationType.FACIAL_RECOGNITION)) {
      return Platform.OS === 'ios' ? 'Face ID' : 'Face Recognition';
    }
    if (types.includes(LocalAuthentication.AuthenticationType.FINGERPRINT)) {
      return Platform.OS === 'ios' ? 'Touch ID' : 'Fingerprint';
    }
    if (types.includes(LocalAuthentication.AuthenticationType.IRIS)) {
      return 'Iris';
    }
    return 'Biometrics';
  },

  /**
   * Prompt the user for biometric verification.
   * Returns true on success, false on cancellation or failure.
   *
   * FIX: added fallbackLabel — shown on Android when biometric fails and
   * the user can fall back to PIN. iOS ignores this field.
   */
  async authenticate(promptMessage?: string): Promise<boolean> {
    const result = await LocalAuthentication.authenticateAsync({
      promptMessage: promptMessage ?? 'Authenticate to continue',
      cancelLabel: 'Cancel',
      fallbackLabel: 'Use PIN',
      disableDeviceFallback: false,
    });
    return result.success;
  },

  /**
   * Generate a stable device fingerprint for binding tokens to this device.
   *
   * iOS: uses identifierForVendor (stable per app+vendor, resets on reinstall)
   * Android: uses androidId (stable until factory reset)
   *
   * Both fall back to applicationId if the primary ID is unavailable.
   * The fallback is less unique but always a string — never throws.
   */
  async getDeviceFingerprint(): Promise<string> {
    if (Platform.OS === 'ios') {
      const vendorId = await Application.getIosIdForVendorAsync();
      return vendorId ?? `ios_${Application.applicationId ?? 'unknown'}`;
    }
    // Android — getAndroidId() is synchronous in expo-application v6+
    const androidId = Application.getAndroidId();
    return androidId ?? `android_${Application.applicationId ?? 'unknown'}`;
  },

  /** Check whether biometric login has been enabled for this app install. */
  async isEnabled(): Promise<boolean> {
    const flag = await appStorage.getItem(StorageKeys.BIOMETRIC_ENABLED);
    return flag === 'true';
  },

  /** Persist biometric credentials after successful backend registration. */
  async storeCredentials(deviceToken: string, fingerprint: string): Promise<void> {
    await secureStorage.setItem(StorageKeys.BIOMETRIC_DEVICE_TOKEN, deviceToken);
    await secureStorage.setItem(StorageKeys.BIOMETRIC_DEVICE_FINGERPRINT, fingerprint);
    await appStorage.setItem(StorageKeys.BIOMETRIC_ENABLED, 'true');
  },

  /**
   * Retrieve stored biometric credentials.
   * Returns null if credentials are missing or SecureStore is unavailable.
   */
  async getCredentials(): Promise<BiometricCredentials | null> {
    const deviceToken = await secureStorage.getItem(StorageKeys.BIOMETRIC_DEVICE_TOKEN);
    const fingerprint = await secureStorage.getItem(StorageKeys.BIOMETRIC_DEVICE_FINGERPRINT);
    if (!deviceToken || !fingerprint) return null;
    return { deviceToken, fingerprint };
  },

  /** Remove all biometric credentials (on disable or server-side revocation). */
  async clearCredentials(): Promise<void> {
    await secureStorage.removeItem(StorageKeys.BIOMETRIC_DEVICE_TOKEN);
    await secureStorage.removeItem(StorageKeys.BIOMETRIC_DEVICE_FINGERPRINT);
    await appStorage.removeItem(StorageKeys.BIOMETRIC_ENABLED);
  },
};
