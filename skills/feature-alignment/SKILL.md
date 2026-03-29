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

### Step 5: Present Pricing for Approval

**IMPORTANT: Do NOT generate the HTML document yet.** First, present the full feature evaluation to the user in a clear summary including:

- Each feature name, category, cost, and estimated weeks
- Component breakdown with cost estimates per component
- Recommended scope summary with total cost and timeline
- Budget range context

Ask the user to:
1. Review and adjust the cost/time estimates if needed
2. Confirm the recommended scope
3. Approve the pricing before proceeding

Only proceed to Step 6 after receiving explicit approval from the user.

### Step 6: Generate the Output

Read the interactive template at `references/interactive-template.html` and populate the `D` (default data) JavaScript object with the evaluated features and user-approved pricing. Save the result as `[ProjectName]_Feature_Alignment.html` in the project directory.

The template includes:
- **localStorage persistence** — client changes (toggling features, editing costs) are saved automatically in the browser
- **Recommended scope panel** — shows the recommended MVP features with total cost/timeline
- **Expedited development toggle** — "Optimize for Pricing" vs "Optimize for Speed" (35% cost premium, compressed timeline by 5/7)
- **Budget gauge** — visual indicator of where the current scope sits relative to the budget range
- **Interactive feature cards** — clients can toggle features on/off, expand details, and edit component costs

**Data format to use:**

```javascript
const D = {
    clientName: "Client Name",
    projectName: "Project Name",
    date: "2026-03-28",
    budgetMin: 30000,
    budgetMax: 50000,
    features: [
        {
            id: 1,
            name: "User Authentication",
            description: "Login, registration, password reset with email verification.",
            category: "core",
            necessity: "Required for any user-facing platform.",
            complexity: 4,
            duration: 3,
            dependencies: [],
            risks: "OAuth provider integration complexity",
            included: true,
            recommended: true,
            components: [
                { id: 1, name: "Login & registration forms", cost: 4000 },
                { id: 2, name: "Password reset flow", cost: 2500 },
                { id: 3, name: "Email verification", cost: 3000 }
            ]
        }
    ]
};
```

**Key data fields:**
- `duration` — estimated weeks for the feature (used for timeline calculations)
- `cost` — on components, not features; feature cost is the sum of its components
- `included` — whether the feature is toggled on in the interactive tool
- `recommended` — whether the feature is in the recommended scope panel
- `category` — determines the tier badge and grouping in the UI

## Examples

**Example 1: Discovery meeting with a SaaS client**

User provides a meeting transcript from a discovery call. Actions:
1. Extract all features mentioned in the transcript
2. Identify implied requirements (auth, admin panel, etc.)
3. Categorize: auth + data model → `core`, dashboard + reporting → `business`, AI features → `enterprise`, mobile app → `not-included`
4. Build recommended scope from core + key business features
5. Present evaluation with costs to user for approval
6. After approval, generate interactive HTML

**Example 2: Budget overrun scenario**

If the recommended scope exceeds `budgetMax`, adjust by:
- Moving lowest-priority `business` features to `enterprise`
- Reducing component scope (e.g., "basic" instead of "advanced" version)
- Flagging the trade-off clearly in the necessity field

## Troubleshooting

**Template not rendering correctly**
Cause: `D` has malformed JSON or missing required fields.
Solution: Ensure all features have `id`, `name`, `category`, `included`, `recommended`, `duration`, and `components` (can be empty array). Verify `budgetMin`, `budgetMax` are numbers (not strings). Each component needs `id`, `name`, and `cost`.

**Component IDs conflict**
Cause: Duplicate `id` values across components.
Solution: Use sequential IDs starting at 1 across all components in the file (not per-feature).

**Budget gauge shows 0**
Cause: All features have `included: false`.
Solution: Set `included: true` for core and business features before saving.

**localStorage stale data**
Cause: Client sees old data after you regenerate the HTML with updated features.
Solution: The storage key is versioned by client+project name. If you need to force a refresh, change the version prefix in `getStorageKey()` or have the client clear localStorage for the page.
