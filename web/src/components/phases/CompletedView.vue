<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";
import { CheckCircle2, FileText } from "lucide-vue-next";
import Button from "@/components/ui/Button.vue";
import SimulatingView from "@/components/phases/SimulatingView.vue";
import type { AgentActionRecord, GraphEdge, GraphNode, SimSnapshot } from "@/types/api";

interface Props {
  simId: string;
  snapshot: SimSnapshot | null;
  actions: AgentActionRecord[];
  agents: GraphNode[];
  edges: GraphEdge[];
  twitterCount: number;
  redditCount: number;
}
const props = defineProps<Props>();
const router = useRouter();

const totalActions = computed(() => props.twitterCount + props.redditCount);
function viewReport() {
  router.push({ name: "report", params: { simId: props.simId } });
}
</script>

<template>
  <div class="layout">
    <div class="banner">
      <div class="banner-left">
        <CheckCircle2 :size="20" />
        <div class="banner-text">
          <strong>Simulation complete.</strong>
          <span>{{ agents.length }} personas · {{ totalActions }} actions · {{ snapshot?.current_round ?? 0 }} rounds</span>
        </div>
      </div>
      <Button variant="primary" @click="viewReport">
        <FileText :size="14" />
        View report
      </Button>
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
    linear-gradient(90deg, color-mix(in srgb, var(--success) 12%, transparent), transparent 60%),
    var(--bg-elevated);
  border-bottom: 1px solid var(--border);
}
.banner-left {
  display: flex;
  align-items: center;
  gap: var(--gap-sm);
  color: var(--success);
}
.banner-text {
  display: flex;
  flex-direction: column;
  color: var(--fg);
  font-size: 13px;
  line-height: 1.3;
}
.banner-text strong {
  color: var(--fg-strong);
  font-weight: 600;
}
.banner-text span {
  font-size: 12px;
  color: var(--fg-muted);
}
.feed-wrap {
  flex: 1;
  min-height: 0;
}
</style>
