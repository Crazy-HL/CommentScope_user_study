<template>
  <main class="question-page" :class="{ 'cra-page': group === 'cra' }">
    <!-- 非 CRA 阶段：文章全宽显示 -->
    <section v-if="group !== 'cra'" class="article-section">
      <ArticleRenderer :article="article" @interaction="recordInteraction" />
    </section>

    <!-- CRA 阶段：记忆提示 -->
    <section v-else class="cra-notice-section">
      <div class="cra-notice-card">
        <p class="memory-notice">文章与评论已隐藏，请根据刚才的阅读记忆作答。</p>
      </div>
    </section>

    <!-- 浮动答题按钮 -->
    <div v-if="currentQuestion && !showQuestionPanel" class="floating-answer-bar">
      <div class="answer-info">
        <span class="answer-badge">{{ groupTitle }}</span>
        <span class="answer-progress">第 {{ currentIndex + 1 }} / {{ questions.length }} 题待作答</span>
      </div>
      <button type="button" class="answer-btn" @click="openQuestionPanel">
        开始答题
      </button>
    </div>

    <!-- 题目弹出面板 -->
    <transition name="fade">
      <div v-if="showQuestionPanel && currentQuestion" class="question-overlay" @click.self="closeQuestionPanel">
        <div class="question-modal">
          <div class="question-modal-header">
            <span class="question-group-tag">{{ groupTitle }}</span>
            <span class="question-count">第 {{ currentIndex + 1 }} 题，共 {{ questions.length }} 题</span>
            <button type="button" class="close-btn" @click="closeQuestionPanel" aria-label="关闭">×</button>
          </div>

          <div class="question-modal-body">
            <p v-if="group === 'cra'" class="memory-notice-inline">文章与评论已隐藏，请根据阅读记忆作答。</p>
            <h2 class="question-prompt">{{ currentQuestion.prompt }}</h2>
            <form @submit.prevent="submit">
              <label
                v-for="option in currentOptions"
                :key="option.key"
                class="option"
                :class="{ selected: selectedOption === option.key }">
                <input
                  :checked="selectedOption === option.key"
                  type="radio"
                  :name="currentQuestion.id"
                  :value="option.key"
                  @change="selectOption(option.key)" />
                <span class="option-key">{{ option.key }}</span>
                <span class="option-text">{{ option.text }}</span>
              </label>
              <p v-if="error" class="error" role="alert">{{ error }}</p>
              <div class="question-actions">
                <button type="button" class="btn-secondary" @click="closeQuestionPanel">稍后再答</button>
                <button type="submit" class="btn-primary" :disabled="!selectedOption || submitting">
                  {{ submitting ? "正在保存…" : "提交答案" }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </transition>

    <!-- 全部完成提示 -->
    <div v-if="!currentQuestion && !showQuestionPanel" class="all-done">
      <div class="done-card">
        <div class="done-icon">✓</div>
        <h3>{{ groupTitle }} 已完成</h3>
        <p>正在进入下一阶段…</p>
      </div>
    </div>
  </main>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import ArticleRenderer from "./ArticleRenderer.vue";
import { createEventId } from "../../experiment/experimentApi";
import { STAGE_TITLES } from "../../experiment/experimentConfig";

const props = defineProps({
  api: { type: Object, required: true },
  sessionId: { type: String, required: true },
  articleOrder: { type: Number, required: true },
  article: { type: Object, required: true },
  group: { type: String, required: true },
  savedResponses: { type: Array, default: () => [] }
});
const emit = defineEmits(["completed", "saved"]);

const questions = computed(() => props.article.questions?.[props.group] || []);
const groupTitle = computed(() => STAGE_TITLES[props.group] || "答题");

const completedIds = ref(new Set(
  props.savedResponses
    .filter(item => item.article_order === props.articleOrder && item.question_type === props.group)
    .map(item => item.question_id)
));
const currentIndex = computed(() => questions.value.findIndex(item => !completedIds.value.has(item.id)));
const currentQuestion = computed(() => currentIndex.value < 0 ? null : questions.value[currentIndex.value]);
const currentOptions = computed(() => {
  const options = currentQuestion.value?.options || [];
  return props.group === "cra" ? options.filter(option => ["A", "B"].includes(option.key)) : options;
});

const showQuestionPanel = ref(false);
const selectedOption = ref("");
const submitting = ref(false);
const error = ref("");
const itemStartMs = ref(Date.now());
const optionClickCount = ref(0);
const optionChangeCount = ref(0);
const scrollEventCount = ref(0);
const totalScrollDistancePx = ref(0);
const maxScrollY = ref(0);
let lastScrollY = 0;
let pendingScrollY = 0;
let scrollTimer = null;

function scrollPosition() {
  return Math.max(0, window.scrollY || document.documentElement.scrollTop || 0);
}

function resetQuestionMetrics() {
  optionClickCount.value = 0;
  optionChangeCount.value = 0;
  scrollEventCount.value = 0;
  totalScrollDistancePx.value = 0;
  lastScrollY = scrollPosition();
  pendingScrollY = lastScrollY;
  maxScrollY.value = lastScrollY;
}

function flushQuestionScroll() {
  if (!scrollTimer) return Promise.resolve();
  window.clearTimeout(scrollTimer);
  scrollTimer = null;
  scrollEventCount.value += 1;
  return props.api.logEvent(props.sessionId, props.article.article_id, "question_scroll", {
    article_order: props.articleOrder,
    stage: props.group,
    question_type: props.group,
    question_id: currentQuestion.value?.id,
    item_index: currentIndex.value,
    scroll_y: pendingScrollY,
    viewport_height: window.innerHeight,
    document_height: document.documentElement.scrollHeight
  }, Date.now(), createEventId("question-scroll")).catch(() => null);
}

function onScroll() {
  const y = scrollPosition();
  totalScrollDistancePx.value += Math.abs(y - lastScrollY);
  lastScrollY = y;
  pendingScrollY = y;
  maxScrollY.value = Math.max(maxScrollY.value, y);
  if (scrollTimer) return;
  scrollTimer = window.setTimeout(() => {
    flushQuestionScroll();
  }, 180);
}

function selectOption(optionKey) {
  const previous = selectedOption.value;
  optionClickCount.value += 1;
  if (previous && previous !== optionKey) optionChangeCount.value += 1;
  selectedOption.value = optionKey;
  props.api.logEvent(props.sessionId, props.article.article_id, "question_option_change", {
    article_order: props.articleOrder,
    stage: props.group,
    question_type: props.group,
    question_id: currentQuestion.value?.id,
    item_index: currentIndex.value,
    selected_option: optionKey,
    elapsed_ms: Date.now() - itemStartMs.value
  }, Date.now(), createEventId("question-option-change")).catch(() => null);
}

function openQuestionPanel() {
  if (!currentQuestion.value) return;
  showQuestionPanel.value = true;
  selectedOption.value = "";
  error.value = "";
  itemStartMs.value = Date.now();
  resetQuestionMetrics();
  props.api.logEvent(props.sessionId, props.article.article_id, "question_display", {
    article_order: props.articleOrder,
    stage: props.group,
    question_type: props.group,
    question_id: currentQuestion.value.id,
    item_index: currentIndex.value
  }, itemStartMs.value, createEventId("question-display")).catch(() => null);
}

function closeQuestionPanel() {
  showQuestionPanel.value = false;
}

function recordInteraction(interaction) {
  props.api.logEvent(
    props.sessionId,
    props.article.article_id,
    interaction.type,
    { article_order: props.articleOrder, stage: props.group, ...interaction.payload },
    Date.now(),
    createEventId(interaction.type)
  ).catch(() => null);
}

watch(() => currentQuestion.value?.id, (newId, oldId) => {
  if (newId && newId !== oldId && showQuestionPanel.value) {
    selectedOption.value = "";
    error.value = "";
    itemStartMs.value = Date.now();
    resetQuestionMetrics();
    props.api.logEvent(props.sessionId, props.article.article_id, "question_display", {
      article_order: props.articleOrder,
      stage: props.group,
      question_type: props.group,
      question_id: newId,
      item_index: currentIndex.value
    }, itemStartMs.value, createEventId("question-display")).catch(() => null);
  }
});

onMounted(() => {
  window.addEventListener("scroll", onScroll, { passive: true });
  resetQuestionMetrics();
});

onBeforeUnmount(() => {
  if (scrollTimer) window.clearTimeout(scrollTimer);
  window.removeEventListener("scroll", onScroll);
});

async function submit() {
  if (!currentQuestion.value || !selectedOption.value || submitting.value) return;
  submitting.value = true;
  error.value = "";
  const question = currentQuestion.value;
  const submitMs = Date.now();
  try {
    await flushQuestionScroll();
    const response = await props.api.submitResponse(props.sessionId, {
      article_order: props.articleOrder,
      article_id: props.article.article_id,
      question_type: props.group,
      question_id: question.id,
      selected_option: selectedOption.value,
      item_start_ms: itemStartMs.value,
      submit_ms: submitMs,
      option_click_count: optionClickCount.value,
      option_change_count: optionChangeCount.value,
      scroll_event_count: scrollEventCount.value,
      total_scroll_distance_px: totalScrollDistancePx.value,
      max_scroll_y: maxScrollY.value
    });
    completedIds.value = new Set([...completedIds.value, question.id]);
    emit("saved", response);
    await props.api.logEvent(props.sessionId, props.article.article_id, "question_submit", {
      question_type: props.group,
      question_id: question.id,
      elapsed_ms: submitMs - itemStartMs.value
    }, submitMs, createEventId("question-submit")).catch(() => null);

    // 关闭当前题目面板
    showQuestionPanel.value = false;

    // 如果还有下一题，短暂延迟后自动打开
    if (currentIndex.value >= 0) {
      setTimeout(() => {
        openQuestionPanel();
      }, 400);
    } else {
      emit("completed");
    }
  } catch (requestError) {
    error.value = requestError.message;
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.question-page {
  min-height: calc(100vh - 62px);
  padding: 24px clamp(18px, 3vw, 42px) 120px;
  color: #263f56;
  background: #f2f6f8;
}

/* 文章区域 */
.article-section {
  width: 100%;
  max-width: 1100px;
  margin: 0 auto;
}

/* CRA 记忆提示 */
.cra-notice-section {
  display: grid;
  place-items: center;
  min-height: 50vh;
}
.cra-notice-card {
  padding: 32px 40px;
  border: 1px solid #d7e5e7;
  border-radius: 14px;
  background: #fff;
  text-align: center;
  box-shadow: 0 8px 28px rgba(36,60,81,.08);
}
.memory-notice {
  margin: 0;
  color: #315a68;
  font-size: 16px;
  line-height: 1.7;
}

/* 浮动答题栏 */
.floating-answer-bar {
  position: fixed;
  right: 24px;
  bottom: 22px;
  left: 24px;
  z-index: 30;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18px;
  width: min(900px, calc(100% - 48px));
  margin: 0 auto;
  padding: 14px 20px;
  border: 1px solid #ccdae2;
  border-radius: 12px;
  background: rgba(255,255,255,.97);
  box-shadow: 0 10px 34px rgba(33,60,79,.18);
  backdrop-filter: blur(8px);
}
.answer-info {
  display: flex;
  align-items: center;
  gap: 12px;
}
.answer-badge {
  padding: 4px 10px;
  border-radius: 6px;
  color: #fff;
  background: #2b7a78;
  font-size: 13px;
  font-weight: 700;
}
.answer-progress {
  color: #536c7d;
  font-size: 14px;
}
.answer-btn {
  padding: 12px 24px;
  border: 0;
  border-radius: 8px;
  color: #fff;
  background: #236b78;
  font-size: 15px;
  font-weight: 800;
  cursor: pointer;
  transition: background .2s;
}
.answer-btn:hover {
  background: #1a5a66;
}

/* 题目弹出面板 */
.question-overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(15, 35, 50, .55);
  backdrop-filter: blur(4px);
}
.question-modal {
  width: min(680px, 100%);
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 24px 64px rgba(0,0,0,.25);
  overflow: hidden;
}
.question-modal-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 22px;
  border-bottom: 1px solid #e8eef2;
  background: #f8fafb;
}
.question-group-tag {
  padding: 4px 10px;
  border-radius: 6px;
  color: #fff;
  background: #2b7a78;
  font-size: 13px;
  font-weight: 700;
}
.question-count {
  flex: 1;
  color: #526b82;
  font-size: 14px;
}
.close-btn {
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border: 0;
  border-radius: 6px;
  color: #8899a8;
  background: transparent;
  font-size: 22px;
  cursor: pointer;
  transition: background .2s, color .2s;
}
.close-btn:hover {
  color: #333;
  background: #eef2f5;
}
.question-modal-body {
  padding: 28px 32px 32px;
  overflow-y: auto;
}
.memory-notice-inline {
  margin: 0 0 16px;
  padding: 10px 14px;
  border: 1px solid #d7e5e7;
  border-radius: 8px;
  color: #315a68;
  background: #eff8f7;
  font-size: 14px;
  line-height: 1.6;
}
.question-prompt {
  margin: 0 0 24px;
  color: #17324d;
  font-size: clamp(18px, 2.2vw, 22px);
  line-height: 1.6;
}
.option {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  margin: 10px 0;
  padding: 14px 16px;
  border: 1px solid #c9d6de;
  border-radius: 10px;
  color: #2a4357;
  cursor: pointer;
  transition: border-color .2s, background .2s;
}
.option:hover {
  border-color: #7fb5c0;
  background: #f7fbfc;
}
.option.selected {
  border-color: #287587;
  background: #f0f8f9;
}
.option input {
  margin-top: 4px;
}
.option-key {
  min-width: 24px;
  font-weight: 800;
  color: #2b6e7c;
}
.option-text {
  flex: 1;
  line-height: 1.6;
}
.question-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}
.btn-primary {
  padding: 12px 24px;
  border: 0;
  border-radius: 8px;
  color: #fff;
  background: #236b78;
  font-weight: 800;
  cursor: pointer;
  transition: background .2s;
}
.btn-primary:hover:not(:disabled) {
  background: #1a5a66;
}
.btn-primary:disabled {
  opacity: .5;
  cursor: not-allowed;
}
.btn-secondary {
  padding: 12px 20px;
  border: 1px solid #c9d6de;
  border-radius: 8px;
  color: #526b82;
  background: #fff;
  font-weight: 600;
  cursor: pointer;
  transition: background .2s;
}
.btn-secondary:hover {
  background: #f5f8fa;
}
.error {
  margin: 12px 0 0;
  color: #8b1e2d;
  font-size: 14px;
}

/* 全部完成 */
.all-done {
  display: grid;
  place-items: center;
  min-height: 50vh;
}
.done-card {
  padding: 36px 48px;
  border: 1px solid #d7e5e7;
  border-radius: 16px;
  background: #fff;
  text-align: center;
  box-shadow: 0 12px 36px rgba(36,60,81,.1);
}
.done-icon {
  width: 56px;
  height: 56px;
  display: grid;
  place-items: center;
  margin: 0 auto 16px;
  border-radius: 50%;
  color: #fff;
  background: #2f8b76;
  font-size: 28px;
}
.done-card h3 {
  margin: 0 0 8px;
  color: #17324d;
}
.done-card p {
  margin: 0;
  color: #526b82;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity .25s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 640px) {
  .question-page {
    padding: 16px 12px 110px;
  }
  .floating-answer-bar {
    right: 10px;
    bottom: 10px;
    left: 10px;
    width: auto;
    flex-direction: column;
    gap: 10px;
    padding: 12px 14px;
  }
  .answer-info {
    width: 100%;
    justify-content: center;
  }
  .answer-btn {
    width: 100%;
  }
  .question-modal-body {
    padding: 20px 18px 24px;
  }
  .question-actions {
    flex-direction: column-reverse;
  }
  .btn-primary, .btn-secondary {
    width: 100%;
  }
}
</style>
