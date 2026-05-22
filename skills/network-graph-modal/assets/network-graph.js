/**
 * Force-directed network graph modal — vis-network implementation.
 *
 * Drop this onto any entity profile page that has an API returning related
 * entities. Customization points are constants at the top of the IIFE,
 * marked with `// CUSTOMIZE:`. Search for that string to find them all.
 *
 * Behaviour:
 *   - Open: root entity in centre, fetch its direct related, render as
 *     a bubble network.
 *   - Hover (any time): visually highlight that node's neighbourhood
 *     (the node + its direct neighbours + the edges between them) and
 *     dim everything else. Sidebar updates if nothing is pinned.
 *   - Click a node/edge to PIN the sidebar to it. Pin survives mouseout
 *     so action buttons stay reachable.
 *   - Click "Expand relations" on a pinned node to fetch its related
 *     (multi-hop walk). Click "Collapse branch" to remove the
 *     descendants it brought in.
 *   - Pattern detection: edges that share the same signal value across
 *     3+ entities get a thicker stroke (fraud-ring style cluster).
 *   - Hard cap at NODE_LIMIT nodes (default 200). Past ~300 vis-network
 *     starts to chug; switch to cytoscape + WebGL if you need bigger.
 *
 * Why vis-network and not cytoscape: we tried both. Cytoscape's fcose
 * layout rendered noticeably worse than vis-network's barnes-hut for
 * the network sizes we actually see in production (10–60 nodes, dense
 * cycles). Don't switch back unless you've got 300+ nodes to render.
 */
(function () {
  'use strict';

  // ===================================================================
  // CUSTOMIZE: domain-specific constants. Change these for your domain.
  // Everything below this block is domain-agnostic and almost never
  // needs touching. The defaults below are intentionally generic — you
  // WILL need to change them. See `references/customization-guide.md`
  // for worked examples (people, accounts, companies, vehicles).
  // ===================================================================

  // CUSTOMIZE: API endpoint pattern. The graph fetches this when opening
  // and on every "Expand relations" click.
  const API_URL_TEMPLATE = (id) => `/api/v1/entities/${id}/related/`;

  // CUSTOMIZE: where the "Open profile →" button on the sidebar links to.
  const PROFILE_URL_FN = (id) => `/entities/${id}/`;

  // CUSTOMIZE: name of the field on the entity object that holds the
  // unique ID. The graph uses this as the vis-network node id, dedup
  // key, and the value passed into API_URL_TEMPLATE and PROFILE_URL_FN.
  const ID_FIELD = 'id';

  // CUSTOMIZE: display-name fields. Primary is preferred; fallback is
  // used if primary is empty. Both fall back to "ID <id>" if neither
  // is set.
  const NAME_FIELD = 'name';
  const FALLBACK_NAME_FIELD = 'display_name';

  // CUSTOMIZE: the key on each related item that holds the entity
  // object. Default is "entity"; common alternatives include "company",
  // "person", "account", "record".
  const ENTITY_KEY = 'entity';

  // CUSTOMIZE: the array key in the API response holding related items.
  // Common alternatives: "related", "matches", "related_companies".
  const RELATED_KEY = 'related_entities';

  // CUSTOMIZE: human labels for each signal type. The keys must match
  // `signals[].type` from your API. Missing keys fall through to the
  // raw type string, so this is non-fatal to leave incomplete. The
  // default set below covers signals that are common across many
  // domains — replace or extend.
  const SIGNAL_LABELS = {
    email:   'Same email',
    phone:   'Same phone',
    address: 'Same address',
    device:  'Same device',
    ip:      'Same IP',
  };

  // CUSTOMIZE: the sidebar's profile tiles. This is the most
  // domain-specific function in the file — REPLACE THIS BODY with the
  // fields YOUR users care about seeing for a related entity. Return
  // an array of HTML strings (one per tile). The `stat()` helper takes
  // (label, value, severity?) where severity is 'bad' | 'warn' | 'good'
  // or omitted for neutral.
  //
  // This default body is illustrative only. It surfaces a handful of
  // fields you might commonly see (status, country, count, sanctions
  // hit) so the demo isn't empty — but you should rewrite it for your
  // schema, not paper over it.
  function renderSidebarTiles(entity) {
    const tiles = [];
    if (entity.status === 'active')   tiles.push(stat('Status', 'Active', 'good'));
    else if (entity.status === 'inactive') tiles.push(stat('Status', 'Inactive', 'bad'));
    else if (entity.status)           tiles.push(stat('Status', String(entity.status)));
    if (entity.country)               tiles.push(stat('Country', String(entity.country)));
    if (typeof entity.record_count === 'number') {
      tiles.push(stat('Records', entity.record_count.toLocaleString()));
    }
    if (entity.flagged === true)      tiles.push(stat('Flagged', 'Yes', 'bad'));
    return tiles;
  }

  // CUSTOMIZE: the address (or one-line subtitle) shown under the name
  // in the sidebar. Return a string or empty string. This is separate
  // from the tiles because it's usually the single most-important
  // identifier alongside the name.
  function renderAddressLine(entity) {
    return entity.address || entity.subtitle || '';
  }

  // CUSTOMIZE: node cap. Past ~300 vis-network's layout slows noticeably.
  const NODE_LIMIT = 200;

  // ===================================================================
  // Below here: domain-agnostic. You should rarely need to touch this.
  // ===================================================================

  const STATE = {
    network: null,
    nodes: null,             // vis.DataSet
    edges: null,             // vis.DataSet
    expanded: new Set(),     // IDs whose related list has been fetched
    userExpanded: new Set(), // IDs the user explicitly expanded (root counts)
    inFlight: new Set(),
    edgeIndex: new Map(),    // edgeId -> {fromId, toId, signals, confidence, riskLevel, addedBy}
    nodeIndex: new Map(),    // id -> {entity, depth, addedBy, item}
    childrenOf: new Map(),   // parentId -> Set of child IDs it brought in
    rootId: null,
    rootName: null,
    abort: null,
    pinned: null,            // {kind: 'node'|'edge', id: string}
  };

  const RISK_COLOURS = {
    high:   { background: '#FCA5A5', border: '#DC2626' },
    medium: { background: '#FDE68A', border: '#F59E0B' },
    low:    { background: '#A7F3D0', border: '#10B981' },
  };

  const FADED_COLOURS = {
    high:   { background: '#FECACA66', border: '#DC262633' },
    medium: { background: '#FEF3C766', border: '#F59E0B33' },
    low:    { background: '#A7F3D066', border: '#10B98133' },
  };

  const RISK_EDGE  = { high: '#DC2626', medium: '#F59E0B', low: '#10B981' };
  const FADED_EDGE = { high: '#DC262622', medium: '#F59E0B22', low: '#10B98122' };

  // ---------------------------------------------------------------------
  // DOM bootstrapping
  // ---------------------------------------------------------------------

  document.addEventListener('DOMContentLoaded', () => {
    const openBtn  = document.getElementById('open-related-graph');
    const closeBtn = document.getElementById('rel-graph-close');
    const modal    = document.getElementById('rel-graph-modal');
    if (!openBtn || !modal) return;

    openBtn.style.display = 'inline-flex';
    openBtn.addEventListener('click', openGraph);
    closeBtn.addEventListener('click', closeGraph);
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeGraph();
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && modal.style.display === 'block') closeGraph();
    });
  });

  function openGraph() {
    const modal = document.getElementById('rel-graph-modal');
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
    if (!STATE.network) {
      STATE.rootId   = String(window.rootEntityId || window.currentCompanyId || '');
      STATE.rootName = window.rootEntityName || window.currentCompanyName || `ID ${STATE.rootId}`;
      if (!STATE.rootId) {
        showError('No entity selected. Set window.rootEntityId on the page.');
        return;
      }
      buildInitialGraph();
    }
  }

  function closeGraph() {
    const modal = document.getElementById('rel-graph-modal');
    modal.style.display = 'none';
    document.body.style.overflow = '';
    if (STATE.abort) { STATE.abort.abort(); STATE.abort = null; }
  }

  // ---------------------------------------------------------------------
  // Initial graph
  // ---------------------------------------------------------------------

  function buildInitialGraph() {
    setLoading(true);
    if (typeof vis === 'undefined') {
      setTimeout(buildInitialGraph, 200);
      return;
    }
    STATE.nodes = new vis.DataSet([makeRootNode(STATE.rootId, STATE.rootName)]);
    STATE.edges = new vis.DataSet([]);
    STATE.nodeIndex.set(STATE.rootId, { id: STATE.rootId, name: STATE.rootName, depth: 0 });
    STATE.userExpanded.add(STATE.rootId);

    const container = document.getElementById('rel-graph-canvas');
    const options = {
      nodes: {
        shape: 'dot',
        size: 14,
        font: { size: 12, face: 'system-ui, sans-serif', color: '#1f2937', strokeWidth: 3, strokeColor: '#ffffff' },
        borderWidth: 2,
      },
      edges: {
        width: 1.5,
        color: { color: '#94a3b8', highlight: '#1E3A5F', hover: '#1E3A5F' },
        smooth: { type: 'dynamic' },
        hoverWidth: 0.5,
      },
      physics: {
        solver: 'barnesHut',
        barnesHut: {
          gravitationalConstant: -8000,
          centralGravity: 0.2,
          springLength: 180,
          springConstant: 0.04,
          damping: 0.4,
          avoidOverlap: 0.6,
        },
        stabilization: { iterations: 300, fit: true },
      },
      interaction: { hover: true, tooltipDelay: 120, navigationButtons: true },
    };
    STATE.network = new vis.Network(container, { nodes: STATE.nodes, edges: STATE.edges }, options);

    STATE.network.on('click',     handleClick);
    STATE.network.on('hoverNode', ({ node }) => onHoverNode(node));
    STATE.network.on('blurNode',  () => onBlurAny());
    STATE.network.on('hoverEdge', ({ edge }) => onHoverEdge(edge));
    STATE.network.on('blurEdge',  () => onBlurAny());

    // Freeze the simulation aggressively any time it has a chance to stop.
    // Without this, barnes-hut keeps integrating forever — every new node,
    // every hover-driven node update, every drag release nudges the graph
    // and it never settles. `restabilize()` flips physics back on for a
    // bounded burst so new nodes still find a spot.
    const freezeSim = () => {
      try { STATE.network.stopSimulation(); } catch (_) {}
      STATE.network.setOptions({ physics: { enabled: false } });
    };
    STATE.network.on('stabilizationIterationsDone', freezeSim);
    STATE.network.on('stabilized', freezeSim);
    STATE.network.on('dragEnd', freezeSim);

    expandNode(STATE.rootId, 1)
      .catch((e) => {
        console.error('initial expand failed', e);
        showError('Could not load the network graph.');
      });
  }

  function makeRootNode(id, name) {
    return {
      id,
      label: truncate(name, 28),
      // `circle` (not `dot`) puts the label *inside* the shape, so the
      // white text stays readable against the navy fill.
      shape: 'circle',
      color: { background: '#1E3A5F', border: '#0F1D2F' },
      font: { color: '#ffffff', size: 13, face: 'system-ui, sans-serif', strokeWidth: 0 },
      borderWidth: 3,
      widthConstraint: { maximum: 130 },
      margin: 10,
      _kind: 'root',
    };
  }

  function makeRelatedNode(item, depth) {
    const entity = item[ENTITY_KEY] || {};
    const id = String(entity[ID_FIELD] || '');
    const colour = RISK_COLOURS[item.risk_level] || RISK_COLOURS.low;
    return {
      id,
      label: truncate(entity[NAME_FIELD] || entity[FALLBACK_NAME_FIELD] || `ID ${id}`, 26),
      color: colour,
      size: 10 + Math.min(6, (item.signals || []).length),
      _depth: depth,
      _risk: item.risk_level || 'low',
    };
  }

  function makeEdge(fromId, toId, item, addedBy) {
    const id = [fromId, toId].sort().join('__');
    const risk = item.risk_level || 'low';
    const dashed = !STATE.userExpanded.has(addedBy);
    return {
      id,
      from: fromId,
      to: toId,
      color: { color: RISK_EDGE[risk], highlight: RISK_EDGE[risk], hover: RISK_EDGE[risk] },
      width: 1 + Math.min(4, (item.signals || []).length * 0.7),
      dashes: dashed ? [6, 6] : false,
      _risk: risk,
      _addedBy: addedBy,
    };
  }

  // ---------------------------------------------------------------------
  // Expansion (multi-hop)
  // ---------------------------------------------------------------------

  async function expandNode(id, depth) {
    if (STATE.expanded.has(id) || STATE.inFlight.has(id)) return;
    if (STATE.nodes.length >= NODE_LIMIT) {
      flash(`Graph already at the ${NODE_LIMIT}-node cap. Close and reopen to reset.`);
      return;
    }
    STATE.inFlight.add(id);
    flash(`Expanding ${id}…`);
    try {
      if (STATE.abort) STATE.abort.abort();
      STATE.abort = new AbortController();
      const resp = await fetch(API_URL_TEMPLATE(id), { signal: STATE.abort.signal });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      if (!data.success) throw new Error(data.error || 'API error');
      const newIds = addRelatedToGraph(id, data[RELATED_KEY] || [], depth);
      STATE.expanded.add(id);
      if (newIds.length) restabilize(id, newIds);
      runPatternHighlight();
      if (STATE.pinned) reapplyPinHighlight();
      setLoading(false);
      const added = (data[RELATED_KEY] || []).length;
      flash(added > 0 ? `Added ${added} related to ${id}.` : `${id} has no related entities.`);
    } catch (e) {
      if (e.name !== 'AbortError') {
        console.error('expandNode failed', e);
        flash(`Failed to expand ${id}.`);
      }
    } finally {
      STATE.inFlight.delete(id);
    }
  }

  function addRelatedToGraph(fromId, items, depth) {
    const newNodes = [];
    const newEdges = [];
    const newIds   = [];
    const myChildren = STATE.childrenOf.get(fromId) || new Set();
    STATE.childrenOf.set(fromId, myChildren);
    for (const item of items) {
      const entity = item[ENTITY_KEY] || {};
      const toId = String(entity[ID_FIELD] || '');
      if (!toId || toId === fromId) continue;
      if (!STATE.nodeIndex.has(toId)) {
        if (STATE.nodes.length + newNodes.length >= NODE_LIMIT) {
          flash(`Hit ${NODE_LIMIT}-node cap — some children not added.`);
          break;
        }
        newNodes.push(makeRelatedNode(item, depth));
        newIds.push(toId);
        STATE.nodeIndex.set(toId, {
          id: toId,
          name: entity[NAME_FIELD] || entity[FALLBACK_NAME_FIELD] || `ID ${toId}`,
          entity, item, depth, addedBy: fromId,
        });
        myChildren.add(toId);
      }
      const edgeId = [fromId, toId].sort().join('__');
      if (!STATE.edgeIndex.has(edgeId)) {
        newEdges.push(makeEdge(fromId, toId, item, fromId));
        STATE.edgeIndex.set(edgeId, {
          fromId, toId,
          signals: item.signals || [],
          confidenceLabel: item.confidence_label,
          riskLevel: item.risk_level,
          addedBy: fromId,
        });
      }
    }
    if (newNodes.length) STATE.nodes.add(newNodes);
    if (newEdges.length) STATE.edges.add(newEdges);
    return newIds;
  }

  /**
   * Re-run the physics solver for a bounded burst so newly added child
   * nodes find a position near their parent rather than flying in from
   * the origin (which makes a level-2+ expansion look like the graph is
   * drifting endlessly).
   */
  function restabilize(parentId, newIds) {
    if (!STATE.network || !newIds || !newIds.length) return;
    const positions = STATE.network.getPositions([parentId]);
    const parent = positions[parentId];
    if (parent) {
      newIds.forEach((id) => {
        const dx = (Math.random() - 0.5) * 60;
        const dy = (Math.random() - 0.5) * 60;
        try { STATE.network.moveNode(id, parent.x + dx, parent.y + dy); }
        catch (_) { /* node may have been removed mid-flight */ }
      });
    }
    STATE.network.setOptions({ physics: { enabled: true } });
    STATE.network.stabilize(200);
  }

  // ---------------------------------------------------------------------
  // Click handling (pin model)
  // ---------------------------------------------------------------------

  function handleClick({ nodes, edges }) {
    if (nodes && nodes.length) {
      const id = String(nodes[0]);
      if (STATE.pinned && STATE.pinned.kind === 'node' && STATE.pinned.id === id) unpinDetail();
      else pinNode(id);
      return;
    }
    if (edges && edges.length) {
      const eid = String(edges[0]);
      if (STATE.pinned && STATE.pinned.kind === 'edge' && STATE.pinned.id === eid) unpinDetail();
      else pinEdge(eid);
      return;
    }
    unpinDetail();
  }

  function pinNode(id) {
    STATE.pinned = { kind: 'node', id };
    highlightNodeNeighbourhood(id);
    showNodeDetail(id, true);
  }

  function pinEdge(id) {
    STATE.pinned = { kind: 'edge', id };
    highlightEdge(id);
    showEdgeDetail(id, true);
  }

  function unpinDetail() {
    STATE.pinned = null;
    clearHighlight();
    resetDetail();
  }

  function onHoverNode(id) {
    highlightNodeNeighbourhood(String(id));
    if (!STATE.pinned) showNodeDetail(String(id), false);
  }

  function onHoverEdge(edgeId) {
    highlightEdge(String(edgeId));
    if (!STATE.pinned) showEdgeDetail(String(edgeId), false);
  }

  function onBlurAny() {
    if (STATE.pinned) { reapplyPinHighlight(); return; }
    clearHighlight();
    resetDetail();
  }

  function reapplyPinHighlight() {
    if (!STATE.pinned) return;
    if (STATE.pinned.kind === 'node') highlightNodeNeighbourhood(STATE.pinned.id);
    else highlightEdge(STATE.pinned.id);
  }

  // ---------------------------------------------------------------------
  // Hover highlight. vis-network doesn't have a native "fade everything
  // except set X" so we walk the datasets and rewrite their colours.
  // ---------------------------------------------------------------------

  function highlightNodeNeighbourhood(id) {
    if (!STATE.network || !STATE.nodes) return;
    const connectedEdges = STATE.network.getConnectedEdges(id);
    const inSet = new Set([id]);
    connectedEdges.forEach((eid) => {
      const e = STATE.edges.get(eid);
      if (e) { inSet.add(e.from); inSet.add(e.to); }
    });
    applyFade(inSet, new Set(connectedEdges));
  }

  function highlightEdge(eid) {
    if (!STATE.network || !STATE.edges) return;
    const e = STATE.edges.get(eid);
    if (!e) return;
    applyFade(new Set([e.from, e.to]), new Set([eid]));
  }

  function applyFade(brightNodeIds, brightEdgeIds) {
    const nodeUpdates = [];
    STATE.nodes.forEach((n) => {
      const isRoot = n._kind === 'root';
      const risk = n._risk || 'low';
      const bright = brightNodeIds.has(n.id);
      if (isRoot) {
        // Root never fades. Fading the navy fill but keeping the white
        // label produced unreadable white-on-light-blue text.
        nodeUpdates.push({ id: n.id, color: { background: '#1E3A5F', border: '#0F1D2F' }, opacity: 1 });
      } else {
        const palette = bright ? RISK_COLOURS[risk] : FADED_COLOURS[risk];
        nodeUpdates.push({ id: n.id, color: palette, opacity: bright ? 1 : 0.25 });
      }
    });
    const edgeUpdates = [];
    STATE.edges.forEach((e) => {
      const risk = e._risk || 'low';
      const bright = brightEdgeIds.has(e.id);
      const colour = bright ? RISK_EDGE[risk] : FADED_EDGE[risk];
      edgeUpdates.push({ id: e.id, color: { color: colour, highlight: colour, hover: colour } });
    });
    STATE.nodes.update(nodeUpdates);
    STATE.edges.update(edgeUpdates);
  }

  function clearHighlight() {
    if (!STATE.nodes || !STATE.edges) return;
    const nodeUpdates = [];
    STATE.nodes.forEach((n) => {
      const isRoot = n._kind === 'root';
      const risk = n._risk || 'low';
      nodeUpdates.push({
        id: n.id,
        color: isRoot ? { background: '#1E3A5F', border: '#0F1D2F' } : RISK_COLOURS[risk],
        opacity: 1,
      });
    });
    const edgeUpdates = [];
    STATE.edges.forEach((e) => {
      const colour = RISK_EDGE[e._risk || 'low'];
      edgeUpdates.push({ id: e.id, color: { color: colour, highlight: colour, hover: colour } });
    });
    STATE.nodes.update(nodeUpdates);
    STATE.edges.update(edgeUpdates);
  }

  // ---------------------------------------------------------------------
  // Branch collapse — removes every descendant a node introduced.
  // ---------------------------------------------------------------------

  function collapseNode(id) {
    STATE.userExpanded.delete(id);
    if (!STATE.expanded.has(id)) return;
    const stack = [id];
    const toRemove = new Set();
    while (stack.length) {
      const cur = stack.pop();
      const kids = STATE.childrenOf.get(cur);
      STATE.childrenOf.delete(cur);
      STATE.expanded.delete(cur);
      STATE.userExpanded.delete(cur);
      if (!kids) continue;
      for (const child of kids) {
        if (child === STATE.rootId || toRemove.has(child)) continue;
        toRemove.add(child);
        stack.push(child);
      }
    }
    const edgesToRemove = [];
    STATE.edgeIndex.forEach((meta, eid) => {
      if (toRemove.has(meta.fromId) || toRemove.has(meta.toId)) edgesToRemove.push(eid);
    });
    edgesToRemove.forEach((eid) => STATE.edgeIndex.delete(eid));
    toRemove.forEach((d) => STATE.nodeIndex.delete(d));
    if (edgesToRemove.length) STATE.edges.remove(edgesToRemove);
    if (toRemove.size) STATE.nodes.remove(Array.from(toRemove));
    runPatternHighlight();
    flash(`Collapsed branch from ${id} (${toRemove.size} node${toRemove.size === 1 ? '' : 's'} removed).`);
  }

  // ---------------------------------------------------------------------
  // Sidebar
  // ---------------------------------------------------------------------

  function stat(label, value, severity) {
    const tone =
      severity === 'bad'  ? 'background:#FEE2E2;color:#991B1B;' :
      severity === 'warn' ? 'background:#FEF3C7;color:#78350F;' :
      severity === 'good' ? 'background:#D1FAE5;color:#065F46;' :
                            'background:#F3F4F6;color:#374151;';
    return `<div style="padding:0.5rem 0.6rem;border-radius:6px;${tone}">
      <div style="font-family:system-ui,sans-serif;text-transform:uppercase;letter-spacing:0.05em;font-size:0.65rem;opacity:0.85;">${label}</div>
      <div style="font-weight:600;font-size:0.9rem;margin-top:0.15rem;">${value}</div>
    </div>`;
  }

  function showNodeDetail(id, pinned) {
    const meta = STATE.nodeIndex.get(String(id));
    if (!meta) return;
    const e = meta.entity || {};
    const tiles = renderSidebarTiles(e);
    const addressLine = renderAddressLine(e);
    const pinBadge = pinned
      ? `<span style="display:inline-flex;align-items:center;gap:0.25rem;background:#1E3A5F;color:#fff;font-family:system-ui,sans-serif;text-transform:uppercase;letter-spacing:0.05em;font-size:0.62rem;padding:0.15rem 0.45rem;border-radius:9999px;margin-left:0.4rem;vertical-align:middle;">📌 pinned</span>`
      : '';

    const signals = (meta.item && meta.item.signals) || [];
    const parentMeta = meta.addedBy ? STATE.nodeIndex.get(meta.addedBy) : null;
    const parentName = parentMeta ? (parentMeta.name || `ID ${meta.addedBy}`) : '';
    const reasonBullets = signals.map((s) =>
      `<li style="margin:0.1rem 0;"><span style="color:#1E3A5F;font-weight:600;">${escapeHtml(SIGNAL_LABELS[s.type] || s.type)}</span>${s.detail ? ` — ${escapeHtml(s.detail)}` : ''}</li>`
    ).join('');
    const reasonsBlock = (String(meta.id) !== STATE.rootId && (signals.length || meta.item))
      ? `
        <p style="font-family:system-ui,sans-serif;text-transform:uppercase;letter-spacing:0.05em;font-size:0.7rem;color:#6b7280;margin:0.6rem 0 0.4rem;">
          Why related${parentName ? ` to ${escapeHtml(parentName)}` : ''}
        </p>
        ${meta.item && meta.item.confidence_label
          ? `<p style="font-size:0.75rem;color:#6b7280;margin:0 0 0.35rem;">${escapeHtml(meta.item.confidence_label)}</p>`
          : ''}
        ${signals.length
          ? `<ul style="padding-left:1.1rem;margin:0 0 0.5rem;font-size:0.8rem;line-height:1.45;color:#374151;">${reasonBullets}</ul>`
          : '<p style="font-size:0.8rem;color:#9ca3af;margin:0 0 0.5rem;">No specific signals recorded.</p>'}`
      : '';

    setDetail(`
      <p style="font-family:system-ui,sans-serif;font-size:1.05rem;font-weight:700;color:#1E3A5F;margin:0 0 0.2rem;">
        ${escapeHtml(e[NAME_FIELD] || meta.name || '')}${pinBadge}
      </p>
      <p style="font-size:0.78rem;color:#6b7280;margin:0 0 0.5rem;">
        ID ${escapeHtml(String(meta.id))}${meta.depth ? ` · depth ${meta.depth}` : ''}
      </p>
      ${addressLine ? `<p style="font-size:0.8rem;color:#374151;margin:0 0 0.6rem;">${escapeHtml(addressLine)}</p>` : ''}
      ${reasonsBlock}

      <p style="font-family:system-ui,sans-serif;text-transform:uppercase;letter-spacing:0.05em;font-size:0.7rem;color:#6b7280;margin:0.4rem 0 0.4rem;">Profile</p>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.4rem;">
        ${tiles.join('') || '<p style="font-size:0.8rem;color:#9ca3af;">No profile fields available.</p>'}
      </div>

      <p style="margin:0.85rem 0 0;display:flex;gap:0.5rem;flex-wrap:wrap;">
        <a href="${PROFILE_URL_FN(encodeURIComponent(String(meta.id)))}" target="_blank" rel="noopener"
           style="display:inline-block;background:#1E3A5F;color:white;padding:0.4rem 0.8rem;border-radius:6px;text-decoration:none;font-size:0.8rem;font-weight:600;font-family:system-ui,sans-serif;">Open profile →</a>
        ${String(meta.id) === STATE.rootId ? '' :
          STATE.userExpanded.has(String(meta.id))
            ? `<button type="button" onclick="window.__relGraphCollapse('${escapeHtml(String(meta.id))}')"
                       style="background:#fee2e2;color:#991B1B;border:1px solid #fecaca;padding:0.35rem 0.7rem;border-radius:6px;font-size:0.8rem;font-weight:600;font-family:system-ui,sans-serif;cursor:pointer;">Collapse branch</button>`
            : `<button type="button" onclick="window.__relGraphExpand('${escapeHtml(String(meta.id))}')"
                       style="background:#e0f2fe;color:#075985;border:1px solid #bae6fd;padding:0.35rem 0.7rem;border-radius:6px;font-size:0.8rem;font-weight:600;font-family:system-ui,sans-serif;cursor:pointer;">${STATE.expanded.has(String(meta.id)) ? 'Confirm expansion' : 'Expand relations'}</button>`}
        ${pinned ? `<button type="button" onclick="window.__relGraphUnpin()" style="background:transparent;border:1px solid #d1d5db;color:#374151;padding:0.35rem 0.7rem;border-radius:6px;font-size:0.8rem;font-weight:600;font-family:system-ui,sans-serif;cursor:pointer;">Unpin</button>` : ''}
      </p>
    `);
  }

  function showEdgeDetail(edgeId, pinned) {
    const meta = STATE.edgeIndex.get(edgeId);
    if (!meta) return;
    const from = STATE.nodeIndex.get(meta.fromId) || {};
    const to = STATE.nodeIndex.get(meta.toId) || {};
    const sigBullets = (meta.signals || []).map((s) =>
      `<li><span style="color:#1E3A5F;font-weight:600;">${escapeHtml(SIGNAL_LABELS[s.type] || s.type)}</span> — ${escapeHtml(s.detail || '')}</li>`
    ).join('');
    const pinBadge = pinned
      ? `<span style="display:inline-flex;align-items:center;gap:0.25rem;background:#1E3A5F;color:#fff;font-family:system-ui,sans-serif;text-transform:uppercase;letter-spacing:0.05em;font-size:0.62rem;padding:0.15rem 0.45rem;border-radius:9999px;margin-left:0.4rem;vertical-align:middle;">📌 pinned</span>`
      : '';
    setDetail(`
      <p style="font-family:system-ui,sans-serif;font-size:0.95rem;font-weight:700;color:#1E3A5F;margin:0 0 0.25rem;">Connection${pinBadge}</p>
      <p style="font-size:0.8rem;color:#374151;margin:0 0 0.5rem;">
        <strong>${escapeHtml(from.name || meta.fromId)}</strong> ↔
        <strong>${escapeHtml(to.name || meta.toId)}</strong>
      </p>
      <p style="font-size:0.78rem;color:#6b7280;margin:0 0 0.6rem;">${escapeHtml(meta.confidenceLabel || '')}</p>
      ${meta.signals && meta.signals.length ? `<ul style="padding-left:1.1rem;margin:0;font-size:0.8rem;line-height:1.45;">${sigBullets}</ul>` : '<p style="font-size:0.8rem;color:#6b7280;">No signal detail.</p>'}
      ${pinned ? `<p style="margin:0.6rem 0 0;"><button type="button" onclick="window.__relGraphUnpin()" style="background:transparent;border:1px solid #d1d5db;color:#374151;padding:0.3rem 0.7rem;border-radius:6px;font-size:0.78rem;font-weight:600;font-family:system-ui,sans-serif;cursor:pointer;">Unpin</button></p>` : ''}
    `);
  }

  function setDetail(html) {
    const empty  = document.getElementById('rel-graph-detail-empty');
    const detail = document.getElementById('rel-graph-detail');
    if (empty)  empty.style.display = 'none';
    if (detail) { detail.style.display = ''; detail.innerHTML = html; }
  }
  function resetDetail() {
    const empty  = document.getElementById('rel-graph-detail-empty');
    const detail = document.getElementById('rel-graph-detail');
    if (empty)  empty.style.display = '';
    if (detail) detail.style.display = 'none';
  }

  // Sidebar action handlers ---------------------------------------------

  window.__relGraphCollapse = (id) => {
    collapseNode(String(id));
    if (STATE.pinned && STATE.pinned.id === String(id)) showNodeDetail(String(id), true);
  };
  window.__relGraphExpand = async (id) => {
    const d = String(id);
    STATE.userExpanded.add(d);
    solidifyEdgesFrom(d);
    const depth = (STATE.nodeIndex.get(d) || {}).depth || 1;
    try { await expandNode(d, depth + 1); } catch (e) { console.error(e); }
    if (STATE.pinned && STATE.pinned.id === d) showNodeDetail(d, true);
  };
  window.__relGraphUnpin = () => unpinDetail();

  function solidifyEdgesFrom(id) {
    if (!STATE.edges) return;
    const updates = [];
    STATE.edges.forEach((e) => {
      if (e._addedBy === id && e.dashes) updates.push({ id: e.id, dashes: false });
    });
    if (updates.length) STATE.edges.update(updates);
  }

  // ---------------------------------------------------------------------
  // Pattern detection — bold edges that share the same signal value
  // across 3+ entities (likely a cluster).
  // ---------------------------------------------------------------------

  function runPatternHighlight() {
    if (!STATE.edges) return;
    const groups = new Map();
    STATE.edgeIndex.forEach((meta, eid) => {
      (meta.signals || []).forEach((s) => {
        if (!s.detail) return;
        const key = `${s.type}::${s.detail.toLowerCase()}`;
        if (!groups.has(key)) groups.set(key, []);
        groups.get(key).push(eid);
      });
    });
    const updates = [];
    groups.forEach((eids) => {
      if (eids.length < 3) return;
      eids.forEach((eid) => updates.push({ id: eid, width: 4 }));
    });
    if (updates.length) STATE.edges.update(updates);
  }

  // ---------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------

  function setLoading(loading) {
    const el = document.getElementById('rel-graph-loading');
    if (el) el.style.display = loading ? '' : 'none';
  }
  function showError(msg) { setLoading(false); flash(msg); }
  function flash(msg) {
    const el = document.getElementById('rel-graph-loading');
    if (!el) return;
    el.style.display = '';
    el.textContent = msg;
    clearTimeout(flash._t);
    flash._t = setTimeout(() => { el.style.display = 'none'; }, 2200);
  }
  function truncate(s, n) {
    s = (s || '').trim();
    if (s.length <= n) return s;
    return s.slice(0, n - 1) + '…';
  }
  function escapeHtml(s) {
    if (s === undefined || s === null) return '';
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

})();
