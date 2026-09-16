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
            <div><dt>总滚动距离</dt><dd>{{ formatScrollDistance(detail.total_scroll_distance_px) }}</dd></div>
            <div><dt>最大滚动位置</dt><dd>{{ formatScrollDistance(detail.max_scroll_y) }}</dd></div>
            <div><dt>评论卡片点击</dt><dd>{{ detail.comment_click_count ?? 0 }} 次</dd></div>
            <div><dt>侧边栏打开 / 关闭</dt><dd>{{ detail.comment_open_count ?? 0 }} / {{ detail.comment_close_count ?? 0 }} 次</dd></div>
            <div><dt>段落评论操作</dt><dd>{{ detail.paragraph_toggle_count ?? 0 }}</dd></div>
            <div class="admin-participant-workload-meta">
              <dt>NASA-TLX / 主观评价</dt>
              <dd v-if="detail.workload" class="workload-visual">
                <div class="workload-group">
                  <div class="workload-group-title">NASA-TLX 负荷（1–7，越高负荷越大）</div>
                  <div class="workload-bars">
                    <div v-for="item in nasaTlxBars(detail.workload)" :key="item.key" class="workload-bar-item">
                      <span class="workload-label">{{ item.label }}</span>
                      <div class="workload-bar-track"><div class="workload-bar-fill workload-demand" :style="{ width: item.percent + '%' }"></div></div>
                      <span class="workload-value">{{ item.value }}</span>
                    </div>
                  </div>
                </div>
                <div class="workload-group">
                  <div class="workload-group-title">主观评价（1–7，越高体验越好）</div>
                  <div class="workload-bars">
                    <div v-for="item in subjectiveBars(detail.workload)" :key="item.key" class="workload-bar-item">
                      <span class="workload-label">{{ item.label }}</span>
                      <div class="workload-bar-track"><div class="workload-bar-fill workload-positive" :style="{ width: item.percent + '%' }"></div></div>
                      <span class="workload-value">{{ item.value }}</span>
                    </div>
                  </div>
                </div>
              </dd>
              <dd v-else>—</dd>
            </div>
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
                    <td>{{ formatDate(response.item_start_time) }}</td>
                    <td>{{ formatDate(response.submit_time) }}</td>
                    <td>{{ formatMilliseconds(response.elapsed_ms) }}</td>
                    <td>{{ response.option_click_count ?? 0 }}</td>
                    <td>{{ response.option_change_count ?? 0 }}</td>
                    <td>{{ response.scroll_event_count ?? 0 }} 次 / {{ formatScrollDistance(response.total_scroll_distance_px) }}</td>
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
                    <td>{{ formatDate(event.client_occurred_at) }}</td><td>{{ event.event_type }}</td><td>{{ event.stage || "—" }}</td><td>{{ event.question_id || "—" }}</td><td class="admin-json-cell">{{ stringify(event.payload) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </details>
        </article>
      </div>

    </template>

    <div class="admin-participant-task-details">
      <article v-for="task in participantTasks" :key="task.session_id" class="admin-panel task-detail-card">
        <div class="task-detail-header">
          <div class="admin-kicker">参与者级任务</div>
          <h3>偏好与访谈</h3>
        </div>

        <!-- 偏好排序 -->
        <div class="task-section">
          <div class="task-section-title">
            <span class="task-section-icon">📋</span>
            <span>界面偏好排序</span>
            <span v-if="task.preference" class="task-submit-time">{{ formatDate(task.preference.submitted_at) }}</span>
          </div>
          <div v-if="task.preference" class="preference-content">
            <div class="preference-ranking">
              <span class="preference-label">排序：</span>
              <div class="preference-badges">
                <template v-for="(cond, idx) in task.preference.ranking" :key="cond">
                  <span class="condition-badge" :class="`condition-${cond.toLowerCase()}`">{{ cond }}</span>
                  <span v-if="idx < task.preference.ranking.length - 1" class="preference-arrow">→</span>
                </template>
              </div>
            </div>
            <div class="preference-favorite">
              <span class="preference-label">首选：</span>
              <span class="condition-badge condition-favorite" :class="`condition-${task.preference.preferred_condition?.toLowerCase()}`">{{ task.preference.preferred_condition || "—" }}</span>
            </div>
            <div class="preference-reason">
              <span class="preference-label">理由：</span>
              <p class="preference-reason-text">{{ task.preference.reason || "—" }}</p>
            </div>
          </div>
          <div v-else class="admin-empty-state compact">尚未提交偏好排序。</div>
        </div>

        <!-- 半结构化访谈 -->
        <div class="task-section">
          <div class="task-section-title">
            <span class="task-section-icon">💬</span>
            <span>半结构化访谈</span>
            <span v-if="task.interview" class="task-submit-time">{{ formatDate(task.interview.submitted_at) }}</span>
          </div>
          <div v-if="task.interview" class="interview-content">
            <div v-for="(question, qIndex) in interviewQuestions" :key="qIndex" class="interview-qa-item">
              <div class="interview-question">
                <span class="interview-q-num">Q{{ qIndex + 1 }}</span>
                <span class="interview-q-text">{{ question }}</span>
              </div>
              <div class="interview-answer">
                {{ task.interview.answers[`q${qIndex + 1}`] || "—" }}
              </div>
            </div>
          </div>
          <div v-else class="admin-empty-state compact">尚未提交访谈回答。</div>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { INTERVIEW_QUESTIONS } from "../../experiment/experimentConfig";
const articleDisplayLabels = { A02: "01", A03: "02", A04: "03", A07: "04" };
const interviewQuestions = INTERVIEW_QUESTIONS;

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
  if (!value && value !== 0) return "—";
  // 处理纯数字字符串形式的毫秒时间戳
  const timestamp = typeof value === "string" && /^\d+$/.test(value) ? Number(value) : value;
  const date = new Date(timestamp);
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
function formatScrollDistance(value) {
  if (value == null || Number.isNaN(Number(value))) return "—";
  const px = Number(value);
  if (px < 1000) return `${px.toFixed(0)} px`;
  // 大于1000px时同时显示米和像素，更直观
  const meters = px / 1000;
  return `${meters.toFixed(2)} m（${px.toFixed(0)} px）`;
}
function statusLabel(status) { return status === "completed" ? "已完成" : status === "active" ? "进行中" : status === "pending" ? "未开始" : (status || "—"); }
function flattenResponses(responses = {}) { return Object.values(responses).flat().sort((a, b) => String(a.question_type).localeCompare(String(b.question_type)) || String(a.question_id).localeCompare(String(b.question_id))); }
function stringify(value) { return value == null ? "—" : JSON.stringify(value); }
function workloadSummary(workload) {
  if (!workload) return "—";
  return `MD ${workload.mental_demand ?? "—"} · Effort ${workload.effort ?? "—"} · Frustration ${workload.frustration ?? "—"}`;
}
function nasaTlxBars(workload) {
  const items = [
    { key: "mental", label: "脑力需求", value: workload.mental_demand },
    { key: "physical", label: "体力需求", value: workload.physical_demand },
    { key: "temporal", label: "时间压力", value: workload.temporal_demand },
    { key: "performance", label: "任务表现", value: workload.performance },
    { key: "effort", label: "努力程度", value: workload.effort },
    { key: "frustration", label: "挫败感", value: workload.frustration }
  ];
  return items.map(item => ({
    ...item,
    value: item.value ?? "—",
    percent: item.value != null ? Math.min(100, Math.max(0, (Number(item.value) / 7) * 100)) : 0
  }));
}
function subjectiveBars(workload) {
  const items = [
    { key: "rc", label: "阅读连续性", value: workload.reading_continuity },
    { key: "ca", label: "评论可及性", value: workload.comment_accessibility }
  ];
  return items.map(item => ({
    ...item,
    value: item.value ?? "—",
    percent: item.value != null ? Math.min(100, Math.max(0, (Number(item.value) / 7) * 100)) : 0
  }));
}
</script>

<style scoped>
.workload-visual { display: flex; flex-direction: column; gap: 12px; }
.workload-group-title { font-size: 11px; font-weight: 700; color: #6b7f8f; margin-bottom: 6px; letter-spacing: .02em; }
.workload-bars { display: grid; grid-template-columns: 1fr 1fr; gap: 4px 12px; }
.workload-bar-item { display: flex; align-items: center; gap: 6px; font-size: 12px; }
.workload-label { flex-shrink: 0; width: 56px; color: #4a6274; font-size: 11px; white-space: nowrap; }
.workload-bar-track { flex: 1; height: 8px; background: #e8eef0; border-radius: 4px; overflow: hidden; min-width: 40px; }
.workload-bar-fill { height: 100%; border-radius: 4px; transition: width .3s ease; }
.workload-bar-fill.workload-demand { background: linear-gradient(90deg, #f0a868, #d97742); }
.workload-bar-fill.workload-positive { background: linear-gradient(90deg, #5fb8a8, #2b7a78); }
.workload-value { flex-shrink: 0; width: 20px; text-align: right; font-weight: 700; color: #2c4a5e; font-size: 12px; }
.admin-participant-workload-meta { grid-column: 1 / -1; }
.admin-participant-workload-meta dt { margin-bottom: 8px; }
.admin-participant-workload-meta dd { margin: 0; }

/* 偏好与访谈卡片 */
.admin-participant-task-details { margin-top: 20px; display: flex; flex-direction: column; gap: 16px; }
.task-detail-card { padding: 0; overflow: hidden; }
.task-detail-header { padding: 16px 20px; border-bottom: 1px solid #e2eaed; background: #f7faf9; }
.task-detail-header h3 { margin: 4px 0 0; color: #17324d; font-size: 17px; }
.task-section { padding: 18px 20px; border-bottom: 1px solid #eef3f4; }
.task-section:last-child { border-bottom: none; }
.task-section-title { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; font-size: 14px; font-weight: 700; color: #2c4a5e; }
.task-section-icon { font-size: 16px; }
.task-submit-time { margin-left: auto; font-size: 11px; font-weight: 400; color: #8a9aa2; }

/* 偏好排序 */
.preference-content { display: flex; flex-direction: column; gap: 12px; }
.preference-ranking, .preference-favorite { display: flex; align-items: center; gap: 8px; }
.preference-label { flex-shrink: 0; width: 40px; font-size: 13px; color: #6b7f8f; font-weight: 600; }
.preference-badges { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.preference-arrow { color: #9fb0b8; font-weight: 700; font-size: 14px; }
.condition-badge { display: inline-flex; align-items: center; justify-content: center; min-width: 36px; height: 26px; padding: 0 10px; border-radius: 6px; font-size: 12px; font-weight: 800; color: #fff; }
.condition-te { background: #2b7a78; }
.condition-cs { background: #c0792e; }
.condition-se { background: #5a6fa8; }
.condition-bl { background: #8b5a8b; }
.condition-favorite { box-shadow: 0 0 0 2px rgba(43,122,120,.3); }
.preference-reason { display: flex; gap: 8px; }
.preference-reason-text { margin: 0; flex: 1; padding: 10px 14px; background: #f0f6f7; border-left: 3px solid #2b7a78; border-radius: 0 8px 8px 0; color: #3a5566; font-size: 13px; line-height: 1.7; }

/* 访谈问答 */
.interview-content { display: flex; flex-direction: column; gap: 14px; }
.interview-qa-item { background: #fafcfc; border: 1px solid #e6edef; border-radius: 10px; overflow: hidden; }
.interview-question { display: flex; align-items: flex-start; gap: 10px; padding: 10px 14px; background: #f0f6f7; border-bottom: 1px solid #e2eaed; }
.interview-q-num { flex-shrink: 0; display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 22px; border-radius: 4px; background: #2b7a78; color: #fff; font-size: 11px; font-weight: 800; }
.interview-q-text { flex: 1; font-size: 13px; font-weight: 700; color: #2c4a5e; line-height: 1.5; }
.interview-answer { padding: 12px 14px; font-size: 13px; color: #4a6274; line-height: 1.8; white-space: pre-wrap; }
</style>
