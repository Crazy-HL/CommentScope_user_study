<template>
  <section class="admin-section admin-heatmap-section" aria-label="参与者文章进度热力图">
    <div class="admin-section-heading">
      <div>
        <h2>参与者进度热力图</h2>
        <p class="admin-section-description">24 名参与者 × 4 篇文章的完成状态；绿色已完成，黄色进行中，灰色未开始。点击格子查看参与者详情。</p>
      </div>
      <div class="admin-heatmap-legend">
        <span><i class="heatmap-legend-dot status-completed"></i>已完成</span>
        <span><i class="heatmap-legend-dot status-active"></i>进行中</span>
        <span><i class="heatmap-legend-dot status-not-started"></i>未开始</span>
      </div>
    </div>
    <div class="admin-heatmap-scroll">
      <div class="admin-heatmap-grid">
        <div class="admin-heatmap-corner"></div>
        <div v-for="col in articleColumns" :key="col.articleId" class="admin-heatmap-col-header">{{ col.label }}</div>
        <template v-for="row in heatmapRows" :key="row.participantId">
          <div class="admin-heatmap-row-header">{{ row.participantId }}</div>
          <div
            v-for="cell in row.cells"
            :key="`${row.participantId}-${cell.articleId}`"
            class="admin-heatmap-cell"
            :class="`heatmap-status-${cell.status}`"
            :title="tooltipText(row, cell)"
            @click="$emit('view-participant', row.participantId)"
          >
            <span class="heatmap-cell-label">{{ cell.displayLabel }}</span>
          </div>
        </template>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  rows: { type: Array, default: () => [] },
});
defineEmits(["view-participant"]);

const articleDisplayLabels = { A02: "01", A03: "02", A04: "03", A07: "04" };
const displayToArticleId = { "01": "A02", "02": "A03", "03": "A04", "04": "A07" };
const articleColumns = [
  { articleId: "A02", label: "文章 01" },
  { articleId: "A03", label: "文章 02" },
  { articleId: "A04", label: "文章 03" },
  { articleId: "A07", label: "文章 04" },
];

function parseSequence(sequence) {
  if (!sequence) return ["01", "02", "03", "04"];
  return String(sequence).split("-").map(s => s.trim());
}

function statusLabel(status) {
  return { completed: "已完成", active: "进行中", not_started: "未开始" }[status] || "未知";
}

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString("zh-CN", { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hour12: false });
}

const heatmapRows = computed(() => {
  // Ensure all 24 participants appear, even those not yet in the data.
  const allIds = Array.from({ length: 24 }, (_, i) => `P${String(i + 1).padStart(2, "0")}`);
  const rowMap = new Map(props.rows.map(r => [r.participant_id, r]));
  return allIds.map(participantId => {
    const row = rowMap.get(participantId) || {};
    const sequence = parseSequence(row.article_sequence);
    const completed = Number(row.article_sessions_completed || 0);
    const started = Number(row.article_sessions_started || row.article_sessions_completed || 0);
    const cells = articleColumns.map((col, colIndex) => {
      // Find which position in the participant's sequence this article occupies.
      const displayNum = articleDisplayLabels[col.articleId];
      const seqIndex = sequence.indexOf(displayNum);
      const position = seqIndex >= 0 ? seqIndex : colIndex;
      let status = "not_started";
      if (position < completed) status = "completed";
      else if (position < started) status = "active";
      return {
        articleId: col.articleId,
        displayLabel: displayNum,
        status,
      };
    });
    return { participantId, cells, lastSeen: row.last_seen_at };
  });
});

function tooltipText(row, cell) {
  const parts = [
    `参与者：${row.participantId}`,
    `文章：${cell.displayLabel}（${cell.articleId}）`,
    `状态：${statusLabel(cell.status)}`,
  ];
  if (row.lastSeen) parts.push(`最近活动：${formatDate(row.lastSeen)}`);
  return parts.join("\n");
}
</script>

<style scoped>
.admin-heatmap-section { margin-top: 12px; }
.admin-heatmap-legend { display: flex; gap: 14px; align-items: center; color: #627b86; font-size: 12px; white-space: nowrap; }
.heatmap-legend-dot { display: inline-block; width: 11px; height: 11px; border-radius: 3px; margin-right: 5px; vertical-align: middle; }
.heatmap-legend-dot.status-completed { background: #3a9d6e; }
.heatmap-legend-dot.status-active { background: #e0a83a; }
.heatmap-legend-dot.status-not-started { background: #d3dde0; }
.admin-heatmap-scroll { overflow-x: auto; border: 1px solid #d9e5e8; border-radius: 13px; background: #fff; box-shadow: 0 6px 22px rgba(38, 74, 87, .05); padding: 12px; }
.admin-heatmap-grid { display: grid; grid-template-columns: 56px repeat(4, minmax(70px, 1fr)); gap: 4px; min-width: 420px; }
.admin-heatmap-corner { height: 28px; }
.admin-heatmap-col-header { display: flex; align-items: center; justify-content: center; height: 28px; color: #627b86; font-size: 12px; font-weight: 800; }
.admin-heatmap-row-header { display: flex; align-items: center; justify-content: center; height: 32px; color: #203f50; font-size: 12px; font-weight: 800; background: #f7faf9; border-radius: 5px; }
.admin-heatmap-cell { display: flex; align-items: center; justify-content: center; height: 32px; border-radius: 5px; cursor: pointer; transition: transform .12s, box-shadow .12s; user-select: none; }
.admin-heatmap-cell:hover { transform: scale(1.06); box-shadow: 0 2px 8px rgba(0,0,0,.15); z-index: 1; }
.heatmap-cell-label { font-size: 12px; font-weight: 800; }
.heatmap-status-completed { background: #3a9d6e; color: #fff; }
.heatmap-status-active { background: #e0a83a; color: #fff; }
.heatmap-status-not-started { background: #e8eef0; color: #9aabb3; }
.heatmap-status-not-started .heatmap-cell-label { color: #9aabb3; }
</style>
