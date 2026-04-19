<script setup lang="ts">
import GraphPanel from "@/components/GraphPanel.vue";
import PersonaCard from "@/components/PersonaCard.vue";
import type { AgentProfile, GraphEdge, GraphNode } from "@/types/api";

interface Props {
  agents: GraphNode[];
  edges: GraphEdge[];
  profiles: AgentProfile[];
  expectedCount: number;
}
defineProps<Props>();
</script>

<template>
  <div class="phase-grid">
    <div class="graph-pane">
      <GraphPanel :agents="agents" :edges="edges" />
    </div>
    <div class="rail">
      <div class="rail-head">
        <h3>Personas</h3>
        <span class="count">
          {{ profiles.length }}<span v-if="expectedCount">/{{ expectedCount }}</span>
        </span>
      </div>
      <div class="rail-list">
        <TransitionGroup name="persona">
          <PersonaCard
            v-for="profile in [...profiles].reverse()"
            :key="profile.user_id ?? profile.username ?? profile.name"
            :profile="profile"
          />
        </TransitionGroup>
        <div v-if="profiles.length === 0" class="empty">
          Generating personas… first one usually takes ~10s.
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.phase-grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 0;
  height: 100%;
  overflow: hidden;
  min-height: 0;
}
.graph-pane {
  position: relative;
  min-width: 0;
  min-height: 0;
  border-right: 1px solid var(--border);
}
.rail {
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
  background: var(--panel);
}
.rail-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: var(--gap-md) var(--gap-lg);
  border-bottom: 1px solid var(--border);
}
.rail-head h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--fg-strong);
}
.count {
  font-size: 12px;
  color: var(--fg-muted);
  font-variant-numeric: tabular-nums;
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
.persona-enter-active {
  transition: all 360ms cubic-bezier(0.34, 1.56, 0.64, 1);
}
.persona-enter-from {
  opacity: 0;
  transform: translateY(-8px) scale(0.96);
  filter: blur(4px);
}
.persona-leave-active {
  transition: all 240ms ease;
}
.persona-leave-to {
  opacity: 0;
  transform: translateX(20px);
}
</style>
