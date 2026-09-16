# Academic Analysis Charts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修复论文图裁切、为任务级准确率增加确认过的均值连线，并把管理员后台已有的核心、阅读、交互、主观和偏好指标整理成统一可导出 PNG 的论文风格图表。

**Architecture:** 保留 `AdminAcademicOverallChart.vue` 与 `AdminAcademicTaskChart.vue` 作为严格控制几何尺寸的论文主图；新增一个可复用的多指标 SVG 论文图组件，用同一套条件颜色、散点、中心趋势、95% CI、网格和导出函数承载其余指标。`AdminDashboard.vue` 负责按分析主题提供真实/模拟数据和图表分组，原始 API/SQLite 数据结构不变。

**Tech Stack:** Vue 3、SVG、现有 `adminChartExport.js` PNG 导出、现有 admin CSS、Node contract tests、Vue CLI build、pytest server tests。

## Global Constraints

- 条件仅为 `TE`、`CS`、`SE`、`BL`，显示顺序统一为 `BL`、`SE`、`TE`、`CS`。
- 论文图统一使用 Arial/DejaVu Sans、黑色细边框、浅灰虚线网格、`coolwarm` 条件色、参与者级散点和中心趋势/95% CI。
- 所有图只导出 PNG；导出内容只包含 SVG 图本身。
- 模拟数据只用于前端预览，不写入 SQLite。
- 不修改参与者端实验流程、文章、题目、评论嵌入布局或原始数据表。
- 不把不同交互机制的原始事件不加区分地合并成一个实验结论。

### Task 1: Add regression contracts for geometry, connected means, and chart inventory

**Files:**
- Modify: `client/tests/admin-dashboard.test.cjs`

- [ ] **Step 1: Write the failing assertions**

Add assertions for:

```js
assert.match(overallChart, /PLOT_BOTTOM \+ 28/);
assert.match(taskChart, /academic-task-mean-line/);
assert.match(taskChart, /taskMeanPoints/);
for (const chartName of ["AdminAcademicMetricChart", "readingMetrics", "interactionMetrics", "subjectiveMetrics", "preference"]) {
  assert.match(dashboard, new RegExp(chartName));
}
```

- [ ] **Step 2: Run the focused contract test and verify it fails for the missing implementation**

Run:

```bash
node client/tests/admin-dashboard.test.cjs
```

Expected: FAIL because the current overall title position and task mean-line implementation do not satisfy the new contracts.

### Task 2: Fix overall figure clipping and restore connected task means

**Files:**
- Modify: `client/src/components/admin/AdminAcademicOverallChart.vue`
- Modify: `client/src/components/admin/AdminAcademicTaskChart.vue`
- Modify: `client/src/components/admin/admin.css`

**Interfaces:**
- `AdminAcademicOverallChart` continues to consume `overallTime` and `overallAccuracy` arrays.
- `AdminAcademicTaskChart` continues to consume `taskAccuracy` object and adds only visual mean-line rendering.

- [ ] **Step 1: Move overall x-axis titles inside the existing reference viewBox**

Change both overall panel title y positions from `PLOT_BOTTOM + 36` to `PLOT_BOTTOM + 28.6`, retaining `viewBox="0 0 854.27125 342.566363"`.

- [ ] **Step 2: Add one connected polyline per condition to the task figure**

Add:

```vue
<polyline
  v-if="taskMeanPoints(condition).length === tasks.length"
  class="academic-task-mean-line"
  :points="taskMeanPoints(condition)"
  :stroke="conditionColor(displayConditions.indexOf(condition))"
/>
```

Place the four polylines behind the task observations and CI/mean markers. Implement:

```js
function taskMeanPoints(condition) {
  return tasks.map((task, taskIndex) => {
    const current = statistic(task, condition);
    return `${taskX(taskIndex) + conditionOffset(displayConditions.indexOf(condition))},${scaleY(current.mean)}`;
  }).join(" ");
}
```

Return an empty string when any task mean is missing, and keep all line points inside the existing clip path.

- [ ] **Step 3: Style connected lines consistently**

Add `.academic-task-mean-line` with condition stroke supplied by SVG, `fill: none`, `stroke-width: 1.35`, `stroke-linecap: round`, and `stroke-linejoin: round`; do not add a separate legend entry because the existing condition legend already identifies the colors.

- [ ] **Step 4: Run the focused contract test**

Run:

```bash
node client/tests/admin-dashboard.test.cjs
```

Expected: PASS for the geometry and mean-line assertions.

### Task 3: Create reusable academic metric chart component

**Files:**
- Create: `client/src/components/admin/AdminAcademicMetricChart.vue`
- Modify: `client/src/components/admin/academicFigureUtils.js`
- Modify: `client/src/components/admin/admin.css`
- Modify: `client/tests/admin-dashboard.test.cjs`

**Interfaces:**

```js
// Props
{
  title: String,
  metric: String,
  series: Object, // { BL: number[], SE: number[], TE: number[], CS: number[] }
  format: Function,
  domain: Array, // [low, high]
  ticks: Array,
  higherIsBetter: Boolean,
  unit: String
}
```

- [ ] **Step 1: Add source contracts for the reusable component**

Assert that the component contains `ref="chartSvg"`, `exportSvgAsPng`, `coolwarm`, participant observations, CI calculation, and PNG export.

- [ ] **Step 2: Implement the SVG metric figure**

Render one horizontal condition row per `BL`, `SE`, `TE`, `CS` with:

- light-gray alternating row bands;
- x-grid and a black panel border;
- jittered observation circles using `coolwarm` colors;
- mean point and horizontal 95% CI;
- condition labels and formatted mean annotations;
- left/right ramp labels according to `higherIsBetter`;
- a toolbar button labeled `导出 PNG`.

The SVG must have a stable viewBox and white background so exported PNGs are publication-ready.

- [ ] **Step 3: Add shared styles and make the component responsive with horizontal overflow**

Reuse the existing academic typography and border rules. Add only component-specific classes; do not change participant-facing styles.

- [ ] **Step 4: Run the focused contract test**

Run:

```bash
node client/tests/admin-dashboard.test.cjs
```

Expected: PASS for the new component source contracts.

### Task 4: Add themed chart sections to the analysis page

**Files:**
- Modify: `client/src/components/admin/AdminDashboard.vue`
- Modify: `client/src/admin/adminDemoData.js`
- Modify: `client/tests/admin-dashboard.test.cjs`

**Interfaces:**
- Keep existing `metric(name)` filtering and real API data path.
- Add computed chart data objects that convert existing metric series into `{ BL, SE, TE, CS }` arrays without changing persistence.

- [ ] **Step 1: Add failing dashboard contracts for all chart groups**

Assert headings and component references for:

```text
核心结果图
阅读行为图
评论交互图
主观评价图
偏好结果图
```

- [ ] **Step 2: Add chart groups**

Use `AdminAcademicMetricChart` for:

- Core: CTIA, CTIRT, CLA, CLT;
- Reading: Initial Reading Time, NSD, Scroll Event Count, Page Focus Loss Count;
- Interaction: Comment Interaction Count, Comment Open Count, Comment Click Count, Comment View Time;
- Subjective: Mental Demand, Effort, Frustration, Reading Continuity, Comment Accessibility.

Add a separate preference figure for average rank and first-place proportion if preference data is available; retain textual reason export only.

- [ ] **Step 3: Add demonstration data only in `adminDemoData.js`**

Provide deterministic arrays for each new figure with 24 participant observations per condition. Do not call the API or persistence layer from the demo generator and display the existing “模拟数据” badge.

- [ ] **Step 4: Run the focused contract test**

Run:

```bash
node client/tests/admin-dashboard.test.cjs
```

Expected: PASS for the full chart inventory.

### Task 5: Verify UI, exports, and complete regression suite

**Files:**
- No additional source files unless verification finds a concrete defect.

- [ ] **Step 1: Build the client**

Run:

```bash
npm --prefix client run build
```

Expected: `DONE Build complete.`; webpack bundle-size warnings may remain but must not be build errors.

- [ ] **Step 2: Run all automated tests**

Run:

```bash
node client/tests/admin-dashboard.test.cjs
npm --prefix client run test:experiment
python3 -m pytest -q server/tests
```

Expected: all contract tests pass, experiment flow/allocation tests pass, and server tests report zero failures.

- [ ] **Step 3: Verify the live analysis page**

Open `/admin/analysis`, enable `使用模拟数据预览论文图表`, and verify:

- the first figure shows complete bottom labels;
- task figure has four connected mean lines, 12 center points, and four legend groups;
- all new chart sections render;
- every chart has one `导出 PNG` button.

- [ ] **Step 4: Verify PNG files**

Click at least the overall, task, core, reading, interaction, subjective, and preference export buttons. Confirm downloaded files have PNG MIME type and non-zero dimensions.
