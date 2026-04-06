---
name: better-scope-gen
description: Use when generating scope agreements and feature outlines for a Benmore client project. Triggers include requests to create scope docs, generate proposals, build scope agreements, or produce feature breakdowns from technical architecture documents.
---

# Better Scope Generator

Generate client-ready development agreements and comprehensive feature outlines from technical architecture documents. Produces two document types: **Scope Agreements** (one per build option, client-facing development agreements) and a **Scope Outline** (single reference doc with full hierarchical feature breakdown).

## Template

**The scope agreement MUST follow the template at `SCOPE_AGREEMENT_TEMPLATE.md` (in the same directory as this skill file).** Read this template file at the start of every scope generation session. The template is the single source of truth for document structure, section ordering, signature formatting, and boilerplate language.

When generating a SCOPE_AGREEMENT.md, copy the template structure exactly and fill in the `[PLACEHOLDER]` values with project-specific content. Do NOT restructure sections, reorder content, change signature formats, or deviate from the template layout.

## Signature & Form Field Conventions

The template uses bracket-delimited shortcodes for interactive form fields. Preserve these exactly as they appear in the template:

| Shortcode | Usage |
|-----------|-------|
| `[SIGNATURE]` | Signature capture field |
| `[PRINTED_NAME]` | Text input for legal name |
| `[DATE]` | Date picker field |
| `[CLIENT_TITLE]` | Text input for client's title |
| `[CHECKBOX:label]` | Checkbox for option/payment selection |

**Rules:**
- Client signature blocks use table format with `[PRINTED_NAME]`, `[CLIENT_TITLE]`, `[SIGNATURE]`, and `[DATE]` — match the template's table layout exactly
- Benmore's signature block uses `[BENMORE_REP_NAME]` and `[BENMORE_REP_TITLE]` placeholders — filled in from the user's input (see Step 1f)
- Multiple signature blocks exist in the template (Section 4 Scope Agreement Signatures, Section 6 Implementation Plan Signatures, Section 8 final Agreement Signatures) — include ALL of them
- Option and payment selection uses `[CHECKBOX:label]` format as shown in the template

<HARD-GATE>
Do NOT generate any documents until you have:
1. Read the template file at `SCOPE_AGREEMENT_TEMPLATE.md` (in the same directory as this skill file)
2. Read the technical architecture file
3. Confirmed the number of build options with the user
4. Asked whether there is a development credit (and if so, the amount)
5. Confirmed the Benmore representative's name and title
6. Received timeline estimates per module from the user
</HARD-GATE>

## Process

### Step 1: Gather Inputs (One Question at a Time)

**1a. Read the Template**
Before anything else, read `SCOPE_AGREEMENT_TEMPLATE.md` (in the same directory as this skill file) to load the current template structure. This is your reference for the entire generation process.

**1b. Architecture File**
Ask: "What is the path to your technical architecture document?"

Read the file. Parse it to identify:
- All major modules (look for patterns like `## MODULE N`, `## N. Module Name`, `## Module Name`, or any consistent H2 structure)
- All subfeatures within each module (H3 sections: `### N.M Feature Name` or similar)
- Descriptions and implementation details under each subfeature
- Any build option annotations (e.g., "Option B/C only", "Option C", "Enterprise")

Present back to the user: "I found N modules with M total subfeatures. Here's what I extracted:" followed by a summary list. Ask them to confirm or correct.

**1c. Build Options**
Ask: "How many build options do you need? (1-3)"

If more than 1 option, ask: "Give me a short label for each option." (e.g., "A: MVP, B: Enterprise" or "A: MVP, B: Premium, C: Enterprise")

**1d. Development Credit**
Ask: "Is there a development credit for this project? If yes, what's the amount?"

If yes, the user provides the credit amount. This value will be used to fill in the Development Credit line items throughout the template (pricing tables, payment schedules, checkbox labels, etc.).

If no, **remove all Development Credit line items** from the generated document — remove the "Development Credit" rows from pricing tables, remove credit references from payment term descriptions, remove credit mentions from the Section 8 checkbox labels, and adjust all "Base Development Cost" / "Total Due" rows so the base cost IS the total (no subtraction step). The template includes Development Credit placeholders by default; strip them entirely when there is no credit.

**1f. Benmore Representative**
Ask: "Who is the Benmore representative signing this agreement? (Name and title)"

This fills the `[BENMORE_REP_NAME]` and `[BENMORE_REP_TITLE]` placeholders in all three Benmore signature blocks (Section 4, Section 6, and Section 8). If the user's name and title can be inferred from the project's CLAUDE.md or from prior conversation context, confirm with them rather than asking from scratch (e.g., "I see Connor West, Technical Consultant in the project docs — should I use that?").

**1g. Timeline Estimates**
Present the extracted module list **for each build option separately**, showing which modules and features are included in that option. Each option may have different modules, different feature scopes within shared modules, or entirely unique modules.

Ask the user to provide timeline estimates (in weeks) **per module, per option**. Do NOT use multipliers — each option gets its own independent estimate because the work involved is different, not just "more of the same."

Present like this:
```
Option A (MVP) modules:
  Accounts & Auth: ?
  Mediator Profiles: ?
  ...

Option B (Premium) — additional modules beyond MVP:
  Outlook Calendar Integration: ?
  Analytics Dashboard: ?
  Custom Admin Dashboard: ?
  ...

Option C (Enterprise) — additional modules beyond Premium:
  Multi-State Expansion: ?
  Mobile Application: ?
  ...
```

The user provides estimates for each. Always add a **2-week buffer** to every option's total.

**Important:** Higher-tier options are additive — they include all work from lower tiers plus their own additional modules. The total for Option B = Option A total + Option B additional modules + buffer. The total for Option C = Option B total + Option C additional modules + buffer.

Present the calculated totals back for confirmation before generating.

### Step 2: Generate Scope Agreement

Generate a **single** `SCOPE_AGREEMENT.md` file containing ALL build options. The client selects their preferred option at signing. Do NOT generate separate documents per option.

**How to use the template:**

1. Start with the template structure from `SCOPE_AGREEMENT_TEMPLATE.md` (in the same directory as this skill file)
2. Replace all `[PLACEHOLDER]` values with project-specific content derived from the architecture doc and user inputs
3. Adjust the number of option columns in tables to match the actual number of build options (1, 2, or 3). If only 1 option, remove the multi-column comparison tables and simplify. If 2 options, remove the third column.
4. Fill in Section 4 (Scope Agreement) with every module and subfeature from the architecture doc, organized into the template's subsections:
   - **4.1 Core Features** — modules/features included in ALL options
   - **4.2 Premium-Only Features** — modules/features included in Options B and C only (omit if only 1 option)
   - **4.3 Enterprise-Only Features** — modules/features included in Option C only (omit if fewer than 3 options)
   - **4.4 Feature Comparison Matrix** — full matrix showing which modules are in which options
   - **4.5 Exclusions** — features explicitly NOT included
   - **4.6 Scope Change Process** — use template's boilerplate exactly
   - **Scope Agreement Signatures** — use template's table-format signature block
5. Fill in all other sections following the template's structure, placeholder patterns, and boilerplate language
6. Include the **Foundation Month Setup** subsection under Section 5 as shown in the template
7. Include **Timeline Risk Scenarios** per option under Section 6 as shown in the template
8. Section 8 must include the **Agreement Terms** numbered list from the template

**Placeholders to fill:**

| Template Placeholder | Source |
|---------------------|--------|
| `[PROJECT_NAME]` | From architecture doc or user |
| `[ONE_LINE_DESCRIPTION]` | Derived from architecture doc |
| `[XXX]` (project number) | From project directory name (e.g., 145) |
| `[CLIENT_NAME]`, `[CLIENT_COMPANY]` | From user or project CLAUDE.md |
| `[BENMORE_REP_NAME]`, `[BENMORE_REP_TITLE]` | From user (Step 1f) — fills all three Benmore signature blocks |
| `[MONTH] [YEAR]` | Current date |
| `[X] modules`, `[X] features` | Count from architecture doc |
| Timeline/week placeholders | From user-provided estimates |
| Price placeholders (`$[RATE_A]`, etc.) | From user — use `[TBD]` if not provided |
| `[KEY_DIFFERENTIATOR_N]` | Project-specific differentiators between options |
| Module/feature placeholders | From architecture doc |
| Risk/vendor/service placeholders | From architecture doc and project context |
| `[DAY]`, `[TIME]` | Meeting schedule from project CLAUDE.md or user |
| `[DOMAIN]` | From project CLAUDE.md or user |

### File Naming

- Always a single file: `SCOPE_AGREEMENT.md`
- All build options are contained within the single document — the client selects their preferred option at signing

### Step 3: Generate Scope Outline

Generate a single `SCOPE_OUTLINE.md` with the full hierarchical feature breakdown. This is the comprehensive reference document. Follow this structure:

```markdown
# {Project Name} — Platform Scope Outline
## Feature Modules, Sub-Features, and Connections

**Last Updated:** {Date}
**Platform:** {One-line platform description}
**Stack:** {Tech stack summary, pipe-separated}

---

## Table of Contents

1. [{Module 1 Name}](#anchor)
2. [{Module 2 Name}](#anchor)
...
N. [Connections Map](#connections-map)
N+1. [Data Flow: End-to-End {Primary Flow Name}](#data-flow)
N+2. [Build Option Coverage Matrix](#build-option-coverage-matrix)
N+3. [Open Decisions](#open-decisions)

---

## Module 1 — {Module Name} <a name="module-1"></a>

**Purpose:** {One sentence describing what this module does}

### 1.1 {Subfeature Name}
- {Implementation detail bullet 1}
- {Implementation detail bullet 2}
- {Implementation detail bullet 3}

### 1.2 {Subfeature Name}
- {Implementation detail bullet 1}
...

### 1.N {Subfeature Name} (Option B)
- {Implementation detail — mark option-specific features in the heading}
...

{Repeat for ALL modules and ALL subfeatures. Include EVERY detail from the architecture doc.
Mark option-specific features in the section heading: "(Option B)", "(Option C)", "(Option B/C)"}

---

## Connections Map <a name="connections-map"></a>

### Dependency Table

| From | To | Connection |
|------|-----|------------|
| Module {X} ({Name}) | Module {Y} ({Name}) | {How X depends on or triggers Y} |
...

{Map EVERY inter-module dependency. Be exhaustive.}

---

## Data Flow: End-to-End {Primary Transaction Name} <a name="data-flow"></a>

### Phase 1 — {Phase Name}

```
{Step-by-step flow showing which modules are involved at each step}
{Use arrow notation and [Module N] references}
{Example: User registers → [Module 2] email verification sent via SendGrid}
```

### Phase 2 — {Phase Name}
...

{Walk through the complete primary transaction lifecycle from start to finish,
showing every module touchpoint. Include 3-5 phases covering the full user journey.}

---

## Build Option Coverage Matrix <a name="build-option-coverage-matrix"></a>

{ONLY include this section if there are multiple build options}

### Module 1 — {Module Name}

| Feature | Option A ({Label}) | Option B ({Label}) | Option C ({Label}) |
|---------|:--------------:|:------------------:|:---------------------:|
| 1.1 {Subfeature name} | ✓ | ✓ | ✓ |
| 1.2 {Subfeature name} | ✓ | ✓ | ✓ |
| 1.N {Option B subfeature} | — | ✓ | ✓ |
...

{Repeat for EVERY module. Use ✓ for included, — for excluded.}

---

## Open Decisions <a name="open-decisions"></a>

| Decision | Stakeholder | Impact |
|----------|-------------|--------|
| {Decision needed} | {Who decides} | {What it affects if not resolved} |
...

---

*This document reflects all decisions made through {date}.*
```

### Step 4: Save and Report

Save all files to the project root directory (same level as CLAUDE.md).

Report to the user:
- List of files created
- Total timeline per option
- Count of modules and subfeatures extracted
- Any gaps or assumptions made

## Key Rules

1. **Always read the template first** — Read `SCOPE_AGREEMENT_TEMPLATE.md` (in the same directory as this skill file) before generating. The template is the canonical structure. If the template has been updated since this skill was last edited, follow the template.
2. **Every subfeature from the architecture doc must appear** in both the scope agreement's feature set section and the scope outline. Nothing gets lost.
3. **Option-specific features** must be clearly marked. If a subfeature only applies to Option B/C, it should NOT appear in Option A's scope agreement.
4. **The scope outline is the source of truth** — it contains ALL features across ALL options with the full hierarchical breakdown.
5. **Scope agreements are client-facing** — professional tone, scannable, clear what they're agreeing to.
6. **Timeline scenarios** always use 20% best / 65% realistic / 15% worst probability split.
7. **Price is always [TBD]** unless the user provides pricing. Never invent costs.
8. **Operating costs** should be realistic estimates based on the tech stack identified in the architecture doc.
9. **Risks** should be honest and specific to the integrations/APIs used.
10. **Exclusions** must explicitly list features that were discussed but deferred or rejected.
11. **The scope agreement feature set is detailed** — each subfeature includes a parenthetical implementation description, not just a name. This is what the client is contractually agreeing to.
12. **Timeline guarantees are always included** — early completion stops billing, Benmore delays are absorbed, client delays extend timeline at standard rate.
13. **Section ordering follows the template's 8-section structure** — (1) Project Summary, (2) Implementation Plan Agreement, (3) Price Agreement, (4) Scope Agreement, (5) Implementation Plan Overview, (6) Timeline Milestones, (7) Non-Code Requirements, (8) Agreement & Signatures.
14. **Multiple signature blocks** — The template includes signature blocks within Section 4 (Scope Agreement), Section 6 (Implementation Plan), and Section 8 (final Agreement). Include ALL of them.
15. **Signature table format is mandatory** — Use the template's table format for all signature blocks (Name/Title/Signature/Date rows in a two-column table). Do NOT use inline shortcodes outside of tables.
16. **Development credit is optional** — The template includes Development Credit placeholders. If the user says there IS a credit, fill in the user-provided amount everywhere the template references it (pricing tables, payment terms, checkbox labels). If there is NO credit, strip all Development Credit rows, references, and subtraction steps from the generated document entirely — Base Development Cost becomes Total Due directly.
17. **Foundation Month Setup** — Always include the foundation/scaffolding subsection under Section 5 as defined in the template.
18. **Agreement Terms** — Section 8 must include the numbered Agreement Terms list covering scope, timeline, early completion, payment, communication, post-launch support, IP, and confidentiality.
19. **Development starts "the day after initial payment is received"** — use this exact phrasing from the template, not "upon contract signing."
20. **Module duration estimates** — Each module in Section 4 must include `*Estimated Duration: [X] week(s)*` under the module heading.
21. **Billing Preference section** — Section 8 includes a Billing Preference subsection (between "Payment Option Selected" and "Agreement Terms") with two billing arrangements: Self-Directed Payment (invoices) and Automatic Payment (Stripe). Always include this section exactly as it appears in the template. It uses initials lines, not `[CHECKBOX:]` shortcodes.
