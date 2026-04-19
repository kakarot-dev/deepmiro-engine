<script setup lang="ts">
import { computed } from "vue";
import { storeToRefs } from "pinia";
import { useRoute } from "vue-router";
import PhaseChip from "@/components/PhaseChip.vue";
import { useAuth } from "@/composables/useAuth";
import { useActiveSimStore } from "@/stores/activeSim";

const route = useRoute();
const { mode, userName, userEmail, signInUrl } = useAuth();
const activeSim = useActiveSimStore();
const {
  simId,
  state,
  progress,
  currentRound,
  totalRounds,
  profilesCount,
  expectedProfiles,
  entitiesCount,
} = storeToRefs(activeSim);

const isAuthenticated = computed(
  () => mode.value === "session" || mode.value === "api_key",
);
const showPhaseChip = computed(
  () => simId.value && route.name === "sim" && simId.value === route.params.simId,
);
</script>

<template>
  <header class="app-header">
    <router-link to="/" class="brand">
      <img src="/logo.png" alt="DeepMiro" class="brand-logo" />
    </router-link>

    <div class="phase">
      <PhaseChip
        v-if="showPhaseChip"
        :state="state"
        :progress="progress"
        :current-round="currentRound"
        :total-rounds="totalRounds"
        :profiles-count="profilesCount"
        :expected-profiles="expectedProfiles"
        :entities-count="entitiesCount"
      />
    </div>

    <nav class="app-nav">
      <router-link v-if="isAuthenticated" to="/history" class="nav-link">
        History
      </router-link>
      <div v-if="mode === 'session'" class="account-chip">
        <span class="account-dot" />
        {{ userName || userEmail || "Signed in" }}
      </div>
      <a v-else-if="mode === 'unauthenticated'" :href="signInUrl()" class="sign-in">
        Sign in
      </a>
    </nav>
  </header>
</template>

<style scoped>
.app-header {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: var(--gap-lg);
  padding: 0 var(--gap-lg);
  height: 56px;
  border-bottom: 1px solid var(--border);
  background: var(--bg-elevated);
  z-index: 10;
  position: relative;
}
.brand { display: inline-flex; align-items: center; }
.brand-logo {
  height: 26px;
  width: auto;
  display: block;
}
.phase {
  display: flex;
  align-items: center;
  justify-content: center;
}
.app-nav {
  display: flex;
  align-items: center;
  gap: var(--gap-sm);
  margin-left: auto;
}
.nav-link {
  padding: 6px 14px;
  border-radius: var(--radius-full);
  color: var(--fg-muted);
  font-size: 13px;
  font-weight: 500;
  transition: all var(--duration-fast) var(--ease-out);
}
.nav-link:hover {
  color: var(--fg);
  background: var(--card);
}
.account-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-full);
  font-size: 12px;
  color: var(--fg-muted);
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.account-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--success);
}
.sign-in {
  padding: 6px 14px;
  background: var(--primary);
  color: var(--bg);
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 600;
  transition: background var(--duration-fast) var(--ease-out);
}
.sign-in:hover {
  background: var(--primary-hover);
  color: var(--bg);
}
</style>
