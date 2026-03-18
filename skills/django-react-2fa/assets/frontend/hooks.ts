/**
 * TOTP 2FA React Query Hooks
 *
 * Mutations for TOTP setup, enable, disable, and backup code regeneration.
 * Auto-updates auth store on enable/disable so the UI reflects the new state.
 *
 * Adapt imports:
 * - QUERY_KEYS: Your query key factory
 * - useAuthStore: Your Zustand auth store
 * - Service functions: From ./service
 */

import { useMutation, useQueryClient } from "@tanstack/react-query"
import { QUERY_KEYS } from "@/query/query-keys" // adapt path
import {
  postTOTPSetup,
  postTOTPEnable,
  postTOTPDisable,
  postTOTPRegenerateBackupCodes,
  postLoginResendOTP,
} from "./service"
import { useAuthStore } from "@/store/auth/auth.store" // adapt path

/**
 * Start TOTP enrollment — returns QR code, secret, provisioning URI.
 * Call this when the setup modal opens.
 */
export function useSetupTOTP() {
  return useMutation({
    mutationKey: QUERY_KEYS.totpSetup(),
    mutationFn: postTOTPSetup,
  })
}

/**
 * Confirm TOTP enrollment with a 6-digit code.
 * On success: updates auth store (totp_enabled=true) and invalidates profile cache.
 */
export function useEnableTOTP() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationKey: QUERY_KEYS.totpEnable(),
    mutationFn: postTOTPEnable,
    onSuccess: (data) => {
      if (data.ok) {
        const { updateUserAuth, userAuth } = useAuthStore.getState()
        updateUserAuth({ totp_enabled: true })
        if (userAuth?.id) {
          queryClient.invalidateQueries({ queryKey: QUERY_KEYS.getUserProfile(userAuth.id) })
        }
      }
    },
  })
}

/**
 * Disable TOTP with authenticator code or backup code.
 * On success: updates auth store (totp_enabled=false) and invalidates profile cache.
 */
export function useDisableTOTP() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationKey: QUERY_KEYS.totpDisable(),
    mutationFn: postTOTPDisable,
    onSuccess: (data) => {
      if (data.ok) {
        const { updateUserAuth, userAuth } = useAuthStore.getState()
        updateUserAuth({ totp_enabled: false })
        if (userAuth?.id) {
          queryClient.invalidateQueries({ queryKey: QUERY_KEYS.getUserProfile(userAuth.id) })
        }
      }
    },
  })
}

/** Regenerate backup codes. Requires a live TOTP code. */
export function useRegenerateBackupCodes() {
  return useMutation({
    mutationKey: QUERY_KEYS.totpRegenerateBackupCodes(),
    mutationFn: postTOTPRegenerateBackupCodes,
  })
}

/** Resend login OTP with optional channel preference (phone/email). */
export function useLoginResendOTP() {
  return useMutation({
    mutationKey: QUERY_KEYS.loginResendOTP(),
    mutationFn: postLoginResendOTP,
  })
}

/**
 * Query keys to add to your QUERY_KEYS factory:
 *
 * totpSetup: () => ["totpSetup"],
 * totpEnable: () => ["totpEnable"],
 * totpDisable: () => ["totpDisable"],
 * totpRegenerateBackupCodes: () => ["totpRegenerateBackupCodes"],
 * loginResendOTP: () => ["loginResendOTP"],
 */
