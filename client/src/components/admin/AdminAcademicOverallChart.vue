<template>
  <section class="academic-overall-figure" aria-label="整体条件比较图">
    <div class="academic-figure-toolbar">
      <button class="academic-export-button" type="button" @click="exportChart">导出 PNG</button>
    </div>

    <svg ref="chartSvg" class="academic-overall-svg academic-figure-svg" viewBox="0 0 854.27125 342.566363" role="img" aria-label="Overall completion time and overall task accuracy 条件比较图">
      <defs>
        <linearGradient id="academic-time-coolwarm" x1="0" x2="1" y1="0" y2="0">
          <stop v-for="(color, index) in COOLWARM_LUT" :key="`time-stop-${index}`" :offset="`${(index / (COOLWARM_LUT.length - 1)) * 100}%`" :stop-color="color" />
        </linearGradient>
        <linearGradient id="academic-accuracy-coolwarm" x1="0" x2="1" y1="0" y2="0">
          <stop v-for="(color, index) in COOLWARM_LUT" :key="`accuracy-stop-${index}`" :offset="`${(index / (COOLWARM_LUT.length - 1)) * 100}%`" :stop-color="color" />
        </linearGradient>
        <clipPath id="academic-time-clip"><rect :x="TIME_X" :y="PLOT_TOP" :width="PLOT_WIDTH" :height="PLOT_HEIGHT" /></clipPath>
        <clipPath id="academic-accuracy-clip"><rect :x="ACCURACY_X" :y="PLOT_TOP" :width="PLOT_WIDTH" :height="PLOT_HEIGHT" /></clipPath>
      </defs>

      <text class="academic-ramp-label" :x="timeRampX" :y="timeRampLabelY" text-anchor="start">← Lower is better</text>
      <rect :x="timeRampX" :y="rampY" :width="rampWidth" height="6" fill="url(#academic-time-coolwarm)" />
      <text class="academic-ramp-label" :x="accuracyRampX + rampWidth" :y="timeRampLabelY" text-anchor="end">Higher is better →</text>
      <rect :x="accuracyRampX" :y="rampY" :width="rampWidth" height="6" fill="url(#academic-accuracy-coolwarm)" />

      <g aria-label="Overall completion time">
        <rect v-for="index in [0, 2]" :key="`time-band-${index}`" class="academic-row-band" :x="TIME_X" :y="rowY(index) - ROW_GAP / 2" :width="PLOT_WIDTH" :height="ROW_GAP" />
        <line v-for="tick in timeTicks" :key="`time-grid-${tick}`" class="academic-grid-line" :x1="timeScale(tick)" :y1="PLOT_TOP" :x2="timeScale(tick)" :y2="PLOT_BOTTOM" />
        <rect class="academic-panel-border" :x="TIME_X" :y="PLOT_TOP" :width="PLOT_WIDTH" :height="PLOT_HEIGHT" />
        <g clip-path="url(#academic-time-clip)">
          <g v-for="(condition, conditionIndex) in displayConditions" :key="`time-${condition}`">
            <circle v-for="(value, valueIndex) in timeObservations(conditionIndex)" :key="`time-dot-${condition}-${valueIndex}`" class="academic-observation academic-time-observation" :cx="timeScale(value)" :cy="rowY(conditionIndex) + timeJitter(valueIndex, conditionIndex)" r="2.645751" :fill="coolwarmColor(normalize(value, timeBounds.low, timeBounds.high))" />
            <line v-if="timeStatistic(conditionIndex).ci95 != null" class="academic-ci-line" :x1="timeScale(timeStatistic(conditionIndex).mean - timeStatistic(conditionIndex).ci95)" :y1="rowY(conditionIndex)" :x2="timeScale(timeStatistic(conditionIndex).mean + timeStatistic(conditionIndex).ci95)" :y2="rowY(conditionIndex)" />
            <circle v-if="timeStatistic(conditionIndex).mean != null" class="academic-overall-center" :cx="timeScale(timeStatistic(conditionIndex).mean)" :cy="rowY(conditionIndex)" r="4.25" />
          </g>
        </g>
        <g v-for="(condition, conditionIndex) in displayConditions" :key="`time-label-${condition}`">
          <text class="academic-condition-label" :x="CONDITION_LABEL_X" :y="rowY(conditionIndex) + 4" text-anchor="end">{{ conditionLabel(condition) }}</text>
          <text v-if="timeStatistic(conditionIndex).mean != null" class="academic-value-label" :x="timeScale(timeStatistic(conditionIndex).mean)" :y="rowY(conditionIndex) - 13" text-anchor="middle">M={{ timeStatistic(conditionIndex).mean.toFixed(1) }}</text>
        </g>
        <text v-for="tick in timeTicks" :key="`time-label-${tick}`" class="academic-axis-label" :x="timeScale(tick)" :y="PLOT_BOTTOM + 14" text-anchor="middle">{{ tick.toFixed(0) }}</text>
        <text class="academic-axis-title" :x="TIME_X + PLOT_WIDTH / 2" :y="PLOT_BOTTOM + 28.6" text-anchor="middle">Overall completion time (seconds)</text>
      </g>

      <g aria-label="Overall task accuracy">
        <rect v-for="index in [0, 2]" :key="`accuracy-band-${index}`" class="academic-row-band" :x="ACCURACY_X" :y="rowY(index) - ROW_GAP / 2" :width="PLOT_WIDTH" :height="ROW_GAP" />
        <line v-for="tick in accuracyTicks" :key="`accuracy-grid-${tick}`" class="academic-grid-line" :x1="accuracyScale(tick)" :y1="PLOT_TOP" :x2="accuracyScale(tick)" :y2="PLOT_BOTTOM" />
        <rect class="academic-panel-border" :x="ACCURACY_X" :y="PLOT_TOP" :width="PLOT_WIDTH" :height="PLOT_HEIGHT" />
        <g clip-path="url(#academic-accuracy-clip)">
          <g v-for="(condition, conditionIndex) in displayConditions" :key="`accuracy-${condition}`">
            <circle v-for="(value, valueIndex) in accuracyObservations(conditionIndex)" :key="`accuracy-dot-${condition}-${valueIndex}`" class="academic-observation academic-accuracy-observation" :cx="accuracyScale(value)" :cy="rowY(conditionIndex) + spreadEqualValues(conditionIndex, value, valueIndex)" r="2.44949" :fill="coolwarmColor(normalize(value, 0, 1))" />
          </g>
        </g>
        <g v-for="(condition, conditionIndex) in displayConditions" :key="`accuracy-label-${condition}`">
          <circle v-if="accuracyStatistic(conditionIndex).median != null" class="academic-overall-center" :cx="accuracyScale(accuracyStatistic(conditionIndex).median)" :cy="rowY(conditionIndex)" r="4.25" />
          <g v-if="accuracyStatistic(conditionIndex).median != null">
            <rect class="academic-accuracy-label-background" :x="accuracyScale(accuracyStatistic(conditionIndex).median) + 8" :y="rowY(conditionIndex) - 25" width="54" height="16" rx="1" />
            <text class="academic-value-label academic-accuracy-label" :x="accuracyScale(accuracyStatistic(conditionIndex).median) + 12" :y="rowY(conditionIndex) - 13" text-anchor="start">Mdn={{ accuracyStatistic(conditionIndex).median.toFixed(2) }}</text>
          </g>
        </g>
        <text v-for="tick in accuracyTicks" :key="`accuracy-label-${tick}`" class="academic-axis-label" :x="accuracyScale(tick)" :y="PLOT_BOTTOM + 14" text-anchor="middle">{{ tick.toFixed(2) }}</text>
        <text class="academic-axis-title" :x="ACCURACY_X + PLOT_WIDTH / 2" :y="PLOT_BOTTOM + 28.6" text-anchor="middle">Overall task accuracy</text>
      </g>
    </svg>
  </section>
</template>

<script setup>
import { computed, ref } from "vue";
import { exportSvgAsPng } from "./adminChartExport";
import { COOLWARM_LUT, coolwarmColor } from "./academicFigureUtils";

const chartSvg = ref(null);
const props = defineProps({
  overallTime: { type: Array, default: () => [] },
  overallAccuracy: { type: Array, default: () => [] }
});

// These dimensions are a direct mapping of figsize=(13.5, 5.35) and
// subplots_adjust(left=.13, right=.985, bottom=.12, top=.80, wspace=.12)
// onto the tight-cropped SVG canvas emitted by Matplotlib (854.27125 × 342.566363 pt).
const DISPLAY_CONDITIONS = ["BL", "SE", "TE", "CS"];
const CONDITION_LABELS = {
  TE: "TE",
  CS: "CS",
  SE: "SE",
  BL: "BL"
};
const CONDITION_INDEX = { TE: 0, CS: 1, SE: 2, BL: 3 };
const FIGURE_WIDTH = 854.27125;
const FIGURE_HEIGHT = 342.566363;
const TIME_X = 21.77125;
const ACCURACY_X = 460.821816;
const PLOT_WIDTH = 392.009434;
const PLOT_TOP = 48.189582;
const PLOT_BOTTOM = 310.125582;
const PLOT_HEIGHT = PLOT_BOTTOM - PLOT_TOP;
const ROW_GAP = PLOT_HEIGHT / 4;
const ROW_TOP = PLOT_TOP + ROW_GAP / 2;
const CONDITION_LABEL_X = 18.5;
const accuracyTicks = [0.5, 0.75, 1];
const displayConditions = DISPLAY_CONDITIONS;
const timeRampX = TIME_X + PLOT_WIDTH * 0.14;
const accuracyRampX = ACCURACY_X + PLOT_WIDTH * 0.14;
const rampWidth = PLOT_WIDTH * 0.74;
const rampY = 13.906782;
const RAMP_LABEL_OFFSET = 2.1;
const timeRampLabelY = rampY - RAMP_LABEL_OFFSET;

async function exportChart() {
  await exportSvgAsPng(chartSvg.value, "overall-performance.png", { scale: 4 });
}

const timeSeries = computed(() => displayConditions.map(condition => valuesFor(props.overallTime, CONDITION_INDEX[condition]).map(value => value / 1000)));
const accuracySeries = computed(() => displayConditions.map(condition => valuesFor(props.overallAccuracy, CONDITION_INDEX[condition])));
const timeSummaryValues = computed(() => timeSeries.value.flat());
const timeBounds = computed(() => {
  const values = timeSummaryValues.value;
  const fallback = values.length ? values : [60, 180];
  const summaries = timeSeries.value.map(valuesForCondition => statistic(valuesForCondition));
  const candidates = [...fallback, ...summaries.flatMap(item => item.ci95 == null ? [] : [item.mean - item.ci95, item.mean + item.ci95])];
  return {
    low: Math.floor(Math.min(...candidates) / 25) * 25,
    high: Math.ceil(Math.max(...candidates) / 25) * 25
  };
});
const timeXDomain = computed(() => ({ low: timeBounds.value.low - 10, high: timeBounds.value.high + 8 }));
const timeTicks = computed(() => {
  const ticks = [];
  for (let tick = timeBounds.value.low; tick <= timeBounds.value.high; tick += 50) ticks.push(tick);
  return ticks;
});

function valuesFor(matrix, sourceIndex) {
  return (matrix || []).map(row => row?.[sourceIndex]).filter(value => value != null && Number.isFinite(Number(value))).map(Number);
}
function mean(values) { return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null; }
function median(values) {
  if (!values.length) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}
function studentTCritical(sampleSize) {
  const table = { 2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571, 7: 2.447, 8: 2.365, 9: 2.306, 10: 2.262, 11: 2.228, 12: 2.201, 13: 2.179, 14: 2.160, 15: 2.145, 16: 2.131, 17: 2.120, 18: 2.110, 19: 2.101, 20: 2.093, 21: 2.086, 22: 2.080, 23: 2.074, 24: 2.069 };
  return table[sampleSize] || (sampleSize > 30 ? 1.96 : null);
}
function ci95(values) {
  if (values.length < 2) return values.length === 1 ? 0 : null;
  const center = mean(values);
  const variance = values.reduce((sum, value) => sum + (value - center) ** 2, 0) / (values.length - 1);
  return studentTCritical(values.length) * Math.sqrt(variance) / Math.sqrt(values.length);
}
function statistic(values) {
  // Do not draw an inferential 95% CI for an interim condition with fewer than
  // four observations. With n=2 or n=3, the t critical value can make the
  // plotting domain span thousands of seconds and hide the actual data.
  // The formal n=24 study view still uses the manuscript's t-based CI.
  const displayCi95 = values.length >= 4 ? ci95(values) : null;
  return { mean: mean(values), median: median(values), ci95: displayCi95 };
}
function rowY(index) { return ROW_TOP + index * ROW_GAP; }
function normalize(value, low, high) { return Math.max(0, Math.min(1, (Number(value) - low) / Math.max(1e-9, high - low))); }
function conditionLabel(condition) { return CONDITION_LABELS[condition] || condition; }
function timeObservations(displayIndex) { return timeSeries.value[displayIndex] || []; }
function accuracyObservations(displayIndex) { return accuracySeries.value[displayIndex] || []; }
function timeStatistic(displayIndex) { return statistic(timeObservations(displayIndex)); }
function accuracyStatistic(displayIndex) { return statistic(accuracyObservations(displayIndex)); }
function timeScale(value) { return TIME_X + normalize(value, timeXDomain.value.low, timeXDomain.value.high) * PLOT_WIDTH; }
function accuracyScale(value) { return ACCURACY_X + normalize(value, 0.475, 1.025) * PLOT_WIDTH; }
function timeJitter(valueIndex, conditionIndex) {
  const count = timeObservations(conditionIndex).length;
  if (!count) return 0;
  const order = Array.from({ length: count }, (_, index) => index).sort((left, right) => ((left * 7 + conditionIndex * 3) % count) - ((right * 7 + conditionIndex * 3) % count));
  const rank = order.indexOf(valueIndex);
  const offset = count === 1 ? 0 : -0.25 + (0.5 * rank) / (count - 1);
  return offset * ROW_GAP;
}
function spreadEqualValues(conditionIndex, value, valueIndex) {
  const values = accuracyObservations(conditionIndex);
  const sameIndexes = values.map((candidate, index) => candidate === value ? index : -1).filter(index => index >= 0);
  const groupIndex = sameIndexes.indexOf(valueIndex);
  const count = sameIndexes.length;
  if (count === 1) return (valueIndex % 2 ? 0.13 : -0.13) * ROW_GAP;
  const half = Math.floor((count + 1) / 2);
  const offsets = Array.from({ length: half }, (_, index) => -(index + 1)).flatMap((negative, index) => [negative, index + 1]).slice(0, count);
  return offsets[groupIndex] * 0.062 * ROW_GAP;
}
</script>
