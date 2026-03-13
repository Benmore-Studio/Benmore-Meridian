# Multi-Diagram Patterns

## When to Split

Split a flow into multiple diagrams when ANY of these apply:

- Flow has more than ~8 stages
- Any section has 2+ decision branches or error loops
- Flow contains parallel sub-flows (e.g., template vs. freehand paths)
- Admin portal with multiple independent modules

**Never put a complex flow into one giant diagram.** Readers can't parse it, and Mermaid rendering degrades with large graphs.

## Structure

1. **Overview diagram** — Simple linear flow showing all stages as single nodes. No subgraphs, no decision branches. Gives the reader orientation at a glance.
2. **One detail diagram per complex section** — Each covers 2-4 stages with full branching, subgraphs, decision nodes, error states. Sized to fit on screen without scrolling.

## Example Splits

### Linear flow (12-stage sales rep)

```
Diagram 1: Overview (12 nodes, linear, no detail)
Diagram 2: Stages 5-7 — Enclosure Design & Measurement Validation
Diagram 3: Stages 8-9 — Parts Selection & Pricing
Diagram 4: Stages 10-12 — Payment, Documents & Submit
```

### Hub-and-spoke (admin portal with 3 modules)

```
Diagram 1: Overview (Login → Dashboard → 3 modules)
Diagram 2: Sub-Flow A — Parts Database Management
Diagram 3: Sub-Flow B — User & Access Management
Diagram 4: Sub-Flow C — Reporting Dashboard
```

### Branching flow (two distinct paths)

```
Diagram 1: Overview showing the branch point and both paths
Diagram 2: Path A — Template-based flow (detail)
Diagram 3: Path B — Freehand flow (detail)
```

## Overview Diagram Styling

Use a two-class approach — `startEnd` (green) for start/end, neutral `stage` for all intermediate nodes:

```
classDef startEnd fill:#34d399,stroke:#059669,color:#000
classDef stage fill:#1e3a5f,stroke:#60a5fa,color:#fff
```

Overview diagrams should be clean and scannable. No subgraphs, no decision diamonds, no error branches. Just the stage names connected linearly.

## Detail Diagram Entry/Exit Nodes

Connect detail diagrams to the overview using green start/end nodes that indicate where the reader is in the overall flow:

```
flowchart TD
    From([From: Customer Info]) --> FirstStep[Select Template]
    FirstStep --> ...
    ... --> LastStep[Save Design]
    LastStep --> To([To: Parts Selection])

    classDef startEnd fill:#34d399,stroke:#059669,color:#000
    class From,To startEnd
```

This gives readers context about where this detail section fits in the bigger picture.

## HTML Structure for Multi-Diagram Pages

```html
<!-- Overview -->
<div class="section">
    <div class="section-header">Complete Workflow Overview</div>
    <p style="color: rgba(255,255,255,0.6); margin-bottom: 16px; font-size: 0.95rem;">
        This overview shows the complete workflow at a glance. Detailed breakdowns for each section follow below.
    </p>
    <div class="diagram-container">
        <pre class="mermaid">[overview diagram]</pre>
    </div>
</div>

<div class="divider"></div>

<!-- Detail section (repeat for each complex section) -->
<div class="section">
    <div class="section-header">[Stage Range]: [Detail Section Name]</div>
    <p style="color: rgba(255,255,255,0.6); margin-bottom: 16px; font-size: 0.95rem;">
        [Context sentence — what this section covers and key decision points]
    </p>
    <div class="diagram-container">
        <pre class="mermaid">[detail diagram]</pre>
    </div>
</div>
```

Each detail section gets:
- A `section-header` with the stage range and name
- A context sentence explaining what this section covers
- Its own `diagram-container` with the detail diagram
- A `divider` between sections
