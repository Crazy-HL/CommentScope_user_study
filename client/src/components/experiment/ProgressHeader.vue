<template>
  <header class="progress-header">
    <div class="header-left">
      <strong>CommentScope 阅读实验</strong>
      <span v-if="participantId" class="participant">{{ participantId }}</span>
    </div>
    <div class="header-right">
      <span v-if="conditionLabel" class="condition-label" :class="`condition-${conditionCode.toLowerCase()}`">{{ conditionLabel }}</span>
      <span v-if="articleOrder" class="progress-text">文章 {{ articleOrder }} / 4 · {{ stageTitle }}</span>
      <span v-else class="progress-text">{{ stageTitle }}</span>
      <button v-if="participantId" type="button" class="exit-btn" @click="handleExit" title="退出当前实验，返回选择页面">退出实验</button>
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
const emit = defineEmits(["exit"]);
const stageTitle = computed(() => STAGE_TITLES[props.stage] || "实验进行中");
const conditionLabel = computed(() => props.renderMode ? conditionLabelForRenderMode(props.renderMode) : "");
const RENDER_MODE_TO_CODE = { layout_a: "TE", layout_b: "CS", layout_c: "SE", layout_d: "BL" };
const conditionCode = computed(() => RENDER_MODE_TO_CODE[props.renderMode] || "");

function handleExit() {
  const confirmed = window.confirm(
    "确定要退出当前实验吗？\n\n退出后当前进度将保存在服务器上，本浏览器可以选择继续之前的实验，或选择其他可用的参与者编号。\n\n如需重置进行中的参与者，请联系研究者通过管理员后台操作。"
  );
  if (confirmed) emit("exit");
}
</script>

<style scoped>
.progress-header { position: sticky; top: 0; z-index: 20; display: flex; justify-content: space-between; gap: 16px; align-items: center; padding: 14px 24px; color: #17324d; background: rgba(255,255,255,.96); border-bottom: 1px solid #dce5ee; backdrop-filter: blur(8px); }
.header-left { display: flex; align-items: center; gap: 4px; }
.header-right { display: flex; align-items: center; gap: 16px; }
.participant { margin-left: 12px; padding: 3px 9px; border-radius: 999px; color: #35536f; background: #eef4f8; font-size: 13px; }
.condition-label { padding: 5px 12px; border-radius: 6px; color: #fff; font-size: 13px; font-weight: 700; white-space: nowrap; }
.condition-label.condition-te { background: linear-gradient(135deg, #2b7a78, #1a5f5d); }
.condition-label.condition-cs { background: linear-gradient(135deg, #c0792e, #a06020); }
.condition-label.condition-se { background: linear-gradient(135deg, #5a6fa8, #45588a); }
.condition-label.condition-bl { background: linear-gradient(135deg, #8b5a8b, #6e456e); }
.progress-text { color: #526b82; font-size: 14px; }
.exit-btn {
  padding: 5px 12px;
  border: 1px solid #c9d6de;
  border-radius: 6px;
  color: #8b1e2d;
  background: #fff;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all .2s;
}
.exit-btn:hover {
  border-color: #8b1e2d;
  background: #fff0f1;
}
@media (max-width: 640px) {
  .progress-header { padding: 12px 14px; flex-wrap: wrap; }
  .header-right { gap: 8px; flex-wrap: wrap; }
  .condition-label { font-size: 12px; padding: 4px 8px; }
}
</style>
