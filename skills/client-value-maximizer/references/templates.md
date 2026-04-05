# Output Templates

## Quick Wins Report

Use this format when synthesizing audit findings into a prioritized list.

```markdown
# Quick Wins Report — [Project Name]
Generated: [date]

## Summary
- Total findings: [N]
- Critical: [N] | High: [N] | Medium: [N] | Low: [N]
- Estimated total effort: [range]
- Quick wins (trivial + small effort): [N] items

## Priority Matrix

### P0 — Critical (fix before next deploy)
| # | Finding | File(s) | Effort | Dimension |
|---|---------|---------|--------|-----------|
| 1 | ...     | ...     | ...    | ...       |

### P1 — High (fix this sprint)
| # | Finding | File(s) | Effort | Dimension |
|---|---------|---------|--------|-----------|

### P2 — Medium (schedule for next sprint)
| # | Finding | File(s) | Effort | Dimension |
|---|---------|---------|--------|-----------|

### P3 — Low (backlog)
| # | Finding | File(s) | Effort | Dimension |
|---|---------|---------|--------|-----------|
```

## Requirements Document

Use this format when writing the implementation requirements from prioritized findings.

```markdown
# Implementation Requirements — [Project Name]
Generated: [date]
Batch: [batch number] of [total batches]

## Scope
Implementing [N] items from Quick Wins Report priorities [P0/P1/P2].

## Items

### [Item number]. [Short title]
- **Source finding**: Quick Win #[N] — [dimension]
- **File(s)**: [paths]
- **Current behavior**: [what happens now]
- **Required behavior**: [what should happen]
- **Acceptance criteria**:
  - [ ] [specific, testable criterion]
  - [ ] [specific, testable criterion]
- **Dependencies**: [none | list items that must be done first]

## Implementation Groups (by file ownership)

### Group A: [description, e.g., "Frontend components"]
Items: #1, #3, #7
Files touched: [list]
Agent assignment: Agent 1

### Group B: [description, e.g., "Backend views"]
Items: #2, #5
Files touched: [list]
Agent assignment: Agent 2

[Ensure no two groups touch the same file.]
```

## Delivery Checklist

Use this format as the final deliverable summary.

```markdown
# Delivery Checklist — [Project Name]
Date: [date]

## Changes Delivered

### [Dimension 1 name]
- [ ] [Change description] — [file path] — [line range or commit]
- [ ] [Change description] — [file path] — [line range or commit]

### [Dimension 2 name]
- [ ] [Change description] — [file path] — [line range or commit]

## Verification

### Build
- [ ] `npm run build` passes with zero errors
- [ ] `npm run lint` passes (or list accepted warnings)
- [ ] No new TypeScript errors introduced

### Tests
- [ ] Existing test suite passes ([N]/[N])
- [ ] [List any new tests added]

### Manual Spot-Checks
- [ ] [Key flow 1] works end-to-end
- [ ] [Key flow 2] works end-to-end

## QA Document Updates
- [ ] [QA doc path] updated with new test cases for [changes]

## Not Addressed (deferred)
- [Item] — Reason: [why deferred]
- [Item] — Reason: [why deferred]

## Notes for Client
[Any context the client should know about the changes.]
```

## QA Update Template

Append to existing QA doc or create new section.

```markdown
## [Date] — Value Maximizer Updates

### New Test Cases

#### [Area/Feature]
| Test Case | Steps | Expected Result | Status |
|-----------|-------|-----------------|--------|
| [name]    | 1. .. | ...             | PASS   |

### Regression Checks
- [ ] [Existing flow] still works after [change]
- [ ] [Existing flow] still works after [change]
```
