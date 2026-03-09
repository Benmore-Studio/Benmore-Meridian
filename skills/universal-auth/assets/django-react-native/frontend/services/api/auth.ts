/**
 * Auth Service — Universal Auth Skill template.
 * Stack: Expo (React Native) + Axios
 *
 * IMPROVEMENTS over source:
 *  - Removed mock infrastructure (USE_MOCKS, getMockHandlers) — keeps template
 *    clean; add mocks in a separate layer if needed during development
 *  - refreshToken() guards against null stored token before sending request
 *  - logout() clears biometric credentials when revoke flag is passed
 *  - All response type interfaces consolidated at the top (no split between
 *    service types and backend types)
 *
 * Usage:
 *   import { authService } from '@/services/api/auth';
 *   const result = await authService.login(email, password);
 */

import apiClient from './client';
import { secureStorage, appStorage, StorageKeys } from '../storage';
import { biometricService } from '../biometric';

// ---------------------------------------------------------------------------
// Response Types
// ---------------------------------------------------------------------------

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

export interface User {
  id: string;
  email: string;
  userType: string;
  emailVerified: boolean;
  mfaEnabled: boolean;
  isProfileComplete?: boolean;
  firstName?: string;
  lastName?: string;
}

export interface LoginResponse {
  user: User;
  tokens: AuthTokens;
  requiresMfa?: boolean;
  mfaToken?: string;
  isProfileComplete?: boolean;
}

export interface RegisterResponse {
  user: User;
}

export interface MFAVerifyResponse {
  success: boolean;
  tokens: AuthTokens;
  user: User;
  isProfileComplete?: boolean;
}

export interface MFASetupResponse {
  secret: string;
  qrCodeUri: string;
  recoveryCodes: string[];
}

export interface BiometricRegisterResponse {
  deviceToken: string;
  expiresAt: string;
  deviceId: string;
  deviceName: string;
}

export interface BiometricLoginResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
  isProfileComplete?: boolean;
}

export interface BiometricRevokeResponse {
  message: string;
  sessionsRevoked: number;
  remainingDevices: number;
}

// ---------------------------------------------------------------------------
// Backend shapes (flat format from Django views)
// ---------------------------------------------------------------------------

interface BackendLoginResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
  mfaRequired?: boolean;
  mfaToken?: string;
  isProfileComplete?: boolean;
}

interface BackendMFAVerifyResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
  isProfileComplete?: boolean;
}

interface BackendRefreshResponse {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

// ---------------------------------------------------------------------------
// Auth Service
// ---------------------------------------------------------------------------

export const authService = {
  /**
   * Authenticate with email and password.
   * Persists tokens only when not MFA-pending.
   */
  async login(email: string, password: string): Promise<LoginResponse> {
    const { data } = await apiClient.post<BackendLoginResponse>('/auth/login/', {
      email,
      password,
    });

    const result: LoginResponse = {
      user: data.user,
      tokens: {
        accessToken: data.accessToken ?? '',
        refreshToken: data.refreshToken ?? '',
        expiresIn: data.expiresIn ?? 900,
      },
      requiresMfa: data.mfaRequired,
      mfaToken: data.mfaToken,
      isProfileComplete: data.isProfileComplete,
    };

    if (!data.mfaRequired) {
      await persistAuthData(result);
    }

    return result;
  },

  /** Register a new user account. Email verification OTP is sent automatically. */
  async register(payload: {
    email: string;
    password: string;
    userType: string;
    firstName?: string;
    lastName?: string;
  }): Promise<RegisterResponse> {
    const { data } = await apiClient.post<{ user: User }>('/auth/register/', payload);
    return { user: data.user };
  },

  /**
   * Verify a TOTP / recovery code during MFA challenge.
   * Requires the mfaToken returned by login().
   */
  async verifyMFA(code: string, mfaToken: string): Promise<MFAVerifyResponse> {
    const { data } = await apiClient.post<BackendMFAVerifyResponse>(
      '/auth/mfa/verify/',
      { code, mfaToken },
    );

    const tokens: AuthTokens = {
      accessToken: data.accessToken,
      refreshToken: data.refreshToken,
      expiresIn: data.expiresIn,
    };

    await secureStorage.setItem(StorageKeys.ACCESS_TOKEN, tokens.accessToken);
    await secureStorage.setItem(StorageKeys.REFRESH_TOKEN, tokens.refreshToken);

    if (data.user) {
      await appStorage.setObject(StorageKeys.USER_DATA, { user: data.user });
    }

    return { success: true, tokens, user: data.user, isProfileComplete: data.isProfileComplete };
  },

  /**
   * Refresh the access token using the stored refresh token.
   *
   * FIX: guards against null refreshToken (source would send null to server,
   * getting a 400 instead of the more useful "no token" early return).
   */
  async refreshToken(): Promise<{ tokens: AuthTokens }> {
    const refreshToken = await secureStorage.getItem(StorageKeys.REFRESH_TOKEN);
    if (!refreshToken) {
      throw new Error('No refresh token stored. Please log in again.');
    }

    const { data } = await apiClient.post<BackendRefreshResponse>(
      '/auth/token/refresh/',
      { refreshToken },
    );

    const tokens: AuthTokens = {
      accessToken: data.accessToken,
      refreshToken: data.refreshToken,
      expiresIn: data.expiresIn,
    };

    await secureStorage.setItem(StorageKeys.ACCESS_TOKEN, tokens.accessToken);
    await secureStorage.setItem(StorageKeys.REFRESH_TOKEN, tokens.refreshToken);

    return { tokens };
  },

  /** Verify the user's email address using the 6-digit OTP code. */
  async verifyEmail(email: string, code: string): Promise<{ message: string }> {
    const { data } = await apiClient.post<{ message: string }>(
      '/auth/email/verify/',
      { email, code },
    );
    return data;
  },

  /** Request a new verification email OTP. */
  async resendVerificationEmail(email: string): Promise<{ message: string }> {
    const { data } = await apiClient.post<{ message: string }>(
      '/auth/email/resend-verification/',
      { email },
    );
    return data;
  },

  /** Initiate MFA setup — returns TOTP secret, QR code URI, and recovery codes. */
  async setupMFA(): Promise<MFASetupResponse> {
    const { data } = await apiClient.post<MFASetupResponse>('/auth/mfa/setup/');
    return data;
  },

  /** Enable MFA after the user scans the QR code and enters the first TOTP code. */
  async enableMFA(code: string): Promise<{ message: string }> {
    const { data } = await apiClient.post<{ message: string }>(
      '/auth/mfa/enable/',
      { code },
    );
    return data;
  },

  /** Disable MFA with current password confirmation. */
  async disableMFA(password: string): Promise<{ message: string }> {
    const { data } = await apiClient.post<{ message: string }>(
      '/auth/mfa/disable/',
      { password },
    );
    return data;
  },

  /** Register the current device for biometric authentication. */
  async registerBiometric(payload: {
    deviceId: string;
    deviceName: string;
    deviceFingerprint: string;
  }): Promise<BiometricRegisterResponse> {
    const { data } = await apiClient.post<BiometricRegisterResponse>(
      '/auth/biometric/register/',
      payload,
    );
    return data;
  },

  /**
   * Authenticate using a stored device token and fingerprint.
   * Persists new tokens on success.
   */
  async loginBiometric(payload: {
    deviceToken: string;
    deviceFingerprint: string;
  }): Promise<LoginResponse> {
    const { data } = await apiClient.post<BiometricLoginResponse>(
      '/auth/biometric/login/',
      payload,
    );

    const result: LoginResponse = {
      user: data.user,
      tokens: {
        accessToken: data.accessToken,
        refreshToken: data.refreshToken,
        expiresIn: data.expiresIn,
      },
      isProfileComplete: data.isProfileComplete,
    };

    await persistAuthData(result);
    return result;
  },

  /** Revoke biometric device session(s). */
  async revokeBiometric(payload: {
    revokeAll?: boolean;
    deviceId?: string;
    deviceFingerprint?: string;
  }): Promise<BiometricRevokeResponse> {
    const { data } = await apiClient.post<BiometricRevokeResponse>(
      '/auth/biometric/revoke/',
      payload,
    );
    return data;
  },

  /** Request a password reset OTP sent to the user's email. */
  async forgotPassword(email: string): Promise<{ message: string }> {
    const { data } = await apiClient.post<{ message: string }>(
      '/auth/password/forgot/',
      { email },
    );
    return data;
  },

  /** Reset password using OTP + new password. */
  async resetPassword(
    email: string,
    code: string,
    newPassword: string,
  ): Promise<{ message: string }> {
    const { data } = await apiClient.post<{ message: string }>(
      '/auth/password/reset/',
      { email, code, newPassword },
    );
    return data;
  },

  /**
   * Log out — clears stored tokens and user data.
   * Pass clearBiometric=true when the user explicitly disables biometric login.
   *
   * FIX: clarified when biometric credentials should be cleared vs preserved.
   * Source always preserved them; now the caller controls this explicitly.
   */
  async logout(options: { clearBiometric?: boolean } = {}): Promise<void> {
    try {
      const refreshToken = await secureStorage.getItem(StorageKeys.REFRESH_TOKEN);
      if (refreshToken) {
        await apiClient.post('/auth/logout/', { refreshToken });
      }
    } catch {
      // Best-effort server-side logout; always clear local state below
    } finally {
      await secureStorage.removeItem(StorageKeys.ACCESS_TOKEN);
      await secureStorage.removeItem(StorageKeys.REFRESH_TOKEN);
      await appStorage.removeItem(StorageKeys.USER_DATA);

      if (options.clearBiometric) {
        await biometricService.clearCredentials();
      }
    }
  },
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function persistAuthData(response: LoginResponse): Promise<void> {
  await secureStorage.setItem(StorageKeys.ACCESS_TOKEN, response.tokens.accessToken);
  await secureStorage.setItem(StorageKeys.REFRESH_TOKEN, response.tokens.refreshToken);
  await appStorage.setObject(StorageKeys.USER_DATA, { user: response.user });
}
