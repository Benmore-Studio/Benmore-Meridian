/**
 * TOTP 2FA TypeScript Types
 *
 * Types for all TOTP operations: setup, enable, disable, backup codes,
 * login verification, and login resend with channel switching.
 */

// ── TOTP Management (Settings Page) ─────────────────────────────────────────

export interface ITOTPSetupResponse {
  secret: string
  provisioning_uri: string
  qr_code_uri: string // base64 data URI for QR code image
}

export interface ITOTPEnableRequest {
  code: string // 6-digit code from authenticator app
}

export interface ITOTPEnableResponse {
  backup_codes: string[] // 10 plaintext codes in XXXXX-XXXXX format
}

export interface ITOTPDisableRequest {
  code: string // 6-digit TOTP code OR backup code (XXXXX-XXXXX)
}

export interface ITOTPRegenerateRequest {
  code: string // 6-digit TOTP code (backup codes NOT accepted)
}

export interface ITOTPRegenerateResponse {
  backup_codes: string[]
}

// ── Login OTP Types ─────────────────────────────────────────────────────────

/** Returned by POST /auth/login/ when OTP is required */
export interface ILoginOTPResponse {
  otp_required: true
  login_token: string
  otp_channel: "phone" | "email" | "totp"
  phone_masked: string | null
}

/** Sent to POST /auth/login/verify-otp/ */
export interface ILoginVerifyOTPRequest {
  login_token: string
  otp: string
}

/** Sent to POST /auth/login/resend-otp/ */
export interface ILoginResendOTPRequest {
  login_token: string
  channel?: "phone" | "email" // optional: force specific channel
}

/** Returned by POST /auth/login/resend-otp/ */
export interface ILoginResendOTPResponse {
  otp_channel: "phone" | "email"
  phone_masked: string | null
  has_phone: boolean // true if user has a phone number (enables channel switching)
}

// ── User type extension ─────────────────────────────────────────────────────

/**
 * Add totp_enabled to your IUser interface:
 *
 * export interface IUser {
 *   id: number
 *   email: string
 *   totp_enabled: boolean
 *   // ... other fields
 * }
 */
