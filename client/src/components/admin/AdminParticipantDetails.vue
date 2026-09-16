<template>
  <section v-if="participantId" id="participant-details" class="admin-section admin-participant-details" aria-label="参与者详细数据">
    <div class="admin-section-heading">
      <div>
        <h2>参与者详细数据 · {{ participantId }}</h2>
        <p class="admin-section-description">这里展示该参与者的完整实验记录。上方统计表仍按当前筛选范围计算。</p>
      </div>
      <span class="admin-status-pill" :class="details.length ? 'status-active' : 'status-empty'">{{ details.length ? `${details.length} 个文章区块` : "暂无文章区块" }}</span>
    </div>

    <div v-if="!details.length" class="admin-empty-state">没有找到 {{ participantId }} 的实验数据；该编号仍然保留在参与者列表中，开始实验后会自动显示。</div>
    <template v-else>
      <div class="admin-simple-table-wrap admin-participant-summary-wrap">
        <table class="admin-simple-table admin-participant-summary-table">
          <thead>
            <tr>
              <th>顺序</th><th>文章</th><th>界面</th><th>区块状态</th><th>阅读时间</th>
              <th>滚动次数</th><th>NSD</th><th>评论交互</th><th>CRA</th><th>ACA</th>
              <th>CTIA</th><th>CTIRT</th><th>CLA</th><th>CLT</th><th>RC</th><th>CA</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="detail in details" :key="`${detail.session_id}-${detail.article_order}`">
              <td>{{ formatOrder(detail.article_order) }}</td>
              <td><strong>文章 {{ articleDisplayLabels[detail.article_id] || detail.article_id }}</strong></td>
              <td><span class="condition-badge" :class="`condition-${String(detail.condition).toLowerCase()}`">{{ detail.condition }}</span></td>
              <td>{{ statusLabel(detail.status) }}</td>
              <td>{{ formatMilliseconds(detail.initial_reading_time_ms) }}</td>
              <td>{{ detail.scroll_event_count ?? 0 }}</td>
              <td>{{ formatNumber(detail.normalized_scroll_distance, 3) }}</td>
              <td>{{ detail.comment_interaction_count ?? 0 }}</td>
              <td>{{ formatScore(detail.CRA) }}</td>
              <td>{{ formatScore(detail.ACA) }}</td>
              <td>{{ formatScore(detail.CTIA) }}</td>
              <td>{{ formatMilliseconds(detail.CTIRT) }}</td>
              <td>{{ formatScore(detail.CLA) }}</td>
              <td>{{ formatMilliseconds(detail.CLT) }}</td>
              <td>{{ formatRating(detail.workload?.reading_continuity) }}</td>
              <td>{{ formatRating(detail.workload?.comment_accessibility) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="admin-participant-detail-list">
        <article v-for="detail in details" :key="`${detail.session_id}-${detail.article_order}-raw`" class="admin-panel admin-participant-detail-card">
          <div class="admin-participant-detail-heading">
            <div>
              <div class="admin-kicker">文章位置 {{ formatOrder(detail.article_order) }}</div>
              <h3>文章 {{ articleDisplayLabels[detail.article_id] || detail.article_id }} · {{ detail.condition }}</h3>
            </div>
            <span>{{ statusLabel(detail.status) }} · {{ detail.responses_total }} 道题 · {{ detail.events?.length || 0 }} 条事件</span>
          </div>
          <dl class="admin-participant-meta-grid">
            <div><dt>Session ID</dt><dd>{{ detail.session_id }}</dd></div>
            <div><dt>阅读开始</dt><dd>{{ formatDate(detail.reading_start_time) }}</dd></div>
            <div><dt>阅读结束</dt><dd>{{ formatDate(detail.reading_end_time) }}</dd></div>
            <div><dt>总滚动距离</dt><dd>{{ formatNumber(detail.total_scroll_distance_px, 1) }} px</dd></div>
            <div><dt>最大滚动位置</dt><dd>{{ formatNumber(detail.max_scroll_y, 1) }} px</dd></div>
            <div><dt>评论点击 / 打开 / 关闭</dt><dd>{{ detail.comment_click_count ?? 0 }} / {{ detail.comment_open_count ?? 0 }} / {{ detail.comment_close_count ?? 0 }}</dd></div>
            <div><dt>段落评论操作</dt><dd>{{ detail.paragraph_toggle_count ?? 0 }}</dd></div>
            <div class="admin-participant-workload-meta"><dt>NASA-TLX / 主观评价</dt><dd>{{ workloadSummary(detail.workload) }}</dd><small v-if="detail.workload">Physical {{ detail.workload.physical_demand ?? "—" }} · Temporal {{ detail.workload.temporal_demand ?? "—" }} · Performance {{ detail.workload.performance ?? "—" }} · RC {{ detail.workload.reading_continuity ?? "—" }} · CA {{ detail.workload.comment_accessibility ?? "—" }}</small></div>
          </dl>

          <details class="admin-participant-raw-section" open>
            <summary>逐题回答明细（{{ detail.responses_total }}）</summary>
            <div class="admin-simple-table-wrap">
              <table class="admin-simple-table admin-raw-table">
                <thead><tr><th>阶段</th><th>题目</th><th>选择</th><th>正确性</th><th>开始时间</th><th>提交时间</th><th>答题时间</th><th>选项点击</th><th>选项更改</th><th>题目滚动</th></tr></thead>
                <tbody>
                  <tr v-for="response in flattenResponses(detail.responses)" :key="`${detail.article_order}-${response.question_type}-${response.question_id}`">
                    <td>{{ response.question_type }}</td>
                    <td>{{ response.question_id }}</td>
                    <td>{{ response.selected_option }}</td>
                    <td>{{ response.correct ? "正确" : "错误" }}</td>
                    <td>{{ response.item_start_time || "—" }}</td>
                    <td>{{ response.submit_time || "—" }}</td>
                    <td>{{ formatMilliseconds(response.elapsed_ms) }}</td>
                    <td>{{ response.option_click_count ?? 0 }}</td>
                    <td>{{ response.option_change_count ?? 0 }}</td>
                    <td>{{ response.scroll_event_count ?? 0 }} 次 / {{ formatNumber(response.total_scroll_distance_px, 1) }} px</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </details>

          <details class="admin-participant-raw-section">
            <summary>评论交互事件（{{ detail.events?.length || 0 }}）</summary>
            <div v-if="!detail.events?.length" class="admin-empty-state compact">该文章区块没有记录评论交互事件。</div>
            <div v-else class="admin-simple-table-wrap">
              <table class="admin-simple-table admin-raw-table">
                <thead><tr><th>时间</th><th>事件</th><th>阶段</th><th>题目</th><th>事件载荷</th></tr></thead>
                <tbody>
                  <tr v-for="event in detail.events" :key="event.event_row_id">
                    <td>{{ event.client_occurred_at }}</td><td>{{ event.event_type }}</td><td>{{ event.stage || "—" }}</td><td>{{ event.question_id || "—" }}</td><td class="admin-json-cell">{{ stringify(event.payload) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </details>
        </article>
      </div>

    </template>

    <div class="admin-overview-columns admin-participant-task-details">
      <article v-for="task in participantTasks" :key="task.session_id" class="admin-panel admin-overview-callout">
        <div class="admin-kicker">Participant-level tasks</div>
        <h3>偏好与访谈 · {{ task.session_id }}</h3>
        <div v-if="task.preference" class="admin-participant-task-block">
          <strong>偏好排序</strong>
          <p>{{ task.preference.ranking?.join(" → ") || "—" }}</p>
          <p>首选界面：<strong>{{ task.preference.preferred_condition || "—" }}</strong></p>
          <p>偏好理由：{{ task.preference.reason || "—" }}</p>
          <small>提交时间：{{ formatDate(task.preference.submitted_at) }}</small>
        </div>
        <div v-else class="admin-empty-state compact">尚未提交偏好排序。</div>
        <div v-if="task.interview" class="admin-participant-task-block">
          <strong>半结构化访谈</strong>
          <div v-for="(answer, question) in task.interview.answers" :key="question" class="admin-interview-answer"><span>{{ question }}</span><p>{{ answer }}</p></div>
          <small>提交时间：{{ formatDate(task.interview.submitted_at) }}</small>
        </div>
        <div v-else class="admin-empty-state compact">尚未提交访谈回答。</div>
      </article>
    </div>
  </section>
</template>

<script setup>
const articleDisplayLabels = { A02: "01", A03: "02", A04: "03", A07: "04" };

defineProps({
  participantId: { type: String, default: "" },
  details: { type: Array, default: () => [] },
  participantTasks: { type: Array, default: () => [] },
});

function formatOrder(value) { return value == null ? "—" : String(value).padStart(2, "0"); }
function formatNumber(value, digits = 2) { return value == null || Number.isNaN(Number(value)) ? "—" : Number(value).toFixed(digits); }
function formatMilliseconds(value) { return value == null || Number.isNaN(Number(value)) ? "—" : `${formatNumber(Number(value) / 1000, 2)} s`; }
function formatScore(value) { return formatNumber(value, 2); }
function formatRating(value) { return formatNumber(value, 1); }
function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false
  });
}
function statusLabel(status) { return status === "completed" ? "已完成" : status === "active" ? "进行中" : status === "pending" ? "未开始" : (status || "—"); }
function flattenResponses(responses = {}) { return Object.values(responses).flat().sort((a, b) => String(a.question_type).localeCompare(String(b.question_type)) || String(a.question_id).localeCompare(String(b.question_id))); }
function stringify(value) { return value == null ? "—" : JSON.stringify(value); }
function workloadSummary(workload) {
  if (!workload) return "—";
  return `MD ${workload.mental_demand ?? "—"} · Effort ${workload.effort ?? "—"} · Frustration ${workload.frustration ?? "—"}`;
}
</script>
