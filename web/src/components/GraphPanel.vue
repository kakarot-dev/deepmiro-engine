<script setup lang="ts">
/**
 * GraphPanel — d3-force visualization with curved gradient links,
 * radial-gradient nodes, glow filter, and HTML-overlay labels.
 *
 * Visual design:
 *   - Links: cubic-bezier curves with per-edge linearGradient defs
 *     interpolating between source and target node colors
 *   - Nodes: radial-gradient circles with feGaussianBlur glow on
 *     active/hovered nodes; pulse on new posts
 *   - Selection: clicked node + its 1-hop neighborhood lit up;
 *     everything else dims to 0.25 opacity
 *   - Labels: HTML pills (backdrop-filter: blur) — only for top-N
 *     active nodes or hovered, so the canvas doesn't get noisy
 *   - Background: subtle dot grid in dark theme
 */
import {
  forceCenter,
  forceCollide,
  forceLink,
  forceManyBody,
  forceSimulation,
  forceX,
  forceY,
  type Simulation,
  type SimulationLinkDatum,
  type SimulationNodeDatum,
} from "d3-force";
import { select } from "d3-selection";
import { drag } from "d3-drag";
import { zoom, zoomIdentity, type ZoomTransform } from "d3-zoom";
import "d3-transition";
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import type { GraphEdge, GraphNode } from "@/types/api";
import { resolveArchetype } from "@/lib/archetypes";

interface Props {
  agents: GraphNode[];
  edges: GraphEdge[];
  // Highlights nodes that just posted; map of nodeId → last-post timestamp ms
  recentlyActive?: Map<number, number>;
}
const props = withDefaults(defineProps<Props>(), {
  recentlyActive: () => new Map<number, number>(),
});
const emit = defineEmits<{ select: [agent: GraphNode | null] }>();

interface D3Node extends GraphNode, SimulationNodeDatum {
  // d3 mutates these
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number | null;
  fy?: number | null;
}
interface D3Link extends SimulationLinkDatum<D3Node> {
  source: D3Node | number;
  target: D3Node | number;
  type?: string;
}

const container = ref<HTMLDivElement | null>(null);
const svgRef = ref<SVGSVGElement | null>(null);
const labelsRef = ref<HTMLDivElement | null>(null);
const selectedId = ref<number | null>(null);
const hoveredId = ref<number | null>(null);
const transform = ref<ZoomTransform>(zoomIdentity);

let simulation: Simulation<D3Node, D3Link> | null = null;
let nodesData: D3Node[] = [];
let linksData: D3Link[] = [];
const nodeMap = new Map<number, D3Node>();

function nodeRadius(n: D3Node): number {
  return Math.min(28, 10 + Math.sqrt(Math.max(0, n.post_count)) * 2.4);
}
function nodeColor(n: D3Node): string {
  return resolveArchetype(n.archetype).color;
}
function isActive(n: D3Node): boolean {
  const ts = props.recentlyActive.get(n.id);
  if (!ts) return false;
  return Date.now() - ts < 2500;
}

const visibleLabels = computed<D3Node[]>(() => {
  // Show labels for: hovered, selected, neighbors of selected, and
  // the top-6 most-active nodes overall.
  const out = new Map<number, D3Node>();
  const sortedByActivity = [...nodesData]
    .sort((a, b) => (b.post_count ?? 0) - (a.post_count ?? 0))
    .slice(0, 6);
  for (const n of sortedByActivity) out.set(n.id, n);
  if (hoveredId.value !== null) {
    const h = nodeMap.get(hoveredId.value);
    if (h) out.set(h.id, h);
  }
  if (selectedId.value !== null) {
    const sel = nodeMap.get(selectedId.value);
    if (sel) out.set(sel.id, sel);
    for (const e of linksData) {
      const s = (e.source as D3Node).id ?? (e.source as number);
      const t = (e.target as D3Node).id ?? (e.target as number);
      if (s === selectedId.value) {
        const n = nodeMap.get(t as number);
        if (n) out.set(n.id, n);
      } else if (t === selectedId.value) {
        const n = nodeMap.get(s as number);
        if (n) out.set(n.id, n);
      }
    }
  }
  return [...out.values()];
});

const dimmedIds = computed<Set<number>>(() => {
  if (selectedId.value === null) return new Set();
  const keep = new Set<number>([selectedId.value]);
  for (const e of linksData) {
    const s = (e.source as D3Node).id ?? (e.source as number);
    const t = (e.target as D3Node).id ?? (e.target as number);
    if (s === selectedId.value) keep.add(t as number);
    if (t === selectedId.value) keep.add(s as number);
  }
  const dim = new Set<number>();
  for (const n of nodesData) if (!keep.has(n.id)) dim.add(n.id);
  return dim;
});

function initSimulation() {
  if (!container.value || !svgRef.value) return;
  const rect = container.value.getBoundingClientRect();
  const width = Math.max(320, rect.width);
  const height = Math.max(320, rect.height);

  simulation = forceSimulation<D3Node, D3Link>()
    .force(
      "link",
      forceLink<D3Node, D3Link>()
        .id((d) => d.id)
        .distance((l) => (l.type === "bridge" ? 140 : 80))
        .strength((l) => (l.type === "bridge" ? 0.15 : 0.4)),
    )
    .force("charge", forceManyBody().strength(-280).distanceMax(360))
    .force("center", forceCenter(width / 2, height / 2))
    .force("collide", forceCollide<D3Node>((d) => nodeRadius(d) + 6))
    .force("x", forceX(width / 2).strength(0.04))
    .force("y", forceY(height / 2).strength(0.04));

  simulation.on("tick", tick);

  const svg = select(svgRef.value);
  svg.call(
    zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.4, 4])
      .on("zoom", (event) => {
        transform.value = event.transform;
        svg.select<SVGGElement>(".graph-root").attr("transform", event.transform.toString());
      }) as any,
  );
  svg.on("dblclick.zoom", null);
  svg.on("click", (event) => {
    if (event.target === svgRef.value) {
      selectedId.value = null;
      emit("select", null);
    }
  });
}

function updateGraph() {
  if (!simulation) return;
  const incomingIds = new Set(props.agents.map((a) => a.id));
  // Remove dropped
  nodesData = nodesData.filter((n) => incomingIds.has(n.id));
  nodeMap.clear();
  for (const n of nodesData) nodeMap.set(n.id, n);
  // Add new / update existing
  for (const agent of props.agents) {
    const existing = nodeMap.get(agent.id);
    if (existing) {
      Object.assign(existing, agent, {
        x: existing.x,
        y: existing.y,
        vx: existing.vx,
        vy: existing.vy,
        fx: existing.fx,
        fy: existing.fy,
      });
    } else {
      const node: D3Node = { ...agent };
      nodesData.push(node);
      nodeMap.set(agent.id, node);
    }
  }
  // Remap edges, dropping any with missing endpoints
  linksData = props.edges
    .map((e) => {
      const sId = typeof e.source === "number" ? e.source : (e.source as GraphNode).id;
      const tId = typeof e.target === "number" ? e.target : (e.target as GraphNode).id;
      return { source: sId, target: tId, type: e.type };
    })
    .filter((e) => nodeMap.has(e.source as number) && nodeMap.has(e.target as number)) as D3Link[];

  simulation.nodes(nodesData);
  (simulation.force("link") as any).links(linksData);
  simulation.alpha(0.6).restart();
  renderJoin();
}

function renderJoin() {
  if (!svgRef.value) return;
  const root = select(svgRef.value).select<SVGGElement>(".graph-root");
  if (root.empty()) return;

  // ---- Defs: per-edge linear gradients ----
  const defs = select(svgRef.value).select<SVGDefsElement>("defs");
  const gradSel = defs
    .selectAll<SVGLinearGradientElement, D3Link>("linearGradient.edge-grad")
    .data(linksData, (d) => `g-${(d.source as D3Node).id ?? d.source}-${(d.target as D3Node).id ?? d.target}`);
  gradSel.exit().remove();
  const gradEnter = gradSel
    .enter()
    .append("linearGradient")
    .attr("class", "edge-grad")
    .attr("id", (d) => `grad-${(d.source as D3Node).id ?? d.source}-${(d.target as D3Node).id ?? d.target}`)
    .attr("gradientUnits", "userSpaceOnUse");
  gradEnter
    .append("stop")
    .attr("class", "stop-source")
    .attr("offset", "0%");
  gradEnter
    .append("stop")
    .attr("class", "stop-target")
    .attr("offset", "100%");

  // ---- Links ----
  const linkSel = root
    .select<SVGGElement>(".links")
    .selectAll<SVGPathElement, D3Link>("path.link")
    .data(linksData, (d) => `l-${(d.source as D3Node).id ?? d.source}-${(d.target as D3Node).id ?? d.target}`);
  linkSel.exit().remove();
  linkSel
    .enter()
    .append("path")
    .attr("class", "link")
    .attr("fill", "none")
    .attr("stroke-width", 1.4)
    .attr("stroke-linecap", "round")
    .attr("stroke", (d) => `url(#grad-${(d.source as D3Node).id ?? d.source}-${(d.target as D3Node).id ?? d.target})`);

  // ---- Nodes ----
  const nodeSel = root
    .select<SVGGElement>(".nodes")
    .selectAll<SVGGElement, D3Node>("g.node")
    .data(nodesData, (d) => String(d.id));
  nodeSel.exit().transition().duration(220).attr("opacity", 0).remove();

  const nodeEnter = nodeSel
    .enter()
    .append("g")
    .attr("class", "node")
    .attr("opacity", 0)
    .style("cursor", "pointer")
    .on("mouseenter", (_event, d) => { hoveredId.value = d.id; })
    .on("mouseleave", () => { hoveredId.value = null; })
    .on("click", (event, d) => {
      event.stopPropagation();
      selectedId.value = selectedId.value === d.id ? null : d.id;
      emit("select", selectedId.value === null ? null : d);
    })
    .call(
      drag<SVGGElement, D3Node>()
        .on("start", (event, d) => {
          if (!event.active) simulation?.alphaTarget(0.3).restart();
          d.fx = d.x ?? 0;
          d.fy = d.y ?? 0;
        })
        .on("drag", (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on("end", (event, d) => {
          if (!event.active) simulation?.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        }) as any,
    );

  nodeEnter
    .append("circle")
    .attr("class", "node-glow")
    .attr("fill", (d) => nodeColor(d))
    .attr("opacity", 0)
    .attr("filter", "url(#glow)");

  nodeEnter
    .append("circle")
    .attr("class", "node-fill")
    .attr("fill", (d) => `url(#node-grad-${archIdx(d.archetype)})`)
    .attr("stroke", "rgba(255,255,255,0.85)")
    .attr("stroke-width", 1.5)
    .attr("r", 0);

  nodeEnter
    .transition()
    .duration(450)
    .attr("opacity", 1);
}

function archIdx(name: string): number {
  return Math.abs(hashString(resolveArchetype(name).label)) % 10;
}
function hashString(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = ((h << 5) - h + s.charCodeAt(i)) | 0;
  return h;
}

function tick() {
  if (!svgRef.value) return;
  const root = select(svgRef.value).select<SVGGElement>(".graph-root");

  // Update gradient endpoints to match link positions
  const defs = select(svgRef.value).select<SVGDefsElement>("defs");
  defs
    .selectAll<SVGLinearGradientElement, D3Link>("linearGradient.edge-grad")
    .attr("x1", (d) => (d.source as D3Node).x ?? 0)
    .attr("y1", (d) => (d.source as D3Node).y ?? 0)
    .attr("x2", (d) => (d.target as D3Node).x ?? 0)
    .attr("y2", (d) => (d.target as D3Node).y ?? 0);

  defs
    .selectAll<SVGStopElement, D3Link>("stop.stop-source")
    .attr("stop-color", (d) => nodeColor(d.source as D3Node))
    .attr("stop-opacity", (d) => edgeOpacity(d));
  defs
    .selectAll<SVGStopElement, D3Link>("stop.stop-target")
    .attr("stop-color", (d) => nodeColor(d.target as D3Node))
    .attr("stop-opacity", (d) => edgeOpacity(d));

  // Curved bezier paths
  root
    .select(".links")
    .selectAll<SVGPathElement, D3Link>("path.link")
    .attr("d", (d) => {
      const s = d.source as D3Node;
      const t = d.target as D3Node;
      const sx = s.x ?? 0, sy = s.y ?? 0, tx = t.x ?? 0, ty = t.y ?? 0;
      const dx = tx - sx, dy = ty - sy;
      const dr = Math.sqrt(dx * dx + dy * dy) * 1.8;
      return `M${sx},${sy} A${dr},${dr} 0 0,1 ${tx},${ty}`;
    });

  // Nodes
  const nodeSel = root.select(".nodes").selectAll<SVGGElement, D3Node>("g.node");
  nodeSel.attr("transform", (d) => `translate(${d.x ?? 0},${d.y ?? 0})`);
  nodeSel.attr("opacity", (d) => (dimmedIds.value.has(d.id) ? 0.22 : 1));
  nodeSel
    .select<SVGCircleElement>("circle.node-fill")
    .attr("r", (d) => nodeRadius(d) * (selectedId.value === d.id ? 1.18 : 1))
    .attr("stroke", (d) =>
      selectedId.value === d.id
        ? "var(--primary)"
        : hoveredId.value === d.id
          ? "rgba(255,255,255,1)"
          : "rgba(255,255,255,0.7)",
    )
    .attr("stroke-width", (d) => (selectedId.value === d.id ? 2.5 : 1.5));
  nodeSel
    .select<SVGCircleElement>("circle.node-glow")
    .attr("r", (d) => nodeRadius(d) * 1.9)
    .attr("opacity", (d) => {
      if (selectedId.value === d.id) return 0.55;
      if (isActive(d)) return 0.45;
      if (hoveredId.value === d.id) return 0.35;
      return 0;
    });
}

function syncLabels() {
  // d3 label positions need to follow zoom transform
  if (!labelsRef.value) return;
  const t = transform.value;
  const els = labelsRef.value.querySelectorAll<HTMLDivElement>(".label");
  els.forEach((el) => {
    const id = Number(el.dataset.id);
    const n = nodeMap.get(id);
    if (!n || n.x == null || n.y == null) {
      el.style.display = "none";
      return;
    }
    const x = t.applyX(n.x);
    const y = t.applyY(n.y);
    el.style.transform = `translate(${x}px, ${y - nodeRadius(n) - 14}px) translate(-50%, -100%)`;
    el.style.display = "block";
  });
}

let labelTimer: number | null = null;
function startLabelLoop() {
  const loop = () => {
    syncLabels();
    labelTimer = requestAnimationFrame(loop);
  };
  loop();
}

let resizeObserver: ResizeObserver | null = null;
function resize() {
  if (!simulation || !container.value) return;
  const rect = container.value.getBoundingClientRect();
  (simulation.force("center") as any).x(rect.width / 2).y(rect.height / 2);
  (simulation.force("x") as any).x(rect.width / 2);
  (simulation.force("y") as any).y(rect.height / 2);
  simulation.alpha(0.2).restart();
}

function edgeOpacity(d: D3Link): number {
  if (selectedId.value !== null) {
    const s = (d.source as D3Node).id;
    const t = (d.target as D3Node).id;
    return s === selectedId.value || t === selectedId.value ? 0.95 : 0.07;
  }
  return 0.55;
}

onMounted(() => {
  initSimulation();
  updateGraph();
  startLabelLoop();
  if (container.value && typeof ResizeObserver !== "undefined") {
    resizeObserver = new ResizeObserver(() => resize());
    resizeObserver.observe(container.value);
  }
});

onBeforeUnmount(() => {
  simulation?.stop();
  simulation = null;
  resizeObserver?.disconnect();
  if (labelTimer != null) cancelAnimationFrame(labelTimer);
});

watch(() => [props.agents, props.edges], () => updateGraph(), { deep: true });
</script>

<template>
  <div class="graph-container" ref="container">
    <svg ref="svgRef" class="graph-svg">
      <defs>
        <!-- glow filter for active/selected nodes -->
        <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="6" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
        <!-- per-archetype radial node fills -->
        <template v-for="(arch, idx) in archetypeColors" :key="arch">
          <radialGradient :id="`node-grad-${idx}`" cx="35%" cy="35%" r="65%">
            <stop offset="0%" :stop-color="lighten(arch, 35)" />
            <stop offset="100%" :stop-color="arch" />
          </radialGradient>
        </template>
      </defs>
      <g class="graph-root">
        <g class="links" />
        <g class="nodes" />
      </g>
    </svg>
    <div class="labels" ref="labelsRef">
      <div
        v-for="n in visibleLabels"
        :key="n.id"
        class="label"
        :data-id="n.id"
      >
        {{ n.name }}
      </div>
    </div>
    <div v-if="agents.length === 0" class="graph-empty">
      <div class="empty-pulse" />
      <p>Personas will appear here as they are generated.</p>
    </div>
  </div>
</template>

<script lang="ts">
const archetypeColors = [
  "#22d3ee",
  "#a78bfa",
  "#f97316",
  "#22c55e",
  "#fbbf24",
  "#84cc16",
  "#38bdf8",
  "#ec4899",
  "#60a5fa",
  "#94a3b8",
];
function lighten(hex: string, pct: number): string {
  const c = hex.replace("#", "");
  const r = parseInt(c.slice(0, 2), 16);
  const g = parseInt(c.slice(2, 4), 16);
  const b = parseInt(c.slice(4, 6), 16);
  const mix = (v: number) => Math.min(255, Math.round(v + (255 - v) * (pct / 100)));
  return `rgb(${mix(r)}, ${mix(g)}, ${mix(b)})`;
}
export default {};
</script>

<style scoped>
.graph-container {
  position: relative;
  width: 100%;
  height: 100%;
  background:
    radial-gradient(ellipse at center, rgba(34, 211, 238, 0.04) 0%, transparent 60%),
    radial-gradient(circle, var(--border-subtle) 1px, transparent 1px);
  background-size: 100% 100%, 28px 28px;
  background-position: center, 0 0;
  overflow: hidden;
}
.graph-svg {
  width: 100%;
  height: 100%;
  display: block;
  cursor: grab;
}
.graph-svg:active { cursor: grabbing; }
.labels {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.label {
  position: absolute;
  top: 0;
  left: 0;
  padding: 3px 8px;
  font-size: 11px;
  font-weight: 500;
  color: var(--fg-strong);
  background: rgba(15, 22, 32, 0.85);
  backdrop-filter: blur(8px);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  white-space: nowrap;
  box-shadow: var(--shadow-sm);
  transition: opacity var(--duration-fast) var(--ease-out);
}
.graph-empty {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--gap-md);
  color: var(--fg-subtle);
  font-size: 13px;
  pointer-events: none;
}
.empty-pulse {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  border: 2px solid var(--primary-muted);
  border-top-color: var(--primary);
  animation: spin 1.4s linear infinite;
}
</style>
