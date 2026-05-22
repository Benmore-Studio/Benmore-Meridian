# Customization guide

Long-form companion to the checklist in `SKILL.md`. Read this when search-and-replace on the `// CUSTOMIZE:` markers isn't enough — usually because the new domain needs an interaction the original didn't, or because the API response shape is meaningfully different.

## Table of contents

1. [The data contract in detail](#data-contract)
2. [Worked examples: people, accounts, companies, vehicles](#worked-examples)
3. [Mapping a non-conforming API](#non-conforming-api)
4. [Replacing the sidebar tiles](#sidebar-tiles)
5. [Adding new signal types](#new-signals)
6. [Changing colour semantics](#colours)
7. [Tuning physics for unusual graph topologies](#physics)
8. [Supporting non-string IDs](#non-string-ids)
9. [Self-hosting vis-network](#self-host)
10. [Adding a client-side cache](#caching)
11. [Switching to cytoscape (don't, unless...)](#cytoscape)

---

## <a name="data-contract"></a>1. The data contract in detail

The graph treats the API response as authoritative. Every field used somewhere in the UI:

```
response.success                              → bail with error if false
response[RELATED_KEY]                         → array of related items
response[RELATED_KEY][n][ENTITY_KEY][ID_FIELD]
                                              → node id (string-coerced)
response[RELATED_KEY][n][ENTITY_KEY][NAME_FIELD]
                                              → node label, truncated to 26 chars
response[RELATED_KEY][n][ENTITY_KEY][FALLBACK_NAME_FIELD]
                                              → used if NAME_FIELD is empty
response[RELATED_KEY][n][ENTITY_KEY].*        → passed to renderSidebarTiles(entity)
                                                and renderAddressLine(entity)
response[RELATED_KEY][n].risk_level           → "high" | "medium" | "low"
                                                controls node + edge colour
response[RELATED_KEY][n].confidence_label     → free-text shown above sidebar tiles
response[RELATED_KEY][n].signals              → array of {type, label, detail, weight}
                                                - `type` keys into SIGNAL_LABELS
                                                - `detail` drives pattern detection
                                                  (3+ edges with the same type+detail
                                                  get a 4px stroke)
                                                - `weight` is read but only displayed
                                                  if you choose to surface it
```

Anything not listed above is ignored. You can pass through extra fields on the entity object and they'll only show up where `renderSidebarTiles` references them.

## <a name="worked-examples"></a>2. Worked examples

### Example A — duplicate-person detection (KYC / AML)

```js
const API_URL_TEMPLATE    = (id) => `/api/v1/people/${id}/related/`;
const PROFILE_URL_FN      = (id) => `/people/${id}/`;
const ID_FIELD            = 'person_id';
const NAME_FIELD          = 'full_name';
const FALLBACK_NAME_FIELD = 'username';
const ENTITY_KEY          = 'person';
const RELATED_KEY         = 'related_people';

const SIGNAL_LABELS = {
  email:   'Same email',
  phone:   'Same phone',
  address: 'Same address',
  device:  'Same device fingerprint',
  ip:      'Same IP',
  ssn4:    'Same SSN last 4',
};

function renderSidebarTiles(p) {
  const tiles = [];
  if (p.kyc_status === 'verified')      tiles.push(stat('KYC', 'Verified', 'good'));
  else if (p.kyc_status === 'rejected') tiles.push(stat('KYC', 'Rejected', 'bad'));
  else                                  tiles.push(stat('KYC', 'Pending', 'warn'));
  if (p.risk_score != null) tiles.push(stat('Risk', p.risk_score.toFixed(2), p.risk_score > 0.7 ? 'bad' : null));
  if (p.country)            tiles.push(stat('Country', p.country));
  if (p.sanctions_hit)      tiles.push(stat('Sanctions', 'Match', 'bad'));
  return tiles;
}
function renderAddressLine(p) { return p.primary_address || ''; }
```

### Example B — shared-operator detection (company registry / trucking)

```js
const API_URL_TEMPLATE    = (id) => `/api/v1/companies/${id}/related/`;
const PROFILE_URL_FN      = (id) => `/company/${id}/`;
const ID_FIELD            = 'dot_number';
const NAME_FIELD          = 'legal_name';
const FALLBACK_NAME_FIELD = 'dba_name';
const ENTITY_KEY          = 'company';
const RELATED_KEY         = 'related_companies';

const SIGNAL_LABELS = {
  phone:         'Same phone',
  email:         'Same email',
  physical_addr: 'Same physical address',
  mailing_addr:  'Same mailing address',
  officer:       'Same officer',
  vin_few:       'Shared VIN(s)',
  vin_many:      '5+ shared VINs',
};

function renderSidebarTiles(c) {
  const tiles = [];
  if (c.is_authorized === false)     tiles.push(stat('Authority', 'Not active', 'bad'));
  else if (c.is_authorized === true) tiles.push(stat('Authority', 'Active', 'good'));
  if (typeof c.power_units === 'number') tiles.push(stat('Power units', c.power_units.toLocaleString()));
  if (c.has_safety_alerts === true)  tiles.push(stat('Safety alerts', 'On file', 'bad'));
  return tiles;
}
```

### Example C — duplicate-vehicle / chameleon-vehicle detection

```js
const API_URL_TEMPLATE = (id) => `/api/v1/vehicles/${id}/related/`;
const ID_FIELD         = 'vin';
const NAME_FIELD       = 'description';
const ENTITY_KEY       = 'vehicle';
const RELATED_KEY      = 'related_vehicles';

const SIGNAL_LABELS = {
  title_lien_holder: 'Same lien holder',
  registered_to:     'Registered to same person',
  body_shop:         'Same body shop record',
  garaging_addr:     'Same garaging address',
};

function renderSidebarTiles(v) {
  const tiles = [];
  if (v.title_status === 'salvage') tiles.push(stat('Title', 'Salvage', 'warn'));
  else if (v.title_status)          tiles.push(stat('Title', v.title_status));
  if (v.year && v.make && v.model)  tiles.push(stat('Vehicle', `${v.year} ${v.make} ${v.model}`));
  if (v.mileage)                    tiles.push(stat('Mileage', v.mileage.toLocaleString()));
  if (v.has_open_recalls)           tiles.push(stat('Recalls', 'Open', 'bad'));
  return tiles;
}
```

The pattern is the same every time: change the 5–6 constants, replace `renderSidebarTiles` body, point at your endpoint. Everything else stays put.

## <a name="non-conforming-api"></a>3. Mapping a non-conforming API

If you can't change the API, write an adapter. Two reasonable places:

**Option A — wrap `fetch` inside the JS:** find `const resp = await fetch(API_URL_TEMPLATE(id), …)` and replace with:

```js
const raw = await (await fetch(API_URL_TEMPLATE(id), …)).json();
const data = adaptResponse(raw);  // your function
```

…and define `adaptResponse()` at the top of the file alongside the other CUSTOMIZE constants. This keeps the rest of the file intact.

**Option B — proxy on the backend:** add a `/related-for-graph/<id>/` endpoint that calls your existing API and reshapes. This is cleaner if multiple frontends consume the same data.

Pick A for one-off adaptations, B if you'll have other consumers.

## <a name="sidebar-tiles"></a>4. Replacing the sidebar tiles

`renderSidebarTiles(entity)` returns an array of HTML strings — one per tile. The tiles render in a 2-column grid. Use the `stat(label, value, severity?)` helper for consistent styling. Severity can be `'bad'` (red), `'warn'` (amber), `'good'` (green), or omitted (gray).

Keep tile values short — the grid cells aren't wide. Long values wrap awkwardly. The pattern is: pick 4–6 fields that a user would scan in 2 seconds to decide "is this match real / is this entity OK / should I dig deeper". More than 6 and the eye stops parsing them.

## <a name="new-signals"></a>5. Adding new signal types

Two places to touch:

1. **Backend** (out of scope for this skill but worth knowing): emit the new signal type from your API. If using Meilisearch/Elasticsearch, the field you filter on must be in the filterable-attributes list, or the search throws at runtime. This is a common gotcha that surfaces here first.

2. **Frontend** (`SIGNAL_LABELS` in the JS): add a key matching the new `type` string. Missing labels fall through to the raw type, so the UI won't break — it'll just look unpolished.

```js
const SIGNAL_LABELS = {
  // existing keys...
  shared_bank_account: 'Shared bank account',
  shared_ip:           'Logged in from same IP',
  shared_device:       'Same device fingerprint',
};
```

Pattern detection works automatically for any signal type as long as `signals[].detail` is set on the API side.

## <a name="colours"></a>6. Changing colour semantics

The reference uses red/amber/green for `high`/`medium`/`low` confidence. This is widely understood and you should think twice before changing it. If you do:

- `RISK_COLOURS` is the node fill+border for normal state.
- `FADED_COLOURS` is the dimmed state (used during hover-highlight on non-neighbourhood nodes). The opacity is baked into the hex (look for `66` and `33` suffixes — these are alpha channels).
- `RISK_EDGE` / `FADED_EDGE` are the edge colours.

If you change to a different palette, keep both bright and faded versions matched. A common mistake: changing only the bright colours and leaving the faded versions pointing at red/amber/green, which produces a confusing flash on hover.

## <a name="physics"></a>7. Tuning physics for unusual topologies

The defaults in `options.physics.barnesHut` were tuned for 10–60 nodes with dense cycles. Symptoms that suggest you should retune:

- **Nodes flying apart** (graph fills the canvas, edges stretched): increase `gravitationalConstant` (less negative — try -4000) or `centralGravity` (try 0.4).
- **Nodes too clumped** (overlap, can't see structure): decrease `gravitationalConstant` (more negative — try -15000) or `springLength` (try 240).
- **Endless drift after settling**: this is what the `freezeSim` handlers prevent. If you see drift, check none of the five `freezeSim` event handlers got removed.
- **New child nodes flying in from origin on expand**: the `restabilize` function seeds them at the parent's position; if you see them shooting in from (0,0), check that `getPositions([parentId])` is returning a valid object.

Don't retune for a graph you've only seen once. Try the same graph on a different machine first — physics simulations are deterministic given a seed, but vis-network does not seed the initial node placement, so two runs of the same data can look noticeably different.

## <a name="non-string-ids"></a>8. Supporting non-string IDs

The JS coerces every ID to string via `String(…)`. This is intentional — vis-network's DataSet treats `1` and `"1"` as different keys, which is a footgun if your API mixes numeric and string IDs.

If your IDs contain characters that need URL encoding (slashes, plus signs), wrap them with `encodeURIComponent()` in `API_URL_TEMPLATE` and `PROFILE_URL_FN`. The `PROFILE_URL_FN` call site already uses `encodeURIComponent` on the way to the anchor.

## <a name="self-host"></a>9. Self-hosting vis-network

If your CSP doesn't allow `unpkg.com`:

```bash
mkdir -p static/vendor
curl -L https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js \
  -o static/vendor/vis-network.min.js
```

Then update the `<script>` tag in `network-graph.html` to point at your static path. Pin a specific version — `vis-network` has had API breaks in major versions, and the graph code is tested against 9.1.9.

## <a name="caching"></a>10. Adding a client-side cache

The graph re-fetches on every expansion, even ones the user has fetched before. For most APIs this is fine. If yours is slow and you want a cache:

```js
const RESPONSE_CACHE = new Map();

async function expandNode(id, depth) {
  // ... existing guards ...
  let data;
  if (RESPONSE_CACHE.has(id)) {
    data = RESPONSE_CACHE.get(id);
  } else {
    const resp = await fetch(API_URL_TEMPLATE(id), { signal: STATE.abort.signal });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    data = await resp.json();
    RESPONSE_CACHE.set(id, data);
  }
  // ... rest unchanged ...
}
```

Subtle: when the user collapses a branch and re-expands the same node, the cached response is reused, so any signals that have shifted in the backend since the original fetch will be stale. If staleness matters, add a TTL or bust the cache on collapse.

## <a name="cytoscape"></a>11. Switching to cytoscape

The reference build evaluated cytoscape + fcose and chose vis-network because:

- At 10–60 nodes with dense cycles, vis-network's barnes-hut produced more readable layouts.
- cytoscape's plain Canvas renderer is slower than vis-network's for our size range. cytoscape's WebGL renderer is faster but adds setup complexity.
- cytoscape's events / DataSet equivalents required more glue code for the pin/hover model.

If you have 300+ nodes loaded at once, cytoscape + the WebGL renderer is probably the right call. At that point the layout choice (fcose, cola, dagre, etc.) matters more than the library. The skill code is not directly portable — pin/hover/expansion logic would need rewriting against cytoscape's API.

If you find yourself wanting to switch for any other reason ("more features", "more popular", "newer"), don't. Measure first.
