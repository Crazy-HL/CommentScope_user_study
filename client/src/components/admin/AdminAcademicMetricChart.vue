<template>
  <section class="academic-metric-figure" :aria-label="title">
    <div class="academic-figure-toolbar">
      <span class="academic-metric-title">{{ title }}</span>
      <button class="academic-export-button" type="button" :disabled="!hasData" @click="exportChart">导出 PNG</button>
    </div>

    <div v-if="hasData" class="academic-metric-chart-scroll">
      <svg ref="chartSvg" class="academic-figure-svg academic-metric-svg" viewBox="0 0 916 420" role="img" :aria-label="`${title} 条件比较图`">
        <defs>
          <linearGradient :id="gradientId" x1="0" x2="1" y1="0" y2="0">
            <stop v-for="(color, index) in COOLWARM_LUT" :key="`${gradientId}-${index}`" :offset="`${(index / (COOLWARM_LUT.length - 1)) * 100}%`" :stop-color="color" />
          </linearGradient>
          <clipPath :id="clipId"><rect :x="plot.x" :y="plot.top" :width="plot.width" :height="plot.height" /></clipPath>
        </defs>

        <text v-if="higherIsBetter === false" class="academic-ramp-label" :x="metricRampX" :y="RAMP_LABEL_Y" text-anchor="start">← Lower is better</text>
        <text v-if="higherIsBetter !== false" class="academic-ramp-label" :x="metricRampX + RAMP_WIDTH" :y="RAMP_LABEL_Y" text-anchor="end">Higher is better →</text>
        <rect class="academic-metric-ramp" :x="metricRampX" :y="RAMP_Y" :width="RAMP_WIDTH" height="6" :fill="`url(#${gradientId})`" />

        <!-- The scatter branch retains the reference-style participant-level display for core outcomes. -->
        <g v-if="isScatterChart" aria-label="参与者散点图">
          <rect v-for="index in [0, 2]" :key="`band-${index}`" class="academic-row-band" :x="plot.x" :y="scatterRowY(index) - scatterRowGap / 2" :width="plot.width" :height="scatterRowGap" />
          <line v-for="tick in ticks" :key="`scatter-grid-${tick}`" class="academic-grid-line" :x1="scaleX(tick)" :y1="scatterPlot.top" :x2="scaleX(tick)" :y2="scatterPlot.bottom" />
          <rect class="academic-panel-border" :x="plot.x" :y="scatterPlot.top" :width="plot.width" :height="scatterPlot.height" />
          <g :clip-path="`url(#${clipId})`">
            <g v-for="(condition, conditionIndex) in displayConditions" :key="condition">
              <circle v-for="(value, valueIndex) in observations(conditionIndex)" :key="`${condition}-${valueIndex}`" class="academic-observation academic-metric-observation" :cx="scaleX(value)" :cy="scatterRowY(conditionIndex) + jitter(valueIndex, conditionIndex)" r="3.15" :fill="coolwarmColor(normalize(value, domain.low, domain.high))" />
              <line v-if="statistic(conditionIndex).ci95 != null" class="academic-ci-line" :x1="scaleX(statistic(conditionIndex).mean - statistic(conditionIndex).ci95)" :y1="scatterRowY(conditionIndex)" :x2="scaleX(statistic(conditionIndex).mean + statistic(conditionIndex).ci95)" :y2="scatterRowY(conditionIndex)" />
              <circle v-if="statistic(conditionIndex).mean != null" class="academic-center academic-metric-center" :cx="scaleX(statistic(conditionIndex).mean)" :cy="scatterRowY(conditionIndex)" r="4.5" />
            </g>
          </g>
          <g v-for="(condition, conditionIndex) in displayConditions" :key="`scatter-labels-${condition}`">
            <text class="academic-condition-label" :x="CONDITION_LABEL_X" :y="scatterRowY(conditionIndex) + 4" text-anchor="end">{{ condition }}</text>
            <text v-if="statistic(conditionIndex).mean != null" class="academic-value-label" :x="annotationX(scaleX(statistic(conditionIndex).mean))" :y="scatterRowY(conditionIndex) - 12" text-anchor="middle">M={{ displayFormat(statistic(conditionIndex).mean) }}</text>
          </g>
          <text v-for="tick in ticks" :key="`scatter-tick-${tick}`" class="academic-axis-label" :x="scaleX(tick)" :y="scatterPlot.bottom + 18" text-anchor="middle">{{ displayFormat(tick) }}</text>
          <text class="academic-axis-title" :x="plot.x + plot.width / 2" :y="scatterPlot.bottom + 37" text-anchor="middle">{{ axisTitle }}</text>
        </g>

        <!-- Bar charts are used for discrete task accuracy, counts, and rating scales. -->
        <g v-else-if="isBarChart" aria-label="条件均值柱状图">
          <line v-for="tick in ticks" :key="`bar-grid-${tick}`" class="academic-grid-line" :x1="plot.x" :y1="barY(tick)" :x2="plot.x + plot.width" :y2="barY(tick)" />
          <rect class="academic-panel-border" :x="plot.x" :y="barPlot.top" :width="plot.width" :height="barPlot.height" />
          <g v-for="(condition, conditionIndex) in displayConditions" :key="`bar-${condition}`">
            <rect v-if="statistic(conditionIndex).mean != null" class="academic-bar" :x="barX(conditionIndex)" :y="barY(statistic(conditionIndex).mean)" :width="barWidth" :height="barPlot.bottom - barY(statistic(conditionIndex).mean)" :fill="conditionColor(conditionIndex)" />
            <line v-if="statistic(conditionIndex).ci95 != null" class="academic-error-line" :x1="barCenterX(conditionIndex)" :y1="barY(statistic(conditionIndex).mean - statistic(conditionIndex).ci95)" :x2="barCenterX(conditionIndex)" :y2="barY(statistic(conditionIndex).mean + statistic(conditionIndex).ci95)" />
            <line v-if="statistic(conditionIndex).ci95 != null" class="academic-error-cap" :x1="barCenterX(conditionIndex) - 8" :y1="barY(statistic(conditionIndex).mean - statistic(conditionIndex).ci95)" :x2="barCenterX(conditionIndex) + 8" :y2="barY(statistic(conditionIndex).mean - statistic(conditionIndex).ci95)" />
            <line v-if="statistic(conditionIndex).ci95 != null" class="academic-error-cap" :x1="barCenterX(conditionIndex) - 8" :y1="barY(statistic(conditionIndex).mean + statistic(conditionIndex).ci95)" :x2="barCenterX(conditionIndex) + 8" :y2="barY(statistic(conditionIndex).mean + statistic(conditionIndex).ci95)" />
            <text v-if="statistic(conditionIndex).mean != null" class="academic-value-label academic-bar-value" :x="barCenterX(conditionIndex)" :y="Math.max(barPlot.top + 13, barY(statistic(conditionIndex).mean) - 8)" text-anchor="middle">{{ displayFormat(statistic(conditionIndex).mean) }}</text>
            <text class="academic-condition-label" :x="barCenterX(conditionIndex)" :y="barPlot.bottom + 22" text-anchor="middle">{{ condition }}</text>
          </g>
          <text v-for="tick in ticks" :key="`bar-tick-${tick}`" class="academic-axis-label" :x="plot.x - 12" :y="barY(tick) + 4" text-anchor="end">{{ displayFormat(tick) }}</text>
          <text class="academic-axis-title" :x="plot.x + plot.width / 2" :y="barPlot.bottom + 50" text-anchor="middle">{{ axisTitle }}</text>
        </g>

        <!-- Boxplots expose skew, quartiles, whiskers, and outliers for time/behavior metrics. -->
        <g v-else-if="isBoxplot" aria-label="条件分布箱线图">
          <line v-for="tick in ticks" :key="`box-grid-${tick}`" class="academic-grid-line" :x1="plot.x" :y1="boxY(tick)" :x2="plot.x + plot.width" :y2="boxY(tick)" />
          <rect class="academic-panel-border" :x="plot.x" :y="boxPlot.top" :width="plot.width" :height="boxPlot.height" />
          <g v-for="(condition, conditionIndex) in displayConditions" :key="`box-${condition}`">
            <g :clip-path="`url(#${clipId})`">
              <circle v-for="(value, valueIndex) in observations(conditionIndex)" :key="`${condition}-point-${valueIndex}`" class="academic-box-point" :cx="boxCenterX(conditionIndex) + jitter(valueIndex, conditionIndex) / 2" :cy="boxY(value)" r="2.7" :fill="conditionColor(conditionIndex)" />
            </g>
            <template v-if="boxSummary(conditionIndex)">
              <line class="academic-box-whisker" :x1="boxCenterX(conditionIndex)" :y1="boxY(boxSummary(conditionIndex).min)" :x2="boxCenterX(conditionIndex)" :y2="boxY(boxSummary(conditionIndex).q1)" />
              <line class="academic-box-whisker" :x1="boxCenterX(conditionIndex)" :y1="boxY(boxSummary(conditionIndex).q3)" :x2="boxCenterX(conditionIndex)" :y2="boxY(boxSummary(conditionIndex).max)" />
              <line class="academic-box-cap" :x1="boxCenterX(conditionIndex) - 14" :y1="boxY(boxSummary(conditionIndex).min)" :x2="boxCenterX(conditionIndex) + 14" :y2="boxY(boxSummary(conditionIndex).min)" />
              <line class="academic-box-cap" :x1="boxCenterX(conditionIndex) - 14" :y1="boxY(boxSummary(conditionIndex).max)" :x2="boxCenterX(conditionIndex) + 14" :y2="boxY(boxSummary(conditionIndex).max)" />
              <rect class="academic-box" :x="boxCenterX(conditionIndex) - 28" :y="boxY(boxSummary(conditionIndex).q3)" width="56" :height="Math.max(2, boxY(boxSummary(conditionIndex).q1) - boxY(boxSummary(conditionIndex).q3))" :fill="conditionColor(conditionIndex)" />
              <line class="academic-box-median" :x1="boxCenterX(conditionIndex) - 28" :y1="boxY(boxSummary(conditionIndex).median)" :x2="boxCenterX(conditionIndex) + 28" :y2="boxY(boxSummary(conditionIndex).median)" />
              <text class="academic-value-label academic-box-value" :x="boxCenterX(conditionIndex)" :y="Math.max(boxPlot.top + 13, boxY(boxSummary(conditionIndex).median) - 10)" text-anchor="middle">Mdn={{ displayFormat(boxSummary(conditionIndex).median) }}</text>
            </template>
            <text class="academic-condition-label" :x="boxCenterX(conditionIndex)" :y="boxPlot.bottom + 22" text-anchor="middle">{{ condition }}</text>
          </g>
          <text v-for="tick in ticks" :key="`box-tick-${tick}`" class="academic-axis-label" :x="plot.x - 12" :y="boxY(tick) + 4" text-anchor="end">{{ displayFormat(tick) }}</text>
          <text class="academic-axis-title" :x="plot.x + plot.width / 2" :y="boxPlot.bottom + 50" text-anchor="middle">{{ axisTitle }}</text>
        </g>

        <!-- Preference results use horizontal bars so rank and share labels remain immediately readable. -->
        <g v-else-if="isHorizontalBarChart" aria-label="条件水平条形图">
          <line v-for="tick in ticks" :key="`horizontal-grid-${tick}`" class="academic-grid-line" :x1="horizontalX(tick)" :y1="horizontalPlot.top" :x2="horizontalX(tick)" :y2="horizontalPlot.bottom" />
          <rect class="academic-panel-border" :x="horizontalPlot.x" :y="horizontalPlot.top" :width="horizontalPlot.width" :height="horizontalPlot.height" />
          <g v-for="(condition, conditionIndex) in displayConditions" :key="`horizontal-${condition}`">
            <rect v-if="statistic(conditionIndex).mean != null" class="academic-horizontal-bar" :x="horizontalPlot.x" :y="horizontalY(conditionIndex) - horizontalBarHeight / 2" :width="Math.max(0, horizontalX(statistic(conditionIndex).mean) - horizontalPlot.x)" :height="horizontalBarHeight" :fill="conditionColor(conditionIndex)" />
            <text class="academic-condition-label" :x="horizontalPlot.x - 14" :y="horizontalY(conditionIndex) + 4" text-anchor="end">{{ condition }}</text>
            <text v-if="statistic(conditionIndex).mean != null" class="academic-value-label" :x="Math.min(horizontalX(statistic(conditionIndex).mean) + 9, horizontalPlot.x + horizontalPlot.width - 5)" :y="horizontalY(conditionIndex) + 4" text-anchor="start">{{ displayFormat(statistic(conditionIndex).mean) }}</text>
          </g>
          <text v-for="tick in ticks" :key="`horizontal-tick-${tick}`" class="academic-axis-label" :x="horizontalX(tick)" :y="horizontalPlot.bottom + 20" text-anchor="middle">{{ displayFormat(tick) }}</text>
          <text class="academic-axis-title" :x="horizontalPlot.x + horizontalPlot.width / 2" :y="horizontalPlot.bottom + 50" text-anchor="middle">{{ axisTitle }}</text>
        </g>
      </svg>
    </div>
    <div v-else class="metric-empty">暂无有效数据</div>

    <div class="academic-metric-table" role="table" :aria-label="`${title} 数值表`">
      <div v-for="(condition, conditionIndex) in displayConditions" :key="`table-${condition}`" class="academic-metric-table-row" role="row">
        <strong>{{ condition }}</strong>
        <span>n={{ observations(conditionIndex).length }}</span>
        <span>{{ isBoxplot ? "Mdn" : "M" }}={{ statistic(conditionIndex).mean == null ? "—" : displayFormat(isBoxplot ? boxSummary(conditionIndex)?.median : statistic(conditionIndex).mean) }}</span>
        <span v-if="!isBoxplot">95% CI={{ statistic(conditionIndex).ci95 == null ? "—" : `±${displayFormat(statistic(conditionIndex).ci95)}` }}</span>
        <span v-else>Q1–Q3={{ boxSummary(conditionIndex) ? `${displayFormat(boxSummary(conditionIndex).q1)}–${displayFormat(boxSummary(conditionIndex).q3)}` : "—" }}</span>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from "vue";
import { COOLWARM_LUT, coolwarmColor } from "./academicFigureUtils";
import { exportSvgAsPng } from "./adminChartExport";

const props = defineProps({
  title: { type: String, required: true },
  metric: { type: String, required: true },
  series: { type: Object, default: () => ({}) },
  format: { type: Function, default: value => Number(value).toFixed(2) },
  domain: { type: Array, default: null },
  ticks: { type: Array, default: null },
  higherIsBetter: { type: Boolean, default: null },
  unit: { type: String, default: "" },
  chartType: { type: String, default: "scatter" }
});

const chartSvg = ref(null);
const displayConditions = ["BL", "SE", "TE", "CS"];
const CONDITION_LABEL_X = 90;
const RAMP_WIDTH = 240;
const RAMP_Y = 27;
const RAMP_LABEL_OFFSET = 2.1;
const RAMP_LABEL_Y = RAMP_Y - RAMP_LABEL_OFFSET;
const plot = { x: 112, width: 770, top: 72, bottom: 352, height: 280 };
const scatterPlot = { top: 72, bottom: 284, height: 212 };
const barPlot = { top: 72, bottom: 334, height: 262 };
const boxPlot = { top: 72, bottom: 334, height: 262 };
const horizontalPlot = { x: 150, width: 732, top: 72, bottom: 318, height: 246 };
const scatterRowGap = 53;
const barWidth = 92;
const horizontalBarHeight = 32;
const timeMetrics = new Set(["CTIRT", "CLT", "Initial Reading Time"]);
const accuracyMetrics = new Set(["CTIA", "CRA", "ACA", "CLA"]);
const ratingMetrics = new Set(["RC", "CA"]);
const isScatterChart = computed(() => props.chartType === "scatter");
const isBarChart = computed(() => props.chartType === "bar");
const isBoxplot = computed(() => props.chartType === "boxplot");
const isHorizontalBarChart = computed(() => props.chartType === "horizontal-bar");
const isTimeMetric = computed(() => timeMetrics.has(props.metric));
const gradientId = `academic-metric-coolwarm-${String(props.metric).toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
const clipId = `academic-metric-clip-${String(props.metric).toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;

const rawObservations = condition => {
  const source = props.series?.[condition];
  const values = Array.isArray(source) ? source : source?.observations || [];
  return values.filter(value => value != null && Number.isFinite(Number(value))).map(Number).map(value => chartValue(value));
};
const observationsByCondition = computed(() => displayConditions.map(rawObservations));
const allValues = computed(() => observationsByCondition.value.flat());
const hasData = computed(() => allValues.value.length > 0);
const domain = computed(() => {
  if (Array.isArray(props.domain) && props.domain.length === 2) return { low: Number(props.domain[0]), high: Number(props.domain[1]) };
  const values = allValues.value;
  if (accuracyMetrics.has(props.metric)) return { low: 0, high: 1 };
  if (ratingMetrics.has(props.metric)) return { low: 1, high: 7 };
  if (props.metric === "NASA-TLX" || props.metric.startsWith("NASA-TLX ")) return { low: 1, high: 7 };
  if (!values.length) return { low: 0, high: 1 };
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  if (isTimeMetric.value) {
    const low = Math.max(0, Math.floor((minimum - 0.25) / 0.5) * 0.5);
    const high = Math.max(low + 1, Math.ceil((maximum + 0.25) / 0.5) * 0.5);
    return { low, high };
  }
  const high = Math.max(1, Math.ceil(maximum * 1.1));
  return { low: 0, high };
});
const ticks = computed(() => {
  if (Array.isArray(props.ticks) && props.ticks.length) return props.ticks.map(Number);
  const { low, high } = domain.value;
  return Array.from({ length: 5 }, (_, index) => low + ((high - low) * index) / 4);
});
const axisTitle = computed(() => {
  if (isTimeMetric.value) return `${props.metric} (seconds)`;
  if (props.unit) return `${props.metric} (${props.unit})`;
  return props.metric;
});

function chartValue(value) { return isTimeMetric.value ? value / 1000 : value; }
function observations(index) { return observationsByCondition.value[index] || []; }
function mean(values) { return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null; }
function studentTCritical(sampleSize) {
  const table = { 2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571, 7: 2.447, 8: 2.365, 9: 2.306, 10: 2.262, 11: 2.228, 12: 2.201, 13: 2.179, 14: 2.160, 15: 2.145, 16: 2.131, 17: 2.120, 18: 2.110, 19: 2.101, 20: 2.093, 21: 2.086, 22: 2.080, 23: 2.074, 24: 2.069 };
  return table[sampleSize] || (sampleSize > 24 ? 1.96 : null);
}
function ci95(values) {
  if (values.length < 2) return values.length === 1 ? 0 : null;
  const center = mean(values);
  const variance = values.reduce((sum, value) => sum + (value - center) ** 2, 0) / (values.length - 1);
  return studentTCritical(values.length) * Math.sqrt(variance) / Math.sqrt(values.length);
}
function statistic(index) {
  const values = observations(index);
  // Small samples are shown descriptively until the formal study has enough observations for a stable t-based interval.
  const displayCi95 = values.length >= 4 ? ci95(values) : null;
  return { mean: mean(values), ci95: displayCi95 };
}
function quartile(values, fraction) {
  if (!values.length) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const position = (sorted.length - 1) * fraction;
  const lower = Math.floor(position);
  const upper = Math.ceil(position);
  if (lower === upper) return sorted[lower];
  return sorted[lower] + (sorted[upper] - sorted[lower]) * (position - lower);
}
function boxSummary(index) {
  const values = observations(index);
  if (!values.length) return null;
  return { min: Math.min(...values), q1: quartile(values, 0.25), median: quartile(values, 0.5), q3: quartile(values, 0.75), max: Math.max(...values) };
}
function normalize(value, low, high) { return Math.max(0, Math.min(1, (Number(value) - low) / Math.max(1e-9, high - low))); }
function scaleX(value) { return plot.x + normalize(value, domain.value.low, domain.value.high) * plot.width; }
const metricRampX = computed(() => plot.x + plot.width / 2 - RAMP_WIDTH / 2);
function scatterRowY(index) { return scatterPlot.top + index * scatterRowGap + 17; }
function jitter(valueIndex, conditionIndex) { return ((valueIndex % 5) - 2) * 7 + (conditionIndex % 2 ? 1 : -1); }
function annotationX(x) { return Math.max(plot.x + 25, Math.min(plot.x + plot.width - 25, x)); }
function conditionColor(index) { return coolwarmColor(index / (displayConditions.length - 1)); }
function scaleY(value, region) { return region.bottom - normalize(value, domain.value.low, domain.value.high) * region.height; }
function barY(value) { return scaleY(value, barPlot); }
function barX(index) { return plot.x + index * (plot.width / 4) + (plot.width / 4 - barWidth) / 2; }
function barCenterX(index) { return barX(index) + barWidth / 2; }
function boxY(value) { return scaleY(value, boxPlot); }
function boxCenterX(index) { return plot.x + (index + 0.5) * (plot.width / 4); }
function horizontalX(value) { return horizontalPlot.x + normalize(value, domain.value.low, domain.value.high) * horizontalPlot.width; }
function horizontalY(index) { return horizontalPlot.top + 39 + index * 50; }
function displayFormat(value) {
  if (value == null || !Number.isFinite(Number(value))) return "—";
  if (isTimeMetric.value) return Number(value).toFixed(2);
  if (accuracyMetrics.has(props.metric)) return Number(value).toFixed(2);
  if (ratingMetrics.has(props.metric)) return Number(value).toFixed(1);
  return Number(value).toFixed(2);
}
async function exportChart() { if (hasData.value) await exportSvgAsPng(chartSvg.value, `${fileName(props.metric)}.png`, { scale: 4 }); }
function fileName(value) { return String(value).trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "academic-metric"; }
</script>
