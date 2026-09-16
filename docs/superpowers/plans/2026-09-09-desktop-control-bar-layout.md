# Desktop Control Bar Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `>=1201px` 桌面视口中，将顶部控制栏改为适度留白的三段式布局，消除右侧大块空白，同时保持中间布局切换器居中。

**Architecture:** 保留现有默认 flex 和 `<=1200px` 响应式规则，仅在 `ArticleContent.vue` 中新增 `@media (min-width: 1201px)` 桌面覆盖。桌面覆盖使用 `minmax(0, 1fr) auto minmax(0, 1fr)` 网格，并分别对三个现有直接子元素设置左、中、右对齐。

**Tech Stack:** Vue 3 SFC、scoped CSS、Node.js `assert` 静态回归测试、浏览器 computed-style 验证。

## Global Constraints

- 仅影响视口宽度 `>=1201px`。
- 桌面端 `.control-panel-inner` 最大宽度为 `1120px` 并保持居中。
- 不增加、删除或重命名控制项。
- 不修改 feature flags、评论颜色、正文布局和评论交互。
- `<=1200px`、`<=768px` 的现有布局必须保持有效。
- 当前 Git 根目录状态特殊，不执行 stage、commit、clean 或大范围 Git 操作。

---

### Task 1: 桌面端三段式控制栏

**Files:**
- Modify: `client/tests/feature-flags.test.cjs`
- Modify: `client/src/components/ArticleContent.vue`

**Interfaces:**
- Consumes: `.control-panel-inner` 的三个现有直接子元素 `.control-group-container`、`.layout-switcher`、`.filter-sliders-compact`。
- Produces: `@media (min-width: 1201px)` 下稳定的三段式桌面布局；不产生新的 Vue props、events 或 JavaScript API。

- [ ] **Step 1: 写入桌面布局失败测试**

在 `client/tests/feature-flags.test.cjs` 中提取 `min-width: 1201px` 媒体查询，并断言以下 CSS 存在：

```js
const minWidth1201 = extractCssBlock(
  article,
  /@media\s*\(\s*min-width\s*:\s*1201px\s*\)\s*\{/
);
assert.ok(minWidth1201, "the desktop control-bar media query should exist");
assert.match(
  minWidth1201,
  /\.control-panel-inner\s*\{(?=[^}]*display:\s*grid\s*;)(?=[^}]*grid-template-columns:\s*minmax\(\s*0\s*,\s*1fr\s*\)\s+auto\s+minmax\(\s*0\s*,\s*1fr\s*\)\s*;)(?=[^}]*max-width:\s*1120px\s*;)[^}]*\}/
);
assert.match(minWidth1201, /:deep\(\.control-group-container\)\s*\{[^}]*justify-self:\s*start\s*;/);
assert.match(minWidth1201, /\.layout-switcher\s*\{[^}]*justify-self:\s*center\s*;/);
assert.match(minWidth1201, /\.filter-sliders-compact\s*\{[^}]*justify-self:\s*end\s*;/);
```

- [ ] **Step 2: 运行测试并确认 RED**

Run:

```bash
cd client && npm run test:feature-flags
```

Expected: FAIL，错误信息为缺少 `min-width: 1201px` 桌面控制栏媒体查询或其网格声明。

- [ ] **Step 3: 添加最小桌面 CSS 实现**

在 `client/src/components/ArticleContent.vue` 的 scoped style 中添加：

```css
@media (min-width: 1201px) {
  .control-panel-inner {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
    max-width: 1120px;
  }
  :deep(.control-group-container) {
    justify-self: start;
  }
  .layout-switcher {
    justify-self: center;
  }
  .filter-sliders-compact {
    justify-self: end;
  }
}
```

- [ ] **Step 4: 运行回归测试并确认 GREEN**

Run:

```bash
cd client && npm run test:feature-flags
```

Expected: PASS，并输出 `feature flag regression checks passed`。

- [ ] **Step 5: 在浏览器验证桌面空间分布**

在 1280×720 下读取 `.control-panel-inner`、三个控件组和页面根元素的位置与 computed style，确认：

```text
.control-panel-inner display = grid
.control-panel-inner max-width = 1120px
.layout-switcher 的中心点接近页面中心点
左侧控件距控制栏左边、右侧滑杆距控制栏右边均约 40–80px
右侧空白显著小于修改前的约 270px
scrollWidth <= clientWidth
```

- [ ] **Step 6: 验证非桌面断点无回归**

分别检查 1200×720、375×720、320×720：

```text
.control-panel-inner display 继续使用 flex
页面根元素 scrollWidth <= clientWidth
原有移动端控件换行和两列布局按钮规则仍生效
```

- [ ] **Step 7: 运行最终测试和生产构建**

Run:

```bash
cd client && npm run test:feature-flags && npm run build
```

Expected: 测试通过，构建退出码为 0；允许现有 Browserslist 过期和资源体积警告。
