# Civicum Legal Assistant — Case Scenarios & Flow Documentation

> **Author:** Rainer Nsa
> **Reviewed by:** Arkash Jain
> **Date:** 2026-02-20
> **Project:** Civicum Legal Assistant

---

## Application Overview

**Stack:**
- Frontend: Next.js 14 (App Router), React Query, session-storage state via `CaseContext`
- Backend: Django REST Framework, OpenAI (classify + chat), SQLite

**Key Files:**
- `frontend/app/case-type/page.tsx` — entry point + privacy modal + AI/consultant split
- `frontend/app/chat/page.tsx` — AI chat interface
- `frontend/app/dashboard/page.tsx` — legal plan view
- `frontend/app/appointment/page.tsx` — consultant booking calendar
- `frontend/app/context/CaseContext.tsx` — session state (caseId, caseType, description, history)
- `backend/api/views/chat.py` — classify + chat views
- `backend/api/views/cases.py` — case submit + status views
- `backend/api/views/scheduling.py` — Calendly URL + webhook

---

## ASCII Flow: Frontend Navigation

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND PAGE FLOW                               │
└─────────────────────────────────────────────────────────────────────────┘

  / (Landing)
       │
       ▼
  /language  ──────── user picks EN or ES
       │
       ▼
  /case-type  ◄─── user types their legal issue description
       │
       │  [user hits Send]
       │
       ▼
  ┌────────────────────────────────────────┐
  │   Privacy Disclosure Modal             │
  │                                        │
  │  [btn-primary: "Continue to Plan →"]   │  ← prominent blue button
  │                                        │
  │  "Prefer no AI? click here"            │  ← text button (fixed ✓)
  └───────────┬───────────────┬────────────┘
              │               │
              ▼               ▼
           /chat          /appointment
              │           (description preserved in CaseContext ✓)
              │
              ▼
  AI classifies case
  (POST /api/chat/classify/)
              │
              ▼
  Multi-turn AI chat
  (POST /api/chat/)
              │
              ▼
  "Analysis Complete" card
              │
              ▼
  submitCase()
  (POST /api/cases/submit/)
              │
              ▼
          /dashboard
              │
  [Not scheduled yet?]
              │
              ▼
         /appointment
         (calendar UI)
              │
              ▼
  [Confirm] → alert() only (no API call yet)


  Out-of-scope cases:
  /case-type ──demo link──► /other-results
                             (static resources page)
```

---

## ASCII Flow: Backend API

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         BACKEND API FLOW                                 │
└─────────────────────────────────────────────────────────────────────────┘

Frontend                    Django REST API              OpenAI / DB
────────                    ─────────────                ───────────

POST /api/chat/classify/
  { description, language }
        │
        ▼
  ClassifyView
        │──── openai_service.classify_case() ──────────► GPT classify
        │◄─── { classification, confidence, reasoning } ◄──────────
        │
        ▼
  { classification, confidence }
        │
        ▼ (frontend stores in CaseContext)

POST /api/chat/
  { message, case_type, history, current_node }
        │
        ▼
  ChatView
        │──── load mindmap/{case_type}.json ──────────── filesystem
        │──── openai_service.generate_chat_response() ── GPT chat
        │◄─── { response, current_node, suggested_actions }
        │
        ▼
  { response, current_node, suggested_actions }
  (suggested_actions: ["submit_case"] triggers Analysis Complete UI)

POST /api/cases/submit/
  { description, language }
        │
        ▼
  CaseSubmitView
        │──── openai_service.classify_case() ──────────► GPT (2nd classify)
        │──── Case.objects.create() ────────────────────► SQLite
        │◄─── { case_id, ai_confidence, status }
        │
        ▼
  { case_id, ai_confidence }
  (frontend stores caseId, pushes to /dashboard)

GET /api/cases/{id}/status/
        │
        ▼
  CaseStatusView
        │──── Case.objects.get(pk=id) ─────────────────► SQLite
        │◄─── CaseStatusSerializer ◄────────────────────
        │
        ▼
  { id, status, case_type, summary, documents,
    appointment_scheduled, appointment_date,
    appointment_completed, reviewer_notes }

GET /api/scheduling/calendly-url/
        │
        ▼
  CalendlyUrlView → returns env CALENDLY_URL
  (⚠ not yet wired to frontend /appointment page)

POST /api/scheduling/webhook/
        │
        ▼
  CalendlyWebhookView → receives Calendly event
  (⚠ TODO: update case.appointment_scheduled, unlock docs)

GET /api/videos/{case_type}/
        │
        ▼
  VideoListView → returns videos for dashboard

GET /api/mindmaps/{case_type}/
        │
        ▼
  MindMapDetailView → returns mindmap JSON structure
```

---

## Bug Fixed: Data Break at AI vs Consultant Choice

```
PREVIOUS BEHAVIOR (broken):
────────────────────────────

/case-type → Privacy Modal
                   │
    ┌──────────────┴──────────────┐
    │                             │
[AI button]              [tiny text link]
    │                             │
    ▼                             ▼
classify() call       <Link href="/appointment">
sets CaseContext                  │
    │                     ✗ NO DATA CARRIED
    ▼
 /chat

FIXED BEHAVIOR:
───────────────

/case-type → Privacy Modal
                   │
    ┌──────────────┴──────────────┐
    │                             │
[AI button]              [text button (onClick)]
    │                             │
    ▼                             ▼
classify() call         setUserDescription(description)
sets CaseContext         router.push("/appointment")
    │                             │
    ▼                             ▼
 /chat                     /appointment
                           (description preserved ✓)
```

**Fix location:** `frontend/app/case-type/page.tsx:215`

---

## 10 Business Case Scenarios

### Scenario 1 — Housing Eviction: AI Path (Happy Path)

**User:** English-speaking tenant in Nogales, AZ who received an eviction notice.

**Flow:**
1. `/language` → selects English
2. `/case-type` → types: *"My landlord gave me a 5-day eviction notice but I paid rent on time"*
3. Privacy Modal → clicks **"Continue to Plan →"**
4. `POST /api/chat/classify/` → `{ classification: "housing", confidence: 0.94 }`
5. `CaseContext` stores description, caseType=`housing`, confidence=`0.94`
6. `/chat` → multi-turn AI conversation about tenant rights and AZ eviction statutes
7. AI returns `suggested_actions: ["submit_case"]` → "Analysis Complete" card shown
8. `POST /api/cases/submit/` → case record created, `caseId` returned
9. `router.push("/dashboard")` → legal plan displayed with videos and locked documents
10. User books appointment from dashboard → `/appointment`

**Expected outcome:** Dashboard shows housing-specific legal plan, documents locked pending appointment.

---

### Scenario 2 — Housing Eviction: Consultant Path (Bug Fixed)

**User:** Same tenant, but prefers speaking with a human consultant directly.

**Flow:**
1. `/language` → selects English
2. `/case-type` → types: *"My landlord gave me a 5-day eviction notice"*
3. Privacy Modal → clicks **"Prefer no AI? click here"**
4. ~~(Bug: plain `<Link>` navigated to /appointment with empty context)~~
5. **(Fixed):** `setUserDescription(description)` called → `router.push("/appointment")`
6. `/appointment` → `CaseContext.userDescription` contains eviction description
7. User selects time slot and books appointment

**Fix reference:** `frontend/app/case-type/page.tsx:215`
**Expected outcome:** Appointment page has user description preserved for consultant context.

---

### Scenario 3 — Domestic Violence: High-Confidence AI Classification

**User:** Spanish-speaking resident describing a domestic violence situation.

**Flow:**
1. `/language` → selects Español
2. `/case-type` → types description in Spanish
3. Privacy Modal → continues with AI
4. `POST /api/chat/classify/` → `{ classification: "domestic_violence", confidence: 0.97 }`
5. High confidence (>0.90) triggers `priority_review=true` flag on backend
6. AI chat guides user through safety planning and legal options in Spanish
7. `POST /api/cases/submit/` → case created with `priority_review=true`
8. `/dashboard` → status badge shows "Under Priority Review"

**Expected outcome:** Priority escalation visible on dashboard; reviewer can add notes.

---

### Scenario 4 — Medical Debt: Out-of-Scope Redirect

**User:** Resident with a medical billing dispute.

**Flow:**
1. `/language` → selects English
2. `/case-type` → types: *"I have $8,000 in medical bills I cannot pay"*
3. Privacy Modal → continues with AI
4. `POST /api/chat/classify/` → `{ classification: "other", confidence: 0.72 }`
5. Currently: only reachable via demo link → `/other-results`
6. Expected: frontend should auto-route to `/other-results` when `classification === "other"`

**Gap identified:** Auto-routing on `other` classification not yet implemented — only accessible via the demo link in `case-type/page.tsx:323-328`.

---

### Scenario 5 — Spanish-Speaking User: Full Bilingual Flow

**User:** Monolingual Spanish speaker.

**Flow:**
1. `/language` → selects Español
2. All UI text renders from Spanish translation keys via `useLanguage()`
3. `/case-type` → types description in Spanish
4. `POST /api/chat/classify/` called with `{ language: "es", description: "..." }`
5. `POST /api/chat/` called with `language: "es"` — OpenAI responds in Spanish
6. `/dashboard` — all labels, video content, and documents in Spanish
7. `/appointment` — booking interface in Spanish

**Expected outcome:** Consistent Spanish UI throughout; backend passes language to OpenAI.

---

### Scenario 6 — API Offline: Demo Mode Fallback

**User:** Any user when backend is unavailable (dev/demo environment).

**Flow:**
1. User reaches `/chat`
2. `POST /api/chat/` fails (network error or 500)
3. Frontend falls back to `sampleConversations[language]` (hardcoded demo data)
4. `POST /api/cases/submit/` fails silently
5. `/dashboard` → `fallbackVideos` displayed instead of API-fetched content
6. Documents section shows locked placeholder

**Expected outcome:** App degrades gracefully without crashing; demo content visible.

---

### Scenario 7 — Case Status Polling: Appointment Unlocks Documents

**User:** Has completed AI chat and submitted case; waiting for appointment.

**Flow:**
1. Case submitted → `caseId` stored in `CaseContext`
2. `/dashboard` → React Query polls `GET /api/cases/{id}/status/` every 30 seconds
3. Case status: `{ appointment_scheduled: false, documents: [{ is_locked: true }] }`
4. User books Calendly appointment
5. Calendly fires `POST /api/scheduling/webhook/` with appointment event
6. **(TODO):** Webhook handler updates `case.appointment_scheduled = True`
7. Next poll returns `{ appointment_scheduled: true }`
8. Dashboard unlocks documents for download

**Gap identified:** `CalendlyWebhookView` is a stub — does not update the case record.

---

### Scenario 8 — Returning User: Session Storage Restore

**User:** Started a chat session, closed the browser tab, then returned.

**Flow:**
1. User completes multi-turn chat, browser closed mid-session
2. User reopens app and navigates to `/chat`
3. `CaseContext` reads from `sessionStorage` on mount
4. Stored state: `{ userDescription, caseType, confidence, chatHistory, currentNode }`
5. Chat UI rehydrates with previous history displayed
6. User continues from the same conversation node

**Expected outcome:** Seamless resume within the same browser session.
**Limitation:** `sessionStorage` clears on browser close — cross-session restore not supported.

---

### Scenario 9 — Low Confidence Classification: Human Escalation

**User:** Describes a situation that doesn't clearly match any supported case type.

**Flow:**
1. `/case-type` → types ambiguous description
2. `POST /api/chat/classify/` → `{ classification: "housing", confidence: 0.43 }`
3. Low confidence (<0.5) → backend sets `priority_review=True` on case creation
4. `/dashboard` → status badge changes to "Under Priority Review"
5. Staff reviewer adds `reviewer_notes` via admin panel
6. `GET /api/cases/{id}/status/` returns updated notes to frontend
7. Dashboard displays reviewer notes to user

**Expected outcome:** Human oversight triggered; user informed their case is under manual review.

---

### Scenario 10 — Consultant Books & Webhook Confirms

**User:** Skipped AI, booked directly with a consultant via Calendly.

**Flow:**
1. `/case-type` → types description → Privacy Modal → clicks "Prefer no AI? click here"
2. **(Fixed):** Description stored in `CaseContext` via `setUserDescription()`
3. `/appointment` → Calendly embed loads (from `GET /api/scheduling/calendly-url/`)
4. User selects time slot and confirms booking in Calendly
5. Calendly fires `POST /api/scheduling/webhook/` with `{ event: "invitee.created" }`
6. **(TODO):** `CalendlyWebhookView` updates: `appointment_scheduled = True`, sets `appointment_date`
7. Next dashboard poll detects `appointment_scheduled: true`
8. Documents unlocked: `is_locked` set to `False`
9. User downloads their legal documents

**Gaps identified:**
- Calendly URL not yet fetched by `/appointment` page
- Webhook does not update the case model (`backend/api/views/scheduling.py:40-42`)
- No `caseId` association when user skips the AI path entirely

---

## Summary of Known Gaps

| # | Issue | File | Status |
|---|-------|------|--------|
| 1 | No-AI path drops user description | `case-type/page.tsx:215` | **Fixed** |
| 2 | Calendly webhook is a stub | `scheduling.py:40-42` | TODO |
| 3 | Documents always locked by default | `models.py` | TODO |
| 4 | `other` classification has no auto-route | `case-type/page.tsx` | TODO |
| 5 | Calendly URL not fetched by appointment page | `appointment/page.tsx` | TODO |
| 6 | No caseId when consultant path taken | `cases.py` / `CaseContext` | TODO |
