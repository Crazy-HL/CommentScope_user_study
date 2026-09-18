<template>
  <section class="academic-metric-figure" :aria-label="title">
    <div class="academic-figure-toolbar">
      <span class="academic-metric-title">{{ title }}</span>
      <button class="academic-export-button" type="button" :disabled="!hasData" @click="exportChart">导出 PNG</button>
    </div>

    <div v-if="hasData" class="pie-chart-container">
      <svg ref="chartSvg" class="academic-figure-svg" viewBox="0 0 400 320" role="img" :aria-label="title">
        <g :transform="`translate(${centerX}, ${centerY})`">
          <path v-for="slice in visibleSlices" :key="slice.condition"
            :d="slice.path"
            :fill="slice.color"
            stroke="#fff"
            stroke-width="2" />
          <text v-for="slice in labeledSlices" :key="`label-${slice.condition}`"
            :x="slice.labelX"
            :y="slice.labelY"
            text-anchor="middle"
            dominant-baseline="middle"
            fill="#fff"
            font-size="13"
            font-weight="700">{{ formatPercent(slice.percent) }}</text>
        </g>
      </svg>
      <div class="pie-legend">
        <div v-for="slice in slices" :key="`legend-${slice.condition}`" class="pie-legend-item">
          <span class="pie-legend-color" :style="{ background: slice.color }"></span>
          <span class="pie-legend-label">{{ slice.condition }}</span>
          <span class="pie-legend-value">{{ formatPercent(slice.percent) }} ({{ slice.count }}人)</span>
        </div>
      </div>
    </div>
    <div v-else class="academic-empty-state">暂无数据</div>
  </section>
</template>

<script setup>
import { computed, ref } from "vue";

const props = defineProps({
  title: { type: String, required: true },
  data: { type: Object, default: () => ({}) },
  total: { type: Number, default: 0 }
});

const chartSvg = ref(null);

const CONDITION_COLORS = {
  TE: "#2b7a78",
  CS: "#c0792e",
  SE: "#5a6fa8",
  BL: "#8b5a8b"
};

const centerX = 140;
const centerY = 160;
const radius = 110;

const hasData = computed(() => {
  return props.total > 0 && Object.values(props.data).some(v => (v?.count || 0) > 0);
});

const slices = computed(() => {
  const conditions = ["TE", "CS", "SE", "BL"];
  const total = props.total || 0;
  let startAngle = -Math.PI / 2;

  return conditions.map(condition => {
    const count = props.data[condition]?.count || 0;
    const percent = total > 0 ? count / total : 0;
    const endAngle = startAngle + percent * Math.PI * 2;

    const largeArc = percent > 0.5 ? 1 : 0;
    const x1 = Math.cos(startAngle) * radius;
    const y1 = Math.sin(startAngle) * radius;
    const x2 = Math.cos(endAngle) * radius;
    const y2 = Math.sin(endAngle) * radius;

    let path = "";
    if (percent >= 0.999) {
      path = `M ${-radius} 0 A ${radius} ${radius} 0 1 1 ${radius} 0 A ${radius} ${radius} 0 1 1 ${-radius} 0 Z`;
    } else if (percent > 0) {
      path = `M 0 0 L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} Z`;
    }

    const midAngle = (startAngle + endAngle) / 2;
    const labelRadius = radius * 0.65;
    const labelX = Math.cos(midAngle) * labelRadius;
    const labelY = Math.sin(midAngle) * labelRadius;

    startAngle = endAngle;

    return { condition, count, percent, path, color: CONDITION_COLORS[condition], labelX, labelY };
  });
});

const visibleSlices = computed(() => slices.value.filter(s => s.percent > 0 && s.path));
const labeledSlices = computed(() => slices.value.filter(s => s.percent >= 0.08 && s.path));

function formatPercent(value) {
  return (value * 100).toFixed(1) + "%";
}

function exportChart() {
  if (!chartSvg.value) return;
  const svgData = new XMLSerializer().serializeToString(chartSvg.value);
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  const img = new Image();
  const svgBlob = new Blob([svgData], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(svgBlob);

  img.onload = () => {
    canvas.width = 800;
    canvas.height = 640;
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    URL.revokeObjectURL(url);

    const link = document.createElement("a");
    link.download = `${props.title.replace(/[·\s/]/g, "_")}.png`;
    link.href = canvas.toDataURL("image/png");
    link.click();
  };
  img.src = url;
}
</script>

<style scoped>
.pie-chart-container { display: flex; align-items: center; gap: 20px; padding: 10px; }
.pie-legend { display: flex; flex-direction: column; gap: 10px; }
.pie-legend-item { display: flex; align-items: center; gap: 8px; font-size: 13px; }
.pie-legend-color { width: 14px; height: 14px; border-radius: 3px; flex-shrink: 0; }
.pie-legend-label { font-weight: 600; color: #17324d; min-width: 30px; }
.pie-legend-value { color: #526b82; }
.academic-empty-state { padding: 40px; text-align: center; color: #8a9baa; font-size: 14px; }
</style>
