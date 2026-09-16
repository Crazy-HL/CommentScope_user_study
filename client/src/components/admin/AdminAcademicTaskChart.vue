<template>
  <section class="academic-task-figure" aria-label="任务级条件比较图">
    <div class="academic-figure-toolbar">
      <button class="academic-export-button" type="button" @click="exportChart">导出 PNG</button>
    </div>

    <svg ref="chartSvg" class="academic-task-svg academic-figure-svg" viewBox="0 0 916.086406 320.917469" role="img" aria-label="Task-type accuracy 条件比较图">
      <g class="academic-figure-legend" aria-label="条件图例">
        <g v-for="(condition, conditionIndex) in displayConditions" :key="`legend-${condition}`" :transform="`translate(${legendX(conditionIndex)}, 9.538437)`">
          <line class="academic-task-legend-ci" x1="0" y1="-5" x2="0" y2="5" :stroke="conditionColor(conditionIndex)" />
          <line class="academic-task-legend-cap" x1="-10" y1="-5" x2="10" y2="-5" :stroke="conditionColor(conditionIndex)" />
          <line class="academic-task-legend-cap" x1="-10" y1="5" x2="10" y2="5" :stroke="conditionColor(conditionIndex)" />
          <circle class="academic-task-legend-center" r="3.1" :fill="conditionColor(conditionIndex)" />
          <text class="academic-legend-label" x="15" y="3.5">{{ conditionLabel(condition) }}</text>
        </g>
      </g>

      <line v-for="tick in ticks" :key="`task-grid-${tick}`" class="academic-task-grid-line" :x1="PLOT_LEFT" :y1="scaleY(tick)" :x2="PLOT_RIGHT" :y2="scaleY(tick)" />
      <text v-for="tick in ticks" :key="`task-y-label-${tick}`" class="academic-axis-label" :x="Y_LABEL_X" :y="scaleY(tick) + 4" text-anchor="end">{{ tick.toFixed(2) }}</text>
      <rect class="academic-panel-border" :x="PLOT_LEFT" :y="PLOT_TOP" :width="PLOT_WIDTH" :height="PLOT_HEIGHT" />
      <g clip-path="url(#academic-task-clip)">
        <g v-for="condition in displayConditions" :key="`task-mean-line-${condition}`">
          <polyline
            v-if="taskMeanPoints(condition)"
            class="academic-task-mean-line"
            :points="taskMeanPoints(condition)"
            :stroke="conditionColor(displayConditions.indexOf(condition))"
          />
        </g>
      </g>

      <g v-for="(task, taskIndex) in tasks" :key="task">
        <g v-for="(condition, conditionIndex) in displayConditions" :key="`${task}-${condition}`">
          <g clip-path="url(#academic-task-clip)">
            <circle v-for="(value, valueIndex) in observations(task, condition)" :key="`${task}-${condition}-${valueIndex}`" class="academic-task-observation" :cx="taskX(taskIndex) + conditionOffset(conditionIndex) + taskJitter(valueIndex, conditionIndex, taskIndex)" :cy="scaleY(value)" r="2.345208" :fill="conditionColor(conditionIndex)" />
          </g>
          <g v-if="statistic(task, condition).ci95 != null">
            <line class="academic-task-ci" :x1="taskX(taskIndex) + conditionOffset(conditionIndex)" :y1="scaleY(clamp(statistic(task, condition).mean - statistic(task, condition).ci95))" :x2="taskX(taskIndex) + conditionOffset(conditionIndex)" :y2="scaleY(clamp(statistic(task, condition).mean + statistic(task, condition).ci95))" :stroke="conditionColor(conditionIndex)" />
            <line class="academic-task-cap" :x1="taskX(taskIndex) + conditionOffset(conditionIndex) - 2.5" :y1="scaleY(clamp(statistic(task, condition).mean - statistic(task, condition).ci95))" :x2="taskX(taskIndex) + conditionOffset(conditionIndex) + 2.5" :y2="scaleY(clamp(statistic(task, condition).mean - statistic(task, condition).ci95))" :stroke="conditionColor(conditionIndex)" />
            <line class="academic-task-cap" :x1="taskX(taskIndex) + conditionOffset(conditionIndex) - 2.5" :y1="scaleY(clamp(statistic(task, condition).mean + statistic(task, condition).ci95))" :x2="taskX(taskIndex) + conditionOffset(conditionIndex) + 2.5" :y2="scaleY(clamp(statistic(task, condition).mean + statistic(task, condition).ci95))" :stroke="conditionColor(conditionIndex)" />
          </g>
          <circle v-if="statistic(task, condition).mean != null" class="academic-task-center" :cx="taskX(taskIndex) + conditionOffset(conditionIndex)" :cy="scaleY(statistic(task, condition).mean)" r="3.1" :fill="conditionColor(conditionIndex)" />
        </g>
        <text class="academic-task-label" :x="taskX(taskIndex)" :y="PLOT_BOTTOM + 10" text-anchor="middle">{{ taskLines(task)[0] }}</text>
        <text class="academic-task-label" :x="taskX(taskIndex)" :y="PLOT_BOTTOM + 24" text-anchor="middle">{{ taskLines(task)[1] }}</text>
      </g>
      <text class="academic-axis-title academic-task-y-title" :x="TASK_Y_TITLE_X" :y="(PLOT_TOP + PLOT_BOTTOM) / 2" text-anchor="middle" transform="rotate(-90 13 176.152)">Task-type accuracy</text>

      <defs>
        <clipPath id="academic-task-clip"><rect :x="PLOT_LEFT" :y="PLOT_TOP" :width="PLOT_WIDTH" :height="PLOT_HEIGHT" /></clipPath>
      </defs>
    </svg>
  </section>
</template>

<script setup>
import { ref } from "vue";
import { exportSvgAsPng } from "./adminChartExport";


const chartSvg = ref(null);
const props = defineProps({
  taskAccuracy: { type: Object, default: () => ({}) }
});

const displayConditions = ["BL", "SE", "TE", "CS"];
const conditionLabels = {
  TE: "TE",
  CS: "CS",
  SE: "SE",
  BL: "BL"
};
// These are the exact four discrete samples emitted by the reference
// Matplotlib coolwarm palette (plt.get_cmap("coolwarm")(linspace(.08, .92, 4))).
const conditionColors = ["#536edd", "#b3cdfb", "#f5c0a7", "#d0473d"];
const tasks = ["Article Comprehension", "Comment-Linked Comprehension", "Comment Location"];
const ticks = [0, 0.25, 0.5, 0.75, 1];
const FIGURE_WIDTH = 916.086406;
const FIGURE_HEIGHT = 320.917469;
const PLOT_LEFT = 44.706406;
const PLOT_RIGHT = 914.646406;
const PLOT_WIDTH = PLOT_RIGHT - PLOT_LEFT;
const PLOT_TOP = 63.832;
const PLOT_BOTTOM = 288.472;
const PLOT_HEIGHT = PLOT_BOTTOM - PLOT_TOP;
const X_LOW = -0.55;
const X_HIGH = 2.45;
const Y_LABEL_X = 39;
const TASK_Y_TITLE_X = 13;

async function exportChart() {
  await exportSvgAsPng(chartSvg.value, "task-performance-profile.png", { scale: 4 });
}
function conditionColor(index) { return conditionColors[index]; }
function conditionLabel(condition) { return conditionLabels[condition] || condition; }
function valuesFor(task, condition) {
  const sourceIndex = { TE: 0, CS: 1, SE: 2, BL: 3 }[condition];
  return (props.taskAccuracy?.[task] || []).map(row => row?.[sourceIndex]).filter(value => value != null && Number.isFinite(Number(value))).map(Number);
}
function mean(values) { return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null; }
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
function statistic(task, condition) {
  const values = valuesFor(task, condition);
  return { mean: mean(values), ci95: ci95(values) };
}
function observations(task, condition) { return valuesFor(task, condition); }
function taskMeanPoints(condition) {
  const points = tasks.map((task, taskIndex) => {
    const current = statistic(task, condition);
    if (current.mean == null) return null;
    return `${taskX(taskIndex) + conditionOffset(displayConditions.indexOf(condition))},${scaleY(current.mean)}`;
  });
  return points.every(Boolean) ? points.join(" ") : "";
}
function taskX(index) { return PLOT_LEFT + ((index - X_LOW) / (X_HIGH - X_LOW)) * PLOT_WIDTH; }
function conditionOffset(index) { return (index - 1.5) * 0.16 * (PLOT_WIDTH / (X_HIGH - X_LOW)); }
function taskJitter(valueIndex, conditionIndex, taskIndex) {
  const value = 0.027 * Math.sin(valueIndex * 1.7 + conditionIndex * 0.9 + taskIndex * 0.4);
  return value * (PLOT_WIDTH / (X_HIGH - X_LOW));
}
function scaleY(value) { return PLOT_BOTTOM - Number(value) * PLOT_HEIGHT; }
function clamp(value) { return Math.max(0, Math.min(1, Number(value))); }
const LEGEND_X = [350.7975, 406.230313, 461.8975, 517.324063];
function legendX(index) { return LEGEND_X[index]; }
function taskLines(task) {
  if (task === "Article Comprehension") return ["Article", "Comprehension"];
  if (task === "Comment-Linked Comprehension") return ["Comment-Linked", "Comprehension"];
  return ["Comment", "Location"];
}
</script>
