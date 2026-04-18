<script setup lang="ts">
import AppHeader from "@/components/AppHeader.vue";
</script>

<template>
  <div class="app-shell">
    <AppHeader />
    <main class="app-main">
      <router-view v-slot="{ Component }">
        <transition name="view-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  display: grid;
  grid-template-rows: auto 1fr;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

.app-main {
  overflow: hidden;
  position: relative;
}

.view-fade-enter-active,
.view-fade-leave-active {
  transition: opacity var(--duration-fast) var(--ease-out);
}

.view-fade-enter-from,
.view-fade-leave-to {
  opacity: 0;
}
</style>
