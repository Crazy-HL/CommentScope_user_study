# Adaptive Academic Chart Types Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the administrator paper-analysis page use the most readable chart type for each metric while keeping the supplied CommentScope Matplotlib visual language and PNG export behavior.

**Architecture:** Keep the two reference-style SVG figures as dedicated components. Extend the existing reusable academic metric component with an explicit `chartType` prop and render scatter, bar, boxplot, or horizontal-bar geometry from the same condition-ordered series. `AdminDashboard.vue` assigns chart types by metric group; all data remains in-memory for demo mode and comes from the existing API for real mode.

**Tech Stack:** Vue 3, SVG, existing PNG export helper, CSS, Node source-contract tests, Vue CLI build, Python server tests.

## Global Constraints

- Display conditions in the unified order `BL`, `SE`, `TE`, `CS`; preserve backend codes `TE`, `CS`, `SE`, `BL`.
- Use the supplied figure language: white canvas, Arial/DejaVu Sans, dark thin axes, light gray dashed grid, coolwarm colors, restrained labels, and complete export bounds.
- Export only PNG using `exportSvgAsPng`; keep simulated data in front-end memory only.
- Do not modify participant flow, articles, questions, comment layout, SQLite schema, allocation logic, or current test data.
- For n < 4, show no t-based CI; for larger samples use the existing Student-t CI rule.

---

### Task 1: Add failing contracts for adaptive chart types

**Files:**
- Modify: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client/tests/admin-dashboard.test.cjs`

**Interfaces:**
- `AdminDashboard.vue` passes explicit chart types to `AdminAcademicMetricChart`.
- `AdminAcademicMetricChart.vue` exposes `scatter`, `bar`, `boxplot`, and `horizontal-bar` render branches and keeps the PNG export contract.

- [ ] **Step 1: Add source assertions**

Add these assertions after the existing chart checks:

```js
assert.match(dashboard, /chart-type="bar"/);
assert.match(dashboard, /chart-type="boxplot"/);
assert.match(dashboard, /chart-type="horizontal-bar"/);
assert.match(academicMetricChart, /chartType/);
assert.match(academicMetricChart, /academic-bar/);
assert.match(academicMetricChart, /academic-box/);
assert.match(academicMetricChart, /academic-horizontal-bar/);
assert.match(academicMetricChart, /errorbar|error-line|ci95/);
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run:

```bash
cd /Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue
node client/tests/admin-dashboard.test.cjs
```

Expected: FAIL because the current metric component has no adaptive chart branches and the dashboard does not pass chart types.

---

### Task 2: Implement adaptive SVG geometry in the reusable metric component

**Files:**
- Modify: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client/src/components/admin/AdminAcademicMetricChart.vue`
- Modify: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client/src/components/admin/admin.css`

**Interfaces:**

```js
// New optional prop; old callers remain scatter-compatible.
chartType: { type: String, default: "scatter" }
```

The component continues accepting `title`, `metric`, `series`, `format`, `domain`, `ticks`, `higherIsBetter`, and `unit`, and continues rendering its per-condition table and PNG export button.

- [ ] **Step 1: Add the prop and computed chart metadata**

Add `chartType` to `defineProps`. Define computed booleans for `isBarChart`, `isBoxplot`, and `isHorizontalBarChart`. Keep time conversion to seconds and the existing condition order.

- [ ] **Step 2: Add bar-chart geometry**

For `bar`, render four condition-colored bars at fixed x positions, condition labels, mean heights, capped 95% CI error lines when available, and value labels. Use domain `[0, 1]` for accuracy metrics; use a data-derived domain for interaction counts; use `[1, 7]` or `[0, 100]` for rating/NASA metrics. Keep the y-axis label and grid inside the SVG viewBox.

- [ ] **Step 3: Add boxplot geometry**

For `boxplot`, compute each condition’s five-number summary (min, Q1, median, Q3, max), draw a colored box, median line, whiskers, caps, and individual light points. Use a numeric y scale, seconds for time metrics, and derived lower/upper bounds with padding. Show median labels and n values without clipping.

- [ ] **Step 4: Add horizontal-bar geometry**

For `horizontal-bar`, draw one horizontal bar per condition with a fixed domain (`[1, 4]` for rank and `[0, 1]` for share), condition labels on the y-axis, a vertical grid, mean/value labels, and the direction label. Keep the chart legible at the existing responsive minimum width.

- [ ] **Step 5: Preserve scatter geometry and export**

Wrap the existing scatter SVG content in the `scatter` branch, leave its current CI and small-sample behavior intact, and make every branch use the same `chartSvg` ref plus `exportSvgAsPng` call.

- [ ] **Step 6: Add shared CSS**

Add only shared SVG classes for bar fills, box outlines, median lines, whiskers, horizontal bars, and chart labels. Reuse the existing typography, grid, axis, and export styles; do not introduce dashboard-card styling into paper figures.

- [ ] **Step 7: Run focused test and build**

Run:

```bash
cd /Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue
node client/tests/admin-dashboard.test.cjs
npm --prefix client run build
```

Expected: source contracts pass and the Vue build exits with code 0.

---

### Task 3: Assign chart types and axis rules in the dashboard

**Files:**
- Modify: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client/src/components/admin/AdminDashboard.vue`

**Interfaces:**
- Core `CTIA` and `CTIRT` remain `scatter`.
- `CRA`, `ACA`, and `CLA` use `bar`.
- `CLT`, reading behavior metrics use `boxplot`.
- Interaction and subjective metrics use `bar`.
- Preference ranking and first-place share use `horizontal-bar`.

- [ ] **Step 1: Add chart type metadata to metric arrays**

Add `chartType` to each metric item, preserving current labels, formatters, direction flags, and units. Add explicit domains/ticks where needed: accuracy `[0, 1]`, ratings `[1, 7]`, NASA `[0, 100]`, ranking `[1, 4]`, share `[0, 1]`.

- [ ] **Step 2: Pass chart metadata to metric components**

Update each `AdminAcademicMetricChart` invocation to pass `:chart-type="item.chartType"`, `:domain="item.domain"`, and `:ticks="item.ticks"`.

- [ ] **Step 3: Switch preference charts to horizontal bars**

Pass `chart-type="horizontal-bar"`, `domain="[1, 4]"` and `domain="[0, 1]"` to the two preference figures. Keep separate PNG buttons and existing demo/real data sources.

- [ ] **Step 4: Run focused source contracts**

Run:

```bash
cd /Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue
node client/tests/admin-dashboard.test.cjs
```

Expected: PASS with all required chart types present.

---

### Task 4: Verify visual inventory, exports, and regressions

**Files:**
- Modify production files only if a verification failure identifies a concrete issue.

- [ ] **Step 1: Run complete automated verification**

```bash
cd /Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue
node client/tests/admin-dashboard.test.cjs
npm --prefix client run test:experiment
python3 -m pytest -q server/tests
npm --prefix client run build
```

Expected: all contract/experiment/server tests pass and the production build exits with code 0.

- [ ] **Step 2: Inspect the running page with demo data**

Open `/admin/analysis`, enable `使用模拟数据预览论文图表`, and verify the page contains the two reference figures plus adaptive charts. Confirm task-level accuracy still has four connected mean lines, all labels are inside SVG bounds, and every chart has exactly one `导出 PNG` button.

- [ ] **Step 3: Verify PNG export behavior**

Use the browser to click one export button in each chart family: overall, task accuracy, scatter core, bar task, boxplot behavior, subjective bar, and horizontal preference. Confirm each download is a non-empty PNG and no SVG/PDF download is offered.

- [ ] **Step 4: Check the real-data path remains safe**

Disable demo data and confirm empty or sparse API data renders `暂无有效数据` or valid sparse charts without NaN coordinates or exaggerated CI intervals.
