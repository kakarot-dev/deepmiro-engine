<script setup lang="ts">
import { computed } from "vue";
interface Props {
  name: string;
  color?: string;
  size?: number;
}
const props = withDefaults(defineProps<Props>(), { size: 36 });
const initials = computed(() => {
  const parts = props.name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
});
</script>

<template>
  <div
    class="avatar"
    :style="{
      width: size + 'px',
      height: size + 'px',
      background: color ? `linear-gradient(135deg, ${color}, color-mix(in srgb, ${color} 60%, #000))` : undefined,
      fontSize: Math.max(10, Math.round(size * 0.36)) + 'px',
    }"
  >
    {{ initials }}
  </div>
</template>

<style scoped>
.avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-full);
  background: linear-gradient(135deg, var(--arch-person), #475569);
  color: white;
  font-weight: 700;
  letter-spacing: 0.02em;
  flex-shrink: 0;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.1);
}
</style>
