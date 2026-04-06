# Propurti Client Demo Plan
**Date**: 2026-04-06 | **Prepared for**: Patrobas | **Prepared by**: Arkash Jain  
**Platform**: Propurti (Property Management SaaS)  
**Build**: v0.9.4 (Frontend) + v1.9.2 (Backend) on `staging`

---

## Purpose

This document is a structured demo walkthrough covering everything addressed from client feedback, QA testing, backend hardening, and upcoming features. Each section maps directly to items raised by Patrobas in the Q/A chat, the QA test plan, and the ship-critical sprint scope.

---

## Demo Agenda Overview

| # | Section | Duration | Focus |
|---|---------|----------|-------|
| 1 | Client Feedback Resolution | 20 min | Walk through every chat item and show fix/status |
| 2 | Property Management — Create & Edit | 15 min | Full property lifecycle with new fields |
| 3 | AI Listing Tool | 5 min | Generate, Refine, Analyze, Optimize |
| 4 | Landlord & Tenant Flows | 15 min | Invite, signup, connections, lease creation |
| 5 | Image Management | 5 min | Upload, delete, limits, memory safety |
| 6 | Search & Filtering | 5 min | City autocomplete, advanced filters |
| 7 | Bulk Import & Export | 5 min | CSV templates, edit pending owners, tenant import |
| 8 | Payments & Plaid | 10 min | Plaid KYC, Stripe setup, tenant payment flow |
| 9 | Security & Compliance Hardening | 5 min | Behind-the-scenes improvements |
| 10 | Performance & Polish | 5 min | Speed, UX, accessibility improvements |
| 11 | Upcoming Features (Roadmap Preview) | 10 min | Payment infrastructure, Apple Sign-In, trust badges |
| **Total** | | **~100 min** | |

---

## Section 1: Client Feedback Resolution (Chat Item Tracker)

Every item Patrobas raised in the Q/A chat, mapped to its resolution status.

### 1.1 Resolved Items (Ready to Demo)

| # | Patrobas Feedback | Status | What Was Done | Demo Action |
|---|-------------------|--------|---------------|-------------|
| CF-1 | **"View Public Website" button should open in new tab** | FIXED | Added `target="_blank"` + `rel="noopener noreferrer"` to the View Public Website button | Click "View Public Website" on any property — confirm it opens in a new browser tab |
| CF-2 | **Session timeout too short while entering property details** | FIXED | Extended session timeout to prevent premature expiry during property entry. Token refresh mechanism improved | Start entering property details, pause for 5-10 minutes, resume — session should persist |
| CF-3 | **State/Province and Zip code not retained on Edit Property** | FIXED | Property Edit Page overhauled (773 lines rewritten). Form initialization changed from `useEffect` to synchronous render-time pattern with `formReady` guard. All fields now populate correctly on load | Navigate to Edit Property — verify State/Province, Zip Code, and all other fields are pre-populated with previously entered data |
| CF-4 | **Policies section not visible / not editable** | FIXED | Added full policy management to Edit Property: Pets Allowed (with pet policy text), Smoking Allowed (with smoking policy text), Parking Available (with parking spots count) | Open Edit Property → scroll to Policies section → toggle each policy on/off → verify conditional fields appear |
| CF-5 | **Property details lost on Edit (type, sq ft, year built, rent, lease type, available date)** | FIXED | Complete edit page overhaul ensures all fields persist. Form initialization now deferred until property data fully loads (skeleton loading state shown until `formReady=true`) | Open Edit Property for an existing property → verify all fields match what was entered during creation |
| CF-6 | **Lease type options don't match between Create and Edit** | FIXED | Property type options expanded from 5 to 11 on Edit page to match the creation form (Single Family, Multi-Family, Condo, Townhouse, Apartment, Duplex, Triplex, Commercial, Industrial, Land, Other) | Compare property type dropdown in Create vs. Edit — options should be identical |
| CF-7 | **Error message saving edited property changes** | FIXED | Error handling improved: now checks `error.data.errors`, `error.data.details`, `error.data.error`, `error.data.detail` in order. Shows field-specific messages instead of generic "Failed to update" | Save an edit with valid data → success toast. Intentionally trigger validation error → verify specific error message shown |
| CF-8 | **AI Listing: Analyze throws "API Request failed"** | FIXED | `handleAnalyze` and `handleOptimize` now correctly pass `existing_title` and `property_features` parameters. Headline field passthrough added | Open AI Listing → Generate → then click Analyze → verify it returns analysis without error |
| CF-9 | **AI Listing: Optimize throws "API Request failed"** | FIXED | Same fix as CF-8 — Optimize function updated with proper parameter passthrough | Open AI Listing → Generate → then click Optimize → verify it returns optimized listing without error |
| CF-10 | **No autocomplete when entering city name** | FIXED | New `CityAutocomplete` component (161 lines) with ARIA combobox pattern, keyboard navigation (arrow keys + Enter + Escape), prefix/substring ranking, and auto-fill of state/province on city selection. Integrated into both Edit page and Create stepper | Type "Cal" in city field → see "Calgary" in dropdown → select → verify state auto-fills to "AB" |
| CF-11 | **"Add More Properties" button doesn't work** | FIXED | Button handler repaired — now correctly routes to the property creation flow | Create a property → on success screen, click "Add More Properties" → verify it navigates to a fresh property creation form |
| CF-12 | **Can't edit pending owner info (name/email) after bulk import** | FIXED | PM can now edit owner name and email for pending connection requests before resending invitations | Import owners via CSV → go to Pending Connections → click edit icon on a pending owner → modify name/email → save → resend invitation |

### 1.2 Items In Progress / Planned

| # | Patrobas Feedback | Status | Plan | Target |
|---|-------------------|--------|------|--------|
| CF-13 | **Search filters only by address — need city, landlords, bedrooms, bathrooms, rent range** | PLANNED | Sprint Stream 2 — advanced search filters with multi-criteria filtering | Next sprint |
| CF-14 | **Lease generation should auto-pull property data** | PLANNED | When selecting a property for a new lease, property info (address, rent, type, etc.) will auto-populate — no re-entry | Next sprint |
| CF-15 | **Tenant bulk import template not easily accessible** | PLANNED | Template download button will be moved to match the landlord/properties import pattern — visible before clicking "Bulk Import" | Next sprint |
| CF-16 | **Need both import AND export options for tenants** | IN PROGRESS | `handleExportTenants` function implemented — generates CSV with Name, Email, Phone, Property, Lease, Rent, Status columns. Export button wired on tenant list page | Demo ready — show Export button on tenant list |
| CF-17 | **Database wipe concern — "no paying client would like this"** | ADDRESSED | Deployed separate testing branch and main branch. Testing environment isolated from production data. Long-term: tenant data migration tooling planned | Explain the testing vs. production branch strategy |
| CF-18 | **Plaid tenant payment flow** | READY TO TEST | Plaid integration active on staging. Tenant can connect bank account via Plaid Link | Walk through Plaid connection flow during demo |

### 1.3 Items Already Working (Confirmed by Testing)

These items Patrobas listed as "yet to be tested" but have been verified internally:

| # | Item | Status | Verification |
|---|------|--------|-------------|
| CT-1 | Accepts connection request + landlord is read-only | VERIFIED | Landlord view enforces read-only permissions on PM-managed properties |
| CT-2 | PM can see accurate stats in dashboard | VERIFIED | Portfolio dashboard renders correct metrics |
| CT-3 | "Manage my property" checkbox no longer shows for invited landlords | VERIFIED | Checkbox conditionally hidden for invited landlord accounts |
| CT-4 | Assign tenant to property → creates lease → sends invite | VERIFIED | Full flow tested — tenant receives invite email, can register and login |

---

## Section 2: Property Management — Create & Edit

### 2.1 Property Creation Flow (Demo Script)

| Step | Action | What to Verify |
|------|--------|----------------|
| 1 | Click "Add Property" from Properties page | Stepper form opens with 5 steps |
| 2 | **Step 1 — Basic Info**: Enter address, city (use autocomplete), unit number | City autocomplete shows suggestions; selecting a city auto-fills state/province |
| 3 | **Step 2 — Details**: Select property type, enter bedrooms/bathrooms/sq ft, year built, amenities | "Pet-friendly" amenity selection triggers `pets_allowed` field on submission |
| 4 | **Step 2 — Policies**: Toggle Smoking Allowed, Parking Available | Conditional fields appear (smoking policy text, parking spots count) |
| 5 | **Step 3 — Media**: Upload property images (max 10) | Preview thumbnails shown; reject files >10MB or wrong type |
| 6 | **Step 4 — Review**: Verify all entered data | All fields display correctly including policies |
| 7 | **Step 5 — Submit** | Property created. "Add More Properties" button works |
| 8 | Leave year_built blank and submit | **Regression check**: No "0" sent to backend (fix M7) |

### 2.2 Property Edit Flow (Demo Script)

| Step | Action | What to Verify |
|------|--------|----------------|
| 1 | Navigate to Properties → click a property → Edit Property | Edit page loads with skeleton until data ready, then all fields populated |
| 2 | Verify pre-populated fields | Address, city, state, zip, property type, sq ft, year built, rent, lease type, headline — all retained from creation |
| 3 | **Policies section**: Toggle Pets Allowed ON | Pet policy text input appears; toggle OFF → input disappears |
| 4 | **Policies section**: Toggle Parking Available ON, enter 3 spots | Parking spots input visible only when toggle is ON |
| 5 | **Policies section**: Toggle Smoking Allowed ON, enter policy | Smoking policy text field appears |
| 6 | **Images**: Upload 2 new images | Preview shown → "Upload 2 Images" button → success toast |
| 7 | **Images**: Delete 1 image | Image moves to "marked for removal" with Undo button → confirm delete |
| 8 | **Amenities**: Add "Pool", try adding "Pool" again | Duplicate blocked silently |
| 9 | Toggle is_public ON | Property will appear on public browse page |
| 10 | Click Save | Success toast → redirect to detail page. All new fields persisted |
| 11 | Verify on detail page | Policy badges shown: Pets (green "Allowed"), Smoking (red/green), Parking (with spot count) |
| 12 | Try to Save while images are uploading | **Save button disabled** during upload/delete operations (fix E1) |

### 2.3 Occupancy Status (Read-Only)

- On the Edit page, occupancy status displays as a styled label — NOT editable
- Shows "Auto-computed from lease" — system calculates this automatically
- **Demo**: Point this out as a deliberate design decision

---

## Section 3: AI Listing Tool

| Step | Action | What to Verify |
|------|--------|----------------|
| 1 | Open AI Listing on a property with headline set | Headline appears in the tool |
| 2 | Click **Generate** | AI generates listing description — should succeed |
| 3 | Click **Refine** | AI refines the generated listing — should succeed |
| 4 | Click **Analyze** | **Previously broken (CF-8)** — now returns analysis without API error |
| 5 | Click **Optimize** | **Previously broken (CF-9)** — now returns optimized listing without API error |
| 6 | Verify `existing_title` uses property headline as fallback | When no existing listing, property headline is used |

**Key Fix**: The Analyze and Optimize functions now correctly pass `existing_title` and `property_features` to the AI backend.

---

## Section 4: Landlord & Tenant Flows

### 4.1 Invite Landlord Flow

| Step | Action | What to Verify |
|------|--------|----------------|
| 1 | PM clicks "Invite Landlord" | Invitation form opens |
| 2 | Enter landlord name and email | Form validates email format |
| 3 | Send invitation | Landlord receives branded email with signup link |
| 4 | **From Add Property page**: Assign landlord inline | Can add landlord without leaving the property creation flow |
| 5 | Create property without landlord | Property saved — landlord can be assigned later |

### 4.2 Landlord Signup & Connection

| Step | Action | What to Verify |
|------|--------|----------------|
| 1 | Landlord clicks signup link from email | Registration page loads |
| 2 | Landlord completes registration | Account created successfully |
| 3 | Landlord accepts connection request | Connection established — landlord linked to PM |
| 4 | Landlord views properties | Read-only access on PM-managed properties |
| 5 | "Manage my property" checkbox | **NOT shown** for invited landlords (CT-3) |

### 4.3 Tenant Assignment & Lease Creation

| Step | Action | What to Verify |
|------|--------|----------------|
| 1 | PM assigns tenant to a property | Lease creation initiated |
| 2 | Add co-tenants | Co-tenant details captured |
| 3 | System sends invite to tenant | Tenant receives email with registration link |
| 4 | Tenant registers and logs in | Account created, tenant dashboard accessible |
| 5 | Tenant views lease details | Lease terms, property info, payment details visible |

### 4.4 Property Detail Views (3 Audiences)

| View | URL Pattern | Policy Badges | What to Verify |
|------|-------------|---------------|----------------|
| **PM Dashboard** | `/dashboard/properties/{id}` | Green "Allowed" / Red "Not allowed" with Check/X icons | All policies shown with correct colors and icons |
| **Landlord Dashboard** | `/landlord-dashboard/properties/{id}` | PawPrint, Cigarette, Car icons | Policies section appears only if at least one policy is defined |
| **Public Browse** | `/browse-properties/{id}` | Policy rows with spot count pluralization | "2 spots" vs "1 spot" — correct grammar |

---

## Section 5: Image Management

| Step | Action | What to Verify |
|------|--------|----------------|
| 1 | Upload PNG, JPG, WEBP images | All 3 formats accepted |
| 2 | Try uploading 15MB file | Rejected with toast error — max 10MB per file |
| 3 | Try uploading .gif file | Rejected — wrong file type |
| 4 | Upload to 9 existing images, try adding 3 more | Only 1 accepted — max 10 images enforced |
| 5 | Delete an image | Image moves to "marked for removal" queue with Undo button |
| 6 | Click Undo | Image restored to main gallery |
| 7 | Confirm delete | Image permanently removed from backend |
| 8 | Select files, navigate away without uploading | No memory leak — blob URLs cleaned up on page exit |

---

## Section 6: Search & Filtering

### 6.1 City Autocomplete (New Feature)

| Step | Action | What to Verify |
|------|--------|----------------|
| 1 | Type "San" in city field | Dropdown appears with matching cities (San Francisco, San Diego, etc.) |
| 2 | Use arrow keys to navigate | Keyboard navigation works (up/down/Enter/Escape) |
| 3 | Select "San Francisco" | City field set, state auto-fills to "CA" |
| 4 | Type a single character "A" | Results appear (no minimum character threshold) |
| 5 | Clear the city field and try to submit | Browser-native required validation fires (fix H3) |
| 6 | Screen reader test | ARIA combobox pattern — announces suggestions |

### 6.2 Current Search Capability

- **Available now**: Search by property address
- **Planned (CF-13)**: Search by city, landlord name, bedrooms, bathrooms, rent price range

---

## Section 7: Bulk Import & Export

### 7.1 Owner/Landlord Import

| Step | Action | What to Verify |
|------|--------|----------------|
| 1 | Download CSV template | Template accessible from the import section |
| 2 | Fill with 8 dummy owners (including intentional typos in emails) | CSV accepted |
| 3 | Import file | All 8 owners imported — shown in Pending Connections |
| 4 | **Edit a pending owner** (CF-12) | Click edit on pending owner → modify name/email → save |
| 5 | Resend connection request | Updated email used for the new invitation |

### 7.2 Tenant Import & Export

| Step | Action | What to Verify |
|------|--------|----------------|
| 1 | **Export tenants** (CF-16) | Click Export button on tenant list → CSV downloads with Name, Email, Phone, Property, Lease, Rent, Status |
| 2 | Access tenant bulk import template | **(CF-15 — Planned)**: Template will be made more accessible in next sprint |
| 3 | Import tenants via CSV | Verify import processes correctly |

### 7.3 Property Import & Export

| Step | Action | What to Verify |
|------|--------|----------------|
| 1 | Download property CSV template | Template available |
| 2 | Import properties | Properties created from CSV data |
| 3 | Export properties (Landlord view) | `handleExportProperties` generates CSV for landlord's properties |

---

## Section 8: Payments & Plaid

### 8.1 Stripe KYC Setup

| Step | Action | What to Verify |
|------|--------|----------------|
| 1 | PM navigates to Stripe Connect setup | Onboarding link generated |
| 2 | Complete Stripe identity verification | Account verified — "Connected" status |
| 3 | Verify return URL security | Cannot be redirected to external domains (open redirect fix) |

### 8.2 Plaid Bank Connection (Tenant)

| Step | Action | What to Verify |
|------|--------|----------------|
| 1 | Tenant opens payment settings | Plaid Link available |
| 2 | Connect bank account via Plaid | Plaid modal opens → bank selected → account linked |
| 3 | Verify connection persists | Bank account shown in payment settings |

### 8.3 Virtual Tour Credits

| Step | Action | What to Verify |
|------|--------|----------------|
| 1 | Open Buy Credits dialog | Custom amount input with $1/credit display |
| 2 | Quick pick: click "25" | Amount updates to 25, price shows $25.00 |
| 3 | Type "2000" | **Clamped to 1000** (fix H4 — max cap enforced) |
| 4 | Clear input to 0 | Purchase button disabled (amount must be >= 1) |
| 5 | Enter valid amount, click Purchase | Credits purchased successfully |

---

## Section 9: Security & Compliance Hardening (Behind the Scenes)

These won't be visible UI features but are critical for production readiness. Walk through at a high level.

### 9.1 Critical Security Fixes

| Fix | What It Prevents | Business Impact |
|-----|-------------------|-----------------|
| **3 IDOR vulnerabilities patched** | Other users accessing/modifying your invoices, expenses, financial reports | Data isolation between PMs/landlords |
| **Open redirect blocked** | Stripe Connect return URLs can't be hijacked to phishing sites | Protects user credentials during payment setup |
| **Timing oracle eliminated** | OTP verification can't be brute-forced via timing analysis | Stronger account security |
| **Payment amount validation** | Prevents $0 or negative rent payments | Financial data integrity |
| **Vacate notice race condition** | Prevents duplicate vacate notices from concurrent requests | Legal correctness |
| **Property views counter** | Atomic increment prevents count corruption | Accurate analytics |
| **Cross-user edit prevention** | PM A cannot edit PM B's properties | Multi-tenant data isolation |

### 9.2 Compliance (Canadian Market)

| Item | What It Does | Legal Requirement |
|------|-------------|-------------------|
| **CASL email footer** | Unsubscribe link on all 16 email templates | Canada's Anti-Spam Legislation — fines up to $10M |
| **Emergency SMS routing** | Maintenance emergencies and eviction notices now deliver via SMS | Tenant safety — immediate delivery for urgent matters |
| **CSV export audit logging** | Every tenant/owner CSV export logged with user, IP, count | PIPEDA privacy compliance — know who accessed personal data |
| **Notification sanitization** | Passwords, tokens stripped from stored notification data | Prevents plaintext credential exposure in database |

### 9.3 Error Handling Improvements

| Scenario | Before | After |
|----------|--------|-------|
| **Rate limited (429)** | "Request failed with status 429" | "Too many requests. Please wait a moment and try again." |
| **Service down (503)** | Generic error | "Service temporarily unavailable. Please try again in a minute." |
| **Property edit errors** | Always generic message | Field-specific error messages from backend |

---

## Section 10: Performance & Polish

### 10.1 Performance Improvements

| Improvement | Impact | Demo |
|------------|--------|------|
| **Cities lazy-loaded** | ~50KB deferred from initial page load — loads on first keystroke | City autocomplete still instant; no visible delay |
| **Confetti lazy-loaded** | ~60KB deferred from waitlist pages | Waitlist success page loads faster |
| **Image optimization enabled** | 30-50% image size reduction via Next.js optimization | Property images load faster on listing pages |
| **9 new database indexes** | Dashboard, listings, and notification queries significantly faster | Portfolio dashboard renders faster with many properties |
| **Pagination on Lease/Application endpoints** | Max 20 per page — prevents server overload | Large portfolios don't crash the server |

### 10.2 Accessibility Improvements

| Item | What Changed |
|------|-------------|
| ARIA labels on policy toggle switches | Screen readers announce "Toggle pets allowed" etc. |
| Accessible image delete buttons | Announces "Remove image 1", "Remove image 2" |
| Skip-to-content links | Tab key reveals skip link on all 3 dashboard layouts |
| Policy badges not color-only | Check/X icons alongside color coding |

### 10.3 UX Polish

| Item | What Changed |
|------|-------------|
| Empty state on landlord financials | Shows "No financial data yet" instead of blank page |
| Mobile step progress dots | Property creation stepper shows dots on mobile |
| SMS "(coming soon)" label | SMS toggle clearly labeled as coming soon |

---

## Section 11: Upcoming Features (Roadmap Preview)

### 11.1 Near-Term (Next Sprint)

| Feature | Description | Relevance |
|---------|-------------|-----------|
| **Advanced search filters** (CF-13) | Search by city, landlord, bedrooms, bathrooms, rent range | Direct client request |
| **Lease auto-populate** (CF-14) | Lease creation pulls property data automatically | Direct client request — eliminates re-entry |
| **Tenant import template** (CF-15) | Template accessible before clicking "Bulk Import" | Direct client request |
| **Apple Sign-In** | Already implemented — awaiting Apple Developer Portal config | New user acquisition channel |
| **Google SSO fix** | Backend now handles both JWT and opaque access tokens | Existing SSO was broken for some flows |

### 11.2 Payment Infrastructure (Stream 3 — Full Build)

| Feature | Description | Business Impact |
|---------|-------------|-----------------|
| **Subscription plans** | Free / Pro / Enterprise tiers with property limits | Propurti's SaaS revenue model |
| **Rent collection via Stripe** | Tenant pays rent → platform fee deducted → PM receives net | Core payment flow |
| **Contractor payouts** | Stripe Connect transfers to contractors after work order completion | Maintenance payment automation |
| **Billing dashboard** | Current plan, usage, upgrade/downgrade, invoice history | PM self-service billing |
| **Tenant payment page** | Pay rent, view history, upcoming due dates | Tenant's primary financial interface |
| **Payment receipts** | Auto-generated receipts for every payment | Legal requirement in many jurisdictions |

### 11.3 UI Enhancements (Stream 2 Highlights)

| Feature | Description |
|---------|-------------|
| **Loading skeletons** | Shimmer loaders replacing spinners across all dashboards |
| **Status dot indicators** | Green/yellow/red dots on property cards for at-a-glance health |
| **Money formatting** | Consistent $1,234.56 display everywhere |
| **Toast on every mutation** | Success/error feedback on every action |
| **Cmd+K command palette** | Quick navigation across the entire platform |
| **Hover states** | Subtle lift + shadow on all clickable cards |
| **Empty states** | Meaningful messages + illustrations on all blank pages |

### 11.4 Frontend-Backend Coherence (Stream 1 Highlights)

| Feature | Description |
|---------|-------------|
| **Utility badges** | Water/electricity/gas/internet inclusions shown on property detail |
| **Condo-specific fields** | Parking stall, storage locker, furnished status for condos |
| **Disclosure badges** | Lead paint, mold, flood zone, bedbug history warnings |
| **Co-tenants & guarantors on lease** | Legally required parties visible on lease detail |
| **Contractor payment status** | Pending/Paid/Failed badge on maintenance detail |

---

## Demo Environment Setup

### Pre-Demo Checklist

- [ ] Staging environment is running and accessible
- [ ] Test PM account created with properties, landlords, and tenants
- [ ] At least 1 property has images, policies, and amenities configured
- [ ] At least 1 landlord invitation is in "Pending" state (for edit demo)
- [ ] Plaid test credentials available (sandbox mode)
- [ ] Stripe test mode active with test card numbers
- [ ] AI Listing API keys configured and working
- [ ] Browser dev tools available for showing network requests (if needed)

### Test Accounts Needed

| Role | Purpose | Pre-Configured? |
|------|---------|-----------------|
| PM (Property Manager) | Main demo account — full access | Yes |
| Landlord (connected) | View property detail in landlord view | Yes |
| Landlord (pending invite) | Demo edit pending owner info | Set up before demo |
| Tenant | Demo tenant dashboard, payment flow | Yes |

### Test Data Needed

| Data | Quantity | Notes |
|------|----------|-------|
| Properties | 5-10 | Mix of types (Single Family, Condo, Apartment) with varying policies |
| Landlords | 3-5 | Mix of connected and pending |
| Tenants | 3-5 | At least 1 with active lease |
| Images | 3-5 per property | For image management demo |
| CSV files | 2 | Owner import template (with intentional email typo), Tenant import template |

---

## Client Feedback Summary — Status Matrix

| ID | Feedback Item | Status | Section |
|----|--------------|--------|---------|
| CF-1 | View Public Website → new tab | FIXED | 1.1 |
| CF-2 | Session timeout too short | FIXED | 1.1 |
| CF-3 | State/Province + Zip not retained on Edit | FIXED | 1.1 |
| CF-4 | Policies section missing on Edit | FIXED | 1.1 |
| CF-5 | Property details lost on Edit | FIXED | 1.1 |
| CF-6 | Lease type mismatch Create vs Edit | FIXED | 1.1 |
| CF-7 | Error message saving edited property | FIXED | 1.1 |
| CF-8 | AI Listing: Analyze API error | FIXED | 1.1 |
| CF-9 | AI Listing: Optimize API error | FIXED | 1.1 |
| CF-10 | No city autocomplete | FIXED | 1.1 |
| CF-11 | "Add More Properties" button broken | FIXED | 1.1 |
| CF-12 | Can't edit pending owner info | FIXED | 1.1 |
| CF-13 | Search filters limited to address only | PLANNED | 1.2 |
| CF-14 | Lease creation should auto-pull property data | PLANNED | 1.2 |
| CF-15 | Tenant bulk import template hard to find | PLANNED | 1.2 |
| CF-16 | Need import AND export for tenants | IN PROGRESS | 1.2 |
| CF-17 | Database wipe concern for live clients | ADDRESSED | 1.2 |
| CF-18 | Plaid tenant payment testing | READY TO TEST | 1.2 |

**Summary**: 12 of 18 items FIXED | 1 IN PROGRESS | 3 PLANNED | 1 ADDRESSED | 1 READY TO TEST

---

## Post-Demo Action Items

After the demo, collect Patrobas's feedback on:

1. [ ] Do the property edit fixes resolve the data persistence concerns?
2. [ ] Is the AI Listing tool working as expected (all 4 actions)?
3. [ ] Does the city autocomplete meet expectations?
4. [ ] Are there additional search filters beyond city/landlord/bedrooms/bathrooms/rent range?
5. [ ] Plaid connection flow — any issues?
6. [ ] Priority ranking of planned items (CF-13, CF-14, CF-15)
7. [ ] Any new UI/UX issues discovered during the demo?
8. [ ] Stripe KYC completion status
9. [ ] Mobile responsiveness — any areas that need attention?
10. [ ] Overall platform readiness assessment for beta launch

---

## Appendix: Test Card Numbers (Stripe Test Mode)

| Card Number | Scenario |
|-------------|----------|
| 4242 4242 4242 4242 | Successful payment |
| 4000 0000 0000 0002 | Card declined |
| 4000 0000 0000 3220 | 3D Secure required |

**Expiry**: Any future date | **CVC**: Any 3 digits | **ZIP**: Any 5 digits
