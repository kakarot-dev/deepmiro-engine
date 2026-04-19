<script setup lang="ts">
interface Props {
  width?: string;
  height?: string;
  radius?: string;
  circle?: boolean;
}
withDefaults(defineProps<Props>(), {
  width: "100%",
  height: "16px",
  radius: "var(--radius-sm)",
  circle: false,
});
</script>

<template>
  <span
    class="skeleton"
    :style="{
      width,
      height,
      borderRadius: circle ? '50%' : radius,
    }"
  />
</template>

<style scoped>
.skeleton {
  display: block;
  background: linear-gradient(
    90deg,
    var(--card) 0%,
    var(--card-hover) 50%,
    var(--card) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.6s linear infinite;
}
</style>
