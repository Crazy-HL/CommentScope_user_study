<template>
  <div class="admin-simple-table-wrap">
    <table class="admin-simple-table admin-detail-table">
      <thead>
        <tr><th>指标</th><th>界面</th><th>n</th><th>均值</th><th>中位数</th><th>标准差</th><th>95% CI</th></tr>
      </thead>
      <tbody>
        <template v-for="group in groups" :key="group.name">
          <tr v-for="condition in conditions" :key="group.name + condition">
            <th scope="row" class="metric-name-cell">{{ group.label }}</th>
            <td><span class="condition-badge" :class="`condition-${condition.toLowerCase()}`">{{ condition }}</span></td>
            <td>{{ metrics[group.name]?.[condition]?.n ?? 0 }}</td>
            <td>{{ formatStat(group, metrics[group.name]?.[condition]?.mean) }}</td>
            <td>{{ formatStat(group, metrics[group.name]?.[condition]?.median) }}</td>
            <td>{{ formatStat(group, metrics[group.name]?.[condition]?.stddev) }}</td>
            <td>{{ formatStat(group, metrics[group.name]?.[condition]?.ci95) }}</td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
</template>

<script setup>
const props = defineProps({
  groups: { type: Array, required: true },
  metrics: { type: Object, required: true },
  conditions: { type: Array, required: true },
});

function formatNumber(value, digits = 2) {
  return value == null || Number.isNaN(Number(value)) ? "—" : Number(value).toFixed(digits);
}
function formatStat(group, value) {
  if (value == null) return "—";
  if (["CTIRT", "CLT", "Initial Reading Time"].includes(group.name)) return `${formatNumber(Number(value) / 1000, 2)} s`;
  if (group.name === "NSD") return formatNumber(value, 3);
  if (["CTIA", "CRA", "ACA", "CLA"].includes(group.name)) return formatNumber(value, 2);
  if (["RC", "CA"].includes(group.name)) return formatNumber(value, 1);
  return formatNumber(value, 2);
}
</script>
