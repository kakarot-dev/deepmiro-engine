<script setup lang="ts">
import SimulatingView from "@/components/phases/SimulatingView.vue";
import type { AgentActionRecord, GraphEdge, GraphNode, SimSnapshot, SimState } from "@/types/api";

interface Props {
  state: SimState;
  error?: string | null;
  actions: AgentActionRecord[];
  agents: GraphNode[];
  edges: GraphEdge[];
  snapshot: SimSnapshot | null;
  twitterCount: number;
  redditCount: number;
  recentlyActive?: Map<number, number>;
  recentlyActiveEdges?: Map<string, number>;
}
const props = withDefaults(defineProps<Props>(), {
  recentlyActive: () => new Map<number, number>(),
  recentlyActiveEdges: () => new Map<string, number>(),
});
const emit = defineEmits<{
  "select-action": [action: AgentActionRecord];
  "select-agent": [agent: GraphNode | null];
  "select-edge": [edge: GraphEdge | null];
}>();
</script>

<template>
  <div class="layout">
    <!-- The interrupted banner is rendered by SimulationRunView at the
         top of every step, so it's not duplicated here. TerminalView's
         job is just to render the data feed + graph. -->
    <div class="feed-wrap">
      <SimulatingView
        :actions="actions"
        :agents="agents"
        :edges="edges"
        :snapshot="snapshot"
        :twitter-count="twitterCount"
        :reddit-count="redditCount"
        :recently-active="recentlyActive"
        :recently-active-edges="recentlyActiveEdges"
        @select-action="(a) => emit('select-action', a)"
        @select-agent="(a) => emit('select-agent', a)"
        @select-edge="(e) => emit('select-edge', e)"
      />
    </div>
  </div>
</template>

<style scoped>
.layout {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}
.banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--gap-md) var(--gap-lg);
  background:
    linear-gradient(90deg, color-mix(in srgb, var(--warning) 12%, transparent), transparent 60%),
    var(--bg-elevated);
  border-bottom: 1px solid var(--border);
  color: var(--warning);
}
.banner-left {
  display: flex;
  align-items: center;
  gap: var(--gap-sm);
}
.banner-text {
  display: flex;
  flex-direction: column;
  font-size: 13px;
  line-height: 1.3;
  color: var(--fg);
}
.banner-text strong { color: var(--fg-strong); font-weight: 600; }
.banner-text span { font-size: 12px; color: var(--fg-muted); }
.feed-wrap { flex: 1; min-height: 0; }
</style>
