<template>
  <header class="progress-header">
    <div class="header-left">
      <strong>CommentScope 阅读实验</strong>
      <span v-if="participantId" class="participant">{{ participantId }}</span>
    </div>
    <div class="header-right">
      <span v-if="conditionLabel" class="condition-label">{{ conditionLabel }}</span>
      <span v-if="articleOrder" class="progress-text">文章 {{ articleOrder }} / 4 · {{ stageTitle }}</span>
      <span v-else class="progress-text">{{ stageTitle }}</span>
    </div>
  </header>
</template>

<script setup>
import { computed } from "vue";
import { STAGE_TITLES, conditionLabelForRenderMode } from "../../experiment/experimentConfig";

const props = defineProps({
  participantId: { type: String, default: "" },
  articleOrder: { type: Number, default: 0 },
  stage: { type: String, default: "instruction" },
  renderMode: { type: String, default: "" }
});
const stageTitle = computed(() => STAGE_TITLES[props.stage] || "实验进行中");
const conditionLabel = computed(() => props.renderMode ? conditionLabelForRenderMode(props.renderMode) : "");
</script>

<style scoped>
.progress-header { position: sticky; top: 0; z-index: 20; display: flex; justify-content: space-between; gap: 16px; align-items: center; padding: 14px 24px; color: #17324d; background: rgba(255,255,255,.96); border-bottom: 1px solid #dce5ee; backdrop-filter: blur(8px); }
.header-left { display: flex; align-items: center; gap: 4px; }
.header-right { display: flex; align-items: center; gap: 16px; }
.participant { margin-left: 12px; padding: 3px 9px; border-radius: 999px; color: #35536f; background: #eef4f8; font-size: 13px; }
.condition-label { padding: 5px 12px; border-radius: 6px; color: #fff; background: linear-gradient(135deg, #2b7a78, #1a5f5d); font-size: 13px; font-weight: 700; white-space: nowrap; }
.progress-text { color: #526b82; font-size: 14px; }
@media (max-width: 640px) {
  .progress-header { padding: 12px 14px; flex-wrap: wrap; }
  .header-right { gap: 8px; flex-wrap: wrap; }
  .condition-label { font-size: 12px; padding: 4px 8px; }
}
</style>
