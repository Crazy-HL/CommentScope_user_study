<template>
  <div id="experiment-app">
    <div v-if="isAdminRoute" class="admin-route-shell">
      <main v-if="booting" class="admin-loading">正在检查管理员登录状态…</main>
      <AdminDashboard v-if="adminAuthenticated && isAdminAnalysisRoute" :username="adminUsername" @logout="adminLogout" />
      <AdminOverview v-else-if="adminAuthenticated" :username="adminUsername" @logout="adminLogout" />
      <AdminLogin v-else @authenticated="adminLoginSuccess" />
    </div>

    <template v-else>
    <ParticipantPicker
      v-if="!state.session && !booting"
      :api="api"
      :client-instance-id="state.clientInstanceId"
      @started="acceptPayload"
    />

    <main v-else-if="booting" class="status-page"><p>正在恢复实验进度…</p></main>

    <template v-else>
      <ProgressHeader
        :participant-id="state.session.participant_id"
        :article-order="headerArticleOrder"
        :stage="state.session.current_stage"
        :render-mode="currentArticle?.render_mode || ''"
        @exit="handleExitExperiment"
      />

      <InstructionStage
        v-if="stage === 'instruction'"
        :article-order="activeArticleOrder"
        :loading="working"
        @continue="beginReading"
      />

      <ReadingStage
        v-else-if="stage === 'reading' && currentArticle"
        :key="`reading-${activeArticleOrder}`"
        :api="api"
        :session-id="sessionId"
        :article-order="activeArticleOrder"
        :article="currentArticle"
        @finished="readingFinished"
      />

      <QuestionStage
        v-else-if="questionStages.includes(stage) && currentArticle"
        :key="`${activeArticleOrder}-${stage}`"
        :api="api"
        :session-id="sessionId"
        :article-order="activeArticleOrder"
        :article="currentArticle"
        :group="stage"
        :saved-responses="state.responses"
        @saved="responseSaved"
        @completed="questionGroupFinished"
      />

      <WorkloadStage
        v-else-if="stage === 'workload'"
        :key="`workload-${activeArticleOrder}`"
        :api="api"
        :session-id="sessionId"
        :article-order="activeArticleOrder"
        @completed="refreshProgress"
      />

      <PreferenceStage
        v-else-if="stage === 'preference'"
        :api="api"
        :session-id="sessionId"
        @completed="refreshProgress"
      />

      <InterviewStage
        v-else-if="stage === 'interview'"
        :api="api"
        :session-id="sessionId"
        @completed="showCompletion"
      />

      <main v-else-if="stage === 'complete'" class="status-page complete-page">
        <section>
          <div class="check">✓</div>
          <h1>实验已完成</h1>
          <p>你的所有作答和操作数据已经保存。感谢参与！</p>
        </section>
      </main>

      <main v-else class="status-page"><p>正在同步实验状态…</p></main>
    </template>

    </template>

    <div v-if="fatalError && !isAdminRoute" class="fatal-error" role="alert">{{ fatalError }}</div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import ParticipantPicker from "./components/experiment/ParticipantPicker.vue";
import AdminLogin from "./components/admin/AdminLogin.vue";
import AdminDashboard from "./components/admin/AdminDashboard.vue";
import AdminOverview from "./components/admin/AdminOverview.vue";
import adminApi from "./admin/adminApi";
import InstructionStage from "./components/experiment/InstructionStage.vue";
import ReadingStage from "./components/experiment/ReadingStage.vue";
import QuestionStage from "./components/experiment/QuestionStage.vue";
import WorkloadStage from "./components/experiment/WorkloadStage.vue";
import PreferenceStage from "./components/experiment/PreferenceStage.vue";
import InterviewStage from "./components/experiment/InterviewStage.vue";
import ProgressHeader from "./components/experiment/ProgressHeader.vue";
import experimentApi from "./experiment/experimentApi";
import { createExperimentStore } from "./experiment/experimentStore";
import { NEXT_STAGE, QUESTION_GROUPS } from "./experiment/experimentConfig";

const api = experimentApi;
const isAdminRoute = window.location.pathname === "/admin" || window.location.pathname.startsWith("/admin/");
const isAdminAnalysisRoute = window.location.pathname === "/admin/analysis";
const adminAuthenticated = ref(false);
const adminUsername = ref("");
const store = createExperimentStore();
const state = store.state;
const booting = ref(true);
const working = ref(false);
const fatalError = ref("");
const questionStages = QUESTION_GROUPS;

const sessionId = computed(() => state.session?.session_id || "");
const stage = computed(() => state.session?.status === "completed" ? "complete" : (state.session?.current_stage || "instruction"));
const activeArticleOrder = computed(() => {
  const savedOrder = Number(state.session?.current_article_order || 0);
  if (stage.value === "instruction") return Math.min(4, Math.max(1, savedOrder + 1));
  return Math.min(4, Math.max(1, savedOrder || 1));
});
const headerArticleOrder = computed(() => ["preference", "interview", "complete"].includes(stage.value) ? 0 : activeArticleOrder.value);
const currentArticle = computed(() => state.articles.find(item => Number(item.article_order) === activeArticleOrder.value) || null);

function acceptPayload(payload) {
  store.hydrate(payload);
  fatalError.value = "";
}

async function syncRequest(operation) {
  working.value = true;
  fatalError.value = "";
  try {
    const payload = await operation();
    if (payload?.session) acceptPayload(payload);
    return payload;
  } catch (error) {
    fatalError.value = error.message;
    throw error;
  } finally {
    working.value = false;
  }
}

async function beginReading() {
  await syncRequest(() => api.advance(sessionId.value, "reading", activeArticleOrder.value));
}

async function readingFinished() {
  await refreshProgress();
}

function responseSaved(response) {
  state.responses.push({ ...response, article_order: activeArticleOrder.value, question_type: stage.value });
}

async function questionGroupFinished() {
  const next = NEXT_STAGE[stage.value];
  await syncRequest(() => api.advance(sessionId.value, next, activeArticleOrder.value));
}

async function refreshProgress() {
  await syncRequest(() => api.getSession(sessionId.value));
}

function adminLoginSuccess(username) {
  adminUsername.value = username || "admin";
  adminAuthenticated.value = true;
}

function adminLogout() {
  adminAuthenticated.value = false;
  adminUsername.value = "";
}

function showCompletion() {
  state.session = { ...state.session, status: "completed", current_stage: "complete" };
}

function handleExitExperiment() {
  // 退出当前实验，清除本地会话，回到选择页面
  // 注意：不清除 client_instance_id，用户可以选择继续之前的实验
  store.clearLocalSession();
  fatalError.value = "";
}

onMounted(async () => {
  try {
    if (isAdminRoute) {
      try {
        const result = await adminApi.me();
        adminUsername.value = result.username || "admin";
        adminAuthenticated.value = true;
      } catch (error) {
        if (error.status !== 401) fatalError.value = error.message;
      }
      return;
    }
    await store.resumeSaved();
  } finally {
    booting.value = false;
  }
});
</script>

<style>
body { margin: 0; min-width: 320px; color: #263f56; }
</style>
<style>
:root { color-scheme: light; font-family: Inter, "PingFang SC", "Microsoft YaHei", system-ui, -apple-system, sans-serif; }
* { box-sizing: border-box; }
html { background: #f4f7f9; }
button, select, textarea, input { font: inherit; }
button:focus-visible, select:focus-visible, textarea:focus-visible, input:focus-visible { outline: 3px solid rgba(41,128,145,.28); outline-offset: 2px; }
.status-page { min-height: 100vh; display: grid; place-items: center; padding: 24px; color: #536c7d; background: #f4f7f9; }
.complete-page section { width: min(560px, 100%); padding: 42px; text-align: center; border: 1px solid #d7e5e7; border-radius: 18px; background: white; box-shadow: 0 16px 48px rgba(34,70,82,.1); }
.complete-page h1 { color: #17324d; }.check { width: 72px; height: 72px; display: grid; place-items: center; margin: auto; border-radius: 50%; color: white; background: #2f8b76; font-size: 40px; }
.fatal-error { position: fixed; z-index: 100; right: 18px; bottom: 18px; max-width: 460px; padding: 12px 16px; color: #8b1e2d; background: #fff0f1; border: 1px solid #edc4ca; border-radius: 9px; box-shadow: 0 8px 24px rgba(80,30,38,.15); }
</style>
