# site-capture — Troubleshooting

Common failure modes, in rough order of how often they bite.

## `playwright-cli: command not found`

You're missing the binary the playwright-cli skill ships. Install:

```bash
npm install -g @playwright/cli@latest
playwright-cli --version
```

Then re-run.

## `Failed to start server / EADDRINUSE / port already in use`

The dev server you assumed lives on port 3000 may have been bumped to 3001, 5001, 5173, etc.

```bash
lsof -iTCP:3000 -sTCP:LISTEN
```

Set `BASE_URL` explicitly:

```bash
BASE_URL=http://localhost:5001 bash capture-all.sh
```

## Frames are completely blank / white

Most likely: the dev server compiled but the page is still loading. Two fixes:

- Increase `wait_ms_after_nav` (e.g. `WAIT_MS_AFTER_NAV=3000`).
- Add a `route.wait_for` selector for the route in `sitemap.json` (currently requires a 2-line patch to `capture-page.sh`; the lib already has a session helper to use).

## Frames show command palette / modal / unexpected overlay

Your eval-driven scroll triggered a global keybind (Cmd+K) or clicked something. Two fixes:

- Don't use `eval` to dispatch events — only `window.scrollTo`. The default scripts do this; if you customised them, revert.
- Add `playwright-cli -s=… press Escape` before the screenshot loop.

## `.next` cache stale — routes 500 after `bun run build`

If `next dev` was running while you ran `next build`, the `.next` directory is partially overwritten and dev-only manifest files are missing. Symptoms: `ENOENT: no such file or directory, open '.next/static/development/_buildManifest.js.tmp.*'`.

```bash
pkill -f "next dev"
rm -rf .next
PORT=5001 bun run dev
```

## Hydration warnings in the playwright-cli output

These show up because `playwright-cli` surfaces browser console messages by default. They almost never affect screenshots. If you want the run to fail loudly when they appear:

```bash
STRICT_CONSOLE=1 bash capture-all.sh
```

*(Note: STRICT_CONSOLE handling lives in the default scripts as a placeholder. If you genuinely care about console errors as a gate, wire it up — see `pw_eval` in `lib.sh` for how to read messages.)*

## GIF is too big to share

Inputs that move the needle, in priority order:

1. `GIF_WIDTH=800` — single largest factor for file size on screenshot content.
2. `QUALITY=78` — `gifski` quality knob. 78–82 is the sweet spot.
3. `FRAMES_PER_PAGE=18` — fewer frames trade smoothness for size.
4. `FPS=10` — slows playback; combined with fewer frames this can halve the file without looking jittery.

Re-stitch without recapturing:

```bash
GIF_WIDTH=800 QUALITY=80 FPS=10 \
  gifski --output captures/out/home/page.gif \
         --fps 10 --quality 80 --width 800 \
         captures/out/home/frames/f-*.png
```

## Components in `sitemap.json` don't render

`playwright-cli screenshot <selector>` quietly fails when the selector matches nothing. Re-test the selector via `playwright-cli snapshot` and refine. Common fixes: replace `:nth-of-type` with a stable `data-*` attribute on the component.

## `ttyd` connection refused

That's vhs, not this skill. site-capture doesn't need ttyd. If you tied a vhs recording into your workflow and want it to work: `brew install ttyd` and rerun.

## Captures land in the wrong directory

The skill resolves paths against `$CAPTURES_DIR`, which defaults to `./captures` (the directory you ran the script from). If you cd'd partway through, set explicitly:

```bash
CAPTURES_DIR=/path/to/project/captures bash capture-all.sh
```

## Many routes 404 in the middle of a run

The dev server probably crashed or rebuilt mid-capture. `capture-all.sh` continues past individual failures and reports the count at the end. Re-run `FILTER=<name>` for just the broken ones.
