/**
 * eval-graph.mjs — headless d3 force-layout eval.
 *
 * Pulls the Vision Pro sim's entity graph + personas off jenny via
 * kubectl exec, fuses them the same way the frontend composable does,
 * runs the same force config, then reports layout metrics:
 *
 *   - canvas usage (bbox area / canvas area)
 *   - mean / min / max edge length
 *   - mean nearest-neighbor distance (label collision proxy)
 *   - count of isolated (no-edge) nodes
 *   - per-node post-tick (x, y) so you can spot clumps
 *
 * Usage: node scripts/eval-graph.mjs
 */
import {
  forceCenter,
  forceCollide,
  forceLink,
  forceManyBody,
  forceSimulation,
  forceX,
  forceY,
} from "d3-force";
import { execSync } from "node:child_process";

const SIM = "sim_0495388679d0";
const WIDTH = 1280;
const HEIGHT = 720;

// ---- Pull data off jenny ----
function ssh(cmd) {
  return execSync(
    `ssh jenny "kubectl exec -n deepmiro deploy/deepmiro-backend -c backend -- ${cmd.replace(/"/g, '\\"')}"`,
    { encoding: "utf8", maxBuffer: 32 * 1024 * 1024 },
  );
}

console.error("[1/3] Fetching sim status…");
const status = JSON.parse(
  ssh(`curl -sS http://localhost:5001/api/simulation/${SIM}/status`),
).data;
const graphId = status.graph_id;
console.error("    graph_id:", graphId);

console.error("[2/3] Fetching entity graph…");
const eg = JSON.parse(
  ssh(`curl -sS http://localhost:5001/api/graph/data/${graphId}`),
).data;
console.error("    entities:", eg.node_count, " edges:", eg.edge_count);

console.error("[3/3] Fetching personas…");
const reddit = JSON.parse(
  ssh(`curl -sS "http://localhost:5001/api/simulation/${SIM}/profiles/realtime?platform=reddit"`),
).data.profiles;
console.error("    personas:", reddit.length);

// ---- Fuse entity + persona (mirror useSimulationEvents) ----
function nameToStableId(name) {
  const norm = name.trim().toLowerCase().replace(/\s+/g, " ");
  let h = 5381;
  for (let i = 0; i < norm.length; i++) {
    h = ((h << 5) + h + norm.charCodeAt(i)) | 0;
  }
  return (Math.abs(h) | 0x40000000) >>> 0;
}

const personaByName = new Map(reddit.map((p) => [
  (p.realname || p.name || p.username || "").trim().toLowerCase(),
  p,
]));

const idByUuid = new Map();
const seen = new Set();
const nodes = [];
for (const ent of eg.nodes) {
  const id = nameToStableId(ent.name);
  idByUuid.set(ent.uuid, id);
  if (seen.has(id)) continue;
  seen.add(id);
  const persona = personaByName.get(ent.name.trim().toLowerCase());
  nodes.push({
    id,
    name: ent.name,
    archetype: persona?.entity_type || persona?.profession || "Entity",
    post_count: 0,
  });
}

const edges = [];
const incident = new Set();
for (const ed of eg.edges) {
  const s = idByUuid.get(ed.source_node_uuid);
  const t = idByUuid.get(ed.target_node_uuid);
  if (s == null || t == null || s === t) continue;
  edges.push({
    source: s,
    target: t,
    type: "fact",
    label: ed.name?.trim() || "related",
  });
  incident.add(s);
  incident.add(t);
}

// Mirror the cluster + bridge fallback layers from the composable.
function archLabel(p) {
  // Quick local match — close enough for the eval since we just need
  // groupings. Real resolveArchetype keyword scoring lives in TS.
  const t = (p?.archetype || "").toLowerCase();
  if (/journalist|reviewer|content/.test(t)) return "Media";
  if (/ceo|founder/.test(t)) return "TechCEO";
  if (/bank|invest/.test(t)) return "Finance";
  if (/platform|hardware/.test(t)) return "Platform";
  if (/developer|engineer/.test(t)) return "Developer";
  if (/studio|enterprise|corporation|brand|company|conglomerate/.test(t)) return "Corporation";
  return "Other";
}
const archIdx = new Map();
for (const n of nodes) {
  const a = archLabel(n);
  if (!archIdx.has(a)) archIdx.set(a, []);
  archIdx.get(a).push(n.id);
}
const factPairs = new Set(edges.map((e) => `${e.source}-${e.target}`));
for (const [arch, ids] of archIdx) {
  if (ids.length < 2) continue;
  for (let i = 0; i < ids.length - 1; i++) {
    const s = ids[i], t = ids[i + 1];
    if (factPairs.has(`${s}-${t}`) || factPairs.has(`${t}-${s}`)) continue;
    edges.push({ source: s, target: t, type: "cluster", label: `Both: ${arch}` });
    incident.add(s);
    incident.add(t);
  }
}
const orphans = nodes.filter((n) => !incident.has(n.id));
if (orphans.length) {
  const degree = new Map();
  for (const e of edges) {
    degree.set(e.source, (degree.get(e.source) ?? 0) + 1);
    degree.set(e.target, (degree.get(e.target) ?? 0) + 1);
  }
  const anchor = nodes.filter((n) => !orphans.includes(n)).sort((a, b) => (degree.get(b.id) ?? 0) - (degree.get(a.id) ?? 0))[0];
  if (anchor) {
    for (const o of orphans) {
      edges.push({ source: o.id, target: anchor.id, type: "bridge", label: "isolated" });
    }
  }
}

console.error(`Fused: ${nodes.length} nodes / ${edges.length} edges`);

// ---- Run the force simulation (matches GraphPanel.vue config) ----
function nodeRadius(n) {
  return Math.min(28, 10 + Math.sqrt(Math.max(0, n.post_count)) * 2.4);
}

const sim = forceSimulation(nodes)
  .force(
    "link",
    forceLink(edges)
      .id((d) => d.id)
      .distance((l) => (l.type === "fact" ? 180 : l.type === "bridge" ? 230 : 140))
      .strength((l) => (l.type === "fact" ? 0.4 : l.type === "bridge" ? 0.12 : 0.32)),
  )
  .force("charge", forceManyBody().strength(-560).distanceMax(640))
  .force("center", forceCenter(WIDTH / 2, HEIGHT / 2))
  .force("collide", forceCollide((d) => nodeRadius(d) + 18))
  .force("x", forceX(WIDTH / 2).strength(0.02))
  .force("y", forceY(HEIGHT / 2).strength(0.02))
  .stop();

// Run to convergence (alphaMin default = 0.001)
let ticks = 0;
const maxTicks = 600;
while (sim.alpha() > sim.alphaMin() && ticks < maxTicks) {
  sim.tick();
  ticks += 1;
}
console.error(`Converged in ${ticks} ticks (final alpha=${sim.alpha().toFixed(4)})`);

// ---- Metrics ----
const xs = nodes.map((n) => n.x);
const ys = nodes.map((n) => n.y);
const minX = Math.min(...xs), maxX = Math.max(...xs);
const minY = Math.min(...ys), maxY = Math.max(...ys);
const bboxW = maxX - minX, bboxH = maxY - minY;
const bboxArea = bboxW * bboxH;
const canvasArea = WIDTH * HEIGHT;

const edgeLen = (e) => {
  const dx = e.target.x - e.source.x;
  const dy = e.target.y - e.source.y;
  return Math.sqrt(dx * dx + dy * dy);
};
const edgeLengths = edges.map(edgeLen);
const meanEdge = edgeLengths.reduce((a, b) => a + b, 0) / (edgeLengths.length || 1);
const minEdge = Math.min(...edgeLengths);
const maxEdge = Math.max(...edgeLengths);

// Nearest-neighbor distance per node
const nnDistances = nodes.map((n) => {
  let best = Infinity;
  for (const m of nodes) {
    if (m === n) continue;
    const dx = m.x - n.x, dy = m.y - n.y;
    const d = Math.sqrt(dx * dx + dy * dy);
    if (d < best) best = d;
  }
  return best;
});
const meanNN = nnDistances.reduce((a, b) => a + b, 0) / (nnDistances.length || 1);
const minNN = Math.min(...nnDistances);

// Isolated nodes (no edges) — use d3-resolved source/target objects
const incidentFinal = new Set();
for (const e of edges) {
  incidentFinal.add(e.source.id ?? e.source);
  incidentFinal.add(e.target.id ?? e.target);
}
const isolated = nodes.filter((n) => !incidentFinal.has(n.id));

// Edge crossings (pair-wise check; OK at 19-edge scale)
function segmentsCross(a, b, c, d) {
  function ccw(p1, p2, p3) {
    return (p3.y - p1.y) * (p2.x - p1.x) > (p2.y - p1.y) * (p3.x - p1.x);
  }
  return (
    ccw(a, c, d) !== ccw(b, c, d) &&
    ccw(a, b, c) !== ccw(a, b, d)
  );
}
let crossings = 0;
for (let i = 0; i < edges.length; i++) {
  for (let j = i + 1; j < edges.length; j++) {
    const e1 = edges[i], e2 = edges[j];
    if (
      e1.source.id === e2.source.id || e1.source.id === e2.target.id ||
      e1.target.id === e2.source.id || e1.target.id === e2.target.id
    ) continue; // share endpoint, can't cross
    if (segmentsCross(e1.source, e1.target, e2.source, e2.target)) crossings += 1;
  }
}

// ---- Report ----
console.log("\n=== LAYOUT METRICS ===");
console.log(`canvas      : ${WIDTH} x ${HEIGHT}`);
console.log(`bbox        : ${bboxW.toFixed(0)} x ${bboxH.toFixed(0)}  (${(bboxArea / canvasArea * 100).toFixed(1)}% of canvas)`);
console.log(`bbox center : (${((minX + maxX) / 2).toFixed(0)}, ${((minY + maxY) / 2).toFixed(0)})`);
console.log(`edge length : mean=${meanEdge.toFixed(0)}, min=${minEdge.toFixed(0)}, max=${maxEdge.toFixed(0)}`);
console.log(`nn distance : mean=${meanNN.toFixed(0)}, min=${minNN.toFixed(0)}`);
console.log(`isolated    : ${isolated.length} (${isolated.map((n) => n.name).join(", ") || "none"})`);
console.log(`crossings   : ${crossings} edge-pair crossings`);

console.log("\n=== POSITIONS (sorted by x) ===");
for (const n of [...nodes].sort((a, b) => a.x - b.x)) {
  console.log(`  (${n.x.toFixed(0).padStart(5)}, ${n.y.toFixed(0).padStart(5)})  ${n.name}`);
}

console.log("\n=== HEURISTICS ===");
const usage = bboxArea / canvasArea;
console.log(`  spread     : ${usage > 0.5 ? "GOOD" : usage > 0.25 ? "OK" : "CLUMPED"} (${(usage * 100).toFixed(1)}% canvas)`);
console.log(`  edge length: ${Math.abs(meanEdge - 180) < 60 ? "GOOD" : "OFF TARGET"} (target ~180 for fact edges)`);
console.log(`  collision  : ${minNN > 36 ? "GOOD" : "OVERLAP RISK"} (min nn=${minNN.toFixed(0)}, collision radius ~28)`);
console.log(`  isolated   : ${isolated.length === 0 ? "GOOD" : "BAD"}`);
console.log(`  readability: ${crossings <= edges.length * 0.5 ? "GOOD" : crossings <= edges.length ? "OK" : "BAD"} (${crossings}/${edges.length} crossings)`);
