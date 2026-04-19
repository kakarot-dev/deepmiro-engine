<script setup lang="ts">
/**
 * PersonasView — universal layout. Graph stays primary on the left;
 * scrollable persona card grid lives in the right rail.
 */
import { computed } from "vue";
import UniversalStepLayout from "@/components/UniversalStepLayout.vue";
import GraphPanel from "@/components/GraphPanel.vue";
import GraphBuildingView from "@/components/phases/GraphBuildingView.vue";
import PersonaCard from "@/components/PersonaCard.vue";
import type { AgentProfile, GraphEdge, GraphNode, SimSnapshot } from "@/types/api";

interface Props {
  profiles: AgentProfile[];
  agents: GraphNode[];
  edges: GraphEdge[];
  snapshot: SimSnapshot | null;
  expectedCount: number;
  generating?: boolean;
  recentlyActive?: Map<number, number>;
  recentlyActiveEdges?: Map<string, number>;
}
const props = withDefaults(defineProps<Props>(), {
  generating: false,
  recentlyActive: () => new Map<number, number>(),
  recentlyActiveEdges: () => new Map<string, number>(),
});
const emit = defineEmits<{
  "select-persona": [profile: AgentProfile];
  "select-agent": [agent: GraphNode | null];
  "select-edge": [edge: GraphEdge | null];
}>();

const ordered = computed(() => {
  if (props.generating) return [...props.profiles].reverse();
  return [...props.profiles].sort((a, b) => {
    const an = (a.realname || a.name || a.username || "").toLowerCase();
    const bn = (b.realname || b.name || b.username || "").toLowerCase();
    return an.localeCompare(bn);
  });
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
        <div class="rail-title">Personas</div>
        <span class="sub">
          {{ profiles.length }}<span v-if="expectedCount">/{{ expectedCount }}</span>
          <span v-if="generating" class="generating-pill">generating…</span>
        </span>
      </div>
      <div class="rail-list">
        <TransitionGroup name="persona">
          <PersonaCard
            v-for="profile in ordered"
            :key="profile.user_id ?? profile.username ?? profile.name"
            :profile="profile"
            @click="emit('select-persona', profile)"
          />
        </TransitionGroup>
        <div v-if="profiles.length === 0" class="empty">
          Personas will appear as they are generated.
        </div>
      </div>
    </template>
  </UniversalStepLayout>
</template>

<style scoped>
.rail-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: var(--gap-md) var(--gap-lg);
  border-bottom: 1px solid var(--border);
}
.rail-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--fg-strong);
}
.sub {
  font-size: 12px;
  color: var(--fg-muted);
  font-variant-numeric: tabular-nums;
  display: inline-flex;
  align-items: center;
  gap: var(--gap-sm);
}
.generating-pill {
  padding: 2px 8px;
  background: color-mix(in srgb, var(--primary) 14%, transparent);
  color: var(--primary);
  border-radius: var(--radius-full);
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  animation: pulse-fade 2s ease-in-out infinite;
}
.rail-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--gap-md);
  display: flex;
  flex-direction: column;
  gap: var(--gap-sm);
}
.empty {
  padding: var(--gap-lg);
  text-align: center;
  font-size: 12px;
  color: var(--fg-subtle);
}
@keyframes pulse-fade {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.55; }
}
.persona-enter-active {
  transition: all 360ms cubic-bezier(0.34, 1.56, 0.64, 1);
}
.persona-enter-from {
  opacity: 0;
  transform: translateY(-8px) scale(0.96);
  filter: blur(4px);
}
.persona-leave-active { transition: all 240ms ease; }
.persona-leave-to { opacity: 0; }
</style>
