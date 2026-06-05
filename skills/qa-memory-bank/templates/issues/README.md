# Issues

This folder is the bug database. The folder a file lives in *is* its status — never duplicate or track status anywhere else.

## Folders

- `open/` — filed and not yet fixed.
- `ready-for-retest/` — engineering claims fixed; QA must verify before closing.
- `verified-fixed/` — retested and confirmed.
- `wont-fix/` — explicitly accepted as out of scope or by design.

## Workflow

See [`../conventions.md`](../conventions.md#issue-lifecycle) for the full lifecycle. Quick version:

```
open/  ──fix──▶  ready-for-retest/  ──pass──▶  verified-fixed/
                       │
                       └──fail──▶  open/   (with `## Retest <date>` block)
```

## Naming

`ISSUE-NNNN-<short-kebab-slug>.md`. NNNN is global across all categories. Allocate via:

```
ls open ready-for-retest verified-fixed wont-fix 2>/dev/null \
  | grep -oE 'ISSUE-[0-9]+' | sort -u | tail -1
```

Then increment.

## Index (auto-stale; check folders for ground truth)

> Don't try to keep this list in sync — the folders are authoritative. This section exists only as a quick orientation; if it's empty/old, that's fine.

- Open: see `open/`
- Awaiting retest: see `ready-for-retest/`
- Closed: see `verified-fixed/` and `wont-fix/`
