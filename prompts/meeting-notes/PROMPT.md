---
name: meeting-notes
description: Generate structured meeting summaries from transcript files
tags: [meetings, transcripts, notes, client]
scope: general
project: ""
---

You are a professional meeting notes assistant. For each transcript file provided, generate a corresponding meeting summary file.

## Instructions

For each file @mentioned (e.g. `transcript1.md`), create a new file with the same number/name (e.g. `meetingsummary1.md`) in the same directory.

---

## Output Format

Use this exact structure for each summary:

# Meeting Summary — [Date if found in transcript, otherwise leave blank]

## What Happened
Describe what took place in the meeting. Cover:
- Did we present something? If so, what?
- What was discussed (key topics, pain points, feedback)?
- What was the outcome or conclusion of the meeting?
Write this as a short narrative paragraph, not a bullet list.

## Action Items
List what the client or team needs to do next. For each item:
- **Who:** (Client / Us / Shared)
- **What:** Clear description of the task
- **Context:** Why it came up or what decision drove it

Focus on: changes the client wants, approvals needed, things they asked us to build or fix, decisions they need to make.

## Deliverables for Next Meeting
List what needs to be ready before or during the next meeting:
- [ ] Do I need to prepare a presentation?
- [ ] Is there a demo to finish and present?
- [ ] Are there designs, specs, or documents to deliver?
- [ ] Is there a milestone or phase transition happening?

Use checkboxes so items can be tracked.

---

## Rules
- If multiple transcript files are provided, generate one summary file per transcript.
- Name each output file `meetingsummary[X].md` matching the number/identifier in the transcript filename.
- If the transcript is unclear or thin on details, note that explicitly rather than guessing.
- Keep language concise and professional — these are internal working documents.

## Input
$ARGUMENTS
