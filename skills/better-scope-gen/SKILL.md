---
name: better-scope-gen
description: >
  Generate client-ready development agreements (SCOPE_AGREEMENT.md) and comprehensive feature outlines
  (SCOPE_OUTLINE.md) from technical architecture documents. Produces a single scope agreement containing
  all build options (1-3 tiers) with pricing tables, timeline milestones, and signature blocks, plus a
  hierarchical scope outline with connections map and data flow. Supersedes the older scope-gen skill.
  Use when the user says "generate scope agreement", "create development agreement", "scope agreement
  from architecture doc", "build scope document", "create proposal from tech architecture", "generate
  scope outline", "scope this project for a client", "create client agreement", or wants to produce
  formal client-facing scope documents from technical architecture deliverables.
metadata:
  author: Benmore Technologies
  version: 1.0.0
  category: discovery
---

# Better Scope Generator

Generate client-ready development agreements and comprehensive feature outlines from technical architecture documents. Produces two document types: a **Scope Agreement** (single document covering all build options, client-facing) and a **Scope Outline** (single reference doc with full hierarchical feature breakdown).

**Important:** This skill supersedes the older `scope-gen` skill. If both are installed, use `better-scope-gen` for all new scope generation work.

## Signature & Form Field Conventions

The template uses bracket-delimited shortcodes for interactive form fields. Preserve these exactly as they appear in the template:

| Shortcode | Usage |
|-----------|-------|
| `[SIGNATURE]` | Signature capture field |
| `[PRINTED_NAME]` | Text input for legal name |
| `[DATE]` | Date picker field |
| `[TEXTBOX:Title]` | Text input for client's title |
| `[CHECKBOX:label]` | Checkbox for option/payment selection |

**Rules:**
- Client signature blocks use table format with `[PRINTED_NAME]`, `[TEXTBOX:Title]`, `[SIGNATURE]`, and `[DATE]` — match the template's table layout exactly
- Benmore's signature block uses `[BENMORE_REP_NAME]` and `[BENMORE_REP_TITLE]` placeholders — filled in from the user's input (see Step 1e)
- Multiple signature blocks exist in the template (Section 4 Scope Agreement Signatures, Section 6 Implementation Plan Signatures, Section 8 final Agreement Signatures) — include ALL of them
- Option and payment selection uses `[CHECKBOX:label]` format as shown in the template
- The Billing Preference section in Section 8 uses `[SIGNATURE]` and `[DATE]` table blocks (not `[CHECKBOX:]` shortcodes)

## Process

### Step 1: Gather Inputs

Do NOT generate any documents until ALL of the following steps are complete.

**1a. Read the Template**
Read `SCOPE_AGREEMENT_TEMPLATE.md` (in the same directory as this skill file) to load the current template structure. The template is the single source of truth for document structure, section ordering, signature formatting, and boilerplate language.

**1b. Architecture File**
Ask: "What is the path to your technical architecture document?"

Read the file. Parse it to identify:
- All major modules (look for patterns like `## MODULE N`, `## N. Module Name`, `## Module Name`, or any consistent H2 structure)
- All subfeatures within each module (H3 sections: `### N.M Feature Name` or similar)
- Descriptions and implementation details under each subfeature
- Any build option annotations (e.g., "Option B/C only", "Option C", "Enterprise")

If the architecture doc does not follow a recognizable heading structure, ask the user to clarify which sections represent modules and which represent subfeatures. If the doc is empty or unreadable, stop and ask the user for a valid file.

Present back to the user: "I found N modules with M total subfeatures. Here's what I extracted:" followed by a summary list. Ask them to confirm or correct before proceeding.

**1c. Build Options**
Ask: "How many build options do you need? (1-3)"

If more than 1 option, ask: "Give me a short label for each option." (e.g., "A: MVP, B: Enterprise" or "A: MVP, B: Premium, C: Enterprise")

**1d. Development Credit**
Ask: "Is there a development credit for this project? If yes, what's the amount?"

If yes, the user provides the credit amount. This value fills the `$[CREDIT_AMOUNT]` placeholder throughout the template.

If no, **remove all Development Credit line items** from the generated document — remove the "Development Credit" rows from pricing tables, remove credit references from payment term descriptions, remove credit mentions from the Section 8 checkbox labels, and adjust all "Base Development Cost" / "Total Due" rows so the base cost IS the total (no subtraction step).

**1e. Benmore Representative**
Ask: "Who is the Benmore representative signing this agreement? (Name and title)"

This fills the `[BENMORE_REP_NAME]` and `[BENMORE_REP_TITLE]` placeholders in all three Benmore signature blocks (Section 4, Section 6, and Section 8). If the user's name and title can be inferred from the project's CLAUDE.md or from prior conversation context, confirm with them rather than asking from scratch.

**1f. Timeline Estimates**
Present the extracted module list for each build option separately. Ask the user to provide timeline estimates (in weeks) per module, per option. Do NOT use multipliers — each option gets its own independent estimate.

Higher-tier options are additive — they include all work from lower tiers plus their own additional modules. The total for Option B = Option A total + Option B additional modules + buffer. The total for Option C = Option B total + Option C additional modules + buffer. Always add a **2-week buffer** to every option's total.

Present the calculated totals back for confirmation before generating.

### Step 2: Generate Scope Agreement

Generate a **single** `SCOPE_AGREEMENT.md` file containing ALL build options. The client selects their preferred option at signing. Do NOT generate separate documents per option.

**How to use the template:**

1. Start with the template structure from `SCOPE_AGREEMENT_TEMPLATE.md`
2. Replace all `[PLACEHOLDER]` values with project-specific content derived from the architecture doc and user inputs
3. Adjust the number of option columns in tables to match the actual number of build options:
   - **1 option:** Remove all multi-column comparison tables. Convert to single-value rows. Remove Sections 4.2, 4.3, and 4.4. Remove per-option phase tables in Section 5 (keep only one). Remove per-option milestone and risk tables in Section 6 (keep only one). Remove the "Build Option Selected" checkboxes in Section 8 (replace with a single statement of the option).
   - **2 options:** Remove the third column from all tables. Remove Section 4.3 (Enterprise-Only). Adjust Section 4.4 to two columns.
   - **3 options:** Use the template as-is.
4. Fill in Section 4 (Scope Agreement) with every module and subfeature from the architecture doc:
   - **4.1 Core Features** — modules/features included in ALL options
   - **4.2 Premium-Only Features** — included in Options B and C only (omit if only 1 option)
   - **4.3 Enterprise-Only Features** — included in Option C only (omit if fewer than 3 options)
   - **4.4 Feature Comparison Matrix** — full matrix (omit if only 1 option)
   - **4.5 Exclusions** — features explicitly NOT included
   - **4.6 Scope Change Process** — use template's boilerplate exactly
   - **Scope Agreement Signatures** — use template's signature block format
5. Each subfeature must include a parenthetical implementation description, not just a name — this is what the client is contractually agreeing to
6. Each module heading must include `*Estimated Duration: [X] week(s)*`
7. Adjust the Foundation Setup subsection heading in Section 5 to match the project's actual timeline (use `Weeks [X]-[X]` not hardcoded weeks)

### Step 3: Generate Scope Outline

Generate a single `SCOPE_OUTLINE.md` with the full hierarchical feature breakdown — the comprehensive reference document containing ALL features across ALL options. Include these sections:

- **Header:** Project name, last updated date, platform description, tech stack
- **Table of Contents:** All modules + Connections Map + Data Flow + Coverage Matrix + Open Decisions
- **Module sections:** Each module with Purpose, all subfeatures with implementation detail bullets. Mark option-specific features in headings: "(Option B)", "(Option C)", "(Option B/C)"
- **Connections Map:** Dependency table mapping every inter-module dependency
- **Data Flow:** End-to-end primary transaction lifecycle (3-5 phases showing module touchpoints)
- **Build Option Coverage Matrix:** Per-module table with checkmark/dash per option (omit if only 1 option)
- **Open Decisions:** Table of unresolved decisions with stakeholder and impact

### Step 4: Save and Report

Save all files to the project root directory (same level as CLAUDE.md).

Report to the user:
- List of files created
- Total timeline per option
- Count of modules and subfeatures extracted
- Any gaps or assumptions made

**Note:** Generated scope agreements contain client PII (names, signatures) and financial terms. Ensure the output directory is appropriate for sensitive documents and consider whether the file should be gitignored.

## Key Rules

1. **Every subfeature from the architecture doc must appear** in both the scope agreement and the scope outline. Nothing gets lost.
2. **Option-specific features** must be clearly marked. If a subfeature only applies to Option B/C, it should NOT appear in Option A's scope.
3. **The scope outline is the source of truth** — it contains ALL features across ALL options with the full hierarchical breakdown. The scope agreement draws from it.
4. **Scope agreements are client-facing** — professional tone, scannable, clear what they're agreeing to.
5. **Timeline scenarios** always use 20% best / 65% realistic / 15% worst probability split.
6. **Price is always [TBD]** unless the user provides pricing. Never invent costs.
7. **Operating costs** should be realistic estimates based on the tech stack identified in the architecture doc. Include a disclaimer that estimates are based on MVP-level traffic and may change.
8. **Risks** should be honest and specific to the integrations/APIs used.
9. **Exclusions** must explicitly list features that were discussed but deferred or rejected.
10. **Early completion** — billing stops when the final deliverable is deployed and accepted by the client. Use this phrasing consistently across all sections.
