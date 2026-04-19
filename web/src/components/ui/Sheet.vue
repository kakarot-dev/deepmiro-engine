<script setup lang="ts">
import {
  DialogRoot,
  DialogPortal,
  DialogOverlay,
  DialogContent,
  DialogTitle,
  DialogDescription,
  DialogClose,
} from "reka-ui";
import { X } from "lucide-vue-next";

interface Props {
  open: boolean;
  title?: string;
  description?: string;
  side?: "right" | "left" | "bottom" | "top";
  width?: string;
}
const props = withDefaults(defineProps<Props>(), { side: "right", width: "380px" });
const emit = defineEmits<{ "update:open": [value: boolean] }>();
</script>

<template>
  <DialogRoot :open="props.open" @update:open="(v) => emit('update:open', v)">
    <DialogPortal>
      <DialogOverlay class="overlay" />
      <DialogContent
        class="content"
        :class="`side-${side}`"
        :style="['left', 'right'].includes(side) ? { width } : undefined"
      >
        <DialogTitle v-if="title" class="title">{{ title }}</DialogTitle>
        <DialogDescription v-if="description" class="desc">{{ description }}</DialogDescription>
        <DialogClose class="close" aria-label="Close">
          <X :size="16" />
        </DialogClose>
        <slot />
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(5, 9, 13, 0.6);
  backdrop-filter: blur(4px);
  z-index: 100;
  animation: fade-in var(--duration-fast) var(--ease-out);
}
.content {
  position: fixed;
  background: var(--bg-elevated);
  border: 1px solid var(--border-strong);
  z-index: 101;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-lg);
  outline: none;
  overflow: hidden;
}
.content.side-right {
  top: 0;
  right: 0;
  height: 100vh;
  border-left: 1px solid var(--border-strong);
  animation: slide-in-right var(--duration-normal) var(--ease-out);
}
.content.side-left {
  top: 0;
  left: 0;
  height: 100vh;
  border-right: 1px solid var(--border-strong);
  animation: slide-in-left var(--duration-normal) var(--ease-out);
}
.title {
  padding: var(--gap-md) var(--gap-lg);
  font-size: 16px;
  font-weight: 600;
  color: var(--fg-strong);
  border-bottom: 1px solid var(--border);
}
.desc {
  padding: 0 var(--gap-lg) var(--gap-md);
  font-size: 13px;
  color: var(--fg-muted);
  border-bottom: 1px solid var(--border);
}
.close {
  position: absolute;
  top: 14px;
  right: 14px;
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  background: transparent;
  border: 1px solid transparent;
  color: var(--fg-muted);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}
.close:hover {
  border-color: var(--border-strong);
  color: var(--fg);
  background: var(--card);
}
@keyframes slide-in-right {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}
@keyframes slide-in-left {
  from { transform: translateX(-100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}
</style>
