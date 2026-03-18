/**
 * TOTP 2FA API Service
 *
 * API functions for all TOTP operations.
 * Adapt the import path for your axios instance and response types.
 */

import type { IGenericApiResponse } from "@/query/configs/interface" // adapt path
import type {
  ITOTPSetupResponse,
  ITOTPEnableRequest,
  ITOTPEnableResponse,
  ITOTPDisableRequest,
  ITOTPRegenerateRequest,
  ITOTPRegenerateResponse,
  ILoginResendOTPRequest,
  ILoginResendOTPResponse,
} from "./types"
import axiosInstance from "@/configs/axios-instance" // adapt path

// ── TOTP Management ─────────────────────────────────────────────────────────

/** Start TOTP enrollment — returns QR code and secret */
export const postTOTPSetup = async (): Promise<IGenericApiResponse<ITOTPSetupResponse>> => {
  const response = await axiosInstance.post("/auth/totp/setup")
  return response.data
}

/** Confirm TOTP enrollment with authenticator code — returns backup codes */
export const postTOTPEnable = async (
  data: ITOTPEnableRequest
): Promise<IGenericApiResponse<ITOTPEnableResponse>> => {
  const response = await axiosInstance.post("/auth/totp/enable", data)
  return response.data
}

/** Disable TOTP with authenticator code or backup code */
export const postTOTPDisable = async (
  data: ITOTPDisableRequest
): Promise<IGenericApiResponse<null>> => {
  const response = await axiosInstance.post("/auth/totp/disable", data)
  return response.data
}

/** Regenerate backup codes — requires live TOTP code */
export const postTOTPRegenerateBackupCodes = async (
  data: ITOTPRegenerateRequest
): Promise<IGenericApiResponse<ITOTPRegenerateResponse>> => {
  const response = await axiosInstance.post("/auth/totp/backup-codes/regenerate", data)
  return response.data
}

// ── Login Resend (with channel switching) ───────────────────────────────────

/** Resend login OTP with optional channel preference */
export const postLoginResendOTP = async ({
  login_token,
  channel,
}: ILoginResendOTPRequest): Promise<IGenericApiResponse<ILoginResendOTPResponse>> => {
  const response = await axiosInstance.post("/auth/login/resend-otp", {
    login_token,
    ...(channel && { channel }),
  })
  return response.data
}
