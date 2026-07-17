---
name: init-bmp-project
description: "Onboard a client project into the Benmore portal: pull blueprint + Slack, seed it, run the AI pipeline"
argument-hint: "[BEN-number]  (optional; else read from the repo path)"
tags: [benmore, portal, onboarding, bmp, tickets, blueprint]
scope: general
project: ""
---

Onboard a client project into the Benmore portal (benmore.ai) and show me the resulting board when it's done.

**BEN number:** $ARGUMENTS
(If that's empty, read it from THIS repo's path — client repos are named with the BEN number, e.g. `.../201-Acme` or `.../BEN-201-Acme`. Confirm the number you're using before doing anything.)

**Hard rules — do not break these:**
- This is read + internal-portal-write ONLY. **Never contact the client. Never post to Slack. Never send email or invites.**
- **Do NOT create or delete tickets/deliverables.** The pipeline generates the board; you run it and report.
- Client Slack content is ALWAYS read via your Slack CLI/MCP — **never** via the Benmore API.

Work top to bottom:

**1. Blueprint lookup.** Read `~/.claude/docs/blueprint-api.md` for the auth + endpoints, then find the blueprint project matching this BEN number. Capture its **project UUID**, its **name**, and its **contract value**. (This is the Benmore/blueprint API, authed per that doc — this is the only thing the Benmore API is used for here.)

**2. Find the Slack channel.** Using your Slack CLI/MCP, find this project's channel — they're named `#benmore-<num>`; if that isn't it, search for the client's name. Capture the channel **ID**. If this session has **no Slack MCP available**, skip steps 2 and 4, seed blueprint-only, and tell me clearly that Slack was skipped.

**3. Create + seed the project.** Run (fill in the values you gathered):
```
bmp add-project <BEN> --name "<name>" --uuid <uuid> --slack <channel-id> --contract <contract-total>
```
This pulls the meetings, transcripts, docs and invoices from blueprint and kicks off extraction. Note: some **discovery meetings may be declined by the model** (mental-health / crisis content) — that is expected and benign, not an error; they'll show as "sources not analysed."

**3b. Extract the development agreement — THE BASELINE (usually the biggest single source; do NOT skip).** `blueprint-sync` pulled the signed agreement as a *document*, but its text is not extracted automatically — and it's the whole scope the client signed up for (all the features, pipelines and code). It's a PDF, so **you** read it. Find the signed development agreement / contract for this project (a blueprint signature doc / the contract asset — get it via the Benmore API or the blueprint doc), read its **full** text, then extract it as the project's baseline:
```
bmp extract-agreement <BEN> < agreement.txt
```
(or pipe the text you read directly). This is **async**: the command queues the extraction and returns in seconds (`queued: 1`) — the worker then extracts it host-side over a few minutes (this deliberately bypasses the edge timeout that a 30k-char synchronous extraction would hit). Agreement-sourced features land as **baseline** tickets. Skipping this is why a board ends up nearly empty — the meetings only mention a handful of features; the agreement is the real scope. If you genuinely cannot locate a signed agreement, say so explicitly. If the agreement is very long, you can also queue the other signed scope docs (technical architecture, user flows) the same way with `--source-id <label>` so each lands under its own source — run them **one at a time** (back-to-back large extractions can trip transient model rate-limits).

**4. Backfill Slack history.** Read the channel's **full** message history AND files via your Slack CLI/MCP. For every shared **file**, actually read its contents and put the extracted text into that message's `text` field — so the file's content gets extracted, not just noted (a file with no text lands as a "shared a file" placeholder). Emit one JSON object per message/file, newline-delimited:
```
{"ts":"<slack ts>","user":"<Uxxxx>","text":"<message OR file content>","files":["name.pdf"]}
```
Then load it:
```
bmp slack-load <BEN> < messages.ndjson
```

**5. Extract everything:**
```
bmp sync <BEN>
```

**5b. Reveal the seeded board (do this LAST, after extraction settles).** Extraction runs as background jobs (a couple of minutes). New client-facing items (features, client commitments) from meetings/Slack are held on a +4h catch window so a *watching* client can't see a bad extraction — but during onboarding there's no watching client, and the whole point of seeding is to get everything visible so you can review it. So once the extraction jobs have finished (give it a few minutes; you can check `svc_facts` applied-vs-pending, or just wait), release the window for this project:
```
bmp publish-now <BEN>
```
This makes every held item visible now and triggers an immediate apply, so the full seeded board is there for review. It's one-shot — ongoing post-onboarding extractions keep the 4h window. If some extraction jobs were still running when you ran it, run it once more after they finish to sweep up stragglers.

**6. Report.** Timing depends on the source:
   - **The signed agreement / scope docs (the baseline) apply IMMEDIATELY** — they're signed, reviewed content, so they skip the catch window. Within a couple of minutes of the extraction jobs finishing (extraction runs as background jobs) + the next `apply_facts` run (every 30m), the **full baseline board is populated for review**. That's the whole point of seeding: seed → everything's there → you review → move on. Give it a few minutes, then `bmp board <BEN>` should show the baseline tickets.
   - **Live meeting/Slack items** (feature tickets and client commitments extracted from meetings/Slack) are still held on a **+4h catch window** (`publish_at ≈ now + 4h`) so a bad extraction can be killed before it reaches a *watching* client's board. Those auto-apply ~4h later. Our-side deliverables (owed_by benmore) apply immediately from any source.

   To confirm success: check the `bmp sync` output ran, then `bmp board <BEN>` for the baseline tickets and `bmp deliverables <BEN>`. If the baseline hasn't appeared after a few minutes, the extraction jobs may still be running or `apply_facts` hasn't ticked yet — read `svc_facts` for the project and count applied vs pending.

   Then report to me: how many meetings extracted (and how many were declined), how many baseline tickets + deliverables landed, any live items still on the 4h window, and anything that looks like slop, a duplicate, or a miscategorised item so we can tune the prompts. If you want the baseline visible the instant you finish (not waiting up to 30m for the `apply_facts` cron), that's fine to note — it self-applies.

**Notes / troubleshooting:**
- If `bmp` isn't on PATH, it's the symlink `/opt/homebrew/bin/bmp` → `scripts/bmp` in the benmore-go checkout; call it by full path if needed.
- If `bmp whoami` says not logged in, run `bmp login` first (browser SSO) and then continue.
- If the project already exists, `add-project` will say so — in that case skip step 3 and just run steps 4–6 to (re)load Slack and re-sync.
