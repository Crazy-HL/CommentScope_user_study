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

          <!-- TE: 文末集中 -->
          <div v-if="condition === 'TE'" class="schematic te-schematic">
            <div class="schematic-article">
              <div class="line full"></div>
              <div class="line full"></div>
              <div class="line med"></div>
              <div class="line full"></div>
              <div class="line short"></div>
            </div>
            <div class="schematic-divider"></div>
            <div class="schematic-comments">
              <div class="comment-line full"></div>
              <div class="comment-line med"></div>
              <div class="comment-line full"></div>
              <div class="comment-line short"></div>
            </div>
            <span class="schematic-label">正文</span>
            <span class="schematic-label comment-label">评论区</span>
          </div>

          <!-- CS: 点击查看 -->
          <div v-else-if="condition === 'CS'" class="schematic cs-schematic">
            <div class="schematic-article">
              <div class="line full"></div>
              <div class="line full with-marker"></div>
              <div class="line med"></div>
              <div class="line full with-marker"></div>
              <div class="line short"></div>
            </div>
            <div class="schematic-arrow">点击 →</div>
            <div class="schematic-sidebar">
              <div class="comment-line full"></div>
              <div class="comment-line med"></div>
              <div class="comment-line full"></div>
            </div>
            <span class="schematic-label">正文（标记处可点击）</span>
            <span class="schematic-label comment-label">侧边栏评论</span>
          </div>

          <!-- SE: 句末跟随 -->
          <div v-else-if="condition === 'SE'" class="schematic se-schematic">
            <div class="schematic-article">
              <div class="line full"></div>
              <div class="line-with-comment">
                <div class="line med"></div>
                <div class="inline-comment"></div>
              </div>
              <div class="line full"></div>
              <div class="line-with-comment">
                <div class="line short"></div>
                <div class="inline-comment"></div>
              </div>
              <div class="line med"></div>
            </div>
            <span class="schematic-label">评论紧跟在句子末尾</span>
          </div>

          <!-- BL: 行间穿插 -->
          <div v-else-if="condition === 'BL'" class="schematic bl-schematic">
            <div class="schematic-article">
              <div class="line full"></div>
              <div class="line med"></div>
              <div class="block-comment full"></div>
              <div class="line full"></div>
              <div class="line short"></div>
              <div class="block-comment med"></div>
              <div class="line full"></div>
            </div>
            <span class="schematic-label">评论以独立段落穿插在行间</span>
          </div>

          <!-- 图例 -->
          <div class="schematic-legend">
            <span class="legend-item">
              <span class="legend-swatch article-swatch"></span>
              <span class="legend-text">正文</span>
            </span>
            <span class="legend-item">
              <span class="legend-swatch comment-swatch"></span>
              <span class="legend-text">读者评论</span>
            </span>
          </div>

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

/* 示意图通用样式 */
.schematic { position: relative; margin-top: 10px; padding: 18px 16px 28px; background: #fff; border: 1px solid #e8eef2; border-radius: 8px; display: flex; gap: 12px; align-items: flex-start; }
.schematic-article { flex: 1; width: 100%; display: flex; flex-direction: column; gap: 7px; }
.schematic .line { display: block; height: 10px; background: #2c2c2c; border-radius: 3px; flex-shrink: 0; }
.schematic .line.full { width: 100%; }
.schematic .line.med { width: 72%; }
.schematic .line.short { width: 45%; }
.schematic .comment-line { display: block; height: 10px; border-radius: 3px; flex-shrink: 0; }
.schematic .comment-line.full { width: 100%; }
.schematic .comment-line.med { width: 70%; }
.schematic .comment-line.short { width: 50%; }
.schematic-label { position: absolute; bottom: 8px; left: 16px; font-size: 11px; color: #8a9baa; }
.schematic-label.comment-label { left: auto; right: 16px; }

/* 图例 */
.schematic-legend { display: flex; gap: 24px; justify-content: center; margin-top: 12px; padding-top: 10px; border-top: 1px solid #eef2f5; }
.legend-item { display: flex; align-items: center; gap: 6px; }
.legend-swatch { display: inline-block; width: 24px; height: 10px; border-radius: 2px; }
.legend-swatch.article-swatch { background: #2c2c2c; }
.legend-swatch.comment-swatch { background: #d32f2f; }
.legend-text { font-size: 12px; color: #5a6a7a; }

/* TE 文末集中 */
.te-schematic { flex-direction: column; }
.te-schematic .schematic-divider { height: 1px; background: #dde4ea; margin: 4px 0; }
.te-schematic .schematic-comments { width: 100%; display: flex; flex-direction: column; gap: 7px; padding-top: 4px; }
.te-schematic .comment-line { background: #d32f2f; }
.te-schematic .comment-label { color: #d32f2f; }

/* CS 点击查看 */
.cs-schematic .schematic-article { flex: 1.2; }
.cs-schematic .line.with-marker { position: relative; }
.cs-schematic .line.with-marker::after { content: ""; position: absolute; right: -4px; top: 50%; transform: translateY(-50%); width: 8px; height: 8px; background: #d32f2f; border-radius: 50%; }
.cs-schematic .schematic-arrow { display: flex; align-items: center; font-size: 12px; color: #d32f2f; font-weight: 600; padding-top: 14px; }
.cs-schematic .schematic-sidebar { flex: 0.7; display: flex; flex-direction: column; gap: 7px; padding: 10px 8px; background: #fef0f0; border: 1px solid #f5c6c6; border-radius: 6px; min-height: 80px; }
.cs-schematic .comment-line { background: #d32f2f; }
.cs-schematic .comment-label { color: #d32f2f; }

/* SE 句末跟随 */
.se-schematic .schematic-article { width: 100%; }
.se-schematic .line-with-comment { display: flex; align-items: center; gap: 6px; }
.se-schematic .inline-comment { height: 10px; background: #d32f2f; border-radius: 3px; flex: 1; min-width: 60px; }
.se-schematic .schematic-label { color: #d32f2f; left: 50%; transform: translateX(-50%); }

/* BL 行间穿插 */
.bl-schematic .schematic-article { width: 100%; }
.bl-schematic .block-comment { height: 14px; background: #d32f2f; border-radius: 3px; margin: 2px 0; }
.bl-schematic .block-comment.full { width: 100%; }
.bl-schematic .block-comment.med { width: 68%; }
.bl-schematic .schematic-label { color: #d32f2f; left: 50%; transform: translateX(-50%); }

.question-intro { margin: 20px 0; padding: 16px 18px; background: #f8f9fa; border-radius: 10px; }
.question-intro ul { margin: 0; padding-left: 20px; }
.question-intro li { font-size: 14px; margin: 6px 0; }

.hint { padding: 13px 15px; border-left: 4px solid #d6a84b; background: #fff9ea; margin: 20px 0; }
button { float: right; min-width: 140px; padding: 13px 20px; border: 0; border-radius: 9px; color: #fff; background: #236b78; font-weight: 800; cursor: pointer; }
button:disabled { opacity: .55; }
</style>
