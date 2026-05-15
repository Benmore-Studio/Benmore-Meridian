# site-capture — Recipes

Common patterns. Each recipe is a one-liner you can paste.

## Faster GIFs (cover more pages, smaller files)

```bash
FPS=18 FRAMES_PER_PAGE=18 GIF_WIDTH=800 QUALITY=80 \
  BASE_URL=http://localhost:5001 \
  bash ~/.claude/skills/site-capture/scripts/capture-all.sh
```

Lower `frames_per_page` makes the visible scroll jump further per frame. Raise `fps` to play those frames back faster. Drop `gif_width` and `quality` for smaller files.

## Light + dark sweep

```bash
for theme in dark light; do
  THEME=$theme OUT_DIR=captures/out-$theme \
    bash ~/.claude/skills/site-capture/scripts/capture-all.sh
done
```

The skill writes everything to a per-theme output directory. Diff with `git diff --stat captures/out-dark captures/out-light` or open both folders side by side.

## Viewport sweep (desktop, tablet, mobile)

```bash
for size in "1280 800" "768 1024" "390 844"; do
  read -r w h <<< "$size"
  VIEWPORT_WIDTH=$w VIEWPORT_HEIGHT=$h OUT_DIR=captures/out-${w}x${h} \
    bash ~/.claude/skills/site-capture/scripts/capture-all.sh
done
```

## Component-only capture (no scroll GIF)

For a single element on a specific page, skip the page wrapper:

```bash
BASE_URL=http://localhost:5001 bash ~/.claude/skills/site-capture/scripts/capture-component.sh \
  /weekly "section:nth-of-type(2)" weekly-grid
```

For *every* component listed under a route in `sitemap.json`, `capture-page.sh` will produce them automatically in `captures/out/<route>/components/`.

## Capture only one section of the sitemap

`FILTER` substring-matches both `name` and `path`:

```bash
FILTER=weekly bash ~/.claude/skills/site-capture/scripts/capture-all.sh
```

## Smoother scroll (overshoot range, capture extras)

```bash
FRAMES_PER_PAGE=60 FPS=24 WAIT_MS_BETWEEN_FRAMES=40 \
  bash ~/.claude/skills/site-capture/scripts/capture-page.sh /
```

## Recapture only the GIF after tweaking PNGs

The frames are kept on disk. If you want to change speed/width without re-navigating:

```bash
FPS=24 GIF_WIDTH=900 \
  gifski --output captures/out/home/page.gif \
         --fps 24 --width 900 --quality 90 \
         captures/out/home/frames/f-*.png
```

## Stitching only some pages into a tour

`stitch-tour.sh` reads sitemap order. To stitch a subset, temporarily comment out routes in `sitemap.json` (or copy `sitemap.json` → `sitemap.subset.json` and set `SITEMAP_FILE=$(pwd)/captures/sitemap.subset.json`).

## Hosting the GIF on the same site

Copy the produced GIF into `public/assets/` and reference it from an MDX page or the relevant skill markdown:

```bash
cp captures/out/tour.gif public/assets/site-tour.gif
# Then add ![](/assets/site-tour.gif) in your markdown.
```

## Sticky elements not behaving

Sticky headers can repeat in every frame. Two options:

1. Hide them while capturing (per route, in `sitemap.json`):
   ```json
   { "path": "/weekly", "name": "weekly", "pre_capture_script": "document.querySelector('header')?.style.setProperty('display','none','important')" }
   ```
   *(Note: `pre_capture_script` is not in the default capture-page.sh — add a one-line `pw_eval` if you need this; it's a 2-line patch.)*
2. Capture only the section you care about with `capture-component.sh`.
