---
name: apple-release
description: Pre-flight checklist for Apple App Store submissions of the Cattle Logic mobile app. Use BEFORE running `eas submit -p ios` or uploading a build to App Store Connect. Catches every Apple rejection class this app has historically hit (2.3.10 screenshots, 3.1.1 external-payment disclosure, 5.1.1(ii) purpose strings, 5.1.1(v) account deletion, 5.1.2 data-use declarations). Verifies `mobile/app.json`, `mobile/eas.json`, version bumps, in-app disclosure modals, and the account-deletion path before you ship.
---

# /apple-release

Use this skill BEFORE every iOS App Store submission. It is a pre-flight checklist — work through each step in order. Several steps run grep/file checks the agent can verify automatically; others require user judgement on App Store Connect state.

**Project**: Cattle Logic (`com.cattlemanagement.mobile`, ASC app id `6762011755`)
**EAS project**: `dfc63cd4-060b-4e87-aa04-c6d33b8e3d35` owned by `ricbenmore`
**Apple Team**: `248U39D5G7` · Apple ID: `cattlelogic.app@gmail.com`

## How this skill works

Walk every step. After each one, mark `[OK]` / `[FIX NEEDED]` and surface remaining work to the user. **Do not skip steps** — Apple's rejection patterns are non-obvious; the entire point of this skill is to catch them all in one pass.

If you find a regression, fix it, bump the iOS `buildNumber`, and re-run this skill from Step 1. Build numbers must monotonically increase.

When a step says "GREP", run the literal command in `Bash`. When a step says "ASK USER", surface the question with the exact wording shown.

---

## Step 1 — Version + Build Numbers

**Why**: Apple rejects duplicate `CFBundleVersion`. The build number must be strictly greater than every previous submission to App Store Connect (including ones that were rejected or removed).

GREP:
```bash
cat mobile/app.json | python3 -c "import json,sys; d=json.load(sys.stdin); print('iOS version=%s buildNumber=%s' % (d['expo']['version'], d['expo']['ios']['buildNumber'])); print('Android versionCode=%s' % d['expo']['android']['versionCode']); print('runtimeVersion=%s' % d['expo'].get('runtimeVersion'))"
cat mobile/package.json | python3 -c "import json,sys; print('package.json version=%s' % json.load(sys.stdin)['version'])"
```

CHECK:
- `expo.ios.buildNumber` > every previously-submitted build (check ASC: https://appstoreconnect.apple.com/apps/6762011755/distribution/ios)
- `expo.android.versionCode` > every previously-submitted versionCode
- `expo.version` matches `mobile/package.json` `version`
- `runtimeVersion` policy: bump it ONLY when this build adds/removes/changes native modules, permissions, or Info.plist keys. JS-only changes leave it pinned (so previous installs can OTA-update).

ASK USER if you aren't sure of the last submitted build number: "What was the last build number on App Store Connect for app id 6762011755? I need to confirm `expo.ios.buildNumber` exceeds it."

---

## Step 2 — Privacy Purpose Strings (Guideline 5.1.1(ii))

**Why**: Apple rejected an earlier build for vague camera/photo-library purpose strings. Every iOS permission must explain WHAT the app does + a CONCRETE EXAMPLE.

**Apple's failure mode**: "App needs camera access" or "Cattle Logic uses the camera" — both are too vague.
**Apple's pass mode**: "Cattle Logic uses the camera so you can document cattle in your operation — for example, photographing arrival receipts..."

GREP:
```bash
python3 -c "
import json
d = json.load(open('mobile/app.json'))
plist = d['expo']['ios'].get('infoPlist', {})
required = [
    'NSCameraUsageDescription',
    'NSMicrophoneUsageDescription',
    'NSPhotoLibraryUsageDescription',
    'NSPhotoLibraryAddUsageDescription',
]
for k in required:
    v = plist.get(k, '')
    ok = 'for example' in v.lower() and len(v) > 80
    print(('OK   ' if ok else 'FAIL '), k, '->', v[:80] + ('...' if len(v) > 80 else ''))
"
```

CHECK every required key exists AND the value contains the literal phrase "for example" AND is at least 80 characters. If `expo.ios.infoPlist` block doesn't exist at all, you must add it explicitly — relying on plugin-injected defaults from `expo-camera` / `expo-image-picker` is fragile.

CONDITIONAL (only if these features are actually used — grep `mobile/src/` first):
- `NSLocationWhenInUseUsageDescription` — required if any screen calls `expo-location`
- `NSContactsUsageDescription` — required if any screen reads contacts
- `NSCalendarsUsageDescription` — required if any screen reads calendar
- `NSBluetoothAlwaysUsageDescription` — required if BLE is used

**DO NOT include** `NSFaceIDUsageDescription` — this app does not use Face ID. Apple rejects builds with unused permission strings as misleading. Same rule applies to any permission key whose feature isn't actually wired.

If a required string is missing or vague, ASK USER for the WHAT + EXAMPLE wording. Default template:
> "Cattle Logic uses the [resource] so you can [user task] — for example, [concrete cattle-feedlot example]."

---

## Step 3 — Account Deletion (Guideline 5.1.1(v))

**Why**: Apple rejected v1.0.0 for missing in-app account deletion. Apps that allow account creation MUST allow account deletion (not deactivation).

GREP:
```bash
grep -n "Delete Account\|deleteAccount" mobile/app/\(settings\)/profile.js | head -10
grep -n "delete_account" backend/accounts/views.py | head -5
grep -n "delete-account" backend/subscriptions/middleware.py | head -3
```

CHECK:
- The mobile delete button is unconditionally visible on the profile screen (not gated behind subscription state, owner role, or any other conditional that could hide it during Apple review).
- The button opens a confirmation modal with password entry (defense against fat-finger deletes).
- The backend `delete_account` endpoint is in `SubscriptionMiddleware.EXACT_EXEMPT_PATHS` so it works even when the subscription is suspended/cancelled.
- The endpoint cancels active Stripe subscriptions + detaches payment methods BEFORE anonymizing PII (prevents orphaned charges). See `backend/accounts/views.py:_cancel_active_subscriptions_for_user`.
- Password is cleared from React state in `finally` block (defense-in-depth — no plaintext lingers in memory after the request).
- Rate limit: `DeleteAccountThrottle` at 3/hour blocks brute-force.

ASK USER (manual verification — Apple wants a video):
> "Have you recorded a screen recording on a physical iOS device showing: (1) signing in with the demo account, (2) navigating to Profile → Delete Account, (3) the full deletion flow from initiation to confirmation? Apple requires this in the App Review Information Notes field."

---

## Step 4 — External Payment Disclosure (Guideline 3.1.1)

**Why**: Apple rejected v1.8.0 for opening the external billing portal without the StoreKit External Purchase Link Entitlement disclosure modal. Without the modal, Apple treats the link as "accessing paid content outside the app without IAP" — automatic 3.1.1 rejection.

GREP:
```bash
grep -rn "openBrowserAsync\|Linking.openURL" mobile/src/ mobile/app/ | grep -iE "billing|account|portal|stripe|subscription" | head -20
grep -rn "APPLE_EXTERNAL_LINK_DISCLOSURE\|responsible for managing" mobile/ | head -10
```

CHECK every external link to a billing/subscription/payment URL:
- Wrapped in `Alert.alert` showing the Apple-mandated disclosure copy (verbatim wording — do not paraphrase):
  > "You're about to visit cattlelogicapp.com. Cattle Logic LLC is responsible for managing all transactions made on its platform. Apple is not responsible for the privacy or security of transactions made with this developer."
- Two buttons: "Stay in App" (cancel style) and "Continue".
- Opens via `expo-web-browser` (`WebBrowser.openBrowserAsync`) — this is SFSafariViewController on iOS. Never an in-app `<WebView>`.

GREP for forbidden CTAs (Apple flags in-app purchase wording even with disclosure):
```bash
grep -rn -iE "subscribe now|buy now|upgrade now|purchase|in-app purchase" mobile/app/ mobile/src/components/ | grep -v ".test.js" | head -10
```
None of these strings should appear in user-visible UI. Only "Manage on the website" / "Manage subscription" wording is allowed (those are management, not purchase, CTAs).

ASK USER (manual — Apple Developer step):
> "Has the StoreKit External Purchase Link Entitlement been requested + approved at https://developer.apple.com/contact/request/storekit-external-purchase-link/ for app id 6762011755? Submission is allowed only after Apple grants the entitlement (separate from app review)."

---

## Step 5 — Data Use & Sharing Declarations (Guideline 5.1.2)

**Why**: This project has historically been rejected for misaligned App Privacy declarations. App Store Connect's "App Privacy" section must declare every data type the app actually collects — Apple cross-checks against the binary.

GREP for actual data collection:
```bash
# Identify PII and telemetry the app sends
grep -rn -iE "email|phone_number|first_name|last_name|firstName|lastName" mobile/src/services/ | grep -iE "post|put|patch|register|signup|profile|auth" | head -20
# Push tokens
grep -rn "device_token\|fcm_token\|expo-notifications" mobile/src/services/ | head -10
# Photos / videos uploaded
grep -rn "ImagePicker\|FormData.*photo\|FormData.*video\|cattle_media\|file_url" mobile/src/services/ | head -10
# Sentry — telemetry collection
grep -n "Sentry.init" mobile/app/_layout.js | head -3
# Privacy policy URL source of truth
grep -n "PRIVACY\|privacy" mobile/src/constants/legal.js
```

DECLARED-VS-ACTUAL CHECKLIST. Confirm each row in App Store Connect → App Privacy:

| Data type | Collected? | Linked to user? | Used for tracking? | App Privacy declaration required |
|---|---|---|---|---|
| Email | YES (signup, login) | YES | NO | Identifiers → Email |
| Name | YES (profile) | YES | NO | Contact Info → Name |
| Phone | YES (profile, optional) | YES | NO | Contact Info → Phone |
| Photos / Videos | YES (cattle media uploads) | YES | NO | User Content → Photos or Videos |
| Push token | YES (FCM device token) | YES | NO | Identifiers → Device ID |
| Crash data | YES (Sentry) | NO (anonymized) | NO | Diagnostics → Crash Data |
| Performance data | YES (Sentry traces) | NO | NO | Diagnostics → Performance Data |

ASK USER (manual verification):
> "Visit https://appstoreconnect.apple.com/apps/6762011755/distribution/privacy and confirm every row in the table above is declared with the listed linkage and tracking flags. Apple cross-checks this against the binary — under-declaration is the most common 5.1.2 rejection cause."

PRIVACY POLICY URL CHECK:
```bash
grep -n "PRIVACY\|TERMS" mobile/src/constants/legal.js
```
Confirm the Iubenda-hosted Privacy Policy URL set in App Store Connect → App Information → "Privacy Policy URL" matches `LEGAL_URLS.PRIVACY` from this file.

FUTURE WATCH ITEM: If you ever add `react-native-tracking-transparency` or any AppTrackingTransparency call, you must add `NSUserTrackingUsageDescription` to `mobile/app.json` `infoPlist`. The app currently does not use ATT — leave the key out.

---

## Step 6 — Screenshots (Guideline 2.3.10)

**Why**: Apple rejected v1.0.0 because screenshots showed the macOS menu bar — captured on macOS instead of in the iOS Simulator. Apple requires screenshots that look like the actual iOS device the user will run on.

CAPTURE METHOD:
```bash
# Boot the desired simulator first via Xcode → Window → Devices and Simulators
xcrun simctl io booted screenshot ~/Desktop/cattle-logic-iphone17promax.png
```

REQUIRED DEVICE SIZES (current App Store Connect specs):
- iPhone 6.7" (1290 × 2796) — iPhone 15 Pro Max / 16 Pro Max / 17 Pro Max
- iPhone 6.5" (1284 × 2778) — iPhone 14 Plus
- iPad 13" (2064 × 2752) — iPad Pro 13"
- iPad 12.9" (2048 × 2732) — iPad Pro 12.9"

CONVENTIONS:
- Status bar should show "9:41" (Apple's iconic time). In the simulator: `xcrun simctl status_bar booted override --time 9:41 --batteryState charged --batteryLevel 100 --cellularBars 4 --wifiBars 3`
- No macOS chrome (menu bar, dock, window borders). The `xcrun simctl io booted screenshot` command captures only the simulator content — do NOT use macOS Cmd+Shift+4 or system screenshot shortcuts.
- Screenshots should reflect the app in use — show real cattle data, not empty states (use a seeded demo operation).

ASK USER:
> "Have all device-size screenshots been re-captured via `xcrun simctl io booted screenshot` since the previous rejection? Confirm none show macOS menu bar or chrome."

---

## Step 7 — Required Capabilities + Entitlements

**Why**: Mismatches between `app.json` and the App Store Connect listing cause "Asset validation failed" errors at submission time.

GREP:
```bash
python3 -c "
import json
d = json.load(open('mobile/app.json'))
ios = d['expo']['ios']
plist = ios.get('infoPlist', {})
print('bundleIdentifier =', ios.get('bundleIdentifier'))
print('appleTeamId      =', ios.get('appleTeamId'))
print('googleServicesFile =', ios.get('googleServicesFile'))
print('ITSAppUsesNonExemptEncryption =', plist.get('ITSAppUsesNonExemptEncryption'))
"
```

CHECK:
- `bundleIdentifier` is `com.cattlemanagement.mobile` (matches ASC app id 6762011755)
- `appleTeamId` is `248U39D5G7`
- `ITSAppUsesNonExemptEncryption` is `false` — saves the App Store Connect encryption questionnaire on every upload. ⚠ Legal review: this app uses `expo-crypto` and `expo-secure-store`. Both rely on Apple-provided crypto APIs which are exempt under U.S. EAR ECCN 5D992 — the `false` declaration is correct as long as no custom non-standard cryptographic implementations are added. Re-confirm with legal counsel before each major release.
- `googleServicesFile` points to `./GoogleService-Info.plist` and that file actually exists in `mobile/`.

---

## Step 8 — EAS Build + Submit Commands

**Why**: Wrong profile = wrong API URL or wrong distribution channel. Production must use the `production` profile in `mobile/eas.json`.

PRODUCTION BUILD + AUTO-SUBMIT (one shot):
```bash
cd mobile
eas build --platform ios --profile production --auto-submit
```

OR split (preferred — gives you a chance to inspect the build before submitting):
```bash
cd mobile
eas build --platform ios --profile production
# wait for build to finish (~25-40 min)
eas submit --platform ios --latest
```

WATCH BUILD STATUS:
- https://expo.dev/accounts/ricbenmore/projects/cattle-management/builds
- Or CLI: `eas build:list --platform ios --limit 5`

AFTER SUBMIT:
- ASC processes the upload (~5 min)
- Then in App Store Connect: select the new build for the listing → fill release notes → submit for review
- Watch status: https://appstoreconnect.apple.com/apps/6762011755/distribution/ios

NOTE: The `production` profile has `autoIncrement: true` — EAS will bump `buildNumber` and `versionCode` automatically on every build. Manual bumps in `app.json` are still recommended (single source of truth) but EAS will not let you submit a duplicate build number.

---

## Step 9 — App Store Connect Metadata Sanity

**Why**: Apple rejects builds where the metadata in App Store Connect doesn't match the actual app behavior.

ASK USER:
> 1. Are demo account credentials in App Review Information still valid? Apple uses these to log in. Test them yourself before submitting.
> 2. Is the screen recording for Guideline 5.1.1(v) (Account Deletion) uploaded in the App Review Information → Notes field? See Step 3.
> 3. Does the app description in ASC mention any features that are not in this build (e.g., a feature you removed)? Apple flags this as 2.3.10 misleading metadata.
> 4. Are the App Privacy declarations (App Store Connect → App Privacy) up to date with Step 5's declared-vs-actual table?
> 5. Is the Privacy Policy URL set to the Iubenda-hosted policy referenced by `mobile/src/constants/legal.js`?
> 6. Has the StoreKit External Purchase Link Entitlement been approved (Step 4)?

---

## Step 10 — Post-Submit Watch + Rejection Loop

**Why**: First Apple message typically arrives within 24–48 hours. If rejected, the rejection details show on the submission page — these become input to the NEXT iteration of this skill.

POST-SUBMIT:
- Bookmark the submission page: https://appstoreconnect.apple.com/apps/6762011755/distribution/ios
- The "Submission Status" updates from "Waiting for Review" → "In Review" → "Pending Developer Release" or "Rejected"

IF REJECTED:
- Read the rejection message carefully — Apple cites a specific guideline number (e.g., 5.1.1(ii))
- Map the guideline to the relevant step in this skill:
  | Guideline | Skill Step |
  |---|---|
  | 2.3.10 (Accurate Metadata) | Step 6 (Screenshots) or Step 9 (Description) |
  | 3.1.1 (Payments — IAP) | Step 4 (Disclosure modal + entitlement) |
  | 5.1.1(ii) (Privacy purpose strings) | Step 2 |
  | 5.1.1(v) (Account Deletion) | Step 3 |
  | 5.1.2 (Data Use & Sharing) | Step 5 |
- Apply the fix
- BUMP the iOS `buildNumber` (+1) so the new submission isn't a duplicate
- Re-run this skill from Step 1
- Add the rejection to `CHANGELOG.md` so the institutional memory persists

---

## Reference: Rejection History for This App

| Submission | Build | Apple Guideline | Root cause | Fix location |
|---|---|---|---|---|
| 31295540 (removed) | 1.0.0 (17) | 5.1.1(ii) Purpose strings | Vague camera/photo wording | `mobile/app.json` `expo.ios.infoPlist` (Step 2) |
| 02b8452f (rejected) | 1.0.0 (17) | 2.3.10 Screenshots | macOS menu bar in screenshots | Re-capture via `xcrun simctl` (Step 6) |
| 02b8452f (rejected) | 1.0.0 (17) | 3.1.1 Payments | Web-portal link without disclosure | `Alert.alert` in `mobile/src/components/common/GraceBanner.js` + `mobile/app/(settings)/profile.js` (Step 4) |
| 02b8452f (rejected) | 1.0.0 (17) | 5.1.1(v) Account Deletion | Missing UI flow | `mobile/app/(settings)/profile.js` Delete Account button + `backend/accounts/views.py:delete_account` (Step 3) |
| (historical) | older | 5.1.2 Data Use | App Privacy declarations under-declared | App Store Connect → App Privacy (Step 5) |

---

## Reference: Files this skill reads

- `mobile/app.json` — versions, infoPlist, plugins
- `mobile/eas.json` — build profiles, submit config
- `mobile/package.json` — version sync
- `mobile/src/constants/legal.js` — Privacy Policy URL source of truth
- `mobile/src/components/common/GraceBanner.js` — disclosure modal location
- `mobile/app/(settings)/profile.js` — delete account UI + manage-subscription disclosure
- `backend/accounts/views.py` — `delete_account` endpoint
- `backend/subscriptions/middleware.py` — middleware exemption list
- `.github/workflows/` — confirms no CI auto-build (manual EAS submit required)

## Reference: Companion docs

- `mobile/EAS_BUILD.md` — full EAS build/submit/OTA reference
- `CHANGELOG.md` — rejection history per release
- `docs/stripe-prod-secrets.md` (gitignored) — webhook + key references for the prod backend
