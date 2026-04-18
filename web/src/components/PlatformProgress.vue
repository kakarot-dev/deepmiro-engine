<script setup lang="ts">
import { computed } from "vue";

interface Props {
  twitterActions: number;
  redditActions: number;
  currentRound: number;
  totalRounds: number;
  twitterRunning?: boolean;
  redditRunning?: boolean;
  twitterCompleted?: boolean;
  redditCompleted?: boolean;
}

const props = defineProps<Props>();

const totalActions = computed(() => props.twitterActions + props.redditActions);

const progressPct = computed(() => {
  if (props.totalRounds <= 0) return 0;
  return Math.min(100, Math.round((props.currentRound / props.totalRounds) * 100));
});
</script>

<template>
  <div class="platform-progress">
    <div class="stat-group">
      <div class="stat-label">Round</div>
      <div class="stat-value">
        <span class="stat-num">{{ currentRound }}</span>
        <span class="stat-divider">/</span>
        <span class="stat-total">{{ totalRounds || "?" }}</span>
      </div>
    </div>

    <div class="round-bar">
      <div class="round-bar-fill" :style="{ width: progressPct + '%' }" />
    </div>

    <div class="platform-stats">
      <div
        v-if="twitterActions > 0 || twitterRunning || twitterCompleted"
        class="platform-stat twitter"
      >
        <span class="platform-label">
          <span class="platform-dot" :class="{ active: twitterRunning, done: twitterCompleted }" />
          Twitter
        </span>
        <span class="platform-value">{{ twitterActions.toLocaleString() }}</span>
      </div>
      <div
        v-if="redditActions > 0 || redditRunning || redditCompleted"
        class="platform-stat reddit"
      >
        <span class="platform-label">
          <span class="platform-dot" :class="{ active: redditRunning, done: redditCompleted }" />
          Reddit
        </span>
        <span class="platform-value">{{ redditActions.toLocaleString() }}</span>
      </div>
      <div class="platform-stat total">
        <span class="platform-label">Total actions</span>
        <span class="platform-value">{{ totalActions.toLocaleString() }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.platform-progress {
  display: flex;
  align-items: center;
  gap: var(--gap-lg);
  padding: var(--gap-sm) var(--gap-lg);
  background: var(--bg-elevated);
  border-top: 1px solid var(--border);
  flex-shrink: 0;
}

.stat-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 100px;
}

.stat-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--fg-subtle);
}

.stat-value {
  display: flex;
  align-items: baseline;
  gap: 4px;
  color: var(--fg-strong);
  font-size: 18px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.stat-num {
  color: var(--primary);
}

.stat-divider,
.stat-total {
  color: var(--fg-muted);
  font-size: 14px;
  font-weight: 500;
}

.round-bar {
  flex: 1;
  height: 6px;
  background: var(--border);
  border-radius: var(--radius-full);
  overflow: hidden;
  max-width: 400px;
}

.round-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary), var(--primary-hover));
  border-radius: var(--radius-full);
  transition: width var(--duration-slow) var(--ease-out);
}

.platform-stats {
  display: flex;
  gap: var(--gap-md);
}

.platform-stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 80px;
}

.platform-label {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--fg-subtle);
}

.platform-value {
  font-size: 15px;
  font-weight: 600;
  color: var(--fg-strong);
  font-variant-numeric: tabular-nums;
}

.platform-dot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  background: var(--fg-subtle);
}

.platform-dot.active {
  background: var(--primary);
  animation: pulse-primary 1.8s infinite;
}

.platform-dot.done {
  background: var(--success);
}
</style>
