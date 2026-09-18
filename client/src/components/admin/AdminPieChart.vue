<template>
  <section class="academic-metric-figure" :aria-label="title">
    <div class="academic-figure-toolbar">
      <span class="academic-metric-title">{{ title }}</span>
      <button class="academic-export-button" type="button" :disabled="!hasData" @click="exportChart">导出 PNG</button>
    </div>

    <div v-if="hasData" class="pie-chart-container">
      <svg ref="chartSvg" class="pie-svg" viewBox="0 0 340 220" role="img" :aria-label="title">
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
            font-size="11"
            font-weight="700">{{ formatPercent(slice.percent) }}</text>
        </g>
        <!-- SVG 内部图例 -->
        <g class="svg-legend">
          <g v-for="(slice, index) in slices" :key="`svg-legend-${slice.condition}`" :transform="`translate(200, ${50 + index * 32})`">
            <rect x="0" y="0" width="14" height="14" rx="2" :fill="slice.color" />
            <text x="22" y="11" font-size="12" font-weight="600" fill="#17324d">{{ slice.condition }}</text>
            <text x="50" y="11" font-size="12" fill="#526b82">{{ formatPercent(slice.percent) }}</text>
          </g>
        </g>
      </svg>
    </div>
    <div v-else class="academic-empty-state">暂无数据</div>
  </section>
</template>

<script setup>
import { computed, ref } from "vue";
import { coolwarmColor } from "./academicFigureUtils";

const props = defineProps({
  title: { type: String, required: true },
  data: { type: Object, default: () => ({}) },
  total: { type: Number, default: 0 }
});

const chartSvg = ref(null);
const CONDITIONS = ["TE", "CS", "SE", "BL"];

const centerX = 100;
const centerY = 110;
const radius = 85;

const hasData = computed(() => {
  return props.total > 0 && Object.values(props.data).some(v => (v?.count || 0) > 0);
});

const slices = computed(() => {
  const total = props.total || 0;
  let startAngle = -Math.PI / 2;

  return CONDITIONS.map((condition, index) => {
    const count = props.data[condition]?.count || 0;
    const percent = total > 0 ? count / total : 0;
    const endAngle = startAngle + percent * Math.PI * 2;
    const color = coolwarmColor(index / (CONDITIONS.length - 1));

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
    const labelRadius = radius * 0.6;
    const labelX = Math.cos(midAngle) * labelRadius;
    const labelY = Math.sin(midAngle) * labelRadius;

    startAngle = endAngle;

    return { condition, count, percent, path, color, labelX, labelY };
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
    canvas.width = 680;
    canvas.height = 440;
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 10, 10, canvas.width - 20, canvas.height - 20);
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
.pie-chart-container { display: flex; align-items: center; padding: 4px; }
.pie-svg { width: 100%; max-width: 340px; height: auto; }
.academic-empty-state { padding: 30px; text-align: center; color: #8a9baa; font-size: 13px; }
</style>
