<script setup lang="ts">
import { Network } from "lucide-vue-next";
import Card from "@/components/ui/Card.vue";
import Skeleton from "@/components/ui/Skeleton.vue";
import type { SimSnapshot } from "@/types/api";

interface Props {
  snapshot: SimSnapshot | null;
}
defineProps<Props>();
</script>

<template>
  <div class="phase-grid">
    <div class="left">
      <div class="hero">
        <div class="hero-icon">
          <Network :size="48" />
        </div>
        <div class="hero-text">
          <h2>Reading the scenario</h2>
          <p>
            Extracting people, organizations, and concepts from your prompt to
            build the knowledge graph that anchors every persona.
          </p>
        </div>
      </div>
      <div class="metric-row">
        <Card padded>
          <div class="metric">
            <span class="metric-label">Entities found</span>
            <span class="metric-value">{{ snapshot?.entities_count ?? "—" }}</span>
          </div>
        </Card>
        <Card padded>
          <div class="metric">
            <span class="metric-label">Progress</span>
            <span class="metric-value">{{ snapshot?.progress_percent ?? 0 }}%</span>
          </div>
        </Card>
      </div>
    </div>
    <div class="right">
      <div class="rail-title">
        <h3>Personas</h3>
        <span class="rail-sub">queued, will appear next</span>
      </div>
      <div class="skeleton-list">
        <Card v-for="i in 6" :key="i" padded>
          <div class="skel-row">
            <Skeleton width="40px" height="40px" circle />
            <div class="skel-text">
              <Skeleton width="60%" height="13px" />
              <Skeleton width="40%" height="11px" />
            </div>
          </div>
          <Skeleton width="100%" height="11px" />
          <Skeleton width="85%" height="11px" />
        </Card>
      </div>
    </div>
  </div>
</template>

<style scoped>
.phase-grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: var(--gap-lg);
  padding: var(--gap-lg);
  height: 100%;
  overflow: hidden;
  min-height: 0;
}
.left {
  display: flex;
  flex-direction: column;
  gap: var(--gap-lg);
  min-width: 0;
  overflow: hidden;
}
.hero {
  display: flex;
  align-items: flex-start;
  gap: var(--gap-md);
  flex: 1;
  min-height: 0;
  background:
    radial-gradient(ellipse at top left, rgba(34, 211, 238, 0.08), transparent 50%),
    var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--gap-xl);
  position: relative;
  overflow: hidden;
}
.hero::after {
  content: "";
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle, var(--border-subtle) 1px, transparent 1px);
  background-size: 28px 28px;
  opacity: 0.6;
  pointer-events: none;
}
.hero-icon {
  width: 72px;
  height: 72px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-lg);
  background: color-mix(in srgb, var(--primary) 14%, transparent);
  color: var(--primary);
  flex-shrink: 0;
  position: relative;
  z-index: 1;
}
.hero-text { position: relative; z-index: 1; }
.hero-text h2 {
  margin: 0 0 var(--gap-sm);
  font-size: 22px;
  color: var(--fg-strong);
}
.hero-text p {
  margin: 0;
  max-width: 520px;
  font-size: 14px;
  line-height: 1.6;
  color: var(--fg-muted);
}
.metric-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--gap-md);
}
.metric {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.metric-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--fg-subtle);
}
.metric-value {
  font-size: 28px;
  font-weight: 600;
  color: var(--fg-strong);
  font-variant-numeric: tabular-nums;
}
.right {
  display: flex;
  flex-direction: column;
  gap: var(--gap-md);
  min-width: 0;
  overflow: hidden;
}
.rail-title {
  display: flex;
  align-items: baseline;
  gap: var(--gap-sm);
}
.rail-title h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--fg-strong);
}
.rail-sub {
  font-size: 11px;
  color: var(--fg-subtle);
}
.skeleton-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--gap-sm);
  overflow-y: auto;
  padding-right: 2px;
}
.skeleton-list :deep(.card) {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.skel-row {
  display: flex;
  gap: var(--gap-sm);
  align-items: center;
}
.skel-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
</style>
