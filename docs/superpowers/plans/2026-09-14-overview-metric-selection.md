# 普通总览按指标模块切换展示 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让普通总览页默认只展示实验进度，并允许管理员通过一个“查看指标”选择器一次查看一个数据模块，避免页面初始堆叠过多内容。

**Architecture:** 保留现有 `filters.dataSection` 作为前端展示状态，不把它发送给后端；后端仍按参与者、文章、条件、顺序、位置和状态筛选数据。模板继续用 `showSection()` 控制模块显示，默认值从 `all` 改为 `progress`，并把选择器文案调整为“查看指标”。参与者总表继续归入实验进度模块，选择参与者后完整详情优先展示，不改变现有数据接口。

**Tech Stack:** Vue 3 Composition API、Vue CLI、现有 AdminOverview 组件、Node.js 源码检查、Pytest 后端测试。

## Global Constraints

- 普通总览页与论文分析页保持为两个独立页面。
- 模拟数据仅用于前端预览，不写入 SQLite。
- 默认页面不得一次性展开所有统计模块。
- 参与者总表继续显示全部预定义参与者；详情逻辑不受影响。
- 不修改实验数据表结构和后端统计接口。

---

### Task 1: 为默认模块选择行为增加前端回归检查

**Files:**
- Modify: `client/tests/admin-dashboard.test.cjs`
- Test: `client/tests/admin-dashboard.test.cjs`

**Interfaces:**
- Consumes: `client/src/components/admin/AdminOverview.vue` 源码中的 `filters` 默认值、模块选项和 `showSection()`。
- Produces: 能防止总览页默认重新回到“全部数据”展开状态的源码回归检查。

- [ ] **Step 1: Write the failing test**

在现有 `AdminOverview.vue` 读取和断言附近加入以下检查：

```js
assert.match(overview, /dataSection:\s*"progress"/);
assert.match(overview, /查看指标/);
assert.match(overview, /<option value="progress">实验进度<\/option>/);
assert.doesNotMatch(overview, /dataSection:\s*"all"/);
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
node client/tests/admin-dashboard.test.cjs
```

Expected: FAIL，因为当前 `AdminOverview.vue` 的 `filters.dataSection` 初始值是 `"all"`，且选择器标题仍为“数据类型”。

- [ ] **Step 3: Write minimal implementation**

本任务只允许在下一任务中修改生产代码；测试失败结果确认后进入 Task 2。

- [ ] **Step 4: Run test to verify it passes**

Task 2 完成后运行同一命令，预期输出：

```text
admin dashboard source checks passed
```

- [ ] **Step 5: Commit**

```bash
git add client/tests/admin-dashboard.test.cjs
 git commit -m "test: guard overview metric selection default"
```

### Task 2: 将普通总览改为单模块展示

**Files:**
- Modify: `client/src/components/admin/AdminOverview.vue:68-84,280,393`
- Modify: `client/src/components/admin/admin.css`（仅在现有筛选器样式不足以承载新标签时调整）
- Test: `client/tests/admin-dashboard.test.cjs`

**Interfaces:**
- Consumes: 现有 `filters.dataSection`、`showSection(section)`、`participantOverview`、各统计模块和 `AdminParticipantDetails`。
- Produces: 默认 `progress` 的总览页；选择 `core`、`reading`、`interaction`、`subjective`、`preference` 或 `interview` 时只渲染对应模块；清除筛选恢复 `progress`。

- [ ] **Step 1: Write the failing test**

Task 1 的断言即为本任务的失败测试；同时补充清除筛选行为的源码检查：

```js
assert.match(overview, /dataSection:\s*"progress"/);
assert.match(overview, /Object\.assign\(filters,\s*\{[^}]*dataSection:\s*"progress"/s);
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
node client/tests/admin-dashboard.test.cjs
```

Expected: FAIL，原因是初始化和 `resetFilters()` 都使用 `dataSection: "all"`。

- [ ] **Step 3: Write minimal implementation**

在模板中将筛选器标签和选项改为：

```vue
<label class="admin-filter">
  查看指标
  <select v-model="filters.dataSection">
    <option value="progress">实验进度</option>
    <option value="core">核心任务指标</option>
    <option value="reading">阅读与滚动</option>
    <option value="interaction">评论交互</option>
    <option value="subjective">主观评价</option>
    <option value="preference">偏好结果</option>
    <option value="interview">访谈进度</option>
  </select>
</label>
```

将响应式筛选状态的默认值改为：

```js
const filters = reactive({
  participant_id: "",
  article_id: "",
  condition: "",
  article_sequence: "",
  article_order: "",
  status: "",
  dataSection: "progress",
});
```

将 `resetFilters()` 中的 `dataSection` 改为 `"progress"`：

```js
function resetFilters() {
  Object.assign(filters, {
    participant_id: "",
    article_id: "",
    condition: "",
    article_sequence: "",
    article_order: "",
    status: "",
    dataSection: "progress",
  });
}
```

保留 `showSection(section) { return filters.dataSection === "all" || filters.dataSection === section; }`，以便兼容已存在的状态和未来需要的全量预览，但界面不再提供“全部数据”选项。

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
node client/tests/admin-dashboard.test.cjs
npm --prefix client run build
```

Expected:

```text
admin dashboard source checks passed
DONE  Build complete
```

- [ ] **Step 5: Commit**

```bash
git add client/src/components/admin/AdminOverview.vue client/tests/admin-dashboard.test.cjs client/src/components/admin/admin.css
git commit -m "feat: show one overview metric section at a time"
```

### Task 3: 验证筛选、详情和服务接口没有回归

**Files:**
- Read: `server/admin_stats.py`
- Read: `server/server.py`
- Test: `server/tests`

**Interfaces:**
- Consumes: 总览页现有 API `/api/admin/summary` 与参与者详情返回结构。
- Produces: 证明展示模块切换只影响前端可见模块，不改变后端筛选结果。

- [ ] **Step 1: Run the full test suite**

```bash
python3 -m pytest -q server/tests
node client/tests/admin-dashboard.test.cjs
npm --prefix client run build
```

Expected: 所有后端测试通过、源码检查通过、前端构建完成。

- [ ] **Step 2: Verify API filters remain unchanged**

使用管理员认证请求以下接口：

```text
/api/admin/summary
/api/admin/summary?participant_id=P01
/api/admin/summary?article_sequence=02-03-04-01
```

确认返回范围分别为 P01–P24、P01、P07–P12；前端 `dataSection` 不应出现在请求参数中。

- [ ] **Step 3: Verify the UI contract**

打开 `http://127.0.0.1:8888/admin`，确认：

1. 首次打开只显示实验进度和参与者总表；
2. 切换“核心任务指标”后只显示核心任务指标；
3. 切换“评论交互”后只显示评论交互；
4. 选择 P01 后仍可查看 P01 的完整数据详情；
5. 点击“清除筛选”后恢复“实验进度”。

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/plans/2026-09-14-overview-metric-selection.md
git commit -m "docs: plan overview metric section selection"
```
