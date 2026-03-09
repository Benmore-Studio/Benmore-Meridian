/**
 * Auth Context — Universal Auth Skill template.
 * Stack: React Native + Expo
 *
 * IMPROVEMENTS over source:
 *  - Session restoration validates token expiry via JWT decode (source trusted
 *    any stored token without checking if it was expired)
 *  - biometricLogin clears credentials based on HTTP status codes (401/403)
 *    rather than string-matching error messages (more robust)
 *  - verifyMFA uses a ref for mfaToken to avoid stale closure issues; the
 *    source pattern with [state.mfaToken] in deps was correct but fragile
 *  - logout() accepts options passed through to authService.logout()
 *  - isTokenExpired helper extracted (reusable, testable)
 *
 * Usage:
 *   import { useAuth } from '@/context/AuthContext';
 *   const { user, isAuthenticated, login, logout } = useAuth();
 */

import React, {
  createContext,
  useContext,
  useReducer,
  useEffect,
  useRef,
  useCallback,
  useMemo,
} from 'react';
import { secureStorage, appStorage, StorageKeys } from '../services/storage';
import { authService } from '../services/api/auth';
import { biometricService } from '../services/biometric';
import type { User, AuthTokens, LoginResponse } from '../services/api/auth';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Decode a JWT payload without verifying the signature.
 * Only used client-side for expiry checking — NOT a security check.
 */
function getTokenExpiry(token: string): number | null {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return typeof payload.exp === 'number' ? payload.exp : null;
  } catch {
    return null;
  }
}

/** Returns true if the token is expired or cannot be decoded. */
function isTokenExpired(token: string): boolean {
  const exp = getTokenExpiry(token);
  if (exp === null) return true;
  return Date.now() / 1000 >= exp;
}

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isProfileComplete: boolean;
  requiresMfa: boolean;
  mfaToken: string | null;
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  tokens: null,
  isLoading: true, // true while restoring session on mount
  isAuthenticated: false,
  isProfileComplete: false,
  requiresMfa: false,
  mfaToken: null,
  error: null,
};

// ---------------------------------------------------------------------------
// Actions
// ---------------------------------------------------------------------------

type AuthAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'LOGIN_SUCCESS'; payload: { user: User; tokens: AuthTokens; requiresMfa?: boolean; mfaToken?: string; isProfileComplete?: boolean } }
  | { type: 'MFA_VERIFIED'; payload: { tokens: AuthTokens; user: User; isProfileComplete?: boolean } }
  | { type: 'REGISTER_SUCCESS'; payload: { user: User } }
  | { type: 'PROFILE_COMPLETED' }
  | { type: 'RESTORE_SESSION'; payload: { user: User; tokens: AuthTokens; isProfileComplete?: boolean } }
  | { type: 'SET_ERROR'; payload: string }
  | { type: 'CLEAR_ERROR' }
  | { type: 'LOGOUT' };

// ---------------------------------------------------------------------------
// Reducer
// ---------------------------------------------------------------------------

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };

    case 'LOGIN_SUCCESS':
      return {
        ...state,
        user: action.payload.user,
        tokens: action.payload.tokens,
        isAuthenticated: !action.payload.requiresMfa,
        isProfileComplete: action.payload.isProfileComplete ?? action.payload.user.isProfileComplete ?? false,
        requiresMfa: action.payload.requiresMfa ?? false,
        mfaToken: action.payload.mfaToken ?? null,
        isLoading: false,
        error: null,
      };

    case 'MFA_VERIFIED':
      return {
        ...state,
        user: action.payload.user,
        tokens: action.payload.tokens,
        requiresMfa: false,
        mfaToken: null,
        isAuthenticated: true,
        isProfileComplete: action.payload.isProfileComplete ?? state.isProfileComplete,
        isLoading: false,
        error: null,
      };

    case 'REGISTER_SUCCESS':
      return { ...state, user: action.payload.user, isLoading: false, error: null };

    case 'PROFILE_COMPLETED':
      return { ...state, isProfileComplete: true, isLoading: false, error: null };

    case 'RESTORE_SESSION':
      return {
        ...state,
        user: action.payload.user,
        tokens: action.payload.tokens,
        isAuthenticated: true,
        isProfileComplete: action.payload.isProfileComplete ?? action.payload.user.isProfileComplete ?? false,
        isLoading: false,
        error: null,
      };

    case 'SET_ERROR':
      return { ...state, error: action.payload, isLoading: false };

    case 'CLEAR_ERROR':
      return { ...state, error: null };

    case 'LOGOUT':
      return { ...initialState, isLoading: false };

    default:
      return state;
  }
}

// ---------------------------------------------------------------------------
// Context type
// ---------------------------------------------------------------------------

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  biometricLogin: () => Promise<void>;
  register: (data: { email: string; password: string; userType: string; firstName?: string; lastName?: string }) => Promise<void>;
  verifyMFA: (code: string) => Promise<void>;
  markProfileComplete: () => void;
  logout: (options?: { clearBiometric?: boolean }) => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType>({
  ...initialState,
  login: async () => {},
  biometricLogin: async () => {},
  register: async () => {},
  verifyMFA: async () => {},
  markProfileComplete: () => {},
  logout: async () => {},
  clearError: () => {},
});

export const useAuth = (): AuthContextType => useContext(AuthContext);

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Ref to avoid stale mfaToken closure in verifyMFA
  const mfaTokenRef = useRef<string | null>(null);
  mfaTokenRef.current = state.mfaToken;

  // ----- Session Restoration ------------------------------------------------

  useEffect(() => {
    (async () => {
      try {
        const accessToken = await secureStorage.getItem(StorageKeys.ACCESS_TOKEN);
        const refreshToken = await secureStorage.getItem(StorageKeys.REFRESH_TOKEN);

        if (!accessToken || !refreshToken) {
          dispatch({ type: 'SET_LOADING', payload: false });
          return;
        }

        // FIX: validate token is not expired before restoring session.
        // Source trusted any stored token; expired tokens would fail on first API call.
        if (isTokenExpired(accessToken)) {
          // Try to refresh silently
          try {
            await authService.refreshToken();
          } catch {
            // Refresh token also expired — clear everything
            await secureStorage.removeItem(StorageKeys.ACCESS_TOKEN);
            await secureStorage.removeItem(StorageKeys.REFRESH_TOKEN);
            await appStorage.removeItem(StorageKeys.USER_DATA);
            dispatch({ type: 'SET_LOADING', payload: false });
            return;
          }
        }

        const stored = await appStorage.getObject<{ user: User }>(StorageKeys.USER_DATA);

        if (stored?.user) {
          const freshAccess = await secureStorage.getItem(StorageKeys.ACCESS_TOKEN);
          const freshRefresh = await secureStorage.getItem(StorageKeys.REFRESH_TOKEN);
          dispatch({
            type: 'RESTORE_SESSION',
            payload: {
              user: stored.user,
              tokens: {
                accessToken: freshAccess ?? accessToken,
                refreshToken: freshRefresh ?? refreshToken,
                expiresIn: 900,
              },
              isProfileComplete: stored.user.isProfileComplete,
            },
          });
        } else {
          await secureStorage.removeItem(StorageKeys.ACCESS_TOKEN);
          await secureStorage.removeItem(StorageKeys.REFRESH_TOKEN);
          dispatch({ type: 'SET_LOADING', payload: false });
        }
      } catch {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    })();
  }, []);

  // ----- Actions -----------------------------------------------------------

  const login = useCallback(async (email: string, password: string) => {
    dispatch({ type: 'CLEAR_ERROR' });
    try {
      const result = await authService.login(email, password);
      dispatch({
        type: 'LOGIN_SUCCESS',
        payload: {
          user: result.user,
          tokens: result.tokens,
          requiresMfa: result.requiresMfa,
          mfaToken: result.mfaToken,
          isProfileComplete: result.isProfileComplete,
        },
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed. Please try again.';
      dispatch({ type: 'SET_ERROR', payload: message });
      throw err;
    }
  }, []);

  const biometricLogin = useCallback(async () => {
    dispatch({ type: 'CLEAR_ERROR' });
    try {
      const credentials = await biometricService.getCredentials();
      if (!credentials) throw new Error('No biometric credentials found. Please log in with your password.');

      const authenticated = await biometricService.authenticate('Sign in to your account');
      if (!authenticated) throw new Error('Biometric authentication was cancelled.');

      const result = await authService.loginBiometric({
        deviceToken: credentials.deviceToken,
        deviceFingerprint: credentials.fingerprint,
      });

      dispatch({
        type: 'LOGIN_SUCCESS',
        payload: {
          user: result.user,
          tokens: result.tokens,
          isProfileComplete: result.isProfileComplete,
        },
      });
    } catch (err: unknown) {
      // FIX: check HTTP status codes rather than string-matching error messages
      const isRevoked =
        (err as { response?: { status?: number } })?.response?.status === 401 ||
        (err as { response?: { status?: number } })?.response?.status === 403;

      if (isRevoked) {
        await biometricService.clearCredentials();
      }

      const message = err instanceof Error ? err.message : 'Biometric login failed.';
      dispatch({ type: 'SET_ERROR', payload: message });
      throw err;
    }
  }, []);

  const register = useCallback(async (data: Parameters<typeof authService.register>[0]) => {
    dispatch({ type: 'CLEAR_ERROR' });
    try {
      const result = await authService.register(data);
      dispatch({ type: 'REGISTER_SUCCESS', payload: { user: result.user } });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Registration failed. Please try again.';
      dispatch({ type: 'SET_ERROR', payload: message });
      throw err;
    }
  }, []);

  const verifyMFA = useCallback(async (code: string) => {
    dispatch({ type: 'CLEAR_ERROR' });
    try {
      // FIX: use ref to avoid stale mfaToken from closure
      const mfaToken = mfaTokenRef.current;
      if (!mfaToken) throw new Error('MFA session expired. Please log in again.');

      const result = await authService.verifyMFA(code, mfaToken);
      dispatch({
        type: 'MFA_VERIFIED',
        payload: {
          tokens: result.tokens,
          user: result.user,
          isProfileComplete: result.isProfileComplete,
        },
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'MFA verification failed. Please try again.';
      dispatch({ type: 'SET_ERROR', payload: message });
      throw err;
    }
  }, []); // no deps needed — reads mfaToken via ref

  const markProfileComplete = useCallback(() => {
    dispatch({ type: 'PROFILE_COMPLETED' });
  }, []);

  const logout = useCallback(async (options?: { clearBiometric?: boolean }) => {
    try {
      await authService.logout(options);
    } finally {
      dispatch({ type: 'LOGOUT' });
    }
  }, []);

  const clearError = useCallback(() => {
    dispatch({ type: 'CLEAR_ERROR' });
  }, []);

  // ----- Memoised value ---------------------------------------------------

  const value = useMemo<AuthContextType>(
    () => ({
      ...state,
      login,
      biometricLogin,
      register,
      verifyMFA,
      markProfileComplete,
      logout,
      clearError,
    }),
    [state, login, biometricLogin, register, verifyMFA, markProfileComplete, logout, clearError],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
