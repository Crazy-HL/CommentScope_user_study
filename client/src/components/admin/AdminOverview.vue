<template>
  <main class="admin-dashboard admin-overview-page">
    <header class="admin-dashboard-header">
      <div>
        <div class="admin-kicker">Experiment overview</div>
        <h1>CommentScope 实验总览</h1>
        <p>登录身份：{{ username }} · {{ lastUpdatedText }}</p>
      </div>
      <div class="admin-header-actions">
        <button class="admin-secondary-button" type="button" :disabled="loading" @click="loadSummary">
          {{ loading ? "刷新中…" : "刷新数据" }}
        </button>
        <button class="admin-secondary-button" type="button" @click="logout">退出登录</button>
      </div>
    </header>

    <nav class="admin-page-nav" aria-label="管理员页面导航">
      <a class="admin-page-nav-link active" href="/admin">普通总览</a>
      <a class="admin-page-nav-link" href="/admin/analysis">论文分析</a>
    </nav>

    <div class="admin-analysis-toolbar admin-overview-toolbar">
      <label class="admin-demo-toggle"><input v-model="showDemoData" type="checkbox" /> 使用模拟数据预览</label>
      <span v-if="showDemoData" class="admin-demo-badge">当前为模拟数据，仅用于测试总览和筛选，不会写入 SQLite</span>
    </div>

    <div v-if="error" class="admin-error" role="alert">{{ error }}</div>
    <div v-if="loading && !summary" class="admin-loading">正在加载实验总览…</div>
    <template v-else>
      <section class="admin-section admin-panel admin-filter-panel" aria-label="总览筛选">
        <div class="admin-filter-heading">
          <h2>筛选数据</h2>
          <p>选择范围后，下方进度、指标和偏好统计会同步更新。</p>
        </div>
        <label class="admin-filter">
          参与者
          <select v-model="filters.participant_id" @change="handleParticipantFilterChange">
            <option value="">全部参与者</option>
            <option v-for="participant in participantOptions" :key="participant" :value="participant">{{ participant }}</option>
          </select>
        </label>
        <label class="admin-filter">
          文章
          <select v-model="filters.article_id">
            <option value="">全部文章</option>
            <option v-for="article in articleOptions" :key="article" :value="article">{{ articleDisplayLabels[article] }}</option>
          </select>
        </label>
        <label class="admin-filter">
          界面条件
          <select v-model="filters.condition">
            <option value="">全部界面</option>
            <option v-for="condition in conditions" :key="condition" :value="condition">{{ condition }}</option>
          </select>
        </label>
        <label class="admin-filter">
          文章顺序（按参与者分组）
          <select v-model="filters.article_sequence" @change="handleSequenceFilterChange">
            <option value="">全部顺序</option>
            <option v-for="sequence in articleSequenceOptions" :key="sequence.value" :value="sequence.value">{{ sequence.label }}</option>
          </select>
        </label>
        <label class="admin-filter">
          文章位置
          <select v-model="filters.article_order">
            <option value="">全部位置</option>
            <option v-for="order in articlePositionOptions" :key="order" :value="String(order)">{{ String(order).padStart(2, "0") }}</option>
          </select>
        </label>
        <label class="admin-filter">
          查看指标
          <select v-model="filters.dataSection">
            <option value="progress">实验进度</option>
            <option value="core">核心任务指标</option>
            <option value="reading">阅读与滚动</option>
            <option value="interaction">评论交互</option>
            <option value="subjective">主观评价</option>
            <option value="preference">偏好结果</option>
            <option value="interview">访谈进度</option>
          </select>
        </label>
        <label class="admin-filter">
          完成状态
          <select v-model="filters.status">
            <option value="">全部状态</option>
            <option value="active">进行中</option>
            <option value="completed">已完成</option>
          </select>
        </label>
        <div class="admin-filter-actions">
          <button class="admin-secondary-button" type="button" :disabled="loading" @click="resetFilters">清除筛选</button>
          <span class="admin-filter-status">{{ filterDescription }}</span><a v-if="filters.participant_id" class="admin-secondary-button admin-anchor-button" href="#participant-details">查看该参与者完整数据</a>
        </div>
      </section>

      <AdminParticipantOverviewTable
        v-if="showSection('progress')"
        :rows="participantOverview"
        @view-participant="selectParticipant"
      />

      <AdminParticipantDetails
        v-if="filters.participant_id"
        :participant-id="filters.participant_id"
        :details="participantDetails"
        :participant-tasks="participantTasks"
      />

      <section v-if="showSection('progress')" class="admin-section">
        <div class="admin-section-heading">
          <div>
            <h2>实验进度</h2>
            <p class="admin-section-description">当前筛选范围内的完成情况；偏好、偏好理由和访谈都是参与者级任务，目标人数为 24。</p>
          </div>
          <span class="admin-status-pill" :class="progressStatus.className">{{ progressStatus.label }}</span>
        </div>
        <div class="admin-overview-grid admin-overview-grid-expanded">
          <article v-for="card in overviewCards" :key="card.label" class="admin-stat-card">
            <span class="admin-stat-label">{{ card.label }}</span>
            <strong class="admin-stat-value">{{ card.value }}</strong>
            <span v-if="card.detail" class="admin-stat-detail">{{ card.detail }}</span>
          </article>
        </div>
      </section>

      <section v-if="showSection('progress')" class="admin-section admin-overview-columns">
        <article class="admin-panel admin-overview-callout">
          <div class="admin-kicker">Task progress</div>
          <h2>逐题回答</h2>
          <div class="admin-progress-list">
            <div v-for="item in responseProgress" :key="item.label" class="admin-progress-row">
              <span>{{ item.label }}</span><strong>{{ item.value }}</strong>
            </div>
          </div>
        </article>
        <article class="admin-panel admin-overview-callout">
          <div class="admin-kicker">Participant-level tasks</div>
          <h2>偏好与访谈</h2>
          <div class="admin-progress-list">
            <div v-for="item in participantTaskProgress" :key="item.label" class="admin-progress-row">
              <span>{{ item.label }}</span><strong>{{ item.value }}</strong>
            </div>
          </div>
        </article>
      </section>

      <section v-if="showSection('core')" class="admin-section">
        <h2>核心任务指标</h2>
        <p class="admin-section-description">按界面条件显示 CTIA、CTIRT、CRA、ACA、CLA 和 CLT 的 n、均值、中位数与标准差。</p>
        <AdminMetricSummaryTable :groups="metricGroups.core" :metrics="metrics" :conditions="visibleConditions" />
      </section>

      <section v-if="showSection('reading')" class="admin-section">
        <h2>阅读与滚动</h2>
        <p class="admin-section-description">用于查看阅读耗时、滚动距离和页面导航行为。</p>
        <AdminMetricSummaryTable :groups="metricGroups.reading" :metrics="metrics" :conditions="visibleConditions" />
      </section>

      <section v-if="showSection('interaction')" class="admin-section">
        <h2>评论交互</h2>
        <p class="admin-section-description">保留不同界面下的评论点击、打开、关闭和段落评论操作统计。</p>
        <AdminMetricSummaryTable :groups="metricGroups.interaction" :metrics="metrics" :conditions="visibleConditions" />
      </section>

      <section v-if="showSection('subjective')" class="admin-section">
        <h2>主观评价</h2>
        <p class="admin-section-description">NASA-TLX 六个维度、Reading Continuity 和 Comment Accessibility 的描述性统计。</p>
        <AdminMetricSummaryTable :groups="metricGroups.subjective" :metrics="metrics" :conditions="visibleConditions" />
      </section>

      <section v-if="showSection('preference')" class="admin-section">
        <h2>偏好结果</h2>
        <p class="admin-section-description">偏好排序和首选界面属于参与者级数据；筛选文章或顺序时，统计的是筛选范围内相关参与者的结果。</p>
        <div class="admin-simple-table-wrap">
          <table class="admin-simple-table admin-detail-table">
            <thead><tr><th>界面</th><th>排名 n</th><th>平均排名</th><th>中位数</th><th>第一名次数</th><th>最后一名次数</th><th>首选次数</th></tr></thead>
            <tbody>
              <tr v-for="condition in visibleConditions" :key="condition">
                <th scope="row"><span class="condition-badge" :class="`condition-${condition.toLowerCase()}`">{{ condition }}</span></th>
                <td>{{ preference.rank?.[condition]?.n ?? 0 }}</td>
                <td>{{ formatNumber(preference.rank?.[condition]?.mean, 2) }}</td>
                <td>{{ formatNumber(preference.rank?.[condition]?.median, 2) }}</td>
                <td>{{ preference.rank_one?.[condition] ?? 0 }}</td>
                <td>{{ preference.rank_four?.[condition] ?? 0 }}</td>
                <td>{{ preference.preferred_condition?.[condition] ?? 0 }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section v-if="showSection('interview')" class="admin-section admin-overview-columns">
        <article class="admin-panel admin-overview-callout">
          <div class="admin-kicker">Interview status</div>
          <h2>半结构化访谈</h2>
          <p>访谈为每位参与者一次，不按文章区块重复计算。</p>
          <strong class="admin-large-progress">{{ overview.interviews || 0 }} / {{ overview.interviews_expected || 24 }}</strong>
        </article>
        <article class="admin-panel admin-overview-callout">
          <div class="admin-kicker">Scope</div>
          <h2>当前统计范围</h2>
          <ul class="admin-overview-list">
            <li>已开始参与者：{{ overview.participants_started || 0 }} / {{ overview.expected_participants || 24 }}</li>
            <li>已完成文章区块：{{ overview.article_sessions_completed || 0 }} / {{ overview.article_sessions_expected || 96 }}</li>
            <li>默认排除已重置会话</li>
          </ul>
        </article>
      </section>

      <section v-if="filters.dataSection === 'all'" class="admin-section">
        <h2>四种界面快速比较</h2>
        <p class="admin-section-description">下面是核心指标的平均值；详细 n、均值、中位数和标准差见上方各数据表。</p>
        <div class="admin-simple-table-wrap">
          <table class="admin-simple-table">
            <thead><tr><th>界面</th><th>CTIA<br><span>正文—评论关联</span></th><th>CTIRT<br><span>关联时间</span></th><th>CRA<br><span>评论记忆</span></th><th>ACA<br><span>正文理解</span></th><th>RC<br><span>阅读连续性</span></th><th>CA<br><span>评论可访问性</span></th></tr></thead>
            <tbody>
              <tr v-for="condition in visibleConditions" :key="condition">
                <th scope="row"><span class="condition-badge" :class="`condition-${condition.toLowerCase()}`">{{ condition }}</span></th>
                <td>{{ metricValue("CTIA", condition, formatAccuracy) }}</td>
                <td>{{ metricValue("CTIRT", condition, formatSeconds, " 秒") }}</td>
                <td>{{ metricValue("CRA", condition, formatAccuracy) }}</td>
                <td>{{ metricValue("ACA", condition, formatAccuracy) }}</td>
                <td>{{ metricValue("RC", condition, formatRating) }}</td>
                <td>{{ metricValue("CA", condition, formatRating) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="admin-section admin-overview-columns">
        <article class="admin-panel admin-overview-callout">
          <div class="admin-kicker">What to do next</div>
          <h2>需要论文统计时</h2>
          <p>进入论文分析页查看条件比较图、均值/中位数、95% CI、数据质量提示和描述性结果文字。</p>
          <a class="admin-primary-button admin-link-button" href="/admin/analysis">打开论文分析页</a>
        </article>
        <article class="admin-panel admin-overview-callout">
          <div class="admin-kicker">Data status</div>
          <h2>当前数据范围</h2>
          <ul class="admin-overview-list">
            <li>已开始参与者：{{ overview.participants_started || 0 }} / {{ overview.expected_participants || 24 }}</li>
            <li>已完成文章区块：{{ overview.article_sessions_completed || 0 }} / {{ overview.article_sessions_expected || 96 }}</li>
            <li>已提交逐题回答：{{ overview.responses?.total || 0 }} / 960</li>
            <li>偏好排序：{{ overview.preferences || 0 }} / {{ overview.preferences_expected || 24 }}</li>
            <li>访谈：{{ overview.interviews || 0 }} / {{ overview.interviews_expected || 24 }}</li>
          </ul>
        </article>
      </section>
    </template>
  </main>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue";
import adminApi from "../../admin/adminApi";
import AdminMetricSummaryTable from "./AdminMetricSummaryTable.vue";
import AdminParticipantDetails from "./AdminParticipantDetails.vue";
import AdminParticipantOverviewTable from "./AdminParticipantOverviewTable.vue";
import { DEMO_OVERVIEW_SUMMARY, buildDemoOverviewSummary } from "../../admin/adminDemoData";
import "./admin.css";

const props = defineProps({ username: { type: String, default: "admin" } });
const emit = defineEmits(["logout"]);
const conditions = ["TE", "CS", "SE", "BL"];
const articleDisplayLabels = { A02: "01", A03: "02", A04: "03", A07: "04" };
const articleOptions = Object.keys(articleDisplayLabels);
const articleSequenceOptions = [
  { value: "01-02-03-04", label: "01 → 02 → 03 → 04" },
  { value: "02-03-04-01", label: "02 → 03 → 04 → 01" },
  { value: "03-04-01-02", label: "03 → 04 → 01 → 02" },
  { value: "04-01-02-03", label: "04 → 01 → 02 → 03" },
];
const articlePositionOptions = [1, 2, 3, 4];
const summary = ref(null);
const showDemoData = ref(false);
const loading = ref(false);
const error = ref("");
const filters = reactive({ participant_id: "", article_id: "", condition: "", article_sequence: "", article_order: "", status: "", dataSection: "progress" });

const metricGroups = {
  core: [
    { name: "CTIA", label: "CTIA — 正文—评论关联正确率" },
    { name: "CTIRT", label: "CTIRT — 正文—评论关联时间", unit: "ms" },
    { name: "CRA", label: "CRA — 评论识别正确率" },
    { name: "ACA", label: "ACA — 正文理解正确率" },
    { name: "CLA", label: "CLA — 评论定位正确率" },
    { name: "CLT", label: "CLT — 评论定位时间", unit: "ms" },
  ],
  reading: [
    { name: "Initial Reading Time", label: "Initial Reading Time — 初始阅读时间", unit: "ms" },
    { name: "NSD", label: "NSD — 归一化滚动距离" },
    { name: "Scroll Events", label: "Scroll Events — 滚动次数" },
    { name: "Total Scroll Distance", label: "Total Scroll Distance — 总滚动距离", unit: "px" },
    { name: "Max Scroll Y", label: "Max Scroll Y — 最大滚动位置", unit: "px" },
  ],
  interaction: [
    { name: "Comment Interaction Count", label: "Comment Interaction Count — 评论交互次数" },
    { name: "Comment Click Count", label: "Comment Click Count — 评论点击次数" },
    { name: "Comment Open Count", label: "Comment Open Count — 评论打开次数" },
    { name: "Comment Close Count", label: "Comment Close Count — 评论关闭次数" },
    { name: "Paragraph Toggle Count", label: "Paragraph Toggle Count — 段落评论操作次数" },
  ],
  subjective: [
    { name: "NASA-TLX Mental Demand", label: "NASA-TLX Mental Demand — 心理需求" },
    { name: "NASA-TLX Physical Demand", label: "NASA-TLX Physical Demand — 生理需求" },
    { name: "NASA-TLX Temporal Demand", label: "NASA-TLX Temporal Demand — 时间需求" },
    { name: "NASA-TLX Performance", label: "NASA-TLX Performance — 自我表现" },
    { name: "NASA-TLX Effort", label: "NASA-TLX Effort — 努力程度" },
    { name: "NASA-TLX Frustration", label: "NASA-TLX Frustration — 挫败感" },
    { name: "RC", label: "RC — 阅读连续性" },
    { name: "CA", label: "CA — 评论可访问性" },
  ],
};

const effectiveSummary = computed(() => showDemoData.value ? buildDemoOverviewSummary(apiFilters.value) : summary.value);
const overview = computed(() => effectiveSummary.value?.overview || {});
const metrics = computed(() => effectiveSummary.value?.metrics || {});
const preference = computed(() => effectiveSummary.value?.preference || {});
const participantDetails = computed(() => effectiveSummary.value?.participant_details || []);
const participantOverview = computed(() => effectiveSummary.value?.participant_overview || []);
const participantTasks = computed(() => effectiveSummary.value?.participant_tasks || []);
const participantOptions = computed(() => effectiveSummary.value?.filter_options?.participants || []);
const lastUpdatedText = computed(() => effectiveSummary.value?.last_updated_at ? `最近活动：${effectiveSummary.value.last_updated_at}` : "暂无实验数据");
const visibleConditions = computed(() => filters.condition ? [filters.condition] : conditions);
const apiFilters = computed(() => {
  const next = Object.fromEntries(Object.entries(filters).filter(([key, value]) => key !== "dataSection" && value));
  // Article sequence means all participants in that allocation group. Do not
  // let stale participant state narrow this group-wide query.
  if (next.article_sequence) delete next.participant_id;
  return next;
});
const filterDescription = computed(() => {
  const parts = [];
  if (filters.participant_id) parts.push(filters.participant_id);
  if (filters.article_id) parts.push(`文章 ${articleDisplayLabels[filters.article_id] || filters.article_id}`);
  if (filters.condition) parts.push(filters.condition);
  if (filters.article_sequence) {
    const sequence = articleSequenceOptions.find(item => item.value === filters.article_sequence);
    parts.push(sequence?.label || filters.article_sequence);
  }
  if (filters.article_order) parts.push(`位置 ${String(filters.article_order).padStart(2, "0")}`);
  if (filters.status) parts.push(filters.status === "completed" ? "已完成" : "进行中");
  return parts.length ? `当前：${parts.join(" / ")}` : "当前：全部未重置数据";
});
const progressStatus = computed(() => {
  const completed = Number(overview.value.article_sessions_completed || 0);
  const expected = Number(overview.value.article_sessions_expected || 96);
  if (!completed) return { label: "尚未开始", className: "status-empty" };
  if (completed >= expected) return { label: "已完成", className: "status-complete" };
  return { label: "进行中", className: "status-active" };
});
const overviewCards = computed(() => [
  { label: "已开始参与者", value: `${overview.value.participants_started || 0} / ${overview.value.expected_participants || 24}`, detail: "参与者编号已分配" },
  { label: "已完成参与者", value: `${overview.value.participants_completed || 0} / ${overview.value.expected_participants || 24}`, detail: "完成全部实验流程" },
  { label: "文章实验区块", value: `${overview.value.article_sessions_completed || 0} / ${overview.value.article_sessions_expected || 96}`, detail: "参与者 × 文章" },
  { label: "逐题回答", value: `${overview.value.responses?.total || 0} / 960`, detail: "CRA、ACA、CTI、定位" },
  { label: "主观评价", value: `${overview.value.surveys || 0} / ${overview.value.surveys_expected || 96}`, detail: "NASA-TLX、RC、CA" },
  { label: "偏好排序", value: `${overview.value.preferences || 0} / ${overview.value.preferences_expected || 24}`, detail: "每位参与者一次" },
  { label: "偏好理由", value: `${overview.value.preference_reason_submitted || 0} / ${overview.value.preference_reasons_expected || 24}`, detail: "每位参与者一次" },
  { label: "半结构化访谈", value: `${overview.value.interviews || 0} / ${overview.value.interviews_expected || 24}`, detail: "每位参与者一次" },
]);
const responseProgress = computed(() => [
  { label: "CRA 评论识别", value: `${overview.value.responses?.cra || 0} / 384` },
  { label: "ACA 正文理解", value: `${overview.value.responses?.aca || 0} / 192` },
  { label: "CTI 正文—评论关联", value: `${overview.value.responses?.cti || 0} / 192` },
  { label: "评论定位", value: `${overview.value.responses?.location || 0} / 192` },
]);
const participantTaskProgress = computed(() => [
  { label: "偏好排序", value: `${overview.value.preferences || 0} / ${overview.value.preferences_expected || 24}` },
  { label: "偏好理由", value: `${overview.value.preference_reason_submitted || 0} / ${overview.value.preference_reasons_expected || 24}` },
  { label: "半结构化访谈", value: `${overview.value.interviews || 0} / ${overview.value.interviews_expected || 24}` },
]);

function showSection(section) { return filters.dataSection === "all" || filters.dataSection === section; }
function formatAccuracy(value) { return formatNumber(value, 2); }
function formatRating(value) { return formatNumber(value, 1); }
function formatSeconds(value) { return formatNumber(Number(value) / 1000, 2); }
function formatNumber(value, digits = 2) { return value == null || Number.isNaN(Number(value)) ? "—" : Number(value).toFixed(digits); }
function metricValue(name, condition, formatter, suffix = "") {
  const item = metrics.value[name]?.[condition];
  return item?.mean == null ? "—" : `${formatter(item.mean)}${suffix}`;
}
function formatMetricStat(name, value) {
  if (value == null) return "—";
  if (["CTIRT", "CLT", "Initial Reading Time"].includes(name)) return `${formatSeconds(value)} s`;
  if (name === "NSD") return formatNumber(value, 3);
  if (["CTIA", "CRA", "ACA", "CLA"].includes(name)) return formatAccuracy(value);
  if (["RC", "CA"].includes(name)) return formatRating(value);
  return formatNumber(value, 2);
}
function resetFilters() {
  Object.assign(filters, { participant_id: "", article_id: "", condition: "", article_sequence: "", article_order: "", status: "", dataSection: "progress" });
}

function selectParticipant(participantId) {
  filters.participant_id = participantId;
  filters.article_sequence = "";
}

function handleParticipantFilterChange() {
  // A participant filter is an individual scope, while article sequence is a
  // participant-group scope. They must not remain active together.
  if (filters.participant_id) filters.article_sequence = "";
}

function handleSequenceFilterChange() {
  // Selecting a complete sequence means "all participants assigned to this
  // sequence", not the participant that happened to be selected previously.
  if (filters.article_sequence) filters.participant_id = "";
}
async function loadSummary() {
  loading.value = true;
  error.value = "";
  try {
    if (showDemoData.value) {
      summary.value = DEMO_OVERVIEW_SUMMARY;
      return;
    }
    summary.value = await adminApi.summary(apiFilters.value);
  } catch (requestError) {
    if (requestError.status === 401) { emit("logout"); return; }
    error.value = requestError.message;
  } finally {
    loading.value = false;
  }
}
async function logout() {
  try { await adminApi.logout(); } finally { emit("logout"); }
}

watch(apiFilters, loadSummary, { deep: true });
watch(showDemoData, loadSummary);
onMounted(loadSummary);
</script>

