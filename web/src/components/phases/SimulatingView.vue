<script setup lang="ts">
import { computed, ref } from "vue";
import { Twitter, MessagesSquare, Network as NetworkIcon, X as XIcon } from "lucide-vue-next";
import ActionCard from "@/components/ActionCard.vue";
import GraphPanel from "@/components/GraphPanel.vue";
import Button from "@/components/ui/Button.vue";
import type { AgentActionRecord, GraphEdge, GraphNode } from "@/types/api";

interface Props {
  actions: AgentActionRecord[];
  agents: GraphNode[];
  edges: GraphEdge[];
  twitterCount: number;
  redditCount: number;
}
const props = defineProps<Props>();

const showGraph = ref(false);
const agentMap = computed(() => {
  const m = new Map<number, GraphNode>();
  for (const a of props.agents) m.set(a.id, a);
  return m;
});
const twitter = computed(() => props.actions.filter((a) => a.platform === "twitter").slice(0, 50));
const reddit = computed(() => props.actions.filter((a) => a.platform === "reddit").slice(0, 50));
</script>

<template>
  <div class="layout">
    <div class="cols">
      <div class="col">
        <div class="col-head">
          <div class="title">
            <Twitter :size="14" />
            <span>Twitter</span>
          </div>
          <span class="count">{{ twitterCount }} actions</span>
        </div>
        <div class="feed">
          <TransitionGroup name="action">
            <ActionCard
              v-for="action in twitter"
              :key="action.timestamp + '_' + action.agent_id + '_' + action.action_type"
              :action="action"
              :agent="agentMap.get(action.agent_id)"
            />
          </TransitionGroup>
          <div v-if="twitter.length === 0" class="empty">No twitter actions yet.</div>
        </div>
      </div>
      <div class="col">
        <div class="col-head">
          <div class="title">
            <MessagesSquare :size="14" />
            <span>Reddit</span>
          </div>
          <span class="count">{{ redditCount }} actions</span>
        </div>
        <div class="feed">
          <TransitionGroup name="action">
            <ActionCard
              v-for="action in reddit"
              :key="action.timestamp + '_' + action.agent_id + '_' + action.action_type"
              :action="action"
              :agent="agentMap.get(action.agent_id)"
            />
          </TransitionGroup>
          <div v-if="reddit.length === 0" class="empty">No reddit actions yet.</div>
        </div>
      </div>
    </div>

    <div class="minimap-toggle">
      <Button size="sm" variant="ghost" @click="showGraph = !showGraph">
        <NetworkIcon :size="14" />
        {{ showGraph ? "Hide" : "Show" }} graph
      </Button>
    </div>

    <Teleport to="body">
      <transition name="map">
        <div v-if="showGraph" class="map-overlay" @click.self="showGraph = false">
          <div class="map-shell">
            <button class="map-close" @click="showGraph = false" aria-label="Close graph">
              <XIcon :size="16" />
            </button>
            <GraphPanel :agents="agents" :edges="edges" />
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<style scoped>
.layout {
  position: relative;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}
.cols {
  display: grid;
  grid-template-columns: 1fr 1fr;
  height: 100%;
  min-height: 0;
}
.col {
  display: flex;
  flex-direction: column;
  min-height: 0;
  border-right: 1px solid var(--border);
}
.col:last-child { border-right: none; }
.col-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--gap-md) var(--gap-lg);
  border-bottom: 1px solid var(--border);
  background: var(--bg-elevated);
}
.title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--fg-strong);
  letter-spacing: 0.02em;
}
.count {
  font-size: 11px;
  color: var(--fg-muted);
  font-variant-numeric: tabular-nums;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.feed {
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
.minimap-toggle {
  position: absolute;
  bottom: var(--gap-md);
  right: var(--gap-md);
  z-index: 8;
}
.map-overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  background: rgba(5, 9, 13, 0.6);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--gap-xl);
}
.map-shell {
  position: relative;
  width: min(1100px, 100%);
  height: min(700px, 100%);
  background: var(--panel);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-lg);
}
.map-close {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 5;
  width: 30px;
  height: 30px;
  border-radius: var(--radius-md);
  background: var(--bg-elevated);
  border: 1px solid var(--border-strong);
  color: var(--fg);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}
.map-close:hover { color: var(--primary); border-color: var(--primary); }
.map-enter-active, .map-leave-active { transition: opacity 220ms ease; }
.map-enter-from, .map-leave-to { opacity: 0; }

.action-enter-active {
  transition: all 320ms cubic-bezier(0.34, 1.56, 0.64, 1);
}
.action-enter-from {
  opacity: 0;
  transform: translateY(-12px);
}
.action-leave-active {
  transition: all 200ms ease;
}
.action-leave-to {
  opacity: 0;
  transform: scale(0.96);
}
</style>
