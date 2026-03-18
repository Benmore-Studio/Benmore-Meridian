/**
 * Backup Codes Display — Algorithm
 *
 * A reusable display for backup codes. Used in two contexts:
 *   1. After TOTP enrollment (step 3 of setup wizard)
 *   2. After regenerating backup codes (from settings)
 *
 * PROPS:
 *   codes: string[]  — array of "XXXXX-XXXXX" formatted codes
 *   onConfirm: (confirmed: boolean) => void  — parent gates "Done" on this
 *   appName?: string  — used in download file header (default: "MyApp")
 *
 * LAYOUT:
 *   - Grid of codes (2 columns works well, each code in monospace)
 *   - "Copy All" button
 *   - "Download .txt" button
 *   - Confirmation checkbox
 *
 * COPY ALGORITHM:
 *   navigator.clipboard.writeText(codes.join("\n"))
 *   Show success/error toast
 *
 * DOWNLOAD ALGORITHM:
 *   1. Build plain text content:
 *      "{appName} Two-Factor Authentication Backup Codes"
 *      "================================================"
 *      "Store these codes in a safe place."
 *      "Each code can only be used once."
 *      ""
 *      ...codes (one per line)
 *      ""
 *      "Generated: {current date}"
 *
 *   2. Create Blob with type "text/plain"
 *   3. Create object URL, create <a> element, set download filename, click, cleanup
 *      Filename: "{appname-lowercase}-backup-codes.txt"
 *
 * CONFIRMATION:
 *   - Checkbox: "I have saved these backup codes in a safe place"
 *   - On change: call onConfirm(checked)
 *   - Parent component should disable its "Done"/"Close" button until confirmed
 *   - Warning styling (amber/yellow border) to draw attention
 */
