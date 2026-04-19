<script setup lang="ts">
interface Props {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md";
  disabled?: boolean;
}
withDefaults(defineProps<Props>(), { variant: "secondary", size: "md", disabled: false });
</script>

<template>
  <button class="btn" :class="[variant, size]" :disabled="disabled">
    <slot />
  </button>
</template>

<style scoped>
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border-radius: var(--radius-md);
  font-weight: 500;
  letter-spacing: 0.01em;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all var(--duration-fast) var(--ease-out);
  white-space: nowrap;
}
.btn:disabled { opacity: 0.45; cursor: not-allowed; }
.btn.sm { height: 28px; padding: 0 10px; font-size: 12px; }
.btn.md { height: 34px; padding: 0 16px; font-size: 13px; }

.btn.primary {
  background: var(--primary);
  color: var(--bg);
  font-weight: 600;
}
.btn.primary:hover:not(:disabled) {
  background: var(--primary-hover);
  box-shadow: var(--glow-primary);
}

.btn.secondary {
  background: var(--card);
  color: var(--fg);
  border-color: var(--border-strong);
}
.btn.secondary:hover:not(:disabled) {
  background: var(--card-hover);
  border-color: var(--primary);
  color: var(--primary);
}

.btn.ghost {
  background: transparent;
  color: var(--fg-muted);
}
.btn.ghost:hover:not(:disabled) {
  background: var(--card);
  color: var(--fg);
}

.btn.danger {
  background: transparent;
  color: var(--danger);
  border-color: color-mix(in srgb, var(--danger) 40%, transparent);
}
.btn.danger:hover:not(:disabled) {
  background: color-mix(in srgb, var(--danger) 12%, transparent);
}
</style>
