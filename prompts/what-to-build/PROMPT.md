Analyze the referenced meeting transcripts and summaries to produce a comprehensive product vision document. Cross-reference all sources — flag any contradictions or ambiguities between transcripts and summaries.

Generate a markdown file called `what-to-build.md` in the current working directory with the following sections:

## 1. Problem Statement
- What problems is the client trying to solve?
- Why do these problems matter to them now? What's the urgency or trigger?
- What is the cost of NOT solving these problems (lost revenue, wasted time, risk)?

## 2. Proposed Solution
- How does the client envision solving these problems?
- What is their dream/ideal solution if there were no constraints?
- Are there existing tools, systems, or workflows this replaces or integrates with?

## 3. Users & Use Cases
- Who will use the tool? List each distinct user role/persona.
- For each user: what will they use it for, and how does their life improve?
- What does a typical day/workflow look like before vs. after the tool?

## 4. Must-Have Features
- List every feature explicitly requested or strongly implied.
- For each feature, note which problem it solves and which user it serves.
- Distinguish between features the client explicitly stated vs. ones you inferred.

## 5. Nice-to-Have / Implied Features
- Features mentioned casually, wished for, or logically needed but not explicitly requested.

## 6. Constraints & Context
- Any mentioned technical constraints (platforms, integrations, existing tech stack).
- Timeline or budget signals (even vague ones like "we need this soon").
- Regulatory, compliance, or security requirements mentioned.

## 7. Open Questions
- Contradictions between different transcripts or summaries.
- Ambiguities that need client clarification before scoping.
- Assumptions you had to make and why.

---

Use direct quotes from the transcripts to support key points. Write in clear, factual prose — this document will be used downstream for scoping and architecture decisions.
