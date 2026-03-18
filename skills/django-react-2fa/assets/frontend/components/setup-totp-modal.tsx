/**
 * TOTP Setup Flow — Algorithm & State Machine
 *
 * This is a 3-step enrollment wizard. Can be implemented as a modal, a full page,
 * a multi-step form, or a side panel — the state machine is the same.
 *
 * ┌─────────┐    auto-fire     ┌──────────┐   verify code   ┌──────────────┐
 * │ Step 1  │ ──────────────→  │ Step 2   │ ─────────────→  │   Step 3     │
 * │ Scan QR │  POST /setup/    │ Verify   │  POST /enable/  │ Backup Codes │
 * └─────────┘                  └──────────┘                  └──────────────┘
 *       ↑                          │                               │
 *       └──── Back button ─────────┘                               │
 *                                                    user confirms saved → Done
 *
 * STATE:
 *   step: 1 | 2 | 3
 *   otpValue: string (6 digits)
 *   backupCodes: string[] (received from enable response)
 *   backupConfirmed: boolean (user checked "I saved these")
 *   verifyError: string
 *   qrData: { secret, provisioning_uri, qr_code_uri } | null
 *
 * STEP 1 — Scan QR Code:
 *   - On mount/open: call POST /auth/totp/setup/
 *   - Show loading spinner while pending
 *   - Display QR code image from qr_code_uri (base64 data URI)
 *   - Provide expandable "Can't scan?" section showing the plain secret
 *   - Copy button for the secret
 *   - "Next" button → step 2
 *
 * STEP 2 — Verify Code:
 *   - 6-digit OTP input
 *   - Auto-submit when 6 digits entered (no button click needed)
 *   - Also provide explicit "Verify & Enable" button
 *   - On submit: POST /auth/totp/enable/ { code }
 *   - Success: save backup_codes from response, move to step 3
 *   - Failure: show error, clear input
 *   - Back button → step 1 (don't re-call setup, reuse existing qrData)
 *
 * STEP 3 — Backup Codes:
 *   - Display codes in a grid (2 columns)
 *   - "Copy All" button: navigator.clipboard.writeText(codes.join("\n"))
 *   - "Download .txt" button: create Blob, trigger download
 *   - Checkbox: "I have saved these backup codes in a safe place"
 *   - "Done" button: only enabled when checkbox is checked
 *   - PREVENT closing (modal dismiss, outside click, escape) until confirmed
 *
 * RESET:
 *   - When the wizard closes/unmounts, reset all state after a short delay (200ms)
 *     to allow close animation to complete
 *
 * HOOKS USED:
 *   - useSetupTOTP() → mutate (POST /auth/totp/setup/)
 *   - useEnableTOTP() → mutate (POST /auth/totp/enable/)
 *     - This hook auto-updates auth store: totp_enabled = true
 */
