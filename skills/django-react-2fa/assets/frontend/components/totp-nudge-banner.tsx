/**
 * TOTP Nudge Banner — Algorithm
 *
 * Dismissible banner prompting authenticated users to enable 2FA.
 * Can be a banner, toast, card, or any UI element — logic is the same.
 *
 * VISIBILITY RULES (all must be true to show):
 *   1. User is authenticated (userAuth exists)
 *   2. User has NOT enabled TOTP (userAuth.totp_enabled === false)
 *   3. User has NOT dismissed the banner (localStorage check)
 *
 * Default to HIDDEN on mount to avoid flash of content before
 * localStorage is read (SSR/hydration safe).
 *
 * STATE:
 *   dismissed: boolean (default: true — hidden until localStorage confirms otherwise)
 *
 * ON MOUNT:
 *   Read localStorage.getItem(storageKey)
 *   If value === "true" → remain dismissed
 *   If value is null/anything else → show banner (set dismissed = false)
 *
 * DISMISS:
 *   Set dismissed = true
 *   localStorage.setItem(storageKey, "true")
 *
 * CONFIGURABLE:
 *   settingsUrl: string — where "Set up now" navigates to
 *     Default: "/settings?tab=privacy" (or wherever your 2FA settings live)
 *     TIP: Use a query parameter so the settings page can auto-select
 *     the security/privacy tab on mount
 *   storageKey: string — localStorage key (default: "totp_nudge_dismissed")
 *
 * CONTENT:
 *   - Shield icon
 *   - "Secure your account — Add an authenticator app for extra protection."
 *   - "Set up now" link → navigates to settingsUrl
 *   - Dismiss (X) button
 *
 * PLACEMENT:
 *   Typically on the dashboard/home page, above the main content.
 *   Add bottom margin (e.g., mb-8) so it doesn't stick to the content below.
 *
 * ANIMATION (optional):
 *   Fade in on show, fade out + slide up on dismiss.
 *
 * READS FROM:
 *   - Auth store: userAuth, userAuth.totp_enabled
 *   - localStorage: storageKey
 */
