---
name: skill-chain-loop
description: Chain skills into automated loops — review, feedback, memory, scheduling
tags: [skills, automation, chaining, loop, orchestration]
scope: general
project: ""
---

Set up a skill chain that loops and improves over time.

Pattern (based on Random Labs skill chaining):
1. **Trigger** — Scheduled scan or event finds work to do
2. **Execute** — Writing/review/code skill drafts output
3. **Human review** — User edits and approves
4. **Feedback** — System diffs draft vs final, records patterns
5. **Learn** — Diffs accumulate, distill into new rules, written back to skill
6. **Loop** — Next trigger produces better output

Apply this to: $ARGUMENTS

Use the three rings:
- **Scheduling**: timed triggers via cron or hooks (no manual invocation)
- **Memory**: results written to files, read into context next run
- **Feedback**: compare output against edits, update rules automatically

Start with one cron job. Memory and feedback will follow.
