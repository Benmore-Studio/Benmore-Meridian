/**
 * Security Settings Card — Algorithm & State Machine
 *
 * The 2FA management panel for the user's settings/security page.
 * Can be a card, a section, a full page — the logic is identical.
 *
 * READS FROM AUTH STORE:
 *   userAuth.totp_enabled: boolean
 *
 * TWO STATES:
 *
 * ┌──────────────────────────────────────┐
 * │ totp_enabled = false                 │
 * │                                      │
 * │ "Add extra security with 2FA..."     │
 * │ [Enable 2FA] button                  │
 * │   → opens SetupTOTPModal/wizard      │
 * └──────────────────────────────────────┘
 *
 * ┌──────────────────────────────────────┐
 * │ totp_enabled = true                  │
 * │                                      │
 * │ ✅ Enabled badge                     │
 * │ "2FA is active on your account..."   │
 * │ [Regenerate Backup Codes] button     │
 * │ [Disable 2FA] button (destructive)   │
 * └──────────────────────────────────────┘
 *
 * ENABLE FLOW:
 *   1. Guard: if totp_enabled, show error toast and return
 *   2. Open the setup wizard (SetupTOTPModal or navigate to setup page)
 *   3. Wizard handles the full flow internally
 *   4. On completion, useEnableTOTP hook auto-updates auth store
 *
 * DISABLE FLOW:
 *   1. Open confirmation prompt (requires TOTP code OR backup code)
 *   2. User enters code
 *   3. Call useDisableTOTP({ code })
 *   4. Success: close prompt, show success toast
 *   5. Hook auto-updates auth store: totp_enabled = false
 *
 * REGENERATE FLOW:
 *   1. Open confirmation prompt (requires TOTP code ONLY — backup codes NOT accepted)
 *   2. User enters code
 *   3. Call useRegenerateBackupCodes({ code })
 *   4. Success: close prompt, show new backup codes display
 *   5. New codes display blocks close until user confirms they saved codes
 *   6. Done → close codes display
 *
 * CONFIRMATION PROMPT:
 *   Reusable component that accepts:
 *     - title, description strings
 *     - onConfirm(code: string) callback
 *     - isPending boolean for loading state
 *     - allowBackupCode boolean (true for disable, false for regenerate)
 *   Supports two input modes:
 *     - 6-digit OTP input (auto-submits on 6 digits)
 *     - Backup code input (XXXXX-XXXXX format, manual submit)
 *   Toggle between modes with a text link
 *
 * BACKUP CODE INPUT FORMATTING:
 *   - Strip non-alphanumeric, uppercase
 *   - Max 10 chars raw
 *   - Auto-insert dash after 5th char: "ABCDE" → "ABCDE", "ABCDEF" → "ABCDE-F"
 *   - Validate with regex: /^[A-Z0-9]{5}-[A-Z0-9]{5}$/
 *
 * HOOKS USED:
 *   - useDisableTOTP() → auto-updates auth store on success
 *   - useRegenerateBackupCodes()
 */
