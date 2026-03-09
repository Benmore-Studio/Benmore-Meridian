/**
 * Storage Service — Universal Auth Skill template.
 * Stack: Expo (React Native) + expo-secure-store + AsyncStorage
 *
 * IMPROVEMENTS over source:
 *  - secureStorage wraps errors with context so failures are debuggable
 *    (expo-secure-store throws on Android when device lock is removed mid-session)
 *  - clearAll() added to secureStorage and appStorage for clean logout
 *  - StorageKeys prefixed with APP_ convention — rename APP_PREFIX to match yours
 *
 * Usage:
 *   import { secureStorage, appStorage, StorageKeys } from '@/services/storage';
 *   await secureStorage.setItem(StorageKeys.ACCESS_TOKEN, token);
 */

import * as SecureStore from 'expo-secure-store';
import AsyncStorage from '@react-native-async-storage/async-storage';

// ---------------------------------------------------------------------------
// App prefix — change to your app name to avoid key collisions between apps
// ---------------------------------------------------------------------------

const APP_PREFIX = 'app';

// ---------------------------------------------------------------------------
// Secure Storage — tokens, credentials, sensitive data
// Backed by iOS Keychain / Android Keystore via expo-secure-store.
// ---------------------------------------------------------------------------

export const secureStorage = {
  async setItem(key: string, value: string): Promise<void> {
    try {
      await SecureStore.setItemAsync(key, value);
    } catch (err) {
      throw new Error(`secureStorage.setItem(${key}) failed: ${String(err)}`);
    }
  },

  async getItem(key: string): Promise<string | null> {
    try {
      return await SecureStore.getItemAsync(key);
    } catch {
      // Keychain unavailable (device locked, biometric lockout) — treat as miss
      return null;
    }
  },

  async removeItem(key: string): Promise<void> {
    try {
      await SecureStore.deleteItemAsync(key);
    } catch {
      // Key may not exist — silent is correct here
    }
  },

  /** Remove all auth-related secure keys. Call on logout or account deletion. */
  async clearAll(): Promise<void> {
    const authKeys = [
      StorageKeys.ACCESS_TOKEN,
      StorageKeys.REFRESH_TOKEN,
      StorageKeys.BIOMETRIC_DEVICE_TOKEN,
      StorageKeys.BIOMETRIC_DEVICE_FINGERPRINT,
    ];
    await Promise.allSettled(authKeys.map((k) => SecureStore.deleteItemAsync(k)));
  },
};

// ---------------------------------------------------------------------------
// App Storage — non-sensitive preferences and cached UI state
// Backed by AsyncStorage (not encrypted).
// ---------------------------------------------------------------------------

export const appStorage = {
  async setItem(key: string, value: string): Promise<void> {
    await AsyncStorage.setItem(key, value);
  },

  async getItem(key: string): Promise<string | null> {
    return AsyncStorage.getItem(key);
  },

  async removeItem(key: string): Promise<void> {
    await AsyncStorage.removeItem(key);
  },

  async setObject<T>(key: string, value: T): Promise<void> {
    await AsyncStorage.setItem(key, JSON.stringify(value));
  },

  async getObject<T>(key: string): Promise<T | null> {
    const value = await AsyncStorage.getItem(key);
    if (!value) return null;
    try {
      return JSON.parse(value) as T;
    } catch {
      return null;
    }
  },

  /** Remove all app-level keys. Call on logout. */
  async clearAll(): Promise<void> {
    const appKeys = [
      StorageKeys.USER_DATA,
      StorageKeys.BIOMETRIC_ENABLED,
      StorageKeys.NOTIFICATION_PREFS,
      StorageKeys.THEME_MODE,
    ];
    await AsyncStorage.multiRemove(appKeys);
  },
};

// ---------------------------------------------------------------------------
// Storage Keys — central registry to prevent key collisions
// CUSTOMIZE: change the APP_PREFIX constant above instead of editing keys here
// ---------------------------------------------------------------------------

export const StorageKeys = {
  // Tokens — stored in SecureStore
  ACCESS_TOKEN: `${APP_PREFIX}_access_token`,
  REFRESH_TOKEN: `${APP_PREFIX}_refresh_token`,

  // User data — stored in AsyncStorage (no PHI here)
  USER_DATA: `${APP_PREFIX}_user_data`,

  // Biometric — device token in SecureStore, flag in AsyncStorage
  BIOMETRIC_DEVICE_TOKEN: `${APP_PREFIX}_biometric_device_token`,
  BIOMETRIC_DEVICE_FINGERPRINT: `${APP_PREFIX}_biometric_fingerprint`,
  BIOMETRIC_ENABLED: `${APP_PREFIX}_biometric_enabled`,

  // Preferences — AsyncStorage
  NOTIFICATION_PREFS: `${APP_PREFIX}_notification_prefs`,
  THEME_MODE: `${APP_PREFIX}_theme_mode`,
} as const;

export type StorageKey = (typeof StorageKeys)[keyof typeof StorageKeys];
