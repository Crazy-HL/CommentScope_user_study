<template>
  <div class="admin-workspace-shell">
    <!-- 左侧固定导航栏 -->
    <nav class="admin-workspace-nav" aria-label="论文分析区块导航">
      <div class="admin-workspace-nav-title">研究分析工作台</div>
      <a
        v-for="item in navItems"
        :key="item.id"
        class="admin-workspace-nav-link"
        :class="{ active: activeSection === item.id }"
        :href="`#${item.id}`"
        @click.prevent="scrollToSection(item.id)"
      >{{ item.label }}</a>
    </nav>

    <!-- 主内容区 -->
    <main class="admin-dashboard admin-workspace-main">
      <header class="admin-dashboard-header">
        <div>
          <div class="admin-kicker">Research workspace</div>
          <h1>CommentScope 研究分析工作台</h1>
          <p>登录身份：{{ username }} · {{ lastUpdatedText }}</p>
        </div>
        <div class="admin-header-actions">
          <!-- 顶部快速导出下拉 -->
          <div class="admin-quick-export" :class="{ open: exportMenuOpen }">
            <button class="admin-secondary-button" type="button" @click="exportMenuOpen = !exportMenuOpen">
              导出数据 ▾
            </button>
            <div v-if="exportMenuOpen" class="admin-quick-export-menu">
              <button type="button" @click="quickExport('csv', 'analysis')">导出分析 CSV</button>
              <button type="button" @click="quickExport('json', 'analysis')">导出分析 JSON</button>
              <button type="button" @click="quickExport('csv', 'events')">导出原始事件 CSV</button>
              <button type="button" @click="quickExport('json', 'events')">导出原始事件 JSON</button>
            </div>
          </div>
          <button class="admin-secondary-button" type="button" :disabled="loading" @click="loadAll">{{ loading ? "刷新中…" : "刷新数据" }}</button>
          <button class="admin-secondary-button" type="button" @click="logout">退出登录</button>
        </div>
      </header>

      <nav class="admin-page-nav" aria-label="管理员页面导航">
        <a class="admin-page-nav-link" href="/admin">普通总览</a>
        <a class="admin-page-nav-link active" href="/admin/analysis">论文分析</a>
      </nav>

      <div class="admin-analysis-toolbar">
        <label class="admin-demo-toggle"><input v-model="showDemoData" type="checkbox" /> 使用模拟数据预览论文图表</label>
        <span v-if="showDemoData" class="admin-demo-badge">当前为模拟数据，仅用于视觉预览，不会写入 SQLite</span>
      </div>

      <div v-if="error" class="admin-error" role="alert">{{ error }}</div>
      <div v-if="loading && !summary" class="admin-loading">正在加载管理员统计…</div>
      <template v-else>
        <!-- 实验总览 -->
        <section id="section-overview" class="admin-section admin-workspace-section">
          <h2>实验总览</h2>
          <div class="admin-overview-grid">
            <article v-for="card in overviewCards" :key="card.label" class="admin-stat-card">
              <span class="admin-stat-label">{{ card.label }}</span>
              <strong class="admin-stat-value">{{ card.value }}</strong>
            </article>
          </div>
        </section>

        <!-- 筛选器（移到顶部） -->
        <section id="section-filters" class="admin-section admin-workspace-section">
          <h2>筛选数据范围</h2>
          <div class="admin-panel admin-filter-panel">
            <label class="admin-filter">参与者
              <select v-model="filters.participant_id">
                <option value="">全部参与者</option>
                <option v-for="participant in participantOptions" :key="participant" :value="participant">{{ participant }}</option>
              </select>
            </label>
            <label class="admin-filter">文章
              <select v-model="filters.article_id"><option value="">全部文章</option><option v-for="article in articles" :key="article" :value="article">{{ article }}</option></select>
            </label>
            <label class="admin-filter">条件
              <select v-model="filters.condition"><option value="">全部条件</option><option v-for="condition in conditions" :key="condition" :value="condition">{{ condition }}</option></select>
            </label>
            <label class="admin-filter">文章区块状态
              <select v-model="filters.status"><option value="">全部状态</option><option value="completed">completed</option><option value="active">active</option></select>
            </label>
            <div class="admin-filter-actions"><button class="admin-primary-button" type="button" @click="loadAll">应用筛选</button><button class="admin-secondary-button" type="button" @click="clearFilters">清除</button></div>
          </div>
        </section>

        <!-- 论文风格统计图 -->
        <section id="section-academic-overall" class="admin-section admin-workspace-section">
          <div class="admin-collapsible-heading" @click="toggleSection('academicOverall')">
            <div>
              <h2>论文风格统计图</h2>
              <p class="admin-section-description">整体条件比较和任务级准确率按照论文图表风格展示：保留参与者级散点、中心趋势和误差范围。</p>
            </div>
            <span class="admin-collapse-icon">{{ collapsedSections.academicOverall ? "▶" : "▼" }}</span>
            <span v-if="showDemoData" class="admin-status-pill status-active">演示数据</span>
          </div>
          <div v-show="!collapsedSections.academicOverall">
            <AdminAcademicOverallChart :overall-time="academicChartData.overallTime" :overall-accuracy="academicChartData.overallAccuracy" />
            <AdminAcademicTaskChart :task-accuracy="academicChartData.taskAccuracy" />
          </div>
        </section>

        <!-- 核心结果图 -->
        <section id="section-core" class="admin-section admin-workspace-section">
          <div class="admin-collapsible-heading" @click="toggleSection('core')">
            <div>
              <h2>核心结果图</h2>
              <p class="admin-section-description">CTIA/CTIRT 直接反映参与者建立正文—评论关系的准确率与反应时间；CLA/CLT 反映评论定位表现。</p>
            </div>
            <span class="admin-collapse-icon">{{ collapsedSections.core ? "▶" : "▼" }}</span>
          </div>
          <div v-show="!collapsedSections.core">
            <!-- 核心结果摘要卡片 -->
            <div class="admin-core-summary-grid">
              <article v-for="card in coreSummaryCards" :key="card.metric" class="admin-panel admin-core-summary-card">
                <span class="admin-stat-label">{{ card.label }}</span>
                <strong class="admin-core-summary-value">{{ card.value }}</strong>
                <span class="admin-core-summary-n">n = {{ card.n }}</span>
              </article>
            </div>
            <div class="admin-metric-grid"><AdminAcademicMetricChart v-for="item in coreMetrics" :key="item.name" :title="item.title" :metric="item.name" :series="academicMetricSeries(item.name)" :format="item.format" :higher-is-better="item.higherIsBetter" :unit="item.unit" :chart-type="item.chartType" :domain="item.domain" :ticks="item.ticks" /></div>
          </div>
        </section>

        <!-- 任务表现图 -->
        <section id="section-task" class="admin-section admin-workspace-section">
          <div class="admin-collapsible-heading" @click="toggleSection('task')">
            <h2>任务表现图</h2>
            <span class="admin-collapse-icon">{{ collapsedSections.task ? "▶" : "▼" }}</span>
          </div>
          <div v-show="!collapsedSections.task">
            <div class="admin-metric-grid"><AdminAcademicMetricChart v-for="item in taskMetrics" :key="item.name" :title="item.title" :metric="item.name" :series="academicMetricSeries(item.name)" :format="item.format" :higher-is-better="item.higherIsBetter" :unit="item.unit" :chart-type="item.chartType" :domain="item.domain" :ticks="item.ticks" /></div>
          </div>
        </section>

        <!-- 阅读行为图 -->
        <section id="section-reading" class="admin-section admin-workspace-section">
          <div class="admin-collapsible-heading" @click="toggleSection('reading')">
            <div>
              <h2>阅读行为图</h2>
              <p class="admin-section-description">阅读时间、滚动距离和滚动事件用于描述阅读过程与页面导航，不作为核心因果结论。</p>
            </div>
            <span class="admin-collapse-icon">{{ collapsedSections.reading ? "▶" : "▼" }}</span>
          </div>
          <div v-show="!collapsedSections.reading">
            <div class="admin-metric-grid"><AdminAcademicMetricChart v-for="item in readingMetrics" :key="item.name" :title="item.title" :metric="item.name" :series="academicMetricSeries(item.name)" :format="item.format" :higher-is-better="item.higherIsBetter" :unit="item.unit" :chart-type="item.chartType" :domain="item.domain" :ticks="item.ticks" /></div>
          </div>
        </section>

        <!-- 评论交互图 -->
        <section id="section-interaction" class="admin-section admin-workspace-section">
          <div class="admin-collapsible-heading" @click="toggleSection('interaction')">
            <div>
              <h2>评论交互图</h2>
              <p class="admin-section-description">保留不同呈现条件下的点击、打开、关闭和段落交互语义，辅助解释评论使用行为。</p>
            </div>
            <span class="admin-collapse-icon">{{ collapsedSections.interaction ? "▶" : "▼" }}</span>
          </div>
          <div v-show="!collapsedSections.interaction">
            <div class="admin-metric-grid"><AdminAcademicMetricChart v-for="item in interactionMetrics" :key="item.name" :title="item.title" :metric="item.name" :series="academicMetricSeries(item.name)" :format="item.format" :higher-is-better="item.higherIsBetter" :unit="item.unit" :chart-type="item.chartType" :domain="item.domain" :ticks="item.ticks" /></div>
          </div>
        </section>

        <!-- 主观评价图 -->
        <section id="section-subjective" class="admin-section admin-workspace-section">
          <div class="admin-collapsible-heading" @click="toggleSection('subjective')">
            <div>
              <h2>主观评价图</h2>
              <p class="admin-section-description">NASA-TLX 六个维度合并为 2×3 参与者散点图；Reading Continuity 与 Comment Accessibility 单独用双面板散点图展示。</p>
            </div>
            <span class="admin-collapse-icon">{{ collapsedSections.subjective ? "▶" : "▼" }}</span>
          </div>
          <div v-show="!collapsedSections.subjective">
            <AdminAcademicSubjectiveChart title="NASA-TLX 六维度" :metrics="subjectiveMetrics.slice(2)" :series-by-metric="subjectiveChartSeries" />
            <AdminAcademicSubjectiveChart title="Reading Continuity & Comment Accessibility" :metrics="subjectiveMetrics.slice(0, 2)" :series-by-metric="continuityChartSeries" />
          </div>
        </section>

        <!-- 偏好结果图 -->
        <section id="section-preference" class="admin-section admin-workspace-section">
          <div class="admin-collapsible-heading" @click="toggleSection('preference')">
            <div>
              <h2>偏好结果图</h2>
              <p class="admin-section-description">平均排名和第一名比例用于展示四种界面的总体偏好；偏好理由全文仍通过数据导出查看。</p>
            </div>
            <span class="admin-collapse-icon">{{ collapsedSections.preference ? "▶" : "▼" }}</span>
          </div>
          <div v-show="!collapsedSections.preference">
            <div class="admin-metric-grid"><AdminAcademicMetricChart title="Preference Ranking · 平均排名" metric="Preference Ranking" :series="preferenceChartData.meanRank" :format="formatNumber" :higher-is-better="false" chart-type="horizontal-bar" :domain="[1, 4]" :ticks="[1, 2, 3, 4]" /><AdminAcademicMetricChart title="First-place Share · 第一名比例" metric="First-place Share" :series="preferenceChartData.firstPlaceShare" :format="formatAccuracy" :higher-is-better="true" chart-type="horizontal-bar" :domain="[0, 1]" :ticks="[0, 0.25, 0.5, 0.75, 1]" /></div>
            <div class="admin-preference-grid"><article v-for="condition in conditions" :key="condition" class="admin-preference-card"><strong>{{ condition }}</strong><span>平均排名：{{ preferenceRank(condition) }}</span><span>第一名：{{ preference.rank_one?.[condition] || 0 }} 次</span><span>最后一名：{{ preference.rank_four?.[condition] || 0 }} 次</span></article></div>
            <p class="admin-muted">已提交偏好：{{ preference.submitted || 0 }}</p>
          </div>
        </section>

        <!-- 描述性结果分析 -->
        <section id="section-analysis" class="admin-section admin-workspace-section">
          <div class="admin-collapsible-heading" @click="toggleSection('analysis')">
            <h2>描述性结果分析</h2>
            <span class="admin-collapse-icon">{{ collapsedSections.analysis ? "▶" : "▼" }}</span>
          </div>
          <div v-show="!collapsedSections.analysis">
            <div v-if="analysisStatements.length" class="admin-analysis-list"><article v-for="statement in analysisStatements" :key="`${statement.metric}-${statement.text}`" class="admin-analysis-item"><strong>{{ statement.metric }}</strong><p>{{ statement.text }}</p></article></div>
            <p v-else class="admin-empty">暂无分析文字。</p>
          </div>
        </section>

        <!-- 数据完整性 -->
        <section id="section-quality" class="admin-section admin-workspace-section">
          <div class="admin-collapsible-heading" @click="toggleSection('quality')">
            <h2>数据完整性</h2>
            <span class="admin-collapse-icon">{{ collapsedSections.quality ? "▶" : "▼" }}</span>
          </div>
          <div v-show="!collapsedSections.quality">
            <div v-if="qualityIssues.length" class="admin-quality-list"><article v-for="issue in qualityIssues" :key="`${issue.code}-${issue.message}`" :class="['admin-quality-item', issue.severity]"><p><strong>{{ issue.code }}</strong> · {{ issue.message }}（{{ issue.count }}）</p></article></div>
            <p v-else class="admin-quality-item info"><strong>当前范围未发现数据完整性问题。</strong></p>
          </div>
        </section>

        <!-- 数据操作 -->
        <section id="section-operations" class="admin-section admin-workspace-section">
          <div class="admin-collapsible-heading" @click="toggleSection('operations')">
            <h2>数据操作</h2>
            <span class="admin-collapse-icon">{{ collapsedSections.operations ? "▶" : "▼" }}</span>
          </div>
          <div v-show="!collapsedSections.operations">
            <div class="admin-panel admin-button-row">
              <button class="admin-secondary-button" type="button" @click='download("csv", "analysis")'>导出分析 CSV</button>
              <button class="admin-secondary-button" type="button" @click='download("json", "analysis")'>导出分析 JSON</button>
              <button class="admin-secondary-button" type="button" @click='download("csv", "events")'>导出原始事件 CSV</button>
              <button class="admin-secondary-button" type="button" @click='download("json", "events")'>导出原始事件 JSON</button>
            </div>
            <div class="admin-danger-panel" style="margin-top: 12px;"><label>重置参与者<select v-model="resetParticipantId" class="admin-reset-select"><option value="">请选择参与者</option><option v-for="participant in participantOptions" :key="participant" :value="participant">{{ participant }}</option></select></label><button class="admin-danger-button" type="button" :disabled="!resetParticipantId || resetting" @click="resetParticipant">{{ resetting ? "重置中…" : "重置参与者" }}</button></div>
          </div>
        </section>
      </template>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from "vue";
import adminApi from "../../admin/adminApi";
import AdminAcademicMetricChart from "./AdminAcademicMetricChart.vue";
import AdminAcademicOverallChart from "./AdminAcademicOverallChart.vue";
import AdminAcademicTaskChart from "./AdminAcademicTaskChart.vue";
import AdminAcademicSubjectiveChart from "./AdminAcademicSubjectiveChart.vue";
import { DEMO_ACADEMIC_DATA, DEMO_ACADEMIC_METRICS, DEMO_PREFERENCE_DATA, buildAcademicDataFromSummary, buildMetricSeriesFromSummary, buildPreferenceSeriesFromSummary } from "../../admin/adminDemoData";
import "./admin.css";
import "./admin-dashboard.css";

const props = defineProps({ username: { type: String, default: "admin" } });
const emit = defineEmits(["logout"]);
const conditions = ["TE", "CS", "SE", "BL"];
const articles = ["A02", "A03", "A04", "A07"];
const filters = ref({ participant_id: "", article_id: "", condition: "", status: "" });
const summary = ref(null);
const analysis = ref(null);
const quality = ref(null);
const loading = ref(false);
const resetting = ref(false);
const error = ref("");
const resetParticipantId = ref("");
const showDemoData = ref(false);
const exportMenuOpen = ref(false);
const activeSection = ref("section-overview");

const collapsedSections = reactive({
  academicOverall: false,
  core: false,
  task: false,
  reading: false,
  interaction: false,
  subjective: false,
  preference: false,
  analysis: false,
  quality: false,
  operations: false,
});

const navItems = [
  { id: "section-overview", label: "实验总览" },
  { id: "section-filters", label: "筛选数据" },
  { id: "section-academic-overall", label: "论文风格统计图" },
  { id: "section-core", label: "核心结果图" },
  { id: "section-task", label: "任务表现图" },
  { id: "section-reading", label: "阅读行为图" },
  { id: "section-interaction", label: "评论交互图" },
  { id: "section-subjective", label: "主观评价图" },
  { id: "section-preference", label: "偏好结果图" },
  { id: "section-analysis", label: "描述性结果分析" },
  { id: "section-quality", label: "数据完整性" },
  { id: "section-operations", label: "数据操作" },
];

const coreMetrics = [
  { name: "CTIA", title: "CTIA · 正文—评论关联准确率", format: formatAccuracy, higherIsBetter: true, chartType: "scatter", domain: [0, 1] },
  { name: "CTIRT", title: "CTIRT · 正文—评论关联反应时间", format: formatSeconds, higherIsBetter: false, chartType: "scatter" }
];
const taskMetrics = [
  { name: "CRA", title: "CRA · 评论自然记忆", format: formatAccuracy, higherIsBetter: true, chartType: "bar", domain: [0, 1], ticks: [0, 0.25, 0.5, 0.75, 1] },
  { name: "ACA", title: "ACA · 正文理解", format: formatAccuracy, higherIsBetter: true, chartType: "bar", domain: [0, 1], ticks: [0, 0.25, 0.5, 0.75, 1] },
  { name: "CLA", title: "CLA · 评论定位准确率", format: formatAccuracy, higherIsBetter: true, chartType: "bar", domain: [0, 1], ticks: [0, 0.25, 0.5, 0.75, 1] },
  { name: "CLT", title: "CLT · 评论定位时间", format: formatSeconds, higherIsBetter: false, chartType: "boxplot" }
];
const readingMetrics = [
  { name: "Initial Reading Time", title: "Initial Reading Time · 初始阅读时间", format: formatSeconds, higherIsBetter: false, chartType: "boxplot" },
  { name: "NSD", title: "NSD · 归一化滚动距离", format: formatNumber, higherIsBetter: false, chartType: "boxplot" },
  { name: "Scroll Events", title: "Scroll Events · 滚动事件数", format: formatNumber, higherIsBetter: false, chartType: "boxplot" },
  { name: "Total Scroll Distance", title: "Total Scroll Distance · 总滚动距离", format: formatNumber, higherIsBetter: false, chartType: "boxplot" },
  { name: "Max Scroll Y", title: "Max Scroll Y · 最大滚动位置", format: formatNumber, higherIsBetter: false, chartType: "boxplot" }
];
const interactionMetrics = [
  { name: "Comment Interaction Count", title: "Comment Interaction Count · 评论交互次数", format: formatNumber, higherIsBetter: false, chartType: "bar" },
  { name: "Comment Click Count", title: "Comment Click Count · 评论点击次数", format: formatNumber, higherIsBetter: false, chartType: "bar" },
  { name: "Comment Open Count", title: "Comment Open Count · 评论打开次数", format: formatNumber, higherIsBetter: false, chartType: "bar" },
  { name: "Comment Close Count", title: "Comment Close Count · 评论关闭次数", format: formatNumber, higherIsBetter: false, chartType: "bar" },
  { name: "Paragraph Toggle Count", title: "Paragraph Toggle Count · 段落交互次数", format: formatNumber, higherIsBetter: false, chartType: "bar" }
];
const subjectiveMetrics = [
  { name: "RC", title: "Reading Continuity", axisTitle: "Reading Continuity (1–7)", format: formatRating, higherIsBetter: true, chartType: "scatter", domain: [1, 7], ticks: [1, 2, 3, 4, 5, 6, 7] },
  { name: "CA", title: "Comment Accessibility", axisTitle: "Comment Accessibility (1–7)", format: formatRating, higherIsBetter: true, chartType: "scatter", domain: [1, 7], ticks: [1, 2, 3, 4, 5, 6, 7] },
  { name: "NASA-TLX Mental Demand", title: "Mental Demand", axisTitle: "Mental Demand (1–7)", format: formatNumber, higherIsBetter: false, chartType: "scatter", domain: [1, 7], ticks: [1, 2, 3, 4, 5, 6, 7] },
  { name: "NASA-TLX Physical Demand", title: "Physical Demand", axisTitle: "Physical Demand (1–7)", format: formatNumber, higherIsBetter: false, chartType: "scatter", domain: [1, 7], ticks: [1, 2, 3, 4, 5, 6, 7] },
  { name: "NASA-TLX Temporal Demand", title: "Temporal Demand", axisTitle: "Temporal Demand (1–7)", format: formatNumber, higherIsBetter: false, chartType: "scatter", domain: [1, 7], ticks: [1, 2, 3, 4, 5, 6, 7] },
  { name: "NASA-TLX Performance", title: "Performance", axisTitle: "Performance (1–7)", format: formatNumber, higherIsBetter: false, chartType: "scatter", domain: [1, 7], ticks: [1, 2, 3, 4, 5, 6, 7] },
  { name: "NASA-TLX Effort", title: "Effort", axisTitle: "Effort (1–7)", format: formatNumber, higherIsBetter: false, chartType: "scatter", domain: [1, 7], ticks: [1, 2, 3, 4, 5, 6, 7] },
  { name: "NASA-TLX Frustration", title: "Frustration", axisTitle: "Frustration (1–7)", format: formatNumber, higherIsBetter: false, chartType: "scatter", domain: [1, 7], ticks: [1, 2, 3, 4, 5, 6, 7] }
];

const participantOptions = computed(() => {
  const ids = new Set();
  for (const item of quality.value?.issues || []) for (const id of item.affected || []) { const match = String(id).match(/P\d{2}/); if (match) ids.add(match[0]); }
  for (let i = 1; i <= 24; i += 1) ids.add(`P${String(i).padStart(2, "0")}`);
  return [...ids].sort();
});
const overview = computed(() => summary.value?.overview || {});
const preference = computed(() => summary.value?.preference || {});
const overviewCards = computed(() => [
  { label: "已开始参与者 / 24", value: `${overview.value.participants_started || 0} / 24` },
  { label: "已完成参与者", value: overview.value.participants_completed || 0 },
  { label: "已完成文章区块 / 96", value: `${overview.value.article_sessions_completed || 0} / 96` },
  { label: "逐题回答 / 960", value: `${overview.value.responses?.total || 0} / 960` },
  { label: "主观评价 / 96", value: `${overview.value.surveys || 0} / 96` },
  { label: "偏好 / 访谈", value: `${overview.value.preferences || 0} / ${overview.value.interviews || 0}` }
]);
const analysisStatements = computed(() => analysis.value?.statements || []);
const academicChartData = computed(() => showDemoData.value ? DEMO_ACADEMIC_DATA : buildAcademicDataFromSummary(summary.value));
const preferenceChartData = computed(() => showDemoData.value ? DEMO_PREFERENCE_DATA : buildPreferenceSeriesFromSummary(summary.value));
const subjectiveChartSeries = computed(() => Object.fromEntries(subjectiveMetrics.map(item => [item.name, academicMetricSeries(item.name)])));
const continuityChartSeries = computed(() => Object.fromEntries(subjectiveMetrics.slice(0, 2).map(item => [item.name, academicMetricSeries(item.name)])));
const qualityIssues = computed(() => quality.value?.issues || []);
const lastUpdatedText = computed(() => summary.value?.last_updated_at ? `最近活动：${formatDate(summary.value.last_updated_at)}` : "暂无实验数据");

// 核心结果摘要卡片：计算各指标在可见条件下的均值
const coreSummaryCards = computed(() => {
  const visibleConds = filters.value.condition ? [filters.value.condition] : conditions;
  function meanFor(metricName) {
    const vals = [];
    let totalN = 0;
    for (const cond of visibleConds) {
      const item = summary.value?.metrics?.[metricName]?.[cond];
      if (item?.mean != null && item?.n) {
        vals.push({ mean: Number(item.mean), n: Number(item.n) });
        totalN += Number(item.n);
      }
    }
    if (!vals.length) return { value: "—", n: 0 };
    const weighted = vals.reduce((sum, v) => sum + v.mean * v.n, 0) / totalN;
    return { value: weighted, n: totalN };
  }
  const ctia = meanFor("CTIA");
  const ctirt = meanFor("CTIRT");
  const cra = meanFor("CRA");
  const aca = meanFor("ACA");
  return [
    { metric: "CTIA", label: "CTIA 准确率（均值）", value: ctia.value === "—" ? "—" : formatAccuracy(ctia.value), n: ctia.n },
    { metric: "CTIRT", label: "CTIRT 反应时间（均值）", value: ctirt.value === "—" ? "—" : `${formatSeconds(ctirt.value)} s`, n: ctirt.n },
    { metric: "CRA", label: "CRA 准确率（均值）", value: cra.value === "—" ? "—" : formatAccuracy(cra.value), n: cra.n },
    { metric: "ACA", label: "ACA 准确率（均值）", value: aca.value === "—" ? "—" : formatAccuracy(aca.value), n: aca.n },
  ];
});

function metric(name) { return summary.value?.metrics?.[name] || {}; }
function academicMetricSeries(name) { return showDemoData.value ? (DEMO_ACADEMIC_METRICS[name] || { }) : buildMetricSeriesFromSummary(summary.value, name); }
function formatNumber(value) { return Number(value).toFixed(2); }
function formatAccuracy(value) { return Number(value).toFixed(2); }
function formatRating(value) { return Number(value).toFixed(1); }
function formatSeconds(value) { return `${(Number(value) / 1000).toFixed(2)}`; }
function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString("zh-CN", { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
}
function preferenceRank(condition) { return preference.value.rank?.[condition]?.mean == null ? "—" : Number(preference.value.rank[condition].mean).toFixed(2); }
function clearFilters() { filters.value = { participant_id: "", article_id: "", condition: "", status: "" }; loadAll(); }

function toggleSection(key) {
  collapsedSections[key] = !collapsedSections[key];
}

function scrollToSection(id) {
  const el = document.getElementById(id);
  if (el) {
    el.scrollIntoView({ behavior: "smooth", block: "start" });
    activeSection.value = id;
  }
}

// 滚动监听：高亮当前区块
let scrollObserver = null;
function setupScrollSpy() {
  const sectionEls = navItems.map(item => document.getElementById(item.id)).filter(Boolean);
  if (!sectionEls.length || !("IntersectionObserver" in window)) return;
  scrollObserver = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (entry.isIntersecting) {
        activeSection.value = entry.target.id;
      }
    }
  }, { rootMargin: "-20% 0px -70% 0px", threshold: 0 });
  sectionEls.forEach(el => scrollObserver.observe(el));
}

function quickExport(format, dataset) {
  exportMenuOpen.value = false;
  download(format, dataset);
}

async function loadAll() {
  loading.value = true;
  error.value = "";
  try {
    const [nextSummary, nextAnalysis, nextQuality] = await Promise.all([adminApi.summary(filters.value), adminApi.analysis(filters.value), adminApi.dataQuality(filters.value)]);
    summary.value = nextSummary;
    analysis.value = nextAnalysis;
    quality.value = nextQuality;
  } catch (requestError) {
    if (requestError.status === 401) { emit("logout"); return; }
    error.value = requestError.message;
  } finally { loading.value = false; }
}

async function logout() {
  try { await adminApi.logout(); } finally { emit("logout"); }
}

async function download(format, dataset = "analysis") {
  try {
    const response = await adminApi.exportData(format, dataset);
    const blob = response.data || response;
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `comment-scope-${dataset}-${format}.${format}`;
    anchor.click();
    URL.revokeObjectURL(url);
  } catch (requestError) { error.value = requestError.message; }
}

async function resetParticipant() {
  if (!resetParticipantId.value || !window.confirm(`确定要重置 ${resetParticipantId.value} 吗？该操作会结束其当前会话。`)) return;
  resetting.value = true;
  try { await adminApi.resetParticipant(resetParticipantId.value); resetParticipantId.value = ""; await loadAll(); } catch (requestError) { error.value = requestError.message; } finally { resetting.value = false; }
}

// 点击外部关闭导出菜单
function handleClickOutside(e) {
  if (exportMenuOpen.value && !e.target.closest(".admin-quick-export")) {
    exportMenuOpen.value = false;
  }
}

onMounted(() => {
  loadAll();
  setTimeout(setupScrollSpy, 500);
  document.addEventListener("click", handleClickOutside);
});
onUnmounted(() => {
  if (scrollObserver) scrollObserver.disconnect();
  document.removeEventListener("click", handleClickOutside);
});
</script>
