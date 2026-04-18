<script setup lang="ts">
import { computed, ref, toRef, watch } from "vue";
import { useRouter } from "vue-router";
import LifecycleBar from "@/components/LifecycleBar.vue";
import GraphPanel from "@/components/GraphPanel.vue";
import ActionFeed from "@/components/ActionFeed.vue";
import PlatformProgress from "@/components/PlatformProgress.vue";
import { useSimulationEvents } from "@/composables/useSimulationEvents";
import { cancelSim } from "@/api/simulation";
import { isTerminal } from "@/types/api";

interface Props {
  simId: string;
}

const props = defineProps<Props>();
const router = useRouter();
const simIdRef = toRef(props, "simId");

const {
  snapshot,
  state,
  progress,
  currentRound,
  totalRounds,
  twitterActions,
  redditActions,
  actions,
  agents,
  edges,
  error,
  isConnected,
} = useSimulationEvents(simIdRef);

const cancelling = ref(false);

const showReportCTA = computed(() => state.value === "COMPLETED");

async function handleCancel() {
  if (cancelling.value) return;
  if (!confirm("Cancel this simulation? Partial results will be preserved.")) return;
  cancelling.value = true;
  try {
    await cancelSim(props.simId);
  } catch (err) {
    console.warn("Cancel failed:", err);
  } finally {
    cancelling.value = false;
  }
}

function goToReport() {
  router.push({ name: "report", params: { simId: props.simId } });
}

// Auto-navigate to report on completion, with a slight delay so the
// final state change is visible.
watch(state, (newState) => {
  if (newState === "COMPLETED") {
    setTimeout(() => {
      if (state.value === "COMPLETED") {
        // Don't force-navigate; show the CTA instead.
      }
    }, 2000);
  }
});
</script>

<template>
  <div class="sim-run-view">
    <LifecycleBar :state="state" :progress="progress" :error="error" />

    <div class="view-grid">
      <div class="graph-pane">
        <GraphPanel :agents="agents" :edges="edges" />
        <div v-if="!isConnected" class="connection-status">
          <span class="status-dot" />
          Reconnecting...
        </div>
        <div v-if="isConnected" class="connection-status connected">
          <span class="status-dot live" />
          Live
        </div>
      </div>

      <div class="feed-pane">
        <ActionFeed :actions="actions" :agents="agents" />
      </div>
    </div>

    <PlatformProgress
      :twitter-actions="twitterActions"
      :reddit-actions="redditActions"
      :current-round="currentRound"
      :total-rounds="totalRounds"
      :twitter-running="snapshot?.twitter_running"
      :reddit-running="snapshot?.reddit_running"
      :twitter-completed="snapshot?.twitter_completed"
      :reddit-completed="snapshot?.reddit_completed"
    />

    <div v-if="error" class="banner error">
      <span class="banner-icon">⚠</span>
      <span class="banner-text">{{ error }}</span>
    </div>

    <div v-if="showReportCTA" class="banner success">
      <span class="banner-icon">✓</span>
      <span class="banner-text">Prediction complete. {{ agents.length }} agents produced {{ twitterActions + redditActions }} actions.</span>
      <button class="primary" @click="goToReport">View report</button>
    </div>

    <div v-if="state === 'SIMULATING'" class="action-bar">
      <button class="secondary" @click="handleCancel" :disabled="cancelling">
        {{ cancelling ? "Cancelling..." : "Cancel simulation" }}
      </button>
    </div>

    <div
      v-if="['FAILED', 'CANCELLED', 'INTERRUPTED'].includes(state)"
      class="action-bar"
    >
      <router-link to="/" class="secondary">Start a new prediction</router-link>
    </div>
  </div>
</template>

<style scoped>
.sim-run-view {
  display: grid;
  grid-template-rows: auto 1fr auto auto;
  height: 100%;
  overflow: hidden;
}

.view-grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  min-height: 0;
  overflow: hidden;
}

.graph-pane {
  position: relative;
  min-height: 0;
  overflow: hidden;
}

.feed-pane {
  min-height: 0;
  overflow: hidden;
}

.connection-status {
  position: absolute;
  top: var(--gap-md);
  right: var(--gap-md);
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: rgba(15, 22, 32, 0.8);
  backdrop-filter: blur(8px);
  border: 1px solid var(--border);
  border-radius: var(--radius-full);
  font-size: 11px;
  color: var(--fg-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  z-index: 5;
}

.connection-status.connected {
  color: var(--primary);
  border-color: rgba(34, 211, 238, 0.3);
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: var(--radius-full);
  background: var(--warning);
}

.status-dot.live {
  background: var(--primary);
  animation: pulse-primary 1.5s infinite;
}

.banner {
  display: flex;
  align-items: center;
  gap: var(--gap-md);
  padding: var(--gap-sm) var(--gap-lg);
  border-top: 1px solid var(--border);
  font-size: 14px;
}

.banner.error {
  background: rgba(239, 68, 68, 0.08);
  color: var(--danger);
}

.banner.success {
  background: rgba(34, 197, 94, 0.08);
  color: var(--success);
}

.banner-icon {
  font-size: 16px;
}

.banner-text {
  flex: 1;
}

.banner .primary {
  padding: 6px 16px;
  font-size: 13px;
  background: var(--primary);
  color: var(--bg);
  border-radius: var(--radius-md);
  font-weight: 600;
}

.action-bar {
  display: flex;
  justify-content: flex-end;
  padding: var(--gap-sm) var(--gap-lg);
  background: var(--bg-elevated);
  border-top: 1px solid var(--border);
}

.secondary {
  padding: 7px 16px;
  background: transparent;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-md);
  color: var(--fg);
  font-size: 13px;
  font-weight: 500;
  transition:
    border-color var(--duration-fast) var(--ease-out),
    background var(--duration-fast) var(--ease-out);
}

.secondary:hover:not(:disabled) {
  border-color: var(--primary);
  background: var(--primary-muted);
  color: var(--primary);
}

.secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
