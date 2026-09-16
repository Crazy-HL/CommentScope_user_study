<template>
  <header class="progress-header">
    <div>
      <strong>CommentScope 阅读实验</strong>
      <span v-if="participantId" class="participant">{{ participantId }}</span>
    </div>
    <div v-if="articleOrder" class="progress-text">文章 {{ articleOrder }} / 4 · {{ stageTitle }}</div>
    <div v-else class="progress-text">{{ stageTitle }}</div>
  </header>
</template>

<script setup>
import { computed } from "vue";
import { STAGE_TITLES } from "../../experiment/experimentConfig";

const props = defineProps({
  participantId: { type: String, default: "" },
  articleOrder: { type: Number, default: 0 },
  stage: { type: String, default: "instruction" }
});
const stageTitle = computed(() => STAGE_TITLES[props.stage] || "实验进行中");
</script>

<style scoped>
.progress-header { position: sticky; top: 0; z-index: 20; display: flex; justify-content: space-between; gap: 16px; align-items: center; padding: 14px 24px; color: #17324d; background: rgba(255,255,255,.96); border-bottom: 1px solid #dce5ee; backdrop-filter: blur(8px); }
.participant { margin-left: 12px; padding: 3px 9px; border-radius: 999px; color: #35536f; background: #eef4f8; font-size: 13px; }
.progress-text { color: #526b82; font-size: 14px; }
@media (max-width: 640px) { .progress-header { padding: 12px 14px; } }
</style>
