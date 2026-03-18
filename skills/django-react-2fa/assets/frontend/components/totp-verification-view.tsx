/**
 * TOTP Login Verification — Algorithm & State Machine
 *
 * Shown during login when otp_channel === "totp". Can be a dialog view,
 * a full page, or an inline panel — the state machine is the same.
 *
 * Three verification tiers with progressive fallback:
 *
 * ┌────────────┐    "use backup"   ┌──────────────┐
 * │   TOTP     │ ───────────────→  │ Backup Code  │
 * │ (default)  │ ←─── "back" ───── │   Entry      │
 * └────────────┘                   └──────────────┘
 *       │
 *       │ "send to email/phone"
 *       ▼
 * ┌──────────────────┐    "send to email"    ┌──────────────────┐
 * │ Fallback Sent    │ ◄──────────────────── │ Fallback Sent    │
 * │ (phone channel)  │ ────────────────────→ │ (email channel)  │
 * └──────────────────┘    "send to phone"    └──────────────────┘
 *
 * STATE:
 *   viewMode: "totp" | "backup" | "fallback-sent"
 *   otpValue: string (6 digits)
 *   fallbackChannel: "phone" | "email" | null  (which channel code was sent to)
 *   phoneMasked: string | null  (e.g. "***-*55-1234")
 *   hasPhone: boolean  (whether channel switching is available)
 *
 * PROPS:
 *   loginToken: string  — from login response
 *   onBack: () => void  — return to login form
 *   onSuccess: () => void  — login complete, close dialog
 *
 * ── TOTP VIEW (default) ──────────────────────────────────────────────────
 *
 *   - 6-digit OTP input, auto-submit on 6 digits
 *   - "Verify & Sign In" button
 *   - On submit: POST /auth/login/verify-otp/ { login_token, otp }
 *     - Success: call onSuccess()
 *     - Failure: show error toast, clear input
 *   - Links below:
 *     1. "Can't access your authenticator app?" → "Use a backup code" → viewMode = "backup"
 *     2. "Lost your backup codes too?" → "Send code to email or phone"
 *        → call handleSendFallbackOTP() → viewMode = "fallback-sent"
 *
 * ── BACKUP CODE VIEW ─────────────────────────────────────────────────────
 *
 *   - Renders BackupCodeEntry (see backup-code-entry.tsx)
 *   - Back button → viewMode = "totp"
 *
 * ── FALLBACK SENT VIEW ──────────────────────────────────────────────────
 *
 *   - Shows icon based on channel (phone icon vs email icon)
 *   - Title: "Verify Your Identity"
 *   - Description: "We sent a 6-digit code to your {channelLabel}"
 *     - channelLabel = phone channel ? "phone {phoneMasked}" : "email"
 *   - 6-digit OTP input, same verify logic as TOTP view
 *   - STAGING HINT (optional):
 *     If your app has a staging/bypass config flag AND channel is phone AND phoneMasked exists:
 *       Show: "Staging: use the last 6 digits of your phone number ({phoneMasked})"
 *       in amber/warning color
 *   - "Didn't receive the code?" → "Resend code"
 *     → call handleSendFallbackOTP(currentChannel)
 *   - CHANNEL SWITCHING (only when hasPhone = true):
 *     If current channel is phone: show "Or send to email instead"
 *     If current channel is email: show "Or send to phone instead"
 *     → call handleSendFallbackOTP("email") or ("phone")
 *
 * ── SEND FALLBACK OTP ────────────────────────────────────────────────────
 *
 *   handleSendFallbackOTP(channel?: "phone" | "email"):
 *     1. Call useLoginResendOTP({ login_token, channel })
 *     2. On success:
 *        - Set fallbackChannel = response.data.otp_channel
 *        - Set phoneMasked = response.data.phone_masked
 *        - Set hasPhone = response.data.has_phone
 *        - Set viewMode = "fallback-sent"
 *        - Clear otpValue
 *        - Show success toast
 *     3. On error: show error toast
 *
 * HOOKS USED:
 *   - useLoginVerifyOTP() → POST /auth/login/verify-otp/
 *   - useLoginResendOTP() → POST /auth/login/resend-otp/
 *
 * IMPORTANT: The login resend endpoint uses LoginOTPResendThrottle (6/hour).
 * Show a clear error if 429 is returned (user has exceeded resend limit).
 */
