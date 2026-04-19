<script setup lang="ts">
import { AlertTriangle, RefreshCw } from "lucide-vue-next";
import Button from "@/components/ui/Button.vue";
import SimulatingView from "@/components/phases/SimulatingView.vue";
import type { AgentActionRecord, GraphEdge, GraphNode, SimState } from "@/types/api";

interface Props {
  state: SimState;
  error?: string | null;
  actions: AgentActionRecord[];
  agents: GraphNode[];
  edges: GraphEdge[];
  twitterCount: number;
  redditCount: number;
}
const props = defineProps<Props>();

const titles: Record<string, string> = {
  FAILED: "Simulation failed",
  CANCELLED: "Simulation cancelled",
  INTERRUPTED: "Simulation interrupted",
};
</script>

<template>
  <div class="layout">
    <div class="banner">
      <div class="banner-left">
        <AlertTriangle :size="20" />
        <div class="banner-text">
          <strong>{{ titles[state] || "Simulation ended early" }}</strong>
          <span v-if="error">{{ error }}</span>
          <span v-else>Partial results below — start a fresh run to continue.</span>
        </div>
      </div>
      <router-link to="/">
        <Button variant="primary">
          <RefreshCw :size="14" />
          New prediction
        </Button>
      </router-link>
    </div>
    <div class="feed-wrap">
      <SimulatingView
        :actions="actions"
        :agents="agents"
        :edges="edges"
        :twitter-count="twitterCount"
        :reddit-count="redditCount"
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
