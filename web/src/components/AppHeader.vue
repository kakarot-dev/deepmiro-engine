<script setup lang="ts">
import { useRoute } from "vue-router";
import { computed } from "vue";

const route = useRoute();
const activeRoute = computed(() => route.name);
</script>

<template>
  <header class="app-header">
    <router-link to="/" class="brand">
      <svg class="brand-mark" viewBox="0 0 32 32" width="24" height="24" aria-hidden="true">
        <circle cx="16" cy="16" r="14" fill="none" stroke="var(--primary)" stroke-width="2.5" />
        <circle cx="16" cy="16" r="6" fill="var(--primary)" opacity="0.8" />
        <circle cx="16" cy="8"  r="2.5" fill="var(--primary-hover)" />
        <circle cx="24" cy="20" r="2.5" fill="var(--primary-hover)" />
        <circle cx="8"  cy="20" r="2.5" fill="var(--primary-hover)" />
      </svg>
      <span class="brand-text">DeepMiro</span>
    </router-link>

    <nav class="app-nav">
      <router-link
        to="/"
        class="nav-link"
        :class="{ active: activeRoute === 'setup' }"
      >
        New prediction
      </router-link>
      <router-link
        to="/history"
        class="nav-link"
        :class="{ active: activeRoute === 'history' }"
      >
        History
      </router-link>
    </nav>
  </header>
</template>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--gap-lg);
  height: 56px;
  border-bottom: 1px solid var(--border);
  background: var(--bg-elevated);
  z-index: 10;
  position: relative;
}

.brand {
  display: flex;
  align-items: center;
  gap: var(--gap-sm);
  color: var(--fg-strong);
  font-weight: 600;
  letter-spacing: 0.02em;
}

.brand:hover {
  color: var(--fg-strong);
}

.brand-mark {
  flex-shrink: 0;
}

.brand-text {
  font-size: 16px;
}

.app-nav {
  display: flex;
  align-items: center;
  gap: var(--gap-xs);
}

.nav-link {
  padding: 6px 14px;
  border-radius: var(--radius-full);
  color: var(--fg-muted);
  font-size: 13px;
  font-weight: 500;
  transition:
    color var(--duration-fast) var(--ease-out),
    background var(--duration-fast) var(--ease-out);
}

.nav-link:hover {
  color: var(--fg);
  background: var(--card);
}

.nav-link.active {
  color: var(--primary);
  background: var(--primary-muted);
}
</style>
