<template>
  <section class="metric-figure" :aria-label="title">
    <div class="academic-figure-toolbar">
      <span>{{ title }}</span>
      <button class="academic-export-button" type="button" :disabled="!hasData" @click="exportChart">导出 PNG</button>
    </div>

    <div v-if="hasData" class="metric-chart-scroll">
      <svg ref="chartSvg" class="academic-figure-svg metric-figure-svg" viewBox="0 0 1120 430" role="img" :aria-label="`${title} 条件比较图`">
        <defs>
          <linearGradient :id="gradientId" x1="0" x2="1" y1="0" y2="0">
            <stop offset="0%" stop-color="#3b4cc0" />
            <stop offset="25%" stop-color="#8db0fe" />
            <stop offset="50%" stop-color="#dddcdc" />
            <stop offset="75%" stop-color="#f49a7a" />
            <stop offset="100%" stop-color="#b40426" />
          </linearGradient>
        </defs>

        <text class="academic-ramp-label" x="135" y="17" text-anchor="start">{{ higherIsBetter === false ? "← Lower is better" : "" }}</text>
        <rect x="190" y="23" width="300" height="10" rx="1" :fill="`url(#${gradientId})`" />
        <text class="academic-ramp-label" x="650" y="17" text-anchor="start">{{ higherIsBetter !== false ? "Higher is better →" : "" }}</text>

        <rect v-for="index in [0, 2]" :key="`band-${index}`" class="academic-row-band" :x="PLOT_X" :y="rowY(index) - 27" :width="PLOT_WIDTH" height="54" />
        <line v-for="tick in ticks" :key="`grid-${tick}`" class="academic-grid-line" :x1="scaleX(tick)" y1="92" :x2="scaleX(tick)" y2="336" />

        <g v-for="(condition, conditionIndex) in displayConditions" :key="condition">
          <text class="academic-condition-label" x="102" :y="rowY(conditionIndex) + 5" text-anchor="end">{{ conditionLabel(condition) }}</text>
          <circle
            v-for="(value, valueIndex) in observations(conditionIndex)"
            :key="`${condition}-${valueIndex}`"
            class="academic-observation"
            :cx="scaleX(value)"
            :cy="rowY(conditionIndex) + jitter(valueIndex, conditionIndex)"
            r="4.5"
            :fill="chartCoolwarmColor(normalize(value, domain.low, domain.high))"
          />
          <line v-if="statistic(conditionIndex).ci95 != null" class="academic-ci-line" :x1="scaleX(statistic(conditionIndex).mean - statistic(conditionIndex).ci95)" :y1="rowY(conditionIndex)" :x2="scaleX(statistic(conditionIndex).mean + statistic(conditionIndex).ci95)" :y2="rowY(conditionIndex)" />
          <circle v-if="statistic(conditionIndex).mean != null" class="academic-center" :cx="scaleX(statistic(conditionIndex).mean)" :cy="rowY(conditionIndex)" r="6" />
          <text v-if="statistic(conditionIndex).mean != null" class="academic-value-label" :x="annotationX(scaleX(statistic(conditionIndex).mean))" :y="rowY(conditionIndex) - 13" text-anchor="middle">M={{ displayFormat(statistic(conditionIndex).mean) }}</text>
        </g>

        <text v-for="tick in ticks" :key="`label-${tick}`" class="academic-axis-label" :x="scaleX(tick)" y="360" text-anchor="middle">{{ displayFormat(tick) }}</text>
        <text class="academic-axis-title" :x="PLOT_X + PLOT_WIDTH / 2" y="391" text-anchor="middle">{{ axisTitle }}</text>
      </svg>
    </div>
    <div v-else class="metric-empty">暂无有效数据</div>

    <div class="metric-table" role="table" :aria-label="`${title} 数值表`">
      <div v-for="condition in displayConditions" :key="`table-${condition}`" class="metric-table-row" role="row">
        <strong>{{ conditionLabel(condition) }}</strong>
        <span>n={{ series[condition]?.n || 0 }}</span>
        <span>M={{ series[condition]?.mean == null ? "—" : format(series[condition].mean) }}</span>
        <span>Mdn={{ series[condition]?.median == null ? "—" : format(series[condition].median) }}</span>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from "vue";
import { exportSvgAsPng } from "./adminChartExport";
import { coolwarmColor } from "./academicFigureUtils";

const props = defineProps({
  title: { type: String, required: true },
  metric: { type: String, required: true },
  series: { type: Object, default: () => ({}) },
  higherIsBetter: { type: Boolean, default: null },
  format: { type: Function, default: value => Number(value).toFixed(2) },
  unit: { type: String, default: "" }
});

const chartSvg = ref(null);
const displayConditions = ["BL", "SE", "TE", "CS"];
const conditionLabels = { TE: "Text-End", CS: "Click-to-Show", SE: "Sentence-End", BL: "Between-Line" };
const PLOT_X = 135;
const PLOT_WIDTH = 870;
const ROW_TOP = 118;
const ROW_GAP = 65;
const timeMetrics = new Set(["CTIRT", "CLT", "Initial Reading Time"]);
const accuracyMetrics = new Set(["CTIA", "CRA", "ACA", "CLA"]);
const ratingMetrics = new Set(["RC", "CA"]);
const gradientId = `metric-coolwarm-${String(props.metric).toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;

const isTimeMetric = computed(() => timeMetrics.has(props.metric));
const rawObservations = condition => (props.series[condition]?.observations || []).filter(value => value != null && Number.isFinite(Number(value))).map(Number);
const observationsByCondition = computed(() => displayConditions.map(condition => rawObservations(condition).map(value => chartValue(value))));
const allValues = computed(() => observationsByCondition.value.flat());
const hasData = computed(() => allValues.value.length > 0);
const domain = computed(() => {
  const values = allValues.value;
  if (!values.length) return defaultDomain();
  if (accuracyMetrics.has(props.metric)) return { low: 0, high: 1 };
  if (ratingMetrics.has(props.metric)) return { low: 1, high: 7 };
  if (isTimeMetric.value) {
    const low = Math.max(0, Math.floor((Math.min(...values) - 0.25) / 0.5) * 0.5);
    const high = Math.max(low + 1, Math.ceil((Math.max(...values) + 0.25) / 0.5) * 0.5);
    return { low, high };
  }
  const high = Math.max(1, Math.ceil(Math.max(...values) * 1.1));
  return { low: 0, high };
});
const ticks = computed(() => {
  const { low, high } = domain.value;
  const count = isTimeMetric.value || high - low <= 10 ? 5 : 5;
  return Array.from({ length: count }, (_, index) => low + ((high - low) * index) / (count - 1));
});
const axisTitle = computed(() => {
  if (isTimeMetric.value) return `${props.metric} (seconds)`;
  if (props.unit) return `${props.metric} (${props.unit})`;
  return props.metric;
});

async function exportChart() {
  if (!hasData.value) return;
  await exportSvgAsPng(chartSvg.value, `${fileName(props.metric)}.png`, { scale: 4 });
}
function fileName(value) {
  return String(value).trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "metric-chart";
}
function defaultDomain() {
  if (accuracyMetrics.has(props.metric)) return { low: 0, high: 1 };
  if (ratingMetrics.has(props.metric)) return { low: 1, high: 7 };
  return { low: 0, high: 1 };
}
function chartValue(value) { return isTimeMetric.value ? value / 1000 : value; }
function valuesForCondition(displayIndex) { return observationsByCondition.value[displayIndex] || []; }
function observations(displayIndex) { return valuesForCondition(displayIndex); }
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
function statistic(displayIndex) {
  const values = observations(displayIndex);
  return { mean: mean(values), ci95: ci95(values) };
}
function scaleX(value) { return PLOT_X + normalize(value, domain.value.low, domain.value.high) * PLOT_WIDTH; }
function normalize(value, low, high) { return Math.max(0, Math.min(1, (Number(value) - low) / Math.max(1e-9, high - low))); }
function jitter(valueIndex, conditionIndex) { return ((valueIndex % 5) - 2) * 7 + (conditionIndex % 2 ? 1 : -1); }
function annotationX(x) { return Math.max(PLOT_X + 20, Math.min(PLOT_X + PLOT_WIDTH - 20, x)); }
function displayFormat(value) {
  if (isTimeMetric.value) return Number(value).toFixed(2);
  if (accuracyMetrics.has(props.metric)) return Number(value).toFixed(2);
  if (ratingMetrics.has(props.metric)) return Number(value).toFixed(1);
  return Number(value).toFixed(2);
}
const chartCoolwarmColor = coolwarmColor;
</script>
