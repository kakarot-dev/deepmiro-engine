<script setup lang="ts">
import { computed } from "vue";
import { resolveArchetype } from "@/lib/archetypes";

interface Props {
  name: string;
  archetype?: string;
  compact?: boolean;
}

const props = defineProps<Props>();

const archInfo = computed(() => resolveArchetype(props.archetype));
</script>

<template>
  <span
    class="agent-chip"
    :class="{ compact: props.compact }"
    :style="{
      borderColor: archInfo.color,
      color: archInfo.color,
    }"
  >
    <span class="agent-chip-dot" :style="{ background: archInfo.color }" />
    <span class="agent-chip-name">{{ name }}</span>
  </span>
</template>

<style scoped>
.agent-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  border-radius: var(--radius-full);
  background: transparent;
  border: 1px solid;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.2;
  white-space: nowrap;
  vertical-align: baseline;
}

.agent-chip.compact {
  padding: 2px 8px;
  font-size: 11px;
}

.agent-chip-dot {
  width: 7px;
  height: 7px;
  border-radius: var(--radius-full);
  flex-shrink: 0;
}

.agent-chip-name {
  color: var(--fg-strong);
}
</style>
