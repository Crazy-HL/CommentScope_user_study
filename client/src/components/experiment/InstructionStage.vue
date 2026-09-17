<template>
  <main class="stage-shell">
    <section class="stage-card">
      <p class="step">第 {{ articleOrder }} 篇，共 4 篇</p>
      <h1>阅读说明</h1>

      <div class="intro-section">
        <p class="intro-text">
          接下来请像平时一样自然阅读文章。文章中会嵌入<strong>其他读者的评论</strong>，
          这些评论与正文内容相关，以不同方式呈现。阅读完成后，你将回答 6 道题目。
        </p>
      </div>

      <div class="condition-intro">
        <h3>本篇评论展示方式</h3>
        <div class="condition-card" :class="conditionClass">
          <span class="condition-label">{{ conditionLabel }}</span>
          <span class="condition-desc">{{ conditionDesc }}</span>
        </div>
        <p class="condition-hint">不同文章会使用不同的评论展示方式，请自然阅读即可。</p>
      </div>

      <div class="question-intro">
        <h3>答题说明</h3>
        <ul>
          <li>共 6 道题目，每题单独弹出</li>
          <li>答题时可以随时返回文章页面查看</li>
          <li>题目提交后不能修改，也不能回到已提交题目</li>
        </ul>
      </div>

      <p class="hint">请在准备好后开始阅读。</p>
      <button type="button" :disabled="loading" @click="$emit('continue')">{{ loading ? "正在加载…" : "开始阅读" }}</button>
    </section>
  </main>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  articleOrder: { type: Number, required: true },
  loading: { type: Boolean, default: false },
  condition: { type: String, default: "" }
});
defineEmits(["continue"]);

const CONDITION_INFO = {
  TE: { label: "文末集中 (Text-End)", desc: "所有评论集中显示在文章末尾，阅读完正文后可查看评论。", class: "te" },
  CS: { label: "点击查看 (Click-to-Show)", desc: "正文中有评论的位置会显示标记，点击标记可在侧边栏查看评论。", class: "cs" },
  SE: { label: "句末跟随 (Sentence-End)", desc: "评论紧跟在相关句子的末尾，与正文连续显示。", class: "se" },
  BL: { label: "行间穿插 (Between-Line)", desc: "评论以独立段落的形式穿插在正文段落之间。", class: "bl" }
};

const conditionInfo = computed(() => CONDITION_INFO[props.condition] || { label: "", desc: "", class: "" });
const conditionLabel = computed(() => conditionInfo.value.label);
const conditionDesc = computed(() => conditionInfo.value.desc);
const conditionClass = computed(() => conditionInfo.value.class);
</script>

<style scoped>
.stage-shell { min-height: calc(100vh - 62px); display: grid; place-items: center; padding: 30px 18px; background: #f5f8fa; }
.stage-card { width: min(720px, 100%); padding: 34px; border: 1px solid #dbe5ec; border-radius: 16px; background: #fff; box-shadow: 0 12px 36px rgba(37,64,88,.08); color: #263f56; }
.step { color: #2b7a78; font-weight: 800; }
h1 { margin-top: 6px; color: #17324d; }
h3 { margin: 0 0 12px; color: #17324d; font-size: 16px; }
p, li { line-height: 1.8; }

.intro-section { margin: 16px 0; padding: 16px 18px; background: #f0f7f8; border-radius: 10px; border-left: 4px solid #2b7a78; }
.intro-text { margin: 0; font-size: 15px; }
.intro-text strong { color: #1a5a66; }

.condition-intro { margin: 20px 0; }
.condition-card { display: flex; flex-direction: column; gap: 8px; padding: 16px 18px; border-radius: 10px; border: 1px solid #e0e8ec; background: #fafbfc; }
.condition-card.te { border-left: 4px solid #2b7a78; }
.condition-card.cs { border-left: 4px solid #c0792e; }
.condition-card.se { border-left: 4px solid #5a6fa8; }
.condition-card.bl { border-left: 4px solid #8b5a8b; }
.condition-label { font-weight: 700; font-size: 15px; color: #17324d; }
.condition-desc { font-size: 14px; color: #4a6072; line-height: 1.7; }
.condition-hint { margin: 10px 0 0; font-size: 13px; color: #7a8ea0; font-style: italic; }

.question-intro { margin: 20px 0; padding: 16px 18px; background: #f8f9fa; border-radius: 10px; }
.question-intro ul { margin: 0; padding-left: 20px; }
.question-intro li { font-size: 14px; margin: 6px 0; }

.hint { padding: 13px 15px; border-left: 4px solid #d6a84b; background: #fff9ea; margin: 20px 0; }
button { float: right; min-width: 140px; padding: 13px 20px; border: 0; border-radius: 9px; color: #fff; background: #236b78; font-weight: 800; cursor: pointer; }
button:disabled { opacity: .55; }
</style>
