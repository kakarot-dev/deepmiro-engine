/**
 * activeSim — shared phase + counters for the simulation currently
 * being viewed. SimulationRunView writes to it; AppHeader reads from
 * it to render the phase chip.
 */
import { defineStore } from "pinia";
import { ref } from "vue";
import type { SimState } from "@/types/api";

export const useActiveSimStore = defineStore("activeSim", () => {
  const simId = ref<string | null>(null);
  const state = ref<SimState>("CREATED");
  const progress = ref(0);
  const currentRound = ref(0);
  const totalRounds = ref(0);
  const profilesCount = ref(0);
  const expectedProfiles = ref(0);
  const entitiesCount = ref(0);

  function reset() {
    simId.value = null;
    state.value = "CREATED";
    progress.value = 0;
    currentRound.value = 0;
    totalRounds.value = 0;
    profilesCount.value = 0;
    expectedProfiles.value = 0;
    entitiesCount.value = 0;
  }

  return {
    simId,
    state,
    progress,
    currentRound,
    totalRounds,
    profilesCount,
    expectedProfiles,
    entitiesCount,
    reset,
  };
});
