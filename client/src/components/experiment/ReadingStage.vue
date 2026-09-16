<template>
  <main class="reading-page">
    <ArticleRenderer :article="article" @interaction="recordInteraction" />
    <div class="finish-bar">
      <span>请确认已经完成自然阅读。</span>
      <button type="button" :disabled="submitting" @click="finish">{{ submitting ? "正在保存…" : "完成阅读并答题" }}</button>
    </div>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
  </main>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue";
import ArticleRenderer from "./ArticleRenderer.vue";
import { createEventId } from "../../experiment/experimentApi";

const props = defineProps({
  api: { type: Object, required: true },
  sessionId: { type: String, required: true },
  articleOrder: { type: Number, required: true },
  article: { type: Object, required: true }
});
const emit = defineEmits(["finished"]);
const startMs = ref(0);
const submitting = ref(false);
const error = ref("");
const interactionCount = ref(0);
const scrollEventCount = ref(0);
const maxScrollY = ref(0);
const commentCounts = ref({
  comment_click_count: 0,
  comment_open_count: 0,
  comment_close_count: 0,
  paragraph_toggle_count: 0
});
let lastY = 0;
let totalDistance = 0;
let pendingScrollY = 0;
let scrollTimer = null;

function event(type, payload = {}, timestamp = Date.now()) {
  return props.api.logEvent(
    props.sessionId,
    props.article.article_id,
    type,
    { article_order: props.articleOrder, stage: "reading", ...payload },
    timestamp,
    createEventId(type)
  ).catch(() => null);
}

function currentScrollY() {
  return Math.max(0, window.scrollY || document.documentElement.scrollTop || 0);
}

function flushScrollSample() {
  if (scrollTimer) {
    window.clearTimeout(scrollTimer);
    scrollTimer = null;
  }
  const y = pendingScrollY;
  scrollEventCount.value += 1;
  return event("scroll", { scroll_y: y, viewport_height: window.innerHeight, document_height: document.documentElement.scrollHeight });
}

function onScroll() {
  const y = currentScrollY();
  totalDistance += Math.abs(y - lastY);
  lastY = y;
  maxScrollY.value = Math.max(maxScrollY.value, y);
  pendingScrollY = y;
  if (scrollTimer) return;
  scrollTimer = window.setTimeout(() => {
    flushScrollSample();
  }, 180);
}

function onVisibility() {
  event(document.hidden ? "reading_interruption" : "reading_resume", { visibility_state: document.visibilityState });
}

function onPageHide() {
  event("page_hide", { scroll_y: currentScrollY() });
}

function recordInteraction(interaction) {
  interactionCount.value += 1;
  if (Object.prototype.hasOwnProperty.call(commentCounts.value, interaction.type + "_count")) {
    commentCounts.value[interaction.type + "_count"] += 1;
  }
  event(interaction.type, interaction.payload || {});
}

onMounted(() => {
  startMs.value = Date.now();
  lastY = currentScrollY();
  pendingScrollY = lastY;
  maxScrollY.value = lastY;
  event("reading_start", { start_ms: startMs.value }, startMs.value);
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("pagehide", onPageHide);
  document.addEventListener("visibilitychange", onVisibility);
});

onBeforeUnmount(() => {
  window.removeEventListener("scroll", onScroll);
  window.removeEventListener("pagehide", onPageHide);
  document.removeEventListener("visibilitychange", onVisibility);
  if (scrollTimer) window.clearTimeout(scrollTimer);
});

async function finish() {
  if (submitting.value) return;
  submitting.value = true;
  error.value = "";
  const endMs = Date.now();
  const documentHeight = Math.max(document.documentElement.scrollHeight, 1);
  try {
    if (scrollTimer) await flushScrollSample();
    await event("reading_end", { end_ms: endMs, scroll_y: currentScrollY() }, endMs);
    await props.api.finishReading(props.sessionId, {
      article_order: props.articleOrder,
      article_id: props.article.article_id,
      reading_start_ms: startMs.value,
      reading_end_ms: endMs,
      document_height: documentHeight,
      normalized_scroll_distance: totalDistance / documentHeight,
      comment_interaction_count: interactionCount.value,
      scroll_event_count: scrollEventCount.value,
      total_scroll_distance_px: totalDistance,
      max_scroll_y: maxScrollY.value,
      comment_counts: commentCounts.value
    });
    emit("finished");
  } catch (requestError) {
    error.value = requestError.message;
    submitting.value = false;
  }
}
</script>

<style scoped>
.reading-page { min-height: 100vh; padding: 28px 18px 110px; background: #f2f6f8; }
.finish-bar { position: fixed; right: 24px; bottom: 22px; left: 24px; z-index: 15; display: flex; justify-content: flex-end; gap: 18px; align-items: center; width: min(900px, calc(100% - 48px)); margin: auto; padding: 13px 16px; border: 1px solid #ccdae2; border-radius: 12px; background: rgba(255,255,255,.97); box-shadow: 0 10px 34px rgba(33,60,79,.18); color: #536c7d; }
button { padding: 12px 18px; border: 0; border-radius: 8px; color: #fff; background: #236b78; font-weight: 800; cursor: pointer; }
button:disabled { opacity: .55; }
.error { position: fixed; bottom: 86px; left: 50%; z-index: 16; transform: translateX(-50%); padding: 10px 14px; color: #8b1e2d; background: #fff0f1; border-radius: 8px; }
@media (max-width: 640px) { .finish-bar { right: 10px; bottom: 10px; left: 10px; width: auto; flex-direction: column; gap: 7px; } }
</style>
