<script setup lang="ts">
import { computed } from "vue";
import { Heart, MessageCircle, Repeat2, ArrowBigUp, Quote, UserPlus, FileText } from "lucide-vue-next";
import Sheet from "@/components/ui/Sheet.vue";
import Avatar from "@/components/ui/Avatar.vue";
import Badge from "@/components/ui/Badge.vue";
import { personaColor } from "@/lib/colors";
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
const args = computed<any>(() => props.action?.action_args ?? {});
const kind = computed(() => props.action?.action_type ?? "");

const verb = computed(() => {
  switch (kind.value) {
    case "CREATE_POST": return props.action?.platform === "reddit" ? "posted" : "tweeted";
    case "CREATE_COMMENT": return "commented";
    case "QUOTE_POST": return "quoted a post";
    case "REPOST": case "RETWEET": return "reposted";
    case "LIKE_POST": case "UPVOTE_POST": case "UPVOTE": return "liked a post";
    case "FOLLOW": return "followed someone";
    case "DO_NOTHING": case "IDLE": return "did nothing this round";
    default: return kind.value.toLowerCase().replace(/_/g, " ");
  }
});
const actionIcon = computed(() => {
  switch (kind.value) {
    case "CREATE_POST": return FileText;
    case "CREATE_COMMENT": return MessageCircle;
    case "QUOTE_POST": return Quote;
    case "REPOST": case "RETWEET": return Repeat2;
    case "LIKE_POST": case "UPVOTE_POST": case "UPVOTE": return Heart;
    case "FOLLOW": return UserPlus;
    default: return ArrowBigUp;
  }
});

// Pull out whichever fields the action_args has for quoted/target content
const ownContent = computed<string>(() => args.value?.content || args.value?.quote_content || "");
const originalContent = computed<string>(() => args.value?.original_content || "");
const originalAuthorName = computed<string>(() => args.value?.original_author_name || "");
const targetPostId = computed<number | null>(() => {
  const id = args.value?.post_id ?? args.value?.quoted_id ?? args.value?.target_post_id;
  return typeof id === "number" ? id : null;
});

const targetUserId = computed<number | null>(() => {
  const id = args.value?.followee_id ?? args.value?.target_user_id;
  return typeof id === "number" ? id : null;
});
const targetUser = computed(() => {
  if (targetUserId.value == null) return null;
  return props.agents.find((a) => a.id === targetUserId.value) ?? null;
});
const originalAuthor = computed(() => {
  if (!originalAuthorName.value) return null;
  return props.agents.find((a) => a.name === originalAuthorName.value) ?? null;
});
</script>

<template>
  <Sheet
    :open="open"
    :width="'440px'"
    @update:open="(v) => emit('update:open', v)"
  >
    <div v-if="action" class="sheet-content">
      <!-- Header: actor + verb + verb icon -->
      <div class="head">
        <Avatar v-if="actor" :name="actor.name" :color="personaColor(actor.name)" :size="44" />
        <div class="head-text">
          <div class="line">
            <span class="actor">{{ actor?.name ?? action.agent_name ?? `Agent ${action.agent_id}` }}</span>
            <span class="verb-row">
              <component :is="actionIcon" :size="14" class="verb-icon" />
              <span class="verb">{{ verb }}</span>
              <template v-if="targetUser">
                → <strong>{{ targetUser.name }}</strong>
              </template>
            </span>
          </div>
          <div class="meta">
            <Badge variant="outline">{{ action.platform || "unknown" }}</Badge>
            <span>round {{ action.round }}</span>
            <span v-if="action.timestamp" class="dim">·
              {{ action.timestamp.replace("T", " ").slice(0, 16) }}
            </span>
          </div>
        </div>
      </div>

      <!-- Their own content (what they wrote for this action) -->
      <div v-if="ownContent" class="block">
        <div class="block-title">{{ verb }}</div>
        <p class="own">{{ ownContent }}</p>
      </div>

      <!-- Post they're responding to (for quote/comment/like/repost) -->
      <div v-if="originalContent" class="block">
        <div class="block-title quoted-title">
          ↳ <span v-if="originalAuthor" class="quoted-author">{{ originalAuthor.name }}</span>
          <span v-else-if="originalAuthorName" class="quoted-author">{{ originalAuthorName }}</span>
          <span v-else class="quoted-author dim">original post</span>
          <span class="dim"> wrote</span>
        </div>
        <p class="quoted">{{ originalContent }}</p>
      </div>

      <!-- Target post reference when we only have the id -->
      <div v-if="!originalContent && targetPostId != null" class="block">
        <div class="block-title quoted-title">
          ↳ post #{{ targetPostId }}
        </div>
        <p class="dim small">(content not in current view buffer)</p>
      </div>

      <!-- Failure detail -->
      <div v-if="!action.success" class="error">
        <Badge variant="danger">failed</Badge>
        <span>{{ action.result || "no detail recorded" }}</span>
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
.head-text { display: flex; flex-direction: column; gap: 8px; min-width: 0; flex: 1; }
.line {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}
.actor {
  font-size: 17px;
  font-weight: 700;
  color: var(--fg-strong);
}
.verb-row {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--fg-muted);
}
.verb-icon { color: var(--primary); }
.verb { font-weight: 500; }
.meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: var(--fg-muted);
}
.dim { color: var(--fg-subtle); }
.small { font-size: 12px; }

.block {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.block-title {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--fg-subtle);
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.quoted-title { text-transform: none; letter-spacing: 0.02em; font-size: 12px; }
.quoted-author { color: var(--fg-strong); font-weight: 600; }

.own {
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
  overflow-wrap: anywhere;
}
.quoted {
  margin: 0;
  padding: var(--gap-sm) var(--gap-md);
  background: var(--bg-elevated);
  border-left: 2px solid var(--border-strong);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  font-size: 13px;
  line-height: 1.55;
  color: var(--fg-muted);
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow-wrap: anywhere;
}

.error {
  display: flex;
  align-items: center;
  gap: var(--gap-sm);
  padding: var(--gap-sm) var(--gap-md);
  background: color-mix(in srgb, var(--danger) 10%, transparent);
  border: 1px solid color-mix(in srgb, var(--danger) 30%, transparent);
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: var(--danger);
}
</style>
