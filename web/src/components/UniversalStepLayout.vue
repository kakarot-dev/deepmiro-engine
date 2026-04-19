<script setup lang="ts">
/**
 * UniversalStepLayout — graph (left) + context rail (right). Used by
 * the Personas + Activity + Graph steps so the force graph stays the
 * primary canvas across the simulation lifecycle.
 *
 * Slots:
 *   default — graph content (left ~60%)
 *   rail    — context content (right ~40%)
 *   header  — optional thin strip above both columns
 */
</script>

<template>
  <div class="universal-layout">
    <slot name="header" />
    <div class="grid">
      <div class="graph-pane">
        <slot />
      </div>
      <div class="rail">
        <slot name="rail" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.universal-layout {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}
.grid {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(320px, 1fr);
  gap: 0;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
.graph-pane {
  position: relative;
  min-height: 0;
  min-width: 0;
  border-right: 1px solid var(--border);
  background: var(--bg);
}
.rail {
  display: flex;
  flex-direction: column;
  min-height: 0;
  min-width: 0;
  overflow: hidden;
  background: var(--panel);
}
@media (max-width: 900px) {
  .grid {
    grid-template-columns: 1fr;
    grid-template-rows: minmax(280px, 1fr) minmax(200px, 1fr);
  }
  .graph-pane { border-right: none; border-bottom: 1px solid var(--border); }
}
</style>
