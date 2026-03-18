/**
 * TOTP Code Confirm — Algorithm
 *
 * Reusable confirmation prompt that requires a TOTP code (and optionally backup code)
 * before allowing a sensitive action. Used by SecuritySettingsCard for:
 *   - Disabling 2FA (allowBackupCode = true)
 *   - Regenerating backup codes (allowBackupCode = false)
 *
 * Can be implemented as a dialog, alert, inline form, or separate page.
 *
 * PROPS:
 *   open: boolean
 *   onOpenChange: (open: boolean) => void
 *   title: string
 *   description: string
 *   onConfirm: (code: string) => void  — called with the entered code
 *   isPending: boolean  — disables inputs while API call is in flight
 *   allowBackupCode?: boolean (default false)
 *
 * STATE:
 *   otpValue: string (6 digits)
 *   backupCode: string (auto-formatted XXXXX-XXXXX)
 *   useBackupCode: boolean (toggle between input modes)
 *
 * OTP MODE (default):
 *   - 6-digit input
 *   - Auto-submit when 6 digits entered: onConfirm(otpValue)
 *   - Also has explicit confirm button
 *   - If allowBackupCode: show "Use a backup code instead" link
 *     → clears otpValue, sets useBackupCode = true
 *
 * BACKUP CODE MODE:
 *   - Text input with XXXXX-XXXXX formatting
 *   - Formatting algorithm:
 *     1. Strip non-alphanumeric chars
 *     2. Uppercase
 *     3. Limit to 10 chars
 *     4. Insert dash after 5th char
 *   - Validation: /^[A-Z0-9]{5}-[A-Z0-9]{5}$/
 *   - "Use authenticator code instead" link → toggle back
 *
 * CONFIRM LOGIC:
 *   canConfirm = useBackupCode ? isBackupCodeValid : otpValue.length === 6
 *   On confirm button click: onConfirm(useBackupCode ? backupCode : otpValue)
 *
 * RESET:
 *   When closed (open becomes false), clear all state after 200ms delay
 */
