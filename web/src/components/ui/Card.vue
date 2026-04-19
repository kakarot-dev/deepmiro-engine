<script setup lang="ts">
interface Props {
  hoverable?: boolean;
  padded?: boolean;
}
withDefaults(defineProps<Props>(), { hoverable: false, padded: true });
</script>

<template>
  <div class="card" :class="{ hoverable, padded }">
    <slot />
  </div>
</template>

<style scoped>
.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  transition:
    border-color var(--duration-fast) var(--ease-out),
    background var(--duration-fast) var(--ease-out),
    transform var(--duration-fast) var(--ease-out);
}
.card.padded { padding: var(--gap-md); }
.card.hoverable:hover {
  background: var(--card-hover);
  border-color: var(--border-strong);
  transform: translateY(-1px);
}
</style>
