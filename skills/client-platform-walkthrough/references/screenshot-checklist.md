# Screenshot Coverage Checklist

A list to verify you didn't miss surfaces. Walk it after Phase 3 capture, before writing the markdown. Tick off only screens you actually have an image for.

The checklist is organized by **typical SaaS persona shape**. Most B2B platforms have 3–4 of these; a B2C app might have just 1–2. Skip rows that don't apply.

---

## Public surfaces (no auth)

- [ ] Welcome / role-picker modal (if the site has one — many do, and it's the most-skipped screenshot)
- [ ] Marketing landing page — hero
- [ ] Marketing landing page — trust signals (logo wall, customer testimonials)
- [ ] Marketing landing page — feature breakdown
- [ ] Marketing landing page — pricing section
- [ ] Marketing landing page — final CTA + footer
- [ ] Eligibility quiz / discovery flow (if any)
- [ ] Login page
- [ ] Register page
- [ ] Public help / get-started page (sometimes hosts a Calendly)
- [ ] Legal pages (privacy / terms / cookies — one screenshot each is enough)

## Buyer / B2B intake (organization signs up)

- [ ] Step 1 — type/contact info — empty
- [ ] Step 1 — type/contact info — filled
- [ ] Step 2 — entity details — empty
- [ ] Step 2 — entity details — filled
- [ ] Step 3 — branding / customization — default theme
- [ ] Step 3 — branding / customization — themed (preset selected, live re-skin shown)
- [ ] Step 4 — security policy (2FA mode picker, etc.)
- [ ] Step 5 — service agreement / contract
- [ ] Step 6 — invite users / upload roster
- [ ] Step 6 — invite users — with one row added (so reader sees the empty + non-empty list)
- [ ] **Verification gate** error banner (most platforms have one — capture it intentionally)
- [ ] Final confirmation / "what happens next" screen

## Invitation / magic-link flow

- [ ] Accept-invite landing — valid token state
- [ ] Accept-invite landing — already-used / expired state (if you can trigger one)
- [ ] Set-password / first-login form

## Two-factor auth

- [ ] 2FA setup — QR + manual entry secret
- [ ] 2FA setup — verification code entry
- [ ] 2FA setup — recovery codes display
- [ ] 2FA challenge prompt (the one that appears at every sensitive action)
- [ ] 2FA challenge — recovery-code fallback

## End-user dashboard

- [ ] Welcome / first-login dialog (institution-context, "you've been added to X" — easy to miss because it only fires once per user)
- [ ] Dashboard home — top of page
- [ ] Dashboard home — scrolled (recent activity, status checklist)
- [ ] Sidebar collapsed / expanded states (only if both are common)
- [ ] Empty state for any dashboard widget that depends on data being present (bank not linked, no documents yet, etc.)

## Feature deep-dives — one screenshot per feature, plus detail views

- [ ] Calculator / planner hub — top inputs
- [ ] Calculator / planner hub — chart / result detail (often a modal — open one and capture it)
- [ ] Tasks / to-do board
- [ ] Learning library
- [ ] Document vault
- [ ] Settings — profile tab
- [ ] Settings — security tab (this often shows session list, recovery codes — high-trust surface)
- [ ] Settings — bank / payments tab (if applicable)
- [ ] Settings — grants / sharing tab (if the platform has CPA/agent/parent access)
- [ ] Settings — notifications preferences

## Vendor-integration tracking pages

- [ ] Order / formation status timeline
- [ ] RFI inbox or vendor-question UI
- [ ] Vendor documents list

## Advisor / read-only personas

- [ ] CPA workspace — empty state ("no grants yet")
- [ ] CPA workspace — populated state (only possible if you can grant a test athlete)
- [ ] Agent workspace — empty
- [ ] Parent / guardian workspace — empty (if applicable)

## Operator / admin

- [ ] Admin overview metrics row
- [ ] Admin sub-pages — at least one screenshot per significant sub-route (athletes, orgs, payments, tasks, reports)
- [ ] Operator-of-buyer dashboard (if there's a "collective" or "team owner" tier between admin and end-user)
- [ ] University / multi-team workspace — roster tab
- [ ] University / multi-team workspace — settings tab

## Cross-cutting

- [ ] Notifications feed (full page, not just the bell)
- [ ] Support center
- [ ] Search results page (if the platform has site-wide search)
- [ ] User-avatar dropdown menu (often where Sign out, Switch org, Settings shortcut live)

---

## After the checklist — name verification

Run this and skim the output:

```bash
ls docs/screenshots/client-guide/ | sort
```

Look for:

- **Numbering gaps** — `01, 02, 04, 05` means `03` got skipped or renamed; either fix the gap or re-number sequentially.
- **Duplicate prefixes** — `11-foo.png` and `11-bar.png` cause confusion in the markdown's image refs; rename one to `11a-` and the other to `11b-`.
- **Mystery files** — leftover screenshots from a different walk. Delete them rather than carry them forward.

The naming convention is a small thing that pays off enormously when the doc gets edited months later by someone else.
