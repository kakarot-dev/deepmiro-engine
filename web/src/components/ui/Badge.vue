<script setup lang="ts">
interface Props {
  variant?: "default" | "success" | "warning" | "danger" | "muted" | "outline";
  color?: string;
  pulse?: boolean;
}
withDefaults(defineProps<Props>(), { variant: "default", pulse: false });
</script>

<template>
  <span class="badge" :class="[variant, { pulse }]" :style="color ? { '--badge-color': color } : undefined">
    <span v-if="pulse" class="dot" />
    <slot />
  </span>
</template>

<style scoped>
.badge {
  --badge-color: var(--primary);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 22px;
  padding: 0 10px;
  border-radius: var(--radius-full);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.02em;
  white-space: nowrap;
  line-height: 1;
  background: color-mix(in srgb, var(--badge-color) 14%, transparent);
  color: var(--badge-color);
  border: 1px solid color-mix(in srgb, var(--badge-color) 30%, transparent);
}
.badge.success { --badge-color: var(--success); }
.badge.warning { --badge-color: var(--warning); }
.badge.danger { --badge-color: var(--danger); }
.badge.muted {
  background: var(--bg-elevated);
  color: var(--fg-muted);
  border-color: var(--border);
}
.badge.outline {
  background: transparent;
  border-color: var(--border-strong);
  color: var(--fg);
}
.dot {
  width: 6px;
  height: 6px;
  border-radius: var(--radius-full);
  background: var(--badge-color);
}
.pulse .dot {
  animation: badge-pulse 1.4s ease-in-out infinite;
}
@keyframes badge-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(0.7); }
}
</style>
