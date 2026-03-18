/**
 * Backup Code Entry — Algorithm
 *
 * Login-time backup code input. Shown when user clicks "Use a backup code"
 * from the TOTP verification view.
 *
 * PROPS:
 *   loginToken: string
 *   onBack: () => void  — return to TOTP view
 *   onSuccess: () => void  — login complete
 *
 * STATE:
 *   code: string  — auto-formatted backup code
 *
 * INPUT FORMATTING:
 *   On every keystroke:
 *     1. Strip non-alphanumeric characters: value.replace(/[^a-zA-Z0-9]/g, "")
 *     2. Uppercase
 *     3. Limit to 10 raw characters
 *     4. Auto-insert dash after 5th character:
 *        length > 5 → `${cleaned.slice(0, 5)}-${cleaned.slice(5)}`
 *        length <= 5 → cleaned (no dash yet)
 *
 * VALIDATION:
 *   Regex: /^[A-Z0-9]{5}-[A-Z0-9]{5}$/
 *   Submit button disabled until valid
 *
 * SUBMIT:
 *   Call POST /auth/login/verify-otp/ { login_token, otp: code }
 *   (The backend's verify_login_otp handles backup codes for TOTP users)
 *   - Success: call onSuccess()
 *   - Failure: show error toast, clear code
 *
 * UI ELEMENTS:
 *   - Back button → onBack()
 *   - Icon (key icon)
 *   - Title: "Enter Backup Code"
 *   - Description: "Enter one of your backup codes. Each code can only be used once."
 *   - Text input: placeholder "XXXXX-XXXXX", monospace, centered, tracking-wider
 *   - Submit button: "Verify & Sign In" (disabled when invalid or pending)
 *   - Link: "Have your authenticator app?" → "Use authenticator code" → onBack()
 *
 * HOOKS USED:
 *   - useLoginVerifyOTP() → same endpoint as TOTP verify
 */
