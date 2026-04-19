<script setup lang="ts">
/**
 * SimulatingView — universal layout. Graph stays primary on the left;
 * the right rail is the live action feed with platform tabs and
 * clickable cards (each opens an ActionSheet).
 */
import { computed, ref, watch, nextTick } from "vue";
import UniversalStepLayout from "@/components/UniversalStepLayout.vue";
import GraphPanel from "@/components/GraphPanel.vue";
import GraphBuildingView from "@/components/phases/GraphBuildingView.vue";
import ActionCard from "@/components/ActionCard.vue";
import type { AgentActionRecord, GraphEdge, GraphNode, SimSnapshot } from "@/types/api";

interface Props {
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

type Filter = "all" | "twitter" | "reddit";
const filter = ref<Filter>("all");
const feedRef = ref<HTMLDivElement | null>(null);

const agentMap = computed(() => {
  const m = new Map<number, GraphNode>();
  for (const a of props.agents) m.set(a.id, a);
  return m;
});
const filtered = computed(() => {
  let list = props.actions;
  if (filter.value !== "all") {
    list = list.filter((a) => a.platform === filter.value);
  }
  return list.slice(0, 100);
});

// Auto-scroll to top when a new action arrives (newest first)
watch(() => props.actions.length, async () => {
  await nextTick();
  feedRef.value?.scrollTo({ top: 0, behavior: "smooth" });
});
</script>

<template>
  <UniversalStepLayout>
    <GraphBuildingView v-if="agents.length === 0" :snapshot="snapshot" />
    <GraphPanel
      v-else
      :agents="agents"
      :edges="edges"
      :recently-active="recentlyActive"
      :recently-active-edges="recentlyActiveEdges"
      @select="(a) => emit('select-agent', a)"
      @select-edge="(e) => emit('select-edge', e)"
    />
    <template #rail>
      <div class="rail-head">
        <div class="rail-title">Live activity</div>
        <div class="filter">
          <button
            v-for="opt in (['all', 'twitter', 'reddit'] as Filter[])"
            :key="opt"
            class="filter-btn"
            :class="{ active: filter === opt }"
            @click="filter = opt"
          >
            {{ opt }}
            <span v-if="opt === 'twitter'" class="dim">{{ twitterCount }}</span>
            <span v-else-if="opt === 'reddit'" class="dim">{{ redditCount }}</span>
            <span v-else class="dim">{{ twitterCount + redditCount }}</span>
          </button>
        </div>
      </div>
      <div class="feed" ref="feedRef">
        <TransitionGroup name="action">
          <ActionCard
            v-for="a in filtered"
            :key="a.timestamp + '_' + a.agent_id + '_' + a.action_type"
            :action="a"
            :agent="agentMap.get(a.agent_id)"
            class="clickable"
            @click="emit('select-action', a)"
          />
        </TransitionGroup>
        <div v-if="filtered.length === 0" class="empty">
          No actions yet.
        </div>
      </div>
    </template>
  </UniversalStepLayout>
</template>

<style scoped>
.rail-head {
  padding: var(--gap-sm) var(--gap-md);
  border-bottom: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: var(--gap-sm);
}
.rail-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--fg-strong);
}
.filter { display: flex; gap: 4px; }
.filter-btn {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 6px 10px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--fg-muted);
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  text-transform: capitalize;
  transition: all var(--duration-fast) var(--ease-out);
}
.filter-btn:hover { color: var(--fg); border-color: var(--border-strong); }
.filter-btn.active {
  background: color-mix(in srgb, var(--primary) 14%, transparent);
  color: var(--primary);
  border-color: color-mix(in srgb, var(--primary) 35%, transparent);
}
.dim { color: var(--fg-subtle); font-variant-numeric: tabular-nums; }
.feed {
  flex: 1;
  overflow-y: auto;
  padding: var(--gap-md);
  display: flex;
  flex-direction: column;
  gap: var(--gap-sm);
  scroll-behavior: smooth;
}
.empty {
  padding: var(--gap-lg);
  text-align: center;
  font-size: 12px;
  color: var(--fg-subtle);
}
.clickable { cursor: pointer; }
.action-enter-active {
  transition: all 360ms cubic-bezier(0.34, 1.56, 0.64, 1);
}
.action-enter-from {
  opacity: 0;
  transform: translateY(-12px) scale(0.97);
  filter: blur(2px);
}
.action-leave-active { transition: all 200ms ease; }
.action-leave-to { opacity: 0; transform: scale(0.96); }
</style>
