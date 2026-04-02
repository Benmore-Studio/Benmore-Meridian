---
name: user-flows-with-edge-cases
description: Create client-facing user flow presentations with SVG diagrams and edge case analysis
tags: [presentation, user-flows, client, edge-cases, discovery]
scope: general
project: ""
---

Using the referenced files, use the /presentation-maker skill to create a client-facing user flows presentation.

## Requirements
- Analyze all referenced files to identify the product, its actors, and their workflows
- For each actor, create a **happy path** slide, then a dedicated **edge cases** slide
- Identify any cross-actor or system-level flows and give them separate slides
- Use inline SVG flow diagrams with shapes and arrows — no ASCII, no Mermaid
- Match the project's existing design system if one exists (check CLAUDE.md and style files)
- Client-facing and non-technical — no internal jargon or implementation details

## Edge cases
For every flow, think deeply about what can go wrong. Consider:
- Timeouts and no-response scenarios
- Authorization or payment failures
- Mid-process cancellations by any party
- Disputes or reversal paths
- Expired credentials or permissions
- Concurrent or duplicate actions
- Connectivity or data failures
- Scope changes discovered mid-process
- Any domain-specific edge cases derived from the referenced materials

## Output
- Single self-contained HTML file (no external dependencies beyond Google Fonts)
- Save to `deliverables/`

$ARGUMENTS
