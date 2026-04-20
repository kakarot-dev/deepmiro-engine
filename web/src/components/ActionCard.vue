<script setup lang="ts">
import { computed } from "vue";
import { Heart, MessageCircle, Repeat2, ArrowUpFromLine, ArrowBigUp, Quote } from "lucide-vue-next";
import Avatar from "@/components/ui/Avatar.vue";
import Badge from "@/components/ui/Badge.vue";
import { resolveArchetype } from "@/lib/archetypes";
import { personaColor } from "@/lib/colors";
import type { AgentActionRecord, GraphNode } from "@/types/api";

interface Props {
  action: AgentActionRecord;
  agent?: GraphNode;
}
const props = defineProps<Props>();

const platform = computed(() => props.action.platform || "twitter");
const archetype = computed(() => resolveArchetype(props.agent?.archetype ?? ""));
const name = computed(() => props.agent?.name ?? props.action.agent_name ?? `Agent ${props.action.agent_id}`);
const handle = computed(() =>
  name.value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_|_$/g, "")
    .slice(0, 22) || "agent",
);
const content = computed(() => props.action.action_args?.content ?? "");

const actionIcon = computed(() => {
  switch (props.action.action_type) {
    case "LIKE_POST":
      return Heart;
    case "CREATE_COMMENT":
      return MessageCircle;
    case "REPOST":
    case "RETWEET":
      return Repeat2;
    case "QUOTE_POST":
      return Quote;
    case "UPVOTE_POST":
    case "UPVOTE":
      return ArrowBigUp;
    case "FOLLOW":
      return ArrowUpFromLine;
    default:
      return null;
  }
});
const actionLabel = computed(() => {
  switch (props.action.action_type) {
    case "CREATE_POST":
      return platform.value === "reddit" ? "posted" : "tweeted";
    case "CREATE_COMMENT":
      return "commented";
    case "REPOST":
    case "RETWEET":
      return "reposted";
    case "QUOTE_POST":
      return "quoted";
    case "LIKE_POST":
      return "liked";
    case "UPVOTE_POST":
    case "UPVOTE":
      return "upvoted";
    case "FOLLOW":
      return "followed";
    default:
      return props.action.action_type.toLowerCase().replace(/_/g, " ");
  }
});
const isContentAction = computed(() =>
  ["CREATE_POST", "CREATE_COMMENT", "QUOTE_POST"].includes(props.action.action_type),
);

function timeAgo(): string {
  if (!props.action.timestamp) return "";
  try {
    const t = new Date(props.action.timestamp).getTime();
    const diff = (Date.now() - t) / 1000;
    if (diff < 60) return `${Math.round(diff)}s`;
    if (diff < 3600) return `${Math.round(diff / 60)}m`;
    return `${Math.round(diff / 3600)}h`;
  } catch {
    return "";
  }
}
</script>

<template>
  <div class="action-card" :class="platform">
    <Avatar :name="name" :color="personaColor(name)" :size="40" />
    <div class="body">
      <div class="header">
        <span class="name">{{ name }}</span>
        <span class="handle">{{ platform === "reddit" ? "u/" : "@" }}{{ handle }}</span>
        <span class="dot">·</span>
        <span class="time">{{ timeAgo() }}</span>
        <span class="dot">·</span>
        <span class="round">r{{ action.round }}</span>
      </div>
      <div v-if="isContentAction && content" class="content">{{ content }}</div>
      <div v-else class="meta-action">
        <component v-if="actionIcon" :is="actionIcon" :size="14" class="meta-icon" />
        <span>{{ actionLabel }}</span>
      </div>
      <div v-if="!action.success" class="failure">
        <Badge variant="danger">failed</Badge>
        <span>{{ action.result || "no detail" }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.action-card {
  display: flex;
  gap: var(--gap-sm);
  padding: var(--gap-md);
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  transition: border-color var(--duration-fast) var(--ease-out);
  position: relative;
  overflow: hidden;
}
.action-card::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  width: 2px;
  background: transparent;
  transition: background var(--duration-fast) var(--ease-out);
}
.action-card.twitter::before { background: linear-gradient(180deg, #1da1f2, transparent); }
.action-card.reddit::before { background: linear-gradient(180deg, #ff4500, transparent); }
.action-card:hover { border-color: var(--border-strong); }
.body { flex: 1; min-width: 0; }
.header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--fg-muted);
  flex-wrap: wrap;
}
.name {
  color: var(--fg-strong);
  font-weight: 600;
}
.handle, .time, .round { color: var(--fg-muted); }
.dot { color: var(--fg-subtle); }
.content {
  margin-top: 6px;
  font-size: 14px;
  line-height: 1.5;
  color: var(--fg);
  white-space: pre-wrap;
  word-wrap: break-word;
}
.meta-action {
  margin-top: 6px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--fg-muted);
  font-style: italic;
}
.meta-icon { color: var(--fg-subtle); }
.failure {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: var(--gap-sm);
  font-size: 11px;
  color: var(--danger);
}
</style>
