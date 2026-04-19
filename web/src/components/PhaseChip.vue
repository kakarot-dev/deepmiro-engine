<script setup lang="ts">
import { computed } from "vue";
import type { SimState } from "@/types/api";

interface Props {
  state: SimState;
  progress?: number;
  currentRound?: number;
  totalRounds?: number;
  profilesCount?: number;
  expectedProfiles?: number;
  entitiesCount?: number;
}
const props = defineProps<Props>();

const phase = computed(() => {
  switch (props.state) {
    case "CREATED":
    case "GRAPH_BUILDING":
      return {
        label: "Building graph",
        detail: props.entitiesCount ? `${props.entitiesCount} entities` : `${props.progress ?? 0}%`,
        color: "var(--info)",
        pulse: true,
      };
    case "GENERATING_PROFILES":
      return {
        label: "Generating personas",
        detail:
          props.expectedProfiles && props.expectedProfiles > 0
            ? `${props.profilesCount ?? 0}/${props.expectedProfiles}`
            : `${props.profilesCount ?? 0}`,
        color: "var(--arch-platform)",
        pulse: true,
      };
    case "READY":
      return { label: "Ready", detail: "starting…", color: "var(--primary)", pulse: true };
    case "SIMULATING":
      return {
        label: "Simulating",
        detail:
          props.totalRounds && props.totalRounds > 0
            ? `round ${props.currentRound ?? 0}/${props.totalRounds}`
            : `round ${props.currentRound ?? 0}`,
        color: "var(--primary)",
        pulse: true,
      };
    case "COMPLETED":
      return { label: "Complete", detail: "", color: "var(--success)", pulse: false };
    case "FAILED":
      return { label: "Failed", detail: "", color: "var(--danger)", pulse: false };
    case "CANCELLED":
      return { label: "Cancelled", detail: "", color: "var(--fg-muted)", pulse: false };
    case "INTERRUPTED":
      return { label: "Interrupted", detail: "", color: "var(--warning)", pulse: false };
    default:
      return { label: String(props.state), detail: "", color: "var(--fg-muted)", pulse: false };
  }
});
</script>

<template>
  <span class="chip" :style="{ '--chip-color': phase.color }">
    <span class="dot" :class="{ pulsing: phase.pulse }" />
    <span class="label">{{ phase.label }}</span>
    <span v-if="phase.detail" class="detail">{{ phase.detail }}</span>
  </span>
</template>

<style scoped>
.chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 28px;
  padding: 0 12px;
  background: color-mix(in srgb, var(--chip-color) 12%, transparent);
  border: 1px solid color-mix(in srgb, var(--chip-color) 35%, transparent);
  border-radius: var(--radius-full);
  color: var(--chip-color);
  font-size: 12px;
  font-weight: 500;
}
.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--chip-color);
}
.dot.pulsing {
  animation: chip-pulse 1.6s ease-in-out infinite;
  box-shadow: 0 0 0 0 var(--chip-color);
}
.label {
  color: var(--chip-color);
  font-weight: 600;
}
.detail {
  color: var(--fg-muted);
  font-variant-numeric: tabular-nums;
}
@keyframes chip-pulse {
  0% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--chip-color) 60%, transparent); }
  70% { box-shadow: 0 0 0 6px color-mix(in srgb, var(--chip-color) 0%, transparent); }
  100% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--chip-color) 0%, transparent); }
}
</style>
