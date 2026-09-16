<template>
  <section class="admin-section admin-participant-overview" aria-label="所有参与者数据总表">
    <div class="admin-section-heading">
      <div>
        <h2>参与者数据总表</h2>
        <p class="admin-section-description">按当前筛选范围逐人汇总实验进度、答题和参与者级任务；尚未开始的参与者也会保留在表中。</p>
      </div>
      <span class="admin-table-count">共 {{ rows.length }} 人</span>
    </div>
    <div class="admin-simple-table-wrap">
      <table class="admin-simple-table admin-participant-table">
        <thead>
          <tr>
            <th>参与者</th>
            <th>分组</th>
            <th>文章顺序</th>
            <th>状态</th>
            <th>文章区块</th>
            <th>逐题回答</th>
            <th>主观评价</th>
            <th>偏好排序</th>
            <th>偏好理由</th>
            <th>访谈</th>
            <th>最近活动</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!rows.length">
            <td colspan="12" class="admin-table-empty">当前筛选范围没有参与者数据。</td>
          </tr>
          <tr v-for="row in rows" :key="row.participant_id">
            <th scope="row">{{ row.participant_id }}</th>
            <td>{{ row.group_id || "—" }}</td>
            <td>{{ row.article_sequence || "—" }}</td>
            <td><span class="admin-status-pill" :class="statusClass(row.session_status)">{{ statusLabel(row.session_status) }}</span></td>
            <td>{{ row.article_sessions_completed ?? 0 }} / {{ row.article_sessions_expected ?? 4 }}</td>
            <td>{{ row.responses_count ?? 0 }} / {{ expectedResponses(row) }}</td>
            <td>{{ row.surveys_count ?? 0 }} / {{ row.article_sessions_expected ?? 4 }}</td>
            <td>{{ submittedLabel(row.preference_submitted) }}</td>
            <td>{{ submittedLabel(row.preference_reason_submitted) }}</td>
            <td>{{ submittedLabel(row.interview_submitted) }}</td>
            <td>{{ formatDate(row.last_seen_at) }}</td>
            <td><button class="admin-secondary-button admin-table-action" type="button" @click="$emit('view-participant', row.participant_id)">查看详情</button></td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup>
defineProps({ rows: { type: Array, required: true } });
defineEmits(["view-participant"]);

function statusLabel(status) {
  return { completed: "已完成", active: "进行中", not_started: "未开始" }[status] || "未知";
}
function statusClass(status) {
  return { completed: "status-complete", active: "status-active", not_started: "status-empty" }[status] || "status-empty";
}
function submittedLabel(value) { return value ? "已提交" : "未提交"; }
function expectedResponses(row) { return Number(row.article_sessions_expected || 4) * 10; }
function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString("zh-CN", { hour12: false });
}
</script>
