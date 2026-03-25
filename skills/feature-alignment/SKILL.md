---
name: feature-alignment
description: Analyzes meeting transcripts and client documents to extract features, evaluate necessity/feasibility/cost, then generates an interactive HTML scoping tool with recommended scope, timeline, editable hours/costs, and localStorage persistence. Triggers on "feature alignment", "evaluate features", "scope features", "scope this project", "MVP vs V2", "feature cost breakdown", "which features should we build", "build a feature alignment".
metadata:
  author: Benmore Technologies
  version: 2.0.0
  category: discovery
---

# Feature Alignment

## Instructions

### Step 1: Gather Inputs

Ask the user for the following. Accept whatever combination they provide:

1. **Meeting transcripts** - Discovery calls, kickoff meetings, follow-ups (any format: raw text, pasted transcript, or file path)
2. **Client documents** - PRDs, requirements docs, technical specs, Lovable/Figma exports, schema docs, or any other project artifacts
3. **Project directory** - Where to save the output HTML file

After analyzing the transcripts/documents but BEFORE generating the HTML, you MUST ask the user these questions interactively (do not skip even if partially mentioned in transcripts):

4. **Budget range** - "What is the client's minimum and maximum budget? (e.g., $30k-$50k)" — Always ask because clients may adjust scope up or down regardless of individual feature prices.
5. **Client timeline** - "What is the client's target launch date or timeline? (e.g., 'by June 2026', '90 days', '3 months')" — This determines how aggressively features must be prioritized and whether dedicated vs shared resources are needed.

These two inputs are critical because:
- Budget determines which features fit in the recommended scope even if individual feature costs are lower or higher — the client will use the interactive tool to toggle features in/out like a configurator
- Timeline constrains the recommended scope to what's achievable within the timeframe at 40 hrs/week

### Step 2: Extract & Analyze Features from Source Materials

Read all provided transcripts and documents carefully. Extract:

- **Explicit feature requests** - Things the client directly asked for
- **Implied requirements** - Infrastructure, auth, compliance, or technical foundations that are necessary but not explicitly requested
- **Nice-to-haves** - Features the client mentioned as optional, future, or "would be nice"
- **Out-of-scope items** - Things explicitly deferred, rejected, or too expensive for current phase
- **Client priorities** - What they emphasized as most important, what has deadlines
- **Technical dependencies** - What must be built before other things can work
- **Third-party integrations** - APIs, services, or vendors mentioned and their procurement complexity
- **Timeline constraints** - Deadlines, launch dates, or phase milestones mentioned

### Step 3: Evaluate Each Feature

For each extracted feature, determine:

| Field | Description |
|-------|-------------|
| Name | Clear, concise feature name |
| Description | What it does in 1-2 sentences |
| Category | `core` / `business` / `enterprise` / `not-included` |
| Necessity | Why needed (or not), referencing transcript/doc context |
| Complexity | 1-10 scale (see table below) |
| Components | Sub-tasks with individual hour AND cost estimates |
| Dependencies | Other features this requires or enables |
| Risks | Technical, business, or compliance risks |
| Included | `true` for core/business, `false` for enterprise/not-included |
| Recommended | `true` for features you recommend building in the current engagement |

**Category definitions:**

- **Core MVP** (`core`): Product does not function without this. Non-negotiable for launch.
- **Business** (`business`): Significantly enhances value. Strongly recommended for launch or near-term.
- **Enterprise** (`enterprise`): Adds value but not essential. V2 or post-launch candidate.
- **Not Included** (`not-included`): Explicitly deferred, out of budget, or not aligned with current phase.

**Complexity scale:**

| Score | Meaning |
|-------|---------|
| 1-3 | Standard CRUD, simple UI, well-known patterns |
| 4-6 | Custom logic, third-party integrations, moderate state management |
| 7-8 | Real-time systems, complex algorithms, multi-system coordination, compliance-heavy |
| 9-10 | ML/AI, novel architecture, regulatory certification, multi-vendor orchestration |

**Component cost estimation:**

Each component gets BOTH an hour estimate AND a cost estimate. These are independent — cost is not derived from hours. Consider:
- Seniority of developer needed (junior vs senior vs specialist)
- Third-party licensing or API costs baked into the component
- Complexity premium for compliance-critical or security-sensitive work
- Whether the work can be parallelized or must be sequential

### Step 4: Build the Recommended Scope

Select which features should be in the **Recommended Scope** — this is your professional recommendation for what the client should build in this engagement. Consider:

- Client's stated priorities and deadlines
- Budget constraints
- Technical dependencies (don't recommend Feature B without Feature A)
- Risk-adjusted timeline (add buffer for API procurement, compliance review, etc.)
- What delivers the most value per dollar spent

The recommended scope should be a subset that fits within or near the budget range and is achievable within the client's timeline.

### Step 5: Generate the Output

Read the interactive template and populate the `defaultProjectData` JavaScript object with:

1. `clientName` - From the transcript/docs
2. `projectName` - Descriptive project name
3. `date` - Today's date
4. `budgetMin` / `budgetMax` - From client input or inferred
5. `features[]` - All evaluated features with components, hours, costs, and recommended flags

**IMPORTANT template location:** The template file is at the path the user specifies, or search for `interactive-template.html` in common locations (`~/Downloads/`, project directory, or `references/` folder).

Save the result as `[ProjectName]_Feature_Alignment.html` in the project directory.

**Data format:**

```javascript
const defaultProjectData = {
    clientName: "Client Name",
    projectName: "Project Name",
    date: "2026-03-24",
    budgetMin: 30000,
    budgetMax: 50000,
    features: [
        {
            id: 1,
            name: "Feature Name",
            description: "What this feature does.",
            category: "core",
            necessity: "Why this is needed, referencing client context.",
            complexity: 7,
            dependencies: ["Other Feature"],
            risks: "Key risks identified.",
            included: true,
            recommended: true,
            components: [
                { id: 1, name: "Sub-task name", hours: 40, cost: 8000 },
                { id: 2, name: "Another sub-task", hours: 60, cost: 12000 }
            ]
        }
    ]
};
```

### Step 6: Present Summary

After generating the file, provide a brief summary:

1. **Total features extracted** and how they were categorized
2. **Recommended scope** - features, total hours, total cost, estimated timeline at 40 hrs/week
3. **Timeline fit** - whether the recommended scope fits within the client's stated timeline, and if not, what needs to be cut or phased
4. **Budget fit** - whether the recommended scope is within budget range, and how the client can use the interactive toggles to adjust
5. **What was deferred** and why
6. **Key risks** that could affect timeline or cost
7. **Open questions** - anything unclear from the transcripts that the client should clarify

## Transcript Analysis Tips

When reading meeting transcripts:

- **Client says "must have" / "non-negotiable" / "can't launch without"** → `core`, `recommended: true`
- **Client says "would be nice" / "eventually" / "Phase 2"** → `enterprise`, `recommended: false`
- **Client says "not right now" / "too expensive" / "maybe later"** → `not-included`, `recommended: false`
- **Developer/consultant mentions risk, complexity, or timeline concern** → Capture in `risks` field
- **Budget numbers mentioned** → Use for `budgetMin`/`budgetMax`
- **Timeline mentioned ("by June", "90 days")** → Factor into recommended scope sizing
- **Multiple meetings** → Later meetings may override or clarify earlier ones. Use the most recent position.

## Examples

**Example 1: Restaurant HRIS from discovery transcripts**

User provides 2 meeting transcripts discussing a restaurant HR/payroll platform. From analysis:
- Auth, payroll engine, tip management, compliance → `core` (can't run restaurants without these)
- Documents, PTO, reporting, notifications → `business` (needed for full product but not day-1 critical)
- Benefits admin, ATS, mobile app, AI chatbot → `enterprise` (high value but too large for MVP)
- SOC2 certification, California compliance → `not-included` (explicitly deferred by client)
- Budget discussed as $30k-$43k dedicated, June deadline → size recommended scope accordingly

**Example 2: SaaS client portal**

User provides a single meeting transcript. Client wants: auth, dashboard, messaging, AI recommendations, mobile app. Budget $20k-$30k.
- Auth + Dashboard → `core`
- Messaging → `business`
- AI recommendations → `enterprise`
- Mobile app → `not-included` (separate project, App Store overhead)
- Recommended scope: auth + dashboard + messaging = ~$24k, fits budget

**Example 3: Budget overrun**

If all recommended features exceed `budgetMax`, present two options:
1. **Reduced scope** - Move lowest-priority `business` features to `enterprise`
2. **Phased approach** - Keep all recommended but split into Phase 1 / Phase 2 with separate timelines

Flag this clearly in the output summary and let the client/team decide.

## Troubleshooting

**Template not found**
Search for `interactive-template.html` in `~/Downloads/`, the project directory, or ask the user for the path.

**Component IDs conflict**
Use sequential IDs starting at 1 across ALL components in the file (not per-feature).

**Features seem too vague**
If transcripts don't provide enough detail for component-level breakdown, create reasonable sub-tasks based on industry standard patterns and flag them as estimates that need validation.

**Cost vs hours mismatch**
Hours and costs are independent. A 40-hour task might cost $12,000 (senior developer) or $6,000 (junior). Price based on the skill level required for that specific component.
