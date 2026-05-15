---
name: site-capture
description: Capture a multi-page screenshot tour or scroll-GIF tour of a running website using the playwright-cli skill, with configurable speed, viewport, theme, and per-page component selectors. Use whenever the user wants to "screenshot every page", "capture the whole site", "make a tour GIF", "demo the site", "record a walkthrough", "show what the site looks like", "build a marketing reel", "capture all components", "visual diff before/after a release", "produce assets for a launch post", or anything that involves walking a sitemap and producing per-route PNGs / per-route GIFs / a single stitched mega-GIF. Especially relevant for personal sites, marketing pages, dashboards, and any Next.js / SPA / static-site project where the user is iterating on UI and wants reproducible visual artifacts. Pair with the playwright-cli skill — this skill is the orchestration layer on top of it.
allowed-tools: Bash(playwright-cli:*) Bash(npx:*) Bash(gifski:*) Bash(ffmpeg:*) Bash(bash:*) Bash(jq:*) Bash(mkdir:*) Bash(cp:*) Bash(mv:*) Bash(rm:*) Bash(ls:*) Bash(cat:*) Read Edit Write
---

# site-capture

Walk a website with the `playwright-cli` skill, take screenshots and per-page scroll GIFs of every route in a configurable sitemap, optionally zoom into named components, and stitch the results into a single tour. Built on top of the `playwright-cli` skill — no Playwright MCP, no `@playwright/test`, no Puppeteer.

The skill is parameterised: point it at any base URL with any sitemap and it produces a reproducible artefact set.

## When this skill earns its keep

- You shipped a UI change and want before/after captures of every page in one shot.
- You're recording a launch demo and need PNGs + a stitched tour GIF without manually clicking through everything.
- You want a deterministic visual regression baseline (`make screenshots` style) outside `@playwright/test`.
- You need per-component crops (the hero, the pricing card, the search palette) for marketing copy.

## Mental model

```
sitemap.json  ──┐
                ├─►  capture-all.sh  ──►  out/<route>/{full.png, frames/, page.gif}
config knobs  ──┘                                            │
(fps, width, theme, viewport)                                ▼
                                              gif-stitch.sh ──► out/tour.gif (optional)
```

Every script reads the same `config.json` so behaviour is consistent across pages.

## Quick start

```bash
# 1. Initialise a capture project in the current repo
bash ~/.claude/skills/site-capture/scripts/init.sh

# 2. Edit captures/sitemap.json to list the routes you care about
#    (init.sh seeds a starter file)

# 3. Run a single page
BASE_URL=http://localhost:3000 bash ~/.claude/skills/site-capture/scripts/capture-page.sh /weekly

# 4. Run the whole sitemap
BASE_URL=http://localhost:3000 bash ~/.claude/skills/site-capture/scripts/capture-all.sh

# 5. Stitch every per-page GIF into one tour
bash ~/.claude/skills/site-capture/scripts/stitch-tour.sh
```

Output lands in `captures/out/` by default (gitignored by `init.sh`).

## Configuration

`captures/config.json` — every script reads this. Defaults are reasonable for a 1280×800 desktop tour at ~12 fps.

```json
{
  "base_url": "http://localhost:3000",
  "viewport": { "width": 1280, "height": 800 },
  "device_scale_factor": 2,
  "theme": "dark",
  "frames_per_page": 30,
  "scroll_step_px": 119,
  "fps": 12,
  "quality": 85,
  "gif_width": 1100,
  "wait_ms_after_nav": 1200,
  "wait_ms_between_frames": 80,
  "browser": "chrome",
  "session_name": "site-capture"
}
```

Override per-run with env vars: `FPS=24 GIF_WIDTH=800 bash capture-all.sh`. Anything not set falls back to `config.json`, which falls back to the SKILL defaults.

`captures/sitemap.json` — list of routes, optionally with per-route overrides and component selectors.

```json
{
  "routes": [
    {
      "path": "/",
      "name": "home",
      "components": [
        { "selector": "header nav", "name": "nav" },
        { "selector": "section:nth-of-type(1)", "name": "hero" }
      ]
    },
    { "path": "/weekly", "name": "weekly-index" },
    {
      "path": "/weekly/2026-W19",
      "name": "w19",
      "frames_per_page": 60,
      "wait_ms_after_nav": 2000
    }
  ]
}
```

Per-route fields:
- `path` *(required)* — appended to `base_url`.
- `name` — output directory name. Defaults to a slugified `path`.
- `components` — list of `{selector, name}` pairs for component-only screenshots.
- Any config knob (e.g. `frames_per_page`, `theme`) — overrides the global for this route only.

## Scripts and what they do

Every script is a thin bash wrapper that shells out to `playwright-cli` and `gifski`. Read them when you need to tune behaviour; they're short.

| Script                 | Purpose                                                                                           |
| ---------------------- | ------------------------------------------------------------------------------------------------- |
| `scripts/init.sh`      | Seed `captures/{config.json, sitemap.json}` in the current repo, add `captures/out/` to gitignore |
| `scripts/capture-page.sh <path>` | Capture one route: full-page PNG, scroll-frame PNGs, per-page GIF, optional component crops |
| `scripts/capture-all.sh` | Iterate every entry in `sitemap.json`, calling `capture-page.sh` for each                       |
| `scripts/capture-component.sh <path> <selector> <name>` | One-off crop of a single element on a single page                |
| `scripts/stitch-tour.sh` | Concatenate every `out/<route>/page.gif` into `out/tour.gif`                                    |
| `scripts/lib.sh`         | Shared bash helpers — config loader, slugify, `playwright-cli` session lifecycle               |
| `scripts/probe.sh <path>` | Sanity-check a route (HTTP status + image counts + console errors) before running the full capture |

Each script accepts `--help` and prints its env-var contract.

See `references/recipes.md` for worked examples (faster GIFs, light+dark sweep, viewport sweep, mobile portrait, sticky-header capture).

See `references/troubleshooting.md` for the common failure modes (`ttyd` connection refused, stale dev server, hydration warnings polluting frames, GIF too large for Slack).

## How this composes with the playwright-cli skill

`site-capture` does not replace `playwright-cli`. Every actual browser action goes through the `playwright-cli` binary the skill ships:

- A named session (`-s=site-capture` by default) is kept alive across pages so per-frame cost stays low.
- All navigation, viewport sizing, theme setting, scrolling, and screenshotting are `playwright-cli` calls.
- The skill exits the session at the end (or on error via a bash `trap`) so the binary never leaves orphaned chrome processes.

If you find yourself wanting a Playwright primitive that the wrapper doesn't expose, drop down to `playwright-cli` directly — it's installed and on PATH. The skill is just orchestration over it.

## Speed control

Three knobs, in order of impact:

1. **`fps`** — frame rate of the output GIF. 8 fps = jittery, smaller file. 18 fps = smooth, ~2x size. Default 12.
2. **`frames_per_page`** — how many scroll-position screenshots per route. More frames = smoother scroll, larger PNGs on disk, bigger final GIF. Default 30.
3. **`scroll_step_px`** — physical pixels scrolled between frames. Calculated as `(scrollHeight - viewportHeight) / (frames_per_page - 1)` by default; override to slow down/speed up the *visible* scroll while keeping frame count fixed.

To make a GIF *play faster* without re-capturing: re-stitch with higher `fps` (`FPS=24 bash stitch-tour.sh`). To make a tour *cover ground faster* with fewer frames: lower `frames_per_page` to 12–16 and the visible scroll will jump further per frame.

## Output layout

```
captures/
├── config.json
├── sitemap.json
└── out/
    ├── home/
    │   ├── full.png            # full-page screenshot
    │   ├── frames/             # f-00.png … f-29.png
    │   ├── page.gif            # stitched scroll GIF
    │   └── components/
    │       ├── nav.png
    │       └── hero.png
    ├── weekly-index/
    │   └── …
    ├── w19/
    │   └── …
    └── tour.gif                # all per-page GIFs concatenated (stitch-tour.sh)
```

PNGs are kept by default — re-stitch the GIF at any speed without recapturing. Delete `frames/` if you're done iterating and need disk.

## Failure modes worth knowing

- **Dev server on a different port.** The dev server may auto-bump if 3000 is occupied. Always pass `BASE_URL` explicitly when in doubt; the scripts will fail fast with a clear message if `BASE_URL` isn't reachable.
- **`ttyd` missing.** Only `stitch-tour.sh` and components needing `vhs` care; `playwright-cli` itself doesn't. If you don't need `vhs` recordings, ignore.
- **`.next` cache stale.** If you ran `next build` while `next dev` was active, the dev server's `.next/static/development/_buildManifest.js.tmp.*` files go missing and routes 500. `rm -rf .next && bun run dev` fixes it.
- **Hydration warnings in console.** Show up in `playwright-cli`'s console output and look alarming. Usually harmless for screenshots; rerun with `STRICT_CONSOLE=1` to fail the capture if anything more severe than `warning` appears.

## Don't

- Don't reinvent the loop in a Node script. The whole point is reproducibility from a terminal a human can drive — keep shelling out to `playwright-cli`.
- Don't write per-project Python or TypeScript capture utilities; extend the bash scripts or add a `recipes.md` entry instead.
- Don't put captured GIFs at the repo root. The shipped `init.sh` adds `captures/out/` to `.gitignore`. If you want to publish a specific GIF on a site, copy it under `public/assets/` and reference it from there.
