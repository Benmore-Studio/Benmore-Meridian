# Doc Template — Client Platform Walkthrough

This is the canonical 17-section skeleton. Copy it as a starting point, drop sections that don't apply, and write the prose around the screenshots you captured.

The structure is **persona-ordered, not feature-ordered**. The reader (often a buyer evaluating the platform) wants to see "what does this look like *for me*" before "what does this platform do." Open with their entry point.

---

## Skeleton (copy verbatim, then fill in)

```markdown
# [Product Name] — Platform Walkthrough Guide

> **A complete, screenshot-driven tour of the [Product Name] platform** — written for the people who will actually use it: [list primary personas].
>
> Every screenshot in this document was captured from the running platform on **YYYY-MM-DD**. UI labels in **bold** match what you see on screen verbatim.

---

## Table of contents

1. What is [Product Name]?
2. Who uses what — a 60-second map
3. First impressions — the public site
4. For [primary buyer persona] — the intake wizard
5. The [invitation / signup / onboarding] flow
6. Two-factor authentication
7. The [end-user] dashboard
8. [High-value feature 1 — e.g., calculator hub]
9. [High-value feature 2 — e.g., document vault]
10. [High-value feature 3 — e.g., business formation]
11. For [advisor personas] (read-only / guest access)
12. Internal: admin and operator dashboards
13. Pricing & plans
14. Security, privacy, and what your data looks like
15. Live features vs. coming soon
16. Support, FAQs, and getting unstuck
17. Page reference

---

## 1. What is [Product Name]?

[2–3 paragraphs of plain-language explanation. What problem does it solve? Whose problem? What does the platform actually *do* in concrete terms? Quantify the value if you can — "saves $X/year," "compresses N months to N weeks." End with a one-line summary of the pricing model so the reader knows the commercial shape immediately.]

---

## 2. Who uses what — a 60-second map

| If you are… | You enter at | You land on | Key thing you do |
|---|---|---|---|
| [Persona 1] | `/url` | `/url` | [primary task] |
| [Persona 2] | `/url` | `/url` | [primary task] |
| [Persona 3] | `/url` | `/url` | [primary task] |
| [Persona 4] | `/url` | `/url` | [primary task] |

[One short paragraph after the table, framing the "expected path" — e.g., "X is invitation-first by design. The expected path is: buyer signs up → invites their users → each user onboards via magic-link." This orients the reader for the section ordering that follows.]

---

## 3. First impressions — the public site

### 3.1 [Welcome modal / role picker / hero]

![Caption describing the screenshot](screenshots/client-guide/01-welcome-modal.png)

[1–2 paragraphs explaining what the user is looking at, what choices they have, and what each choice leads to. Quote button labels in **bold**.]

### 3.2 The marketing landing

![Hero section](screenshots/client-guide/02-landing-hero.png)

[Then walk down the page section-by-section, using a numbered list. Each item gets one line of description and one screenshot.]

1. **Trusted by** — logo wall of opt-in customers.
   ![](screenshots/client-guide/03-landing-trusted.png)
2. **Feature breakdown** — concrete examples of what the platform does.
   ![](screenshots/client-guide/04-landing-features.png)
3. **Pricing** — fees stated upfront, with an interactive calculator.
   ![](screenshots/client-guide/05-landing-pricing.png)
4. **Final CTA + footer** — links to onboarding and legal pages.
   ![](screenshots/client-guide/06-landing-cta-footer.png)

### 3.3 [Eligibility / discovery flow]

![Quiz or qualifier](screenshots/client-guide/07-quiz.png)

### 3.4 Login and registration

![Login](screenshots/client-guide/08-login.png)
![Register](screenshots/client-guide/09-register.png)

[Note any auth providers — Google SSO, Microsoft SSO, magic-link, password — and the "Show password" / "Remember me" / "Forgot password?" affordances. List the trust-signal badges shown in the footer (e.g., "256-bit SSL Encryption," "SOC 2 Type II Certified").]

---

## 4. For [primary buyer persona] — the intake wizard

[This is where the buyer signs up. Walk through every step. Each step gets its own subsection with the empty state, the filled state, and a callout for any gates or surprises.]

### 4.1 Step 1 — Who you are

![Empty state](screenshots/client-guide/11a-step1-empty.png)

[List the form fields with their exact labels. Note required vs. optional. Note any "fast-track" copy that influences user behavior — e.g., ".edu addresses unlock automatic verification."]

![Filled state](screenshots/client-guide/11b-step1-filled.png)

### 4.2 Step 2 — [Title]

[Same shape: empty + filled + field-list + callouts.]

### 4.3 Step N — [Branding / customization]

[For SaaS with white-label features, screenshot the live preview *re-skinning* in real time when a preset is selected. Side-by-side empty and themed.]

### 4.N — Final step + verification gate

> **Heads-up — verification gate.** Many platforms hold the new account in a draft state until support reviews and approves. Show the actual error banner the user will see and explain what to do.
>
> ![Verification gate](screenshots/client-guide/22-verify-gate.png)

---

## 5. The invitation / magic-link flow

![Accept-invite landing](screenshots/client-guide/27-accept-invite.png)

[Explain what the page does, the three states it handles (valid / already used / expired) in a small table, and the security guarantees (single-use, replay-protected, rate-limited).]

| State | What you see |
|---|---|
| Valid token | "..." |
| Already used | "..." |
| Expired | "..." |

---

## 6. Two-factor authentication

### 6.1 Setup — `/2fa/setup`

![](screenshots/client-guide/25-2fa-setup.png)

[QR code, manual entry secret, 6-digit verification, recovery codes. Note grace period if any.]

### 6.2 Challenge — `/2fa/challenge`

![](screenshots/client-guide/26-2fa-challenge.png)

[On every sensitive action. Note the "trouble with your authenticator" recovery path.]

---

## 7. The [end-user] dashboard

![Welcome dialog](screenshots/client-guide/28-dashboard-welcome.png)

### 7.1 Layout overview

![Dashboard home](screenshots/client-guide/29-dashboard-home.png)

[Describe the layout: sidebar nav, top banner, main content area. List every sidebar item. List every top-right icon.]

**Left sidebar:**
- **[Item 1]** (the page you're on)
- **[Item 2]**
- ...

**Top banner:** [page heading, personalized greeting, search button, notifications bell, user avatar menu]

**Main area:** [overview cards, status checklist, recent activity timeline]

---

## 8. [Feature deep-dive — e.g., Calculator hub]

![Hub overview](screenshots/client-guide/31-calculators.png)

### 8.1 The shared inputs

[List every input. Note default values and persistence behavior — "defaults to $250,000 for first-time visitors, persisted to local storage thereafter."]

### 8.2 The result calculators / sub-features

| Feature | What it does |
|---|---|
| **[Name]** | [One-line description] |
| **[Name]** | [One-line description] |
| ... | ... |

[For visualizations, mention the charting library used so the customer's brand team can match it if they want to extract data — e.g., "the platform uses recharts for visualization."]

---

## 9. [Feature deep-dive — secondary surfaces]

[Repeat the §8 pattern for tasks, learning, documents, settings, etc. Each gets a section with one screenshot and a paragraph + bullet list.]

---

## 10. [Feature deep-dive — vendor integrations]

[For features driven by external integrations (formation, banking, payments), explicitly name the vendor and explain the user does not interact with the vendor directly — the platform mediates. This is reassuring for buyers who don't want to learn another system.]

---

## 11. For [advisor personas] (read-only)

### 11.1 [Advisor type 1] workspace

![](screenshots/client-guide/23-advisor1-landing.png)

[The lead text the user sees verbatim. The empty state. What appears once a grant arrives. What stays masked.]

### 11.2 [Advisor type 2] workspace

[Same shape.]

> **Audit-log guarantee.** Every advisor view, export, and message is recorded in an append-only audit log that the granting user can pull on demand. If the user revokes the grant, the advisor loses access immediately.

---

## 12. Internal: admin and operator dashboards

### 12.1 Admin dashboard

![](screenshots/client-guide/40-admin.png)

[Describe the metric cards, charts, sub-pages. Bullet-list the sub-routes.]

### 12.2 [Other operator persona] dashboard

[Repeat.]

---

## 13. Pricing & plans

| Item | Price | When charged | What it covers |
|---|---|---|---|
| **[Setup fee]** | $X | [trigger] | [scope] |
| **[Recurring]** | $X / month / unit | [trigger] | [scope] |
| **[Tier 1]** | Custom | Annual contract | [features] |
| **[Tier 2]** | Custom | Annual contract | [features] |

[One paragraph on payment methods, billing cadence, and discount levers if any.]

---

## 14. Security, privacy, and what your data looks like

### 14.1 At rest

- Encryption mechanism (e.g., Fernet, AES-256-GCM), what fields are encrypted, key rotation cadence.
- Storage tier (S3, encrypted disks), object URL TTL.
- Audit log properties (append-only, retention period).

### 14.2 In transit

- TLS version, HSTS status.
- Secret management (env vars, no source code, gitleaks-scanned).
- 2FA scope.

### 14.3 Access control

- Row-level RBAC scope per persona.
- Audit-log read/write trail.
- Magic-link properties (single-use, hashed, rate-limited, revocable).

### 14.4 What gets shown vs. masked

| Field | [User] sees | [Admin] sees | [Advisor] sees |
|---|---|---|---|
| [Sensitive field] | ❌ (masked: `***-**-1234`) | ❌ | ❌ |
| [Internal ID] | ✅ | ✅ | ✅ |
| ... | ... | ... | ... |

### 14.5 Privacy rights

[Data export SLA, erasure SLA, grant revocation latency.]

---

## 15. Live features vs. coming soon

[The honesty section. Two lists.]

### ✅ Live today

- [Feature 1]
- [Feature 2]
- ...

### ⚠️ Coming soon

- **[Feature]** — [why it's not live, what's blocking, ETA if known]
- ...

[Close with a one-line statement of overall production-readiness — e.g., "The platform's overall production-readiness score is ~95/100 as of YYYY-MM-DD."]

---

## 16. Support, FAQs, and getting unstuck

### 16.1 In-app

- Notifications bell, sidebar Support link, in-app FAQ, help cursor on key terms.

### 16.2 Email and phone

- Athlete-facing support email and SLA.
- Buyer-facing support (account manager, dedicated Slack-connect channel for premium tiers).
- Compliance / legal address.
- Security disclosure address with PGP key reference.

### 16.3 Common questions

- "How long does setup actually take?" — [answer]
- "Can I still use my existing CPA / agent / vendor?" — [answer]
- "What happens if I leave [my school / org]?" — [answer]
- ...

---

## 17. Page reference

| URL | Who | Auth | Section |
|---|---|---|---|
| `/` | anyone | none | §3 |
| `/quiz` | prospective users | none | §3.3 |
| `/login` | anyone | none | §3.4 |
| ...one row per route... |

---

## Appendix — How this guide was built

Every screenshot in this document was captured live on **YYYY-MM-DD** using the Playwright CLI against `http://localhost:[port]`. The [primary] wizard was walked through end-to-end with synthetic but realistic data ("[demo data examples]"). The [end-user] dashboard screenshots were taken under a real JWT obtained by registering a demo account through the `/api/v1/auth/register/` endpoint.

Screenshot files live at `docs/screenshots/client-guide/NN-name.png`. They are checked into the repository so this guide stays renderable offline.

If a screen has changed and the image looks stale, regenerate it by:

1. Booting the dev environment.
2. Reproducing the screen via the playwright-cli.
3. Replacing the file at the same path.

A reproduction harness for re-running the entire walkthrough lives in `docs/[ENGINEER_FACING_GUIDE].md` (the engineer-focused companion to this client guide).

---

*[Product Name] — built by [Company]. Questions: [contact-email].*
```

---

## Voice patterns to copy

These are the prose patterns that work. Paste and adapt — don't reinvent.

### Action-oriented step description

> Click **Continue as Athlete** to proceed.
>
> Pick **University** if you're an athletic department or **Collective** if you're an NIL group. Each card lists what you get; pick what fits.

### Honest verification-gate disclosure

> **Heads-up — verification gate.** New institutions start in **draft** status. The platform will hold your invitation send until your account is **verified** (Echelon support reviews and approves new institutions, usually within one business day). You'll see this message if you try to send before verification: *"Institution must be verified first (current: draft)."* This one-time gate exists to prevent spoofed institutions from blasting invites with school branding.

### Coming-soon callout (per-feature)

> **Note.** Email notifications are live (delivered via SendGrid). SMS and push notifications are stubbed in the current release — toggling them on saves your preference but no message is sent yet. They'll go live as soon as Twilio and Expo Push integration ships.

### Behind-the-scenes vendor disclosure

> **Behind the scenes.** Echelon's formation flow uses **CorpNet** as the registered-agent vendor. Athletes never deal with CorpNet directly — Echelon submits the order, polls for updates, and surfaces everything in the unified UI above. The integration is two-way: CorpNet's RFI requests flow in, and the athlete's responses flow back out.

### Persona-scoped FAQ

> "What happens to my account if I leave the school?" — Your athlete account is yours, not the school's. The school loses admin visibility into your data, but your LLC, bank account, documents, and Echelon account stay intact and you continue at the same $199/month rate.

---

## What to drop

You don't always need every section. Common ones to drop:

- **§6 (2FA)** if the platform doesn't have it. Don't fake it.
- **§11 (advisor personas)** if it's a single-persona product.
- **§12 (operator dashboards)** if the user is asking for a *purely* customer-facing doc and won't show internal screens.
- **§14.5 (privacy rights)** if the platform is pre-GDPR-compliance and you'd be writing aspirational text.

When in doubt, drop the section rather than write filler. Filler is more damaging to a client doc than a missing topic — clients use the headings as a checklist of "what works."
