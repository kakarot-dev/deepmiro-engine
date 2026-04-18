<script setup lang="ts">
import { computed } from "vue";
import type { SimState } from "@/types/api";
import { isTerminal } from "@/types/api";

interface Props {
  state: SimState;
  progress: number;
  error?: string | null;
}

const props = defineProps<Props>();

interface Phase {
  key: SimState;
  label: string;
}

const phases: Phase[] = [
  { key: "CREATED", label: "Initializing" },
  { key: "GRAPH_BUILDING", label: "Building graph" },
  { key: "GENERATING_PROFILES", label: "Generating personas" },
  { key: "SIMULATING", label: "Simulating" },
  { key: "COMPLETED", label: "Complete" },
];

const currentIndex = computed(() => {
  const idx = phases.findIndex((p) => p.key === props.state);
  if (idx >= 0) return idx;
  // Non-happy-path terminal states get mapped to the last known position.
  if (["FAILED", "CANCELLED", "INTERRUPTED"].includes(props.state)) {
    return phases.length - 1;
  }
  return 0;
});

const isFailed = computed(() =>
  ["FAILED", "CANCELLED", "INTERRUPTED"].includes(props.state),
);

const isDone = computed(() => props.state === "COMPLETED");

function isActive(index: number): boolean {
  return index === currentIndex.value && !isTerminal(props.state);
}

function isComplete(index: number): boolean {
  return index < currentIndex.value || isDone.value;
}
</script>

<template>
  <div class="lifecycle-bar" :class="{ failed: isFailed, done: isDone }">
    <template v-for="(phase, idx) in phases" :key="phase.key">
      <div
        class="phase"
        :class="{
          active: isActive(idx),
          complete: isComplete(idx),
          failed: isFailed && idx === currentIndex,
        }"
      >
        <div class="phase-dot">
          <span v-if="isComplete(idx) && !isFailed">✓</span>
          <span v-else-if="isFailed && idx === currentIndex">!</span>
          <span v-else class="phase-pulse" />
        </div>
        <div class="phase-label">{{ phase.label }}</div>
      </div>
      <div
        v-if="idx < phases.length - 1"
        class="phase-connector"
        :class="{ complete: isComplete(idx + 1) }"
      >
        <div class="connector-fill" :style="{ width: isActive(idx) ? `${progress}%` : isComplete(idx + 1) ? '100%' : '0%' }" />
      </div>
    </template>
  </div>
</template>

<style scoped>
.lifecycle-bar {
  display: flex;
  align-items: center;
  padding: var(--gap-md) var(--gap-lg);
  background: var(--card);
  border-bottom: 1px solid var(--border);
  gap: 0;
  overflow-x: auto;
}

.phase {
  display: flex;
  align-items: center;
  gap: var(--gap-sm);
  flex-shrink: 0;
  color: var(--fg-subtle);
  transition: color var(--duration-normal) var(--ease-out);
}

.phase.active {
  color: var(--primary);
}

.phase.complete {
  color: var(--success);
}

.phase.failed {
  color: var(--danger);
}

.phase-dot {
  width: 22px;
  height: 22px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  background: var(--bg);
  border: 2px solid currentColor;
  position: relative;
  transition: border-color var(--duration-normal) var(--ease-out);
}

.phase.active .phase-dot {
  animation: pulse-primary 1.6s infinite;
}

.phase-pulse {
  width: 6px;
  height: 6px;
  border-radius: var(--radius-full);
  background: currentColor;
}

.phase-label {
  font-size: 13px;
  font-weight: 500;
  letter-spacing: 0.01em;
  white-space: nowrap;
}

.phase-connector {
  flex: 1;
  min-width: 32px;
  height: 2px;
  background: var(--border);
  margin: 0 var(--gap-sm);
  position: relative;
  overflow: hidden;
  border-radius: 1px;
}

.connector-fill {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    90deg,
    var(--primary),
    var(--primary-hover)
  );
  transition: width var(--duration-slow) var(--ease-out);
}

.phase-connector.complete .connector-fill {
  background: var(--success);
}
</style>
