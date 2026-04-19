<script setup lang="ts">
import { computed } from "vue";
import Sheet from "@/components/ui/Sheet.vue";
import Avatar from "@/components/ui/Avatar.vue";
import Badge from "@/components/ui/Badge.vue";
import { resolveArchetype } from "@/lib/archetypes";
import type { AgentActionRecord, GraphNode } from "@/types/api";

interface Props {
  open: boolean;
  action: AgentActionRecord | null;
  agents: GraphNode[];
}
const props = defineProps<Props>();
const emit = defineEmits<{ "update:open": [value: boolean] }>();

const actor = computed(() => {
  if (!props.action) return null;
  return props.agents.find((a) => a.id === props.action!.agent_id) ?? null;
});
const archetype = computed(() =>
  actor.value ? resolveArchetype(actor.value.archetype) : { label: "", color: "#94a3b8" },
);
const verb = computed(() => {
  switch (props.action?.action_type) {
    case "CREATE_POST": return "posted";
    case "CREATE_COMMENT": return "commented";
    case "QUOTE_POST": return "quoted a post";
    case "REPOST": case "RETWEET": return "reposted";
    case "LIKE_POST": case "UPVOTE_POST": case "UPVOTE": return "liked a post";
    case "FOLLOW": return "followed someone";
    default: return props.action?.action_type.toLowerCase().replace(/_/g, " ") ?? "did something";
  }
});
const content = computed(() => (props.action?.action_args as any)?.content as string | undefined);
const otherArgs = computed(() => {
  const args = (props.action?.action_args as any) ?? {};
  return Object.entries(args).filter(
    ([k]) => k !== "content" && args[k] != null && args[k] !== "",
  );
});
</script>

<template>
  <Sheet
    :open="open"
    :width="'420px'"
    @update:open="(v) => emit('update:open', v)"
  >
    <div v-if="action" class="sheet-content">
      <div class="head">
        <Avatar v-if="actor" :name="actor.name" :color="archetype.color" :size="48" />
        <div class="head-text">
          <div class="line">
            <span class="name">{{ actor?.name ?? action.agent_name ?? `Agent ${action.agent_id}` }}</span>
            <span class="verb">{{ verb }}</span>
          </div>
          <div class="meta">
            <Badge variant="outline">{{ action.platform || "unknown" }}</Badge>
            <span>round {{ action.round }}</span>
            <span class="dim">· {{ action.timestamp?.replace("T", " ").slice(0, 16) }}</span>
          </div>
        </div>
      </div>

      <div v-if="content" class="content-block">
        <div class="section-title">Content</div>
        <p>{{ content }}</p>
      </div>

      <div v-if="otherArgs.length" class="section">
        <div class="section-title">Action arguments</div>
        <dl class="args">
          <template v-for="[k, v] in otherArgs" :key="k">
            <dt>{{ k }}</dt>
            <dd>{{ String(v) }}</dd>
          </template>
        </dl>
      </div>

      <div v-if="!action.success" class="section error">
        <div class="section-title">Failure</div>
        <p>{{ action.result || "no detail recorded" }}</p>
      </div>
    </div>
  </Sheet>
</template>

<style scoped>
.sheet-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--gap-lg);
  display: flex;
  flex-direction: column;
  gap: var(--gap-md);
}
.head {
  display: flex;
  gap: var(--gap-md);
  align-items: flex-start;
  padding-right: 36px;
}
.head-text { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.line { display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px; }
.name { font-size: 16px; font-weight: 700; color: var(--fg-strong); }
.verb { color: var(--fg-muted); font-size: 13px; font-style: italic; }
.meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: var(--fg-muted);
}
.dim { color: var(--fg-subtle); }
.content-block {
  display: flex;
  flex-direction: column;
  gap: var(--gap-sm);
}
.content-block p {
  margin: 0;
  padding: var(--gap-md);
  background: var(--card);
  border-left: 2px solid var(--primary);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  font-size: 14px;
  line-height: 1.55;
  color: var(--fg);
  white-space: pre-wrap;
  word-wrap: break-word;
}
.section { display: flex; flex-direction: column; gap: var(--gap-sm); }
.section-title {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--fg-subtle);
}
.args {
  margin: 0;
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: 6px var(--gap-md);
}
.args dt {
  font-family: var(--font-mono, ui-monospace, monospace);
  font-size: 11px;
  color: var(--fg-subtle);
  text-transform: lowercase;
}
.args dd {
  margin: 0;
  font-size: 12px;
  color: var(--fg);
  font-family: var(--font-mono, ui-monospace, monospace);
  word-break: break-all;
}
.error { color: var(--danger); }
.error p {
  margin: 0;
  padding: var(--gap-sm) var(--gap-md);
  background: color-mix(in srgb, var(--danger) 10%, transparent);
  border: 1px solid color-mix(in srgb, var(--danger) 30%, transparent);
  border-radius: var(--radius-sm);
  font-size: 12px;
}
</style>
