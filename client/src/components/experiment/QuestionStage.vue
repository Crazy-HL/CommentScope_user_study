<template>
  <main class="question-page" :class="{ 'cra-page': group === 'cra' }">
    <section v-if="group !== 'cra'" ref="articlePanel" class="article-panel">
      <div class="article-panel-header">
        <span>文章与评论</span>
        <small>答题时可以继续查看文章内容和评论</small>
      </div>
      <ArticleRenderer :article="article" @interaction="recordInteraction" />
    </section>

    <section class="question-card" v-if="currentQuestion">
      <p v-if="group === 'cra'" class="memory-notice">文章与评论已隐藏，请根据刚才的阅读记忆作答。</p>
      <p class="count">本部分第 {{ currentIndex + 1 }} 题，共 {{ questions.length }} 题</p>
      <h1>{{ currentQuestion.prompt }}</h1>
      <form @submit.prevent="submit">
        <label v-for="option in currentOptions" :key="option.key" class="option" :class="{ selected: selectedOption === option.key }">
          <input :checked="selectedOption === option.key" type="radio" :name="currentQuestion.id" :value="option.key" @change="selectOption(option.key)" />
          <span class="option-key">{{ option.key }}</span>
          <span>{{ option.text }}</span>
        </label>
        <p v-if="error" class="error" role="alert">{{ error }}</p>
        <button type="submit" :disabled="!selectedOption || submitting">{{ submitting ? "正在保存…" : "提交答案" }}</button>
      </form>
    </section>
  </main>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import ArticleRenderer from "./ArticleRenderer.vue";
import { createEventId } from "../../experiment/experimentApi";

const props = defineProps({
  api: { type: Object, required: true },
  sessionId: { type: String, required: true },
  articleOrder: { type: Number, required: true },
  article: { type: Object, required: true },
  group: { type: String, required: true },
  savedResponses: { type: Array, default: () => [] }
});
const emit = defineEmits(["completed", "saved"]);
const articlePanel = ref(null);
const questions = computed(() => props.article.questions?.[props.group] || []);
const completedIds = ref(new Set(props.savedResponses.filter(item => item.article_order === props.articleOrder && item.question_type === props.group).map(item => item.question_id)));
const currentIndex = computed(() => questions.value.findIndex(item => !completedIds.value.has(item.id)));
const currentQuestion = computed(() => currentIndex.value < 0 ? null : questions.value[currentIndex.value]);
const currentOptions = computed(() => {
  const options = currentQuestion.value?.options || [];
  return props.group === "cra" ? options.filter(option => ["A", "B"].includes(option.key)) : options;
});
const selectedOption = ref("");
const submitting = ref(false);
const error = ref("");
const itemStartMs = ref(Date.now());
const optionClickCount = ref(0);
const optionChangeCount = ref(0);
const scrollEventCount = ref(0);
const totalScrollDistancePx = ref(0);
const maxScrollY = ref(0);
let scrollTarget = null;
let lastScrollY = 0;
let pendingScrollY = 0;
let scrollTimer = null;

function scrollPosition() {
  if (scrollTarget && scrollTarget !== window) return Math.max(0, scrollTarget.scrollTop || 0);
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
    document_height: scrollTarget?.scrollHeight || document.documentElement.scrollHeight
  }, Date.now(), createEventId("question-scroll")).catch(() => null);
}

function onQuestionScroll() {
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

async function recordDisplay() {
  if (!currentQuestion.value) {
    emit("completed");
    return;
  }
  itemStartMs.value = Date.now();
  resetQuestionMetrics();
  await props.api.logEvent(props.sessionId, props.article.article_id, "question_display", {
    article_order: props.articleOrder,
    stage: props.group,
    question_type: props.group,
    question_id: currentQuestion.value.id,
    item_index: currentIndex.value
  }, itemStartMs.value, createEventId("question-display")).catch(() => null);
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

watch(() => currentQuestion.value?.id, () => {
  selectedOption.value = "";
  error.value = "";
  recordDisplay();
}, { immediate: true });

onMounted(() => {
  if (props.group === "cra") return;
  scrollTarget = articlePanel.value?.querySelector(".article-renderer") || window;
  scrollTarget.addEventListener("scroll", onQuestionScroll, { passive: true });
  resetQuestionMetrics();
});

onBeforeUnmount(() => {
  if (scrollTimer) window.clearTimeout(scrollTimer);
  if (scrollTarget) scrollTarget.removeEventListener("scroll", onQuestionScroll);
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
    if (currentIndex.value < 0) emit("completed");
  } catch (requestError) {
    error.value = requestError.message;
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.question-page { min-height: calc(100vh - 62px); display: grid; grid-template-columns: minmax(0, 1.12fr) minmax(360px, .88fr); gap: 24px; align-items: start; padding: 24px clamp(18px, 3vw, 42px) 42px; color: #263f56; background: #f2f6f8; }
.article-panel { min-width: 0; }
.article-panel-header { display: flex; justify-content: space-between; gap: 14px; align-items: baseline; width: min(920px, 100%); margin: 0 auto 10px; color: #315a68; font-weight: 800; }
.article-panel-header small { color: #68808f; font-weight: 500; }
.article-panel :deep(.article-renderer) { width: 100%; max-height: calc(100vh - 145px); overflow: auto; margin: 0; padding: clamp(24px, 3vw, 40px); }
.cra-page { grid-template-columns: minmax(360px, 760px); justify-content: center; }
.cra-page .question-card { position: static; }
.memory-notice { margin: 0 0 18px; padding: 12px 14px; border: 1px solid #d7e5e7; border-radius: 9px; color: #315a68; background: #eff8f7; line-height: 1.6; }
.question-card { position: sticky; top: 24px; width: 100%; padding: clamp(24px, 4vw, 42px); border: 1px solid #d9e4ea; border-radius: 16px; background: #fff; box-shadow: 0 14px 42px rgba(36,60,81,.09); }
.count { color: #2b7a78; font-weight: 800; }
h1 { margin: 12px 0 26px; color: #17324d; font-size: clamp(22px, 3vw, 29px); line-height: 1.55; }
.option { display: flex; gap: 12px; align-items: flex-start; margin: 12px 0; padding: 15px; border: 1px solid #c9d6de; border-radius: 10px; color: #2a4357; cursor: pointer; }
.option.selected { border-color: #287587; }
.option input { margin-top: 5px; }
.option-key { min-width: 24px; font-weight: 800; color: #2b6e7c; }
button { display: block; min-width: 140px; margin: 24px 0 0 auto; padding: 13px 20px; border: 0; border-radius: 9px; color: #236b78; border: 1px solid #236b78; font-weight: 800; cursor: pointer; }
button:disabled { opacity: .5; cursor: not-allowed; }
.error { color: #8b1e2d; }
@media (max-width: 900px) {
  .question-page { grid-template-columns: 1fr; }
  .question-card { position: static; }
  .article-panel :deep(.article-renderer) { max-height: none; }
}
@media (max-width: 640px) {
  .article-panel-header { display: block; }
  .article-panel-header small { display: block; margin-top: 4px; }
  .question-page { padding-right: 10px; padding-left: 10px; }
}
</style>
