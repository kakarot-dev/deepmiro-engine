<script setup lang="ts">
import GraphPanel from "@/components/GraphPanel.vue";
import GraphBuildingView from "@/components/phases/GraphBuildingView.vue";
import type { GraphEdge, GraphNode, SimSnapshot } from "@/types/api";

interface Props {
  agents: GraphNode[];
  edges: GraphEdge[];
  snapshot: SimSnapshot | null;
  recentlyActive?: Map<number, number>;
  recentlyActiveEdges?: Map<string, number>;
}
const props = withDefaults(defineProps<Props>(), {
  recentlyActive: () => new Map<number, number>(),
  recentlyActiveEdges: () => new Map<string, number>(),
});
const emit = defineEmits<{
  select: [agent: GraphNode | null];
  "select-edge": [edge: GraphEdge | null];
}>();

const isEmpty = () => props.agents.length === 0;
</script>

<template>
  <GraphBuildingView v-if="isEmpty()" :snapshot="snapshot" />
  <div v-else class="graph-wrap">
    <GraphPanel
      :agents="agents"
      :edges="edges"
      :recently-active="recentlyActive"
      :recently-active-edges="recentlyActiveEdges"
      @select="(a) => emit('select', a)"
      @select-edge="(e) => emit('select-edge', e)"
    />
  </div>
</template>

<style scoped>
.graph-wrap {
  height: 100%;
  min-height: 0;
}
</style>
