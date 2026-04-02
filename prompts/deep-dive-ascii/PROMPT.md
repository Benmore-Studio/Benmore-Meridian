---
name: deep-dive-ascii
description: Build thorough ASCII flow presentations with pipe alignment verification
tags: [presentation, ascii, research, playground]
scope: general
project: ""
---

Use the /playground skill and use the presentation, use context7mcp, websearch, /find-skills, /superpowers, and build very very thorough ASCII flows of API exchanges and features, be hyper-critical, and do a deep research for each of those features. Make a new presentation for me.

CRITICAL REQUIREMENT — ASCII PIPE ALIGNMENT:
Every ASCII diagram MUST have perfectly aligned pipes. Follow these rules during GENERATION and then VERIFY after.

## Generation Rules (prevent misalignment at source)

### Sequence Diagrams
1. FIRST define canonical column positions as a comment to yourself: e.g. "Entity A=col 2, Entity B=col 25, Entity C=col 46"
2. Use those EXACT column numbers for EVERY pipe on EVERY line — no eyeballing
3. When text between pipes is shorter than the column gap, pad with spaces to hit the exact column
4. When text is longer than the gap, truncate or abbreviate — NEVER push a pipe to a different column
5. The header pipe line (first line with all entity pipes) MUST match the body lines exactly

### Box Diagrams
1. Count the border width: if top-left is at col X and top-right is at col Y, then EVERY content border must be at col X and col Y — no exceptions
2. Pad ALL content lines to the SAME width before adding the right border
3. For nested boxes: define outer width first, then inner width, and verify both independently
4. Bottom border must have the SAME number of dash chars as the top border

### Tables (pipe-delimited)
1. Define column widths from the header row
2. Pad every cell to match its column width exactly

## Verification (run AFTER all ASCII blocks are written)

After writing the complete HTML file, run an inline Python checker via Bash (do NOT create a .py file). The checker must:

1. Find all `<div class="ascii-flow">...</div>` blocks
2. Strip HTML tags and decode entities to get pure visual text
3. For each block, find all lines with 3+ pipe characters
4. Count how often each column position appears across all pipe-lines
5. Group nearby columns (within 3 chars) and pick the most frequent as canonical
6. Report any line where a pipe is NOT at a canonical position (drift > 0)
7. IGNORE intentional nested structure: if a non-canonical position appears on 5+ lines consistently, it's an inner box, not drift

Fix every real drift issue found. Then re-run the checker to confirm zero issues.

## Common Pitfalls (from real debugging sessions)
- HTML `<span>` tags add zero visual width but complicate post-hoc fixing — get alignment right BEFORE wrapping text in color spans
- Sequence diagram lines where text spans multiple columns (like long API paths) are the #1 source of drift — count characters explicitly
- Nested box right edges wobble when content lines have different text lengths — always pad to border width
- Box bottom borders often end up 1 dash short — count dashes, don't eyeball

$ARGUMENTS
