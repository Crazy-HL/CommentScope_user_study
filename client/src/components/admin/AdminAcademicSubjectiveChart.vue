<template>
  <section class="academic-subjective-figure" :aria-label="title">
    <div class="academic-figure-toolbar">
      <span class="academic-metric-title">{{ title }}</span>
      <button class="academic-export-button" type="button" :disabled="!hasData" @click="exportChart">导出 PNG</button>
    </div>

    <div v-if="hasData" class="academic-subjective-chart-wrap">
      <!-- A fixed viewBox gives every panel the same paper geometry while width:100% makes it responsive. -->
      <svg ref="chartSvg" class="academic-figure-svg academic-subjective-svg" :viewBox="`0 0 ${SUBJECTIVE_FIGURE_WIDTH} ${figureHeight}`" role="img" :aria-label="`${title} 条件比较图`">
        <defs>
          <linearGradient :id="gradientId" x1="0" x2="1" y1="0" y2="0">
            <stop v-for="(color, index) in COOLWARM_LUT" :key="`${gradientId}-${index}`" :offset="`${(index / (COOLWARM_LUT.length - 1)) * 100}%`" :stop-color="color" />
          </linearGradient>
        </defs>

        <!-- One direction key per combined figure; it is intentionally not repeated in every panel. -->
        <text class="academic-ramp-label academic-subjective-global-legend" :x="globalDirectionIsLower ? SUBJECTIVE_RAMP_X : SUBJECTIVE_RAMP_X + SUBJECTIVE_RAMP_WIDTH" :y="SUBJECTIVE_RAMP_LABEL_Y" :text-anchor="globalDirectionIsLower ? 'start' : 'end'">{{ globalDirectionText }}</text>
        <rect class="academic-subjective-ramp academic-subjective-global-legend" :x="SUBJECTIVE_RAMP_X" :y="SUBJECTIVE_RAMP_Y" :width="SUBJECTIVE_RAMP_WIDTH" height="5" :fill="`url(#${gradientId})`" />

        <g v-for="(item, metricIndex) in metrics" :key="item.name" class="subjective-panel" :transform="`translate(${panelX(metricIndex)}, ${panelY(metricIndex)})`">
          <g v-for="index in [0, 2]" :key="`${item.name}-band-${index}`">
            <rect class="academic-row-band" :x="PANEL_LEFT" :y="rowY(index) - ROW_GAP / 2" :width="PLOT_WIDTH" :height="ROW_GAP" />
          </g>
          <line v-for="tick in ticksFor(item)" :key="`${item.name}-grid-${tick}`" class="academic-grid-line" :x1="scaleX(tick, item)" :y1="PLOT_TOP" :x2="scaleX(tick, item)" :y2="PLOT_BOTTOM" />
          <rect class="academic-panel-border" :x="PANEL_LEFT" :y="PLOT_TOP" :width="PLOT_WIDTH" :height="PLOT_HEIGHT" />

          <g v-for="(condition, conditionIndex) in displayConditions" :key="`${item.name}-${condition}`">
            <circle v-for="(value, valueIndex) in observations(item.name, condition)" :key="`${item.name}-${condition}-${valueIndex}`" class="academic-observation academic-subjective-observation" :cx="scaleX(value, item)" :cy="rowY(conditionIndex) + jitter(valueIndex, conditionIndex)" r="2.7" :fill="coolwarmColor(normalize(value, item.domain))" />
            <line v-if="statistic(item.name, condition).ci95 != null" class="academic-ci-line" :x1="scaleX(statistic(item.name, condition).mean - statistic(item.name, condition).ci95, item)" :y1="rowY(conditionIndex)" :x2="scaleX(statistic(item.name, condition).mean + statistic(item.name, condition).ci95, item)" :y2="rowY(conditionIndex)" />
            <circle v-if="statistic(item.name, condition).mean != null" class="academic-center academic-subjective-center" :cx="scaleX(statistic(item.name, condition).mean, item)" :cy="rowY(conditionIndex)" r="4" />
          </g>

          <g v-for="(condition, conditionIndex) in displayConditions" :key="`${item.name}-label-${condition}`">
            <text class="academic-condition-label" :x="CONDITION_LABEL_X" :y="rowY(conditionIndex) + 4" text-anchor="end">{{ condition }}</text>
            <text v-if="statistic(item.name, condition).mean != null" class="academic-value-label" :x="annotationX(scaleX(statistic(item.name, condition).mean, item))" :y="rowY(conditionIndex) - 10" text-anchor="middle">M={{ formatValue(item, statistic(item.name, condition).mean) }}</text>
          </g>
          <text v-for="tick in ticksFor(item)" :key="`${item.name}-tick-${tick}`" class="academic-axis-label" :x="scaleX(tick, item)" :y="PLOT_BOTTOM + 17" text-anchor="middle">{{ formatAxisValue(item, tick) }}</text>
          <text class="academic-axis-title" :x="PANEL_LEFT + PLOT_WIDTH / 2" :y="PLOT_BOTTOM + 37" text-anchor="middle">{{ panelCaption(item, metricIndex) }}</text>
        </g>
      </svg>
    </div>
    <div v-else class="academic-subjective-empty">暂无足够数据</div>
  </section>
</template>

<script setup>
import { computed, ref } from "vue";
import { exportSvgAsPng } from "./adminChartExport";
import { COOLWARM_LUT, coolwarmColor } from "./academicFigureUtils";

const props = defineProps({
  title: { type: String, default: "主观评价" },
  metrics: { type: Array, default: () => [] },
  seriesByMetric: { type: Object, default: () => ({}) }
});

const chartSvg = ref(null);
// NASA-TLX is rendered as a 2x3 grid: Mental Demand, Physical Demand, Temporal Demand,
// Performance, Effort, and Frustration. RC and CA use the same component as a 1x2 grid.
const SUBJECTIVE_METRIC_LABELS = ["Mental Demand", "Physical Demand", "Temporal Demand", "Performance", "Effort", "Frustration", "RC", "CA"];
// NASA-TLX uses the compact 1–7 response scale.
const NASA_TLX_TICKS = [1, 2, 3, 4, 5, 6, 7];
const displayConditions = ["BL", "SE", "TE", "CS"];
const PANEL_WIDTH = 332;
const PANEL_HEIGHT = 286;
const PANEL_GAP_X = 18;
const PANEL_GAP_Y = 16;
const PANEL_LEFT = 48;
const PLOT_TOP = 39;
const PLOT_BOTTOM = 218;
const PLOT_HEIGHT = PLOT_BOTTOM - PLOT_TOP;
const PLOT_WIDTH = 260;
const ROW_GAP = PLOT_HEIGHT / 4;
const PLOT_LEFT = PANEL_LEFT;
const PLOT_RIGHT = PANEL_LEFT + PLOT_WIDTH;
const CONDITION_LABEL_X = PANEL_LEFT - 8;
const SUBJECTIVE_FIGURE_WIDTH = 1080;
const SUBJECTIVE_RAMP_WIDTH = 180;
const SUBJECTIVE_RAMP_X = (SUBJECTIVE_FIGURE_WIDTH - SUBJECTIVE_RAMP_WIDTH) / 2;
const SUBJECTIVE_RAMP_Y = 20;
const SUBJECTIVE_RAMP_LABEL_OFFSET = 2.1;
const SUBJECTIVE_RAMP_LABEL_Y = SUBJECTIVE_RAMP_Y - SUBJECTIVE_RAMP_LABEL_OFFSET;
const gradientId = `academic-subjective-gradient-${Math.random().toString(36).slice(2)}`;

const figureHeight = computed(() => props.metrics.length > 3 ? 612 : 316);
const globalDirectionIsLower = computed(() => props.metrics.every(item => item.higherIsBetter === false));
const globalDirectionText = computed(() => globalDirectionIsLower.value ? "← Lower is better" : "Higher is better →");
const hasData = computed(() => props.metrics.some(item => displayConditions.some(condition => observations(item.name, condition).length)));

function panelX(index) { return 18 + (index % 3) * (PANEL_WIDTH + PANEL_GAP_X); }
function panelY(index) { return 24 + Math.floor(index / 3) * (PANEL_HEIGHT + PANEL_GAP_Y); }
function rowY(index) { return PLOT_TOP + ROW_GAP / 2 + index * ROW_GAP; }
function observations(metricName, condition) {
  const series = props.seriesByMetric?.[metricName]?.[condition];
  if (Array.isArray(series)) return series.map(Number).filter(Number.isFinite);
  if (Array.isArray(series?.observations)) return series.observations.map(Number).filter(Number.isFinite);
  return [];
}
function mean(values) { return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null; }
function studentTCritical(sampleSize) {
  const table = { 2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571, 7: 2.447, 8: 2.365, 9: 2.306, 10: 2.262, 11: 2.228, 12: 2.201, 13: 2.179, 14: 2.160, 15: 2.145, 16: 2.131, 17: 2.120, 18: 2.110, 19: 2.101, 20: 2.093, 21: 2.086, 22: 2.080, 23: 2.074, 24: 2.069 };
  return table[sampleSize] || (sampleSize > 24 ? 1.96 : null);
}
function ci95(values) {
  if (values.length < 2) return null;
  const center = mean(values);
  const variance = values.reduce((sum, value) => sum + (value - center) ** 2, 0) / (values.length - 1);
  return studentTCritical(values.length) * Math.sqrt(variance) / Math.sqrt(values.length);
}
function statistic(metricName, condition) {
  const values = observations(metricName, condition);
  return { mean: mean(values), ci95: values.length >= 4 ? ci95(values) : null };
}
function domainFor(item) {
  const domain = item.domain || [0, 1];
  return { low: Number(domain[0]), high: Number(domain[1]) };
}
function isNASA(item) { return String(item.name || "").startsWith("NASA-TLX") || String(item.title || "").startsWith("NASA-TLX"); }
function ticksFor(item) {
  if (Array.isArray(item.ticks) && item.ticks.length) return item.ticks.map(Number);
  if (isNASA(item)) return NASA_TLX_TICKS;
  const { low, high } = domainFor(item);
  return Array.from({ length: 5 }, (_, index) => low + ((high - low) * index) / 4);
}
function normalize(value, domain) { return Math.max(0, Math.min(1, (Number(value) - domain[0]) / Math.max(1e-9, domain[1] - domain[0]))); }
function scaleX(value, item) { const domain = item.domain || [0, 1]; return PLOT_LEFT + normalize(value, domain) * PLOT_WIDTH; }
function jitter(valueIndex, conditionIndex) { return ((valueIndex % 5) - 2) * 5.5 + (conditionIndex % 2 ? 1 : -1); }
function annotationX(x) { return Math.max(PLOT_LEFT + 24, Math.min(PLOT_RIGHT - 24, x)); }
function panelCaption(item, index) {
  const letter = String.fromCharCode(65 + index);
  return `${letter}. ${item.title || item.name}`;
}
function formatValue(item, value) {
  if (value == null || !Number.isFinite(Number(value))) return "—";
  if (typeof item.format === "function") return item.format(Number(value));
  return Number(value).toFixed(item.domain?.[1] <= 1 ? 2 : item.domain?.[1] <= 7 ? 1 : 0);
}
function formatAxisValue(item, value) {
  if (isNASA(item)) return Number(value).toFixed(0);
  return formatValue(item, value);
}
async function exportChart() {
  if (hasData.value) await exportSvgAsPng(chartSvg.value, `${fileName(props.title)}.png`, { scale: 4 });
}
function fileName(value) { return String(value).trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "academic-subjective"; }
</script>
