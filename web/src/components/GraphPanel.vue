<script setup lang="ts">
import {
  forceCenter,
  forceCollide,
  forceLink,
  forceManyBody,
  forceSimulation,
  type Simulation,
  type SimulationLinkDatum,
  type SimulationNodeDatum,
} from "d3-force";
import { select } from "d3-selection";
import { drag } from "d3-drag";
import { zoom } from "d3-zoom";
import "d3-transition";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import type { GraphEdge, GraphNode } from "@/types/api";
import { resolveArchetype } from "@/lib/archetypes";
import { truncate } from "@/lib/format";

interface Props {
  agents: GraphNode[];
  edges: GraphEdge[];
}

const props = defineProps<Props>();

const container = ref<HTMLDivElement | null>(null);
const svgRef = ref<SVGSVGElement | null>(null);
const tooltipRef = ref<HTMLDivElement | null>(null);

interface D3Node extends GraphNode, SimulationNodeDatum {}
interface D3Link extends SimulationLinkDatum<D3Node> {}

let simulation: Simulation<D3Node, D3Link> | null = null;
let nodesData: D3Node[] = [];
let linksData: D3Link[] = [];
const nodeMap = new Map<number, D3Node>();

function nodeRadius(n: D3Node): number {
  // Base 8 + per-post growth, capped.
  return Math.min(24, 8 + Math.sqrt(Math.max(0, n.post_count)) * 2.2);
}

function nodeColor(n: D3Node): string {
  return resolveArchetype(n.archetype).color;
}

function initSimulation() {
  if (!container.value || !svgRef.value) return;
  const rect = container.value.getBoundingClientRect();
  const width = Math.max(320, rect.width);
  const height = Math.max(320, rect.height);

  simulation = forceSimulation<D3Node, D3Link>()
    .force(
      "link",
      forceLink<D3Node, D3Link>()
        // Return the same type that links carry in source/target
        // (numbers). Returning String(d.id) here while edges have
        // numeric source/target means d3 can't match them, treats
        // the raw number as a node, and crashes in forceLink with
        // "Cannot create property 'vx' on number '1'".
        .id((d) => d.id)
        .distance(60)
        .strength(0.3),
    )
    .force("charge", forceManyBody().strength(-240))
    .force("center", forceCenter(width / 2, height / 2))
    .force("collide", forceCollide<D3Node>((d) => nodeRadius(d) + 4));

  // Zoom + pan
  const svg = select(svgRef.value);
  svg.call(
    zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.4, 3])
      .on("zoom", (event) => {
        svg.select<SVGGElement>(".graph-root").attr("transform", event.transform.toString());
      }) as any,
  );
  svg.call((sel) => {
    sel.on("dblclick.zoom", null);
  });
}

function updateGraph() {
  if (!simulation || !svgRef.value) return;

  // Merge incoming props.agents into nodesData preserving positions.
  const existingIds = new Set(nodesData.map((n) => n.id));
  const incomingIds = new Set(props.agents.map((a) => a.id));

  // Remove dropped
  nodesData = nodesData.filter((n) => incomingIds.has(n.id));
  nodeMap.clear();
  for (const n of nodesData) nodeMap.set(n.id, n);

  // Add new / update existing
  for (const agent of props.agents) {
    const existing = nodeMap.get(agent.id);
    if (existing) {
      existing.post_count = agent.post_count;
      existing.lastPost = agent.lastPost;
      existing.name = agent.name;
      existing.archetype = agent.archetype;
    } else {
      const node: D3Node = { ...agent };
      nodesData.push(node);
      nodeMap.set(agent.id, node);
    }
  }

  // Remap edges so d3 resolves source/target objects.
  linksData = props.edges
    .map((e) => ({
      source: typeof e.source === "number" ? e.source : (e.source as GraphNode).id,
      target: typeof e.target === "number" ? e.target : (e.target as GraphNode).id,
    }))
    .filter((e) => nodeMap.has(Number(e.source)) && nodeMap.has(Number(e.target))) as D3Link[];

  simulation.nodes(nodesData);
  (simulation.force("link") as any).links(linksData);
  simulation.alpha(0.6).restart();

  renderJoin();
}

function renderJoin() {
  if (!svgRef.value) return;
  const svg = select(svgRef.value).select<SVGGElement>(".graph-root");
  if (svg.empty()) return;

  // Links
  const linkSel = svg
    .select<SVGGElement>(".links")
    .selectAll<SVGLineElement, D3Link>("line")
    .data(linksData, (d) => `${(d.source as D3Node).id ?? d.source}-${(d.target as D3Node).id ?? d.target}`);

  linkSel.exit().remove();
  linkSel.enter().append("line").attr("stroke", "var(--border-strong)").attr("stroke-width", 1);

  // Nodes
  const nodeSel = svg
    .select<SVGGElement>(".nodes")
    .selectAll<SVGGElement, D3Node>("g.node")
    .data(nodesData, (d) => String(d.id));

  nodeSel.exit().transition().duration(300).attr("opacity", 0).remove();

  const nodeEnter = nodeSel
    .enter()
    .append("g")
    .attr("class", "node")
    .attr("opacity", 0)
    .on("mouseenter", (event: MouseEvent, d) => showTooltip(event, d))
    .on("mousemove", (event: MouseEvent, d) => moveTooltip(event, d))
    .on("mouseleave", () => hideTooltip())
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
    .attr("r", 0)
    .attr("fill", (d) => nodeColor(d))
    .attr("stroke", "var(--bg)")
    .attr("stroke-width", 2);

  nodeEnter
    .append("text")
    .attr("class", "node-label")
    .attr("dy", 4)
    .attr("text-anchor", "middle")
    .attr("font-size", 10)
    .attr("fill", "var(--fg-strong)")
    .attr("pointer-events", "none")
    .text((d) => initials(d.name));

  nodeEnter.transition().duration(600).attr("opacity", 1);

  // Merge + update
  const merged = nodeEnter.merge(nodeSel as any);
  merged
    .select<SVGCircleElement>("circle")
    .transition()
    .duration(400)
    .attr("r", (d) => nodeRadius(d))
    .attr("fill", (d) => nodeColor(d));
  merged.select("text").text((d) => initials(d.name));

  simulation?.on("tick", () => {
    svg
      .select(".links")
      .selectAll<SVGLineElement, D3Link>("line")
      .attr("x1", (d) => (d.source as D3Node).x ?? 0)
      .attr("y1", (d) => (d.source as D3Node).y ?? 0)
      .attr("x2", (d) => (d.target as D3Node).x ?? 0)
      .attr("y2", (d) => (d.target as D3Node).y ?? 0);
    svg
      .select(".nodes")
      .selectAll<SVGGElement, D3Node>("g.node")
      .attr("transform", (d) => `translate(${d.x ?? 0}, ${d.y ?? 0})`);
  });
}

function initials(name: string): string {
  if (!name) return "?";
  const parts = name.split(/\s+/).filter(Boolean);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function showTooltip(event: MouseEvent, d: D3Node) {
  if (!tooltipRef.value) return;
  const arch = resolveArchetype(d.archetype);
  tooltipRef.value.innerHTML = `
    <div class="tt-name" style="color:${arch.color}">${d.name}</div>
    <div class="tt-meta">${arch.label} · ${d.post_count} posts</div>
    ${d.lastPost ? `<div class="tt-post">"${truncate(d.lastPost, 160)}"</div>` : ""}
  `;
  tooltipRef.value.style.display = "block";
  moveTooltip(event, d);
}

function moveTooltip(event: MouseEvent, _d: D3Node) {
  if (!tooltipRef.value || !container.value) return;
  const rect = container.value.getBoundingClientRect();
  tooltipRef.value.style.left = `${event.clientX - rect.left + 12}px`;
  tooltipRef.value.style.top = `${event.clientY - rect.top + 12}px`;
}

function hideTooltip() {
  if (tooltipRef.value) tooltipRef.value.style.display = "none";
}

function resize() {
  if (!simulation || !container.value) return;
  const rect = container.value.getBoundingClientRect();
  (simulation.force("center") as any).x(rect.width / 2).y(rect.height / 2);
  simulation.alpha(0.2).restart();
}

let resizeObserver: ResizeObserver | null = null;

onMounted(() => {
  initSimulation();
  updateGraph();
  if (container.value && typeof ResizeObserver !== "undefined") {
    resizeObserver = new ResizeObserver(() => resize());
    resizeObserver.observe(container.value);
  }
});

onBeforeUnmount(() => {
  simulation?.stop();
  simulation = null;
  resizeObserver?.disconnect();
});

watch(
  () => [props.agents, props.edges],
  () => updateGraph(),
  { deep: true },
);
</script>

<template>
  <div class="graph-container" ref="container">
    <svg ref="svgRef" class="graph-svg">
      <g class="graph-root">
        <g class="links" />
        <g class="nodes" />
      </g>
    </svg>
    <div class="graph-tooltip" ref="tooltipRef" />
    <div v-if="props.agents.length === 0" class="graph-empty">
      <p>Personas will appear here once the simulation starts.</p>
    </div>
    <div class="graph-legend">
      <div
        v-for="arch in legendItems"
        :key="arch.label"
        class="legend-item"
      >
        <span class="legend-dot" :style="{ background: arch.color }" />
        {{ arch.label }}
      </div>
    </div>
  </div>
</template>

<script lang="ts">
// Module-level legend derived from a subset of common archetypes.
// We compute it once — archetype→color is stable.
import { resolveArchetype as _resolve } from "@/lib/archetypes";
const legendKeys = [
  "TechCEO",
  "Politician",
  "Journalist",
  "AdvocacyGroup",
  "Corporation",
  "AppDeveloper",
  "Subreddit",
  "Person",
];
const seen = new Set<string>();
const legendItems = legendKeys
  .map((key) => _resolve(key))
  .filter((a) => {
    if (seen.has(a.label)) return false;
    seen.add(a.label);
    return true;
  });
export default {};
</script>

<style scoped>
.graph-container {
  position: relative;
  width: 100%;
  height: 100%;
  background:
    radial-gradient(
      ellipse at center,
      var(--panel) 0%,
      var(--bg) 100%
    );
  overflow: hidden;
}

.graph-svg {
  width: 100%;
  height: 100%;
  display: block;
  cursor: grab;
}

.graph-svg:active {
  cursor: grabbing;
}

.graph-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--fg-subtle);
  font-size: 14px;
  pointer-events: none;
}

.graph-tooltip {
  position: absolute;
  display: none;
  max-width: 280px;
  padding: 10px 12px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-md);
  color: var(--fg);
  font-size: 12px;
  box-shadow: var(--shadow-lg);
  pointer-events: none;
  z-index: 50;
}

.graph-tooltip :deep(.tt-name) {
  font-weight: 600;
  font-size: 13px;
  margin-bottom: 2px;
}

.graph-tooltip :deep(.tt-meta) {
  color: var(--fg-muted);
  margin-bottom: 6px;
  font-size: 11px;
}

.graph-tooltip :deep(.tt-post) {
  color: var(--fg);
  font-style: italic;
  border-top: 1px solid var(--border-subtle);
  padding-top: 6px;
  margin-top: 4px;
  line-height: 1.4;
}

.graph-legend {
  position: absolute;
  bottom: var(--gap-md);
  left: var(--gap-md);
  display: flex;
  flex-wrap: wrap;
  gap: var(--gap-xs) var(--gap-sm);
  max-width: 320px;
  padding: var(--gap-sm) var(--gap-md);
  background: rgba(15, 22, 32, 0.8);
  backdrop-filter: blur(8px);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  font-size: 11px;
  color: var(--fg-muted);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: var(--radius-full);
}
</style>
