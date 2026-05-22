---
name: network-graph-modal
description: Use when adding a force-directed network/bubble graph modal to an entity profile page — the kind that shows "related records" around a root entity with hover-highlight neighbourhoods, click-to-pin sidebar, multi-hop expansion, branch collapse, and pattern detection on shared signal values. Trigger on phrases like "bubble network graph", "force-directed graph modal", "network view of related X", "vis-network modal", "related-entities graph", "fraud-cluster visualisation", "duplicate-account network", "shared-signal clustering", "show relationships as a graph", "expand/collapse network branches", "pin a node in a network graph", "hover highlight 1-hop neighbourhood", "graph of who's connected to whom", or any time the user wants vis-network-style interactive exploration of a small-to-medium graph (10–200 nodes) on top of an existing JSON API that returns related entities. Works for any entity type — people, accounts, companies, vehicles, properties, claims, transactions — and any signal set (shared email/phone/address/device/IP/officer/VIN/whatever).
---

# Network graph modal (force-directed, pin-and-expand)

## What this skill is for

You want to drop a force-directed network graph modal into an entity profile page. The user opens it, sees their entity in the centre, sees related entities around it, can hover to highlight a node's 1-hop neighbourhood, click to pin the sidebar to a node/edge, expand any pinned node to fetch its own related entities (multi-hop walk), and collapse a branch to remove everything it brought in.

**This skill is ONLY the graph.** It is not the related-entity API, the scoring/confidence model, the list view, or the search index — it assumes those already exist and return the agreed JSON shape below. If the user also needs to build the API, weights, signals, etc., that's a separate concern.

The reference implementation is at `assets/network-graph.js` + `assets/network-graph.html`. They are intentionally hand-rolled (vanilla JS, no build step, inline styles) so they drop into any backend templating engine without dragging in a bundler. Copy them, search-and-replace the customization points listed below, and you have a working graph in well under an hour.

The interaction model — bright/faded colours by confidence bucket, hover-fade for 1-hop neighbourhood, click-to-pin sidebar, dashed-vs-solid edges for previewed-vs-confirmed expansions, pattern-detection for shared signal values — has been used in production for related-entity exploration (duplicate-account detection, shared-operator detection, KYC link analysis). Each behaviour exists because something earlier didn't work — see the comments inline.

## When to use it

- A "related X" feature on a profile page where X = company, person, account, property, vehicle, claim, transaction, or any entity with shared-signal links to other records.
- Graphs in the 10–200 node range. Below ~10 a list is fine. Above ~200 vis-network's barnes-hut layout starts to chug — switch to cytoscape + WebGL at that point.
- You already have (or can stand up) an API that, given an entity ID, returns a JSON list of related entities with the signals that connected them.

## When NOT to use it

- Pure org charts / tree structures — use a tree layout, not force-directed.
- Massive graphs (500+ nodes loaded at once) — performance falls off.
- Static infographics — the whole point of this is interactive pin/expand/highlight. If it's read-only, render a simpler SVG.

## Process

Follow these steps in order. Don't skip the customization checklist — every step represents something we got wrong at least once in the original build.

### 1. Confirm the data contract

The graph fetches `/your/entity/<id>/related/` and expects the response shape below. **If your API doesn't already return this shape, decide before writing any UI code whether to (a) update the API, or (b) write a thin adapter on the frontend.** Don't paper over an API mismatch in the middle of the graph code — it makes the customization points hard to find later.

```jsonc
{
  "success": true,
  "summary": {                                       // optional, only used if you keep summary tiles
    "total_related": 12,
    "high_risk": 3, "medium_risk": 5, "low_risk": 4
  },
  "related_entities": [                              // array key is configurable — set RELATED_KEY in the JS
    {
      "entity": {                                    // the related record. Field names are domain-specific.
        "id":   "abc-123",                           // REQUIRED: unique ID. Whatever field, set ID_FIELD.
        "name": "Example Record",                    // REQUIRED: display name. Set NAME_FIELD.
        // … any other fields you want to show in the sidebar tiles …
      },
      "risk_level": "high",                          // "high" | "medium" | "low" — controls node + edge colour.
      "confidence_label": "Almost certainly related",// free-text label shown in the sidebar.
      "signals": [                                   // what data points connect this entity to its parent.
        { "type": "phone", "label": "Same phone", "detail": "+1 555 0100", "weight": 30 }
      ]
    }
  ]
}
```

Two things the JS treats as load-bearing:

- Every related entity **must** have a stable unique ID at `entity[ID_FIELD]` — the graph uses it as the vis-network node id, the dedup key, the edge id seed, and the expansion fetch URL. If your IDs can be numeric or string, coerce to string consistently.
- `signals[].type` + `signals[].detail` drive the pattern-detection bolding ("3+ entities share the same value"). If `detail` is missing for a signal type, that signal won't participate in pattern detection — that's fine, just be aware.

The names `entity` / `related_entities` above are the defaults baked into the skill's JS. If your existing API uses different keys (`company` / `related_companies`, `person` / `related_people`, `account` / `matches`, etc.), don't rename your API — just set `ENTITY_KEY` and `RELATED_KEY` in the JS to match.

### 2. Walk the customization checklist

Open `assets/network-graph.js` and search for `// CUSTOMIZE:` — every customization point is marked. The full list, with explanation of *why* each one matters:

| Constant / function | What to change | Why it matters |
|---|---|---|
| `API_URL_TEMPLATE(id)` | The endpoint pattern, e.g. `` `/api/v1/people/${id}/related/` `` | The graph re-fetches from this URL on every "Expand relations". Get the path right or multi-hop silently fails. |
| `ID_FIELD` | The field on `entity` that holds the unique ID (`"id"`, `"uuid"`, `"dot_number"`, …) | Used as the vis-network node id everywhere. Pick one and stick with it. |
| `NAME_FIELD` / `FALLBACK_NAME_FIELD` | Display name fields (primary + fallback) | Truncated to 26–28 chars for the node label. |
| `ENTITY_KEY` | The key holding the entity object on each related item (`"entity"`, `"company"`, `"person"`, `"account"`) | Mirrors the API. Default is `"entity"`. |
| `RELATED_KEY` | The array key in the response (`"related_entities"`, `"related"`, `"matches"`) | Mirrors the API. Default is `"related_entities"`. |
| `SIGNAL_LABELS` | Map of signal type → human label (`phone` → `"Same phone"`) | Used in sidebar bullets and on edge hover. Missing keys fall through to the raw type, so it won't crash — just look unpolished. |
| `renderSidebarTiles(entity)` | The compliance/profile tiles in the sidebar | This is the most domain-specific function — replace its body wholesale with the fields that matter to your users. The default shows a few common shapes (status, country, account count, sanctions hit) but you should rewrite it. |
| `renderAddressLine(entity)` | The address line shown above the tiles | Return a string or `''`. |
| `PROFILE_URL_FN(id)` | Where the "Open profile →" button links | Trivial but easy to forget. |
| `RISK_COLOURS` / `RISK_EDGE` | Bucket colours | Defaults are red/amber/green. Change only if your design system demands it — red-amber-green semantics are well-understood and switching them away costs more than it gives. |
| `NODE_LIMIT` | Hard cap, default 200 | Past ~300 vis-network's layout slows noticeably. Bump only if you've profiled it. |

The JS file groups these constants at the top so the changes land in one diff without scrolling through the body.

### 3. Drop in the modal markup

Copy `assets/network-graph.html` into a partial/include in your templating engine (Django `{% include %}`, ERB, Liquid, JSX-as-string, whatever). It expects:

- A trigger button somewhere on the page with `id="open-related-graph"`. The supplied include has one stub button — move it to wherever the "View as graph" entry point lives on your profile page.
- Two globals on `window` so the JS knows the root entity: `window.rootEntityId` and `window.rootEntityName`. Set them in a `<script>` block on the profile page, e.g. `<script>window.rootEntityId='{{ entity.id }}'; window.rootEntityName='{{ entity.name|escapejs }}';</script>`.
- vis-network loaded from a CDN (or self-hosted). The include has `<script src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js" defer></script>`. **Check your CSP allowlist** — if `unpkg.com` isn't in `script-src`, either add it or self-host the bundle. This is a common gotcha in stricter security environments.

### 4. Tailwind purge warning (read this even if you don't use Tailwind)

If your project uses Tailwind with content-based purging, **the modal's utility classes WILL be silently dropped** if the template lives outside the configured content paths. The supplied HTML uses inline `style=""` attributes and a single hand-rolled `<style>` block instead of Tailwind utilities, on purpose. Don't "clean it up" into utility classes without first verifying your purge config catches them. Same applies to other CSS-in-JS / atomic-CSS frameworks with build-time tree-shaking.

### 5. Verify the interactions

A working build supports every one of these. Walk through them after you wire it up — they're the load-bearing UX behaviours and each one has at least one subtle bug we hit during the original build:

- **Hover a node** → fades everything outside its 1-hop neighbourhood; sidebar updates to that node's profile.
- **Hover an edge** → fades everything outside the two endpoints; sidebar updates to the connection's signals.
- **Click a node** → pins the sidebar to that node. The pin survives mouseout (this is the whole point — without it the action buttons would lose focus when you move the mouse to click them).
- **Click an edge** → pins to the edge.
- **Click the pinned element again, or click empty canvas** → unpins.
- **Click "Expand relations"** on a pinned node → fetches `/api/.../related/` for that node, adds the new nodes/edges, re-runs pattern detection.
- **Click "Collapse branch"** → removes every descendant the node introduced, recursively (but never removes the root, even if a cycle would suggest doing so).
- **Click "Open profile →"** → opens the entity's profile in a new tab.
- **Pattern detection** runs automatically after every expand/collapse: any signal+value (e.g. phone "+1 555 0100") shared by 3+ edges thickens those edges to width 4.
- **Node cap** → hitting the cap surfaces a flash message and stops adding nodes (it doesn't crash mid-add).
- **ESC closes the modal**; clicking the dark backdrop closes the modal.

### 6. What you do NOT need to change

These are domain-agnostic and almost certainly correct as-is:

- The barnes-hut physics constants. They were tuned for 10–60 node clusters with cycles. If your graphs are sparser or denser, defer tuning until you've actually seen it look wrong.
- The "freeze physics after stabilization" logic. Without it, barnes-hut keeps integrating forever and the graph drifts on every interaction. There are five different events that re-freeze the sim; that's deliberate.
- The dashed-edge "preview" behaviour. The auto-expand wave that produces the dashed edges is off by default in this skill (we found it produced visual noise), but the dashed-vs-solid edge distinction is in the code in case you want to add an auto-expand wave later.
- The seed-children-near-parent jitter on multi-hop expansion. Without it, new nodes fly in from the origin and the graph looks like it's drifting.

## Common adaptation mistakes (worth flagging early)

These are real mistakes that have shown up in past adaptations:

1. **Forgetting to set `window.rootEntityId` and `window.rootEntityName` on the profile page.** The graph opens, finds no root, throws "No entity selected." Easy to debug, easy to miss.
2. **Tailwind utility classes silently purged.** Touched on above. Symptom: modal looks like unstyled HTML in production but fine in dev.
3. **Backend API doesn't filter on the signal field.** If your search index requires fields to be declared as "filterable" before they can appear in a WHERE clause (Meilisearch, Algolia, some Elasticsearch configs), and you add a new signal to the response without adding it to the filterable list, the query throws at runtime. Not the graph's problem strictly, but the first symptom shows up here, so worth knowing about.
4. **Going back to cytoscape because "it has more features".** It does. It also rendered worse than vis-network for our graph sizes. Don't switch unless you have >300 nodes loaded AND have measured layout time. Cytoscape's WebGL renderer might pay off at that point.
5. **Caching the related-entities responses on the client.** The skill does NOT cache today — every "Expand relations" re-fetches. If your API is slow you may want to add a `Map<id, response>` cache, but watch out: if the user collapses a branch then expands it, they probably want fresh data, not stale. Easy to get wrong.

## Reference files

- `assets/network-graph.js` — the JS implementation, with customization points marked.
- `assets/network-graph.html` — the modal HTML, ready to include.
- `references/customization-guide.md` — long-form walkthrough of every customization point, with code snippets for several worked domain examples (people, accounts, companies, vehicles).
