<script setup lang="ts">
import { computed, onBeforeUnmount, ref, toRef, watch } from "vue";
import { XCircle } from "lucide-vue-next";
import GraphBuildingView from "@/components/phases/GraphBuildingView.vue";
import ProfileGenerationView from "@/components/phases/ProfileGenerationView.vue";
import SimulatingView from "@/components/phases/SimulatingView.vue";
import CompletedView from "@/components/phases/CompletedView.vue";
import TerminalView from "@/components/phases/TerminalView.vue";
import Button from "@/components/ui/Button.vue";
import { useSimulationEvents } from "@/composables/useSimulationEvents";
import { cancelSim } from "@/api/simulation";
import { useActiveSimStore } from "@/stores/activeSim";

interface Props {
  simId: string;
}
const props = defineProps<Props>();
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
  profiles,
  error,
} = useSimulationEvents(simIdRef);

// Push reactive sim state into the global active-sim store so the
// AppHeader can render the phase chip.
const activeSim = useActiveSimStore();
watch(
  () => ({
    simId: props.simId,
    state: state.value,
    progress: progress.value,
    currentRound: currentRound.value,
    totalRounds: totalRounds.value,
    profilesCount: profiles.value.length,
    expectedProfiles: snapshot.value?.entities_count ?? 0,
    entitiesCount: snapshot.value?.entities_count ?? 0,
  }),
  (v) => {
    activeSim.simId = v.simId;
    activeSim.state = v.state;
    activeSim.progress = v.progress;
    activeSim.currentRound = v.currentRound;
    activeSim.totalRounds = v.totalRounds;
    activeSim.profilesCount = v.profilesCount;
    activeSim.expectedProfiles = v.expectedProfiles;
    activeSim.entitiesCount = v.entitiesCount;
  },
  { immediate: true, deep: false },
);
onBeforeUnmount(() => activeSim.reset());

const cancelling = ref(false);
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

const isTerminal = computed(() =>
  ["FAILED", "CANCELLED", "INTERRUPTED"].includes(state.value),
);
</script>

<template>
  <div class="run-view">
    <component
      :is="
        state === 'CREATED' || state === 'GRAPH_BUILDING'
          ? GraphBuildingView
          : state === 'GENERATING_PROFILES' || state === 'READY'
            ? ProfileGenerationView
            : state === 'SIMULATING'
              ? SimulatingView
              : state === 'COMPLETED'
                ? CompletedView
                : TerminalView
      "
      :sim-id="simId"
      :snapshot="snapshot"
      :state="state"
      :error="error"
      :actions="actions"
      :agents="agents"
      :edges="edges"
      :profiles="profiles"
      :twitter-count="twitterActions"
      :reddit-count="redditActions"
      :expected-count="snapshot?.entities_count ?? 0"
    />

    <div v-if="state === 'SIMULATING'" class="floating-actions">
      <Button variant="danger" size="sm" :disabled="cancelling" @click="handleCancel">
        <XCircle :size="14" />
        {{ cancelling ? "Cancelling…" : "Cancel" }}
      </Button>
    </div>

    <div v-if="error && !isTerminal && state !== 'COMPLETED'" class="error-toast">
      <span>{{ error }}</span>
    </div>
  </div>
</template>

<style scoped>
.run-view {
  position: relative;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}
.floating-actions {
  position: absolute;
  top: var(--gap-md);
  right: var(--gap-lg);
  z-index: 8;
  display: flex;
  gap: var(--gap-sm);
}
.error-toast {
  position: absolute;
  bottom: var(--gap-md);
  left: 50%;
  transform: translateX(-50%);
  padding: 10px 16px;
  background: color-mix(in srgb, var(--danger) 20%, var(--bg-elevated));
  border: 1px solid color-mix(in srgb, var(--danger) 50%, transparent);
  border-radius: var(--radius-md);
  color: var(--danger);
  font-size: 12px;
  z-index: 9;
  box-shadow: var(--shadow-md);
}
</style>
