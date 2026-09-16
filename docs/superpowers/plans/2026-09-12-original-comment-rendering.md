# 原系统文章与评论展示恢复实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不改变实验流程、P01–P24 分配、题目、SQLite 表结构和事件采集接口的前提下，把实验系统的文章与评论展示恢复到原系统的结构、样式和四种布局语义，并保持 CRA 阶段完全隐藏文章与评论。

**Architecture:** 继续使用实验专用 `ArticleRenderer.vue`，但将其改造成原系统展示核心的兼容渲染器，而不是直接挂载包含研究者控制功能的原 `ArticleContent.vue`。渲染器从实验材料字段生成原系统所需的文章元信息、段落/句子结构、评论卡片和锚点映射；`article.render_mode` 单向决定布局，组件只通过既有 `interaction` 事件向阶段组件上报行为。实验阶段组件、服务端接口、题目和数据库结构保持不变。

**Tech Stack:** Vue 3、Vue CLI、现有实验组件与 CSS、Node.js 静态契约测试、Python pytest、SQLite、Tornado。

## Global Constraints

- 不修改文章、评论、题目、P01–P24 分配条件和顺序。
- 不修改 SQLite 数据表结构、正式数据库或已有完整备份。
- 不执行 `git reset --hard`，不清理工程目录中既有的路径迁移删除/未跟踪状态。
- `layout_a -> baseline`、`layout_b -> cs`、`layout_c -> se`、`layout_d -> be`；不得继续把 `layout_a` 映射为 `te`。
- CRA 阶段不挂载 `ArticleRenderer`，文章正文和全部评论不得出现在可见 DOM 中。
- ACA、CTIA、评论定位阶段显示文章与评论；参与者不能切换布局、筛选评论、查看研究者控制栏或图表控制。
- 继续发出 `comment_open`、`comment_close`、`comment_click` 事件，由现有阶段组件写入 SQLite。
- 材料中缺失的作者、时间、头像等原系统字段使用空值/不显示策略，不伪造研究数据。

## 文件清单与职责

- 修改 `client/src/components/experiment/ArticleRenderer.vue`：实验专用兼容渲染器；负责文章标题、元信息、正文段落、评论标记、四种布局和评论交互事件。
- 修改 `client/tests/experiment-flow.test.cjs`：增加渲染器 DOM/源码契约、布局映射、控制栏隐藏和 CRA 隐藏回归断言。
- 必要时修改 `client/src/components/experiment/ReadingStage.vue`、`client/src/components/experiment/QuestionStage.vue`：仅在渲染器事件或阶段可见性契约需要时调整，不改变既有 API 和实验数据语义。
- 必要时修改 `client/src/components/experiment/*.vue` 的局部样式：只修复实验页面容器对原系统展示的必要兼容，不引入研究者控制。
- 不修改 `server/server.py`、`server/materials.json`、SQLite schema、题目和分配逻辑。

## Task 1: 锁定原系统展示结构与布局映射

**Files:**
- Modify: `client/tests/experiment-flow.test.cjs`
- Test target: `client/src/components/experiment/ArticleRenderer.vue`

**Interfaces:**
- Consumes: 当前实验文章材料对象 `{ title, body, comments, render_mode }`。
- Produces: 可由后续任务逐步满足的源码/DOM 契约，包含 `.article-container`、`.article-title`、`.article-meta`、`.article-content`、`.paragraph-block`、`.paragraph-text`、`.article-footer`、`.baseline-comments`、`.comment-item`、`.comment-user`、`.comment-text`、`.comment-stats` 以及 `baseline/cs/se/be` 分支。

- [ ] **Step 1: 写失败测试**

  在 `experiment-flow.test.cjs` 增加静态契约断言：
  - 渲染器声明原系统关键结构类名；
  - 显式包含 `layout_a: "baseline"`、`layout_b: "cs"`、`layout_c: "se"`、`layout_d: "be"`；
  - 不再包含 `layout_a: "te"`；
  - 不包含研究者控制栏、布局切换、筛选滑杆、图表或高频词开关的参与者端入口；
  - 保留 `comment_open`、`comment_close`、`comment_click`。

- [ ] **Step 2: 运行失败测试**

  运行：
  ```bash
  cd /Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client
  node tests/experiment-flow.test.cjs
  ```
  预期：因当前渲染器仍使用 `te`、简化类名和简化评论卡片而失败。

- [ ] **Step 3: 记录失败原因并保持测试范围最小**

  确认失败只指向展示结构/布局映射契约，不把无关的服务端、题目或数据库测试混入本任务。

## Task 2: 迁移文章容器、标题、元信息、正文段落和 footer

**Files:**
- Modify: `client/src/components/experiment/ArticleRenderer.vue`
- Test: `client/tests/experiment-flow.test.cjs`

**Interfaces:**
- Consumes: 实验材料的 `title`、`body`，以及可选文章元数据；缺失字段不伪造。
- Produces: 原系统兼容的 `.article-container`、`.article-title`、`.article-meta`、`.article-content`、`.paragraph-block`、`.paragraph-text`、`.article-footer` 结构；正文可被四种布局复用。

- [ ] **Step 1: 增加文章结构失败断言**

  断言渲染器包含标题、元信息安全渲染、按段落输出正文和 footer 的结构标识，并保持正文文本不被丢失。

- [ ] **Step 2: 运行对应测试并确认失败**

  运行 `node tests/experiment-flow.test.cjs`，记录当前简化 `.article-body`/`h1` 结构不满足原系统契约。

- [ ] **Step 3: 实现最小文章结构迁移**

  将根节点和文章内容改为原系统兼容的结构；将 `body` 按原系统段落边界拆分，逐段输出 `.paragraph-block > .paragraph-text`；只在材料提供时显示作者、时间等元信息；保留实验页面自己的完成阅读/答题操作条，不把研究者工具栏移入渲染器。

- [ ] **Step 4: 运行前端契约测试**

  运行 `node tests/experiment-flow.test.cjs`，确认文章结构相关断言通过。

- [ ] **Step 5: 提交独立变更**

  ```bash
  git add client/src/components/experiment/ArticleRenderer.vue client/tests/experiment-flow.test.cjs
  git commit -m "feat: restore original article structure"
  ```

## Task 3: 恢复 baseline 集中评论布局

**Files:**
- Modify: `client/src/components/experiment/ArticleRenderer.vue`
- Test: `client/tests/experiment-flow.test.cjs`

**Interfaces:**
- Consumes: `article.comments` 的 `text`、`like_count`、`reply_count`、`internal_id` 等兼容字段。
- Produces: `baseline` 分支中的 `.baseline-comments`、`.baseline-comment-item`/`.comment-item`、用户信息区域、评论正文、统计区域和评论点击事件。

- [ ] **Step 1: 写 baseline 失败断言**

  断言存在集中评论区域、原系统评论卡片关键类名、评论文本与统计字段兼容映射，以及 `comment_click` 上报。

- [ ] **Step 2: 运行测试确认失败**

  运行 `node tests/experiment-flow.test.cjs`，预期当前 `.comment-section`/`.comment-card` 不满足原系统契约。

- [ ] **Step 3: 实现 baseline 评论卡片**

  建立兼容评论视图模型：将 `text` 映射到 `.comment-text`，`like_count`/`reply_count` 映射到 `.comment-stats`，有真实用户字段才显示 `.comment-user` 内容；保留可点击评论项与原系统集中评论的视觉层级。

- [ ] **Step 4: 运行测试确认通过**

  运行前端实验测试，确认 baseline 结构和事件契约通过。

- [ ] **Step 5: 提交独立变更**

  ```bash
  git add client/src/components/experiment/ArticleRenderer.vue client/tests/experiment-flow.test.cjs
  git commit -m "feat: restore baseline comment presentation"
  ```

## Task 4: 恢复 cs 点击标记展开评论布局

**Files:**
- Modify: `client/src/components/experiment/ArticleRenderer.vue`
- Test: `client/tests/experiment-flow.test.cjs`

**Interfaces:**
- Consumes: 段落/句子锚点和评论的 `internal_anchor`、`position_band`。
- Produces: `.comment-marker` 点击入口、展开面板、`comment_open`/`comment_close`/`comment_click` 事件。

- [ ] **Step 1: 写 cs 失败断言**

  断言 `cs` 分支包含原系统标记、展开容器、`aria-expanded` 或等价无障碍状态和展开/收起事件。

- [ ] **Step 2: 运行测试确认失败**

  运行前端实验测试，预期当前分支名称和结构仍不符合原系统布局映射。

- [ ] **Step 3: 实现 cs 交互**

  使用 `render_mode === layout_b` 固定进入 `cs`；按锚点把评论分配到对应句子/段落；点击正文标记展开/收起评论，评论项点击继续上报，不提供布局切换或研究者控制。

- [ ] **Step 4: 运行测试确认通过**

  运行前端实验测试并确认事件名称、payload 和无障碍属性未回归。

- [ ] **Step 5: 提交独立变更**

  ```bash
  git add client/src/components/experiment/ArticleRenderer.vue client/tests/experiment-flow.test.cjs
  git commit -m "feat: restore click-to-show comment layout"
  ```

## Task 5: 恢复 se 句末评论布局

**Files:**
- Modify: `client/src/components/experiment/ArticleRenderer.vue`
- Test: `client/tests/experiment-flow.test.cjs`

**Interfaces:**
- Consumes: 与 Task 4 相同的句子/评论锚点模型。
- Produces: `se` 分支中评论紧随相关句子出现的原系统兼容结构和样式类名，不需要参与者额外打开评论。

- [ ] **Step 1: 写 se 失败断言**

  断言存在 `se` 分支、句子级正文结构和 `.sentence-comments`/原系统等价评论容器，且评论点击事件仍存在。

- [ ] **Step 2: 运行测试确认失败**

  运行前端实验测试，预期当前简化 `.segmented-body` 结构不满足原系统句末结构契约。

- [ ] **Step 3: 实现 se 布局**

  将评论插入其锚定句子之后，使用原系统评论项结构和兼容样式；避免重复渲染评论，保留事件 payload 中稳定的 `comment_index`。

- [ ] **Step 4: 运行测试确认通过**

  运行前端实验测试并检查句末评论分支通过。

- [ ] **Step 5: 提交独立变更**

  ```bash
  git add client/src/components/experiment/ArticleRenderer.vue client/tests/experiment-flow.test.cjs
  git commit -m "feat: restore sentence-end comments"
  ```

## Task 6: 恢复 be 段间评论布局

**Files:**
- Modify: `client/src/components/experiment/ArticleRenderer.vue`
- Test: `client/tests/experiment-flow.test.cjs`

**Interfaces:**
- Consumes: 段落锚点和评论视图模型。
- Produces: `be` 分支中评论位于相关正文段落之间的原系统兼容结构和样式。

- [ ] **Step 1: 写 be 失败断言**

  断言存在 `be` 分支、段落之间评论容器和评论卡片结构，不再使用实验版 `bl` 作为外部布局语义。

- [ ] **Step 2: 运行测试确认失败**

  运行前端实验测试，预期当前 `bl` 分支和简化 `.between-comments` 契约失败。

- [ ] **Step 3: 实现 be 布局**

  将评论在对应 `.paragraph-block` 之间渲染，使用原系统间隔、边界和卡片结构；评论点击继续发送 `comment_click`。

- [ ] **Step 4: 运行测试确认通过**

  运行前端实验测试并确认四种布局名称和结构统一。

- [ ] **Step 5: 提交独立变更**

  ```bash
  git add client/src/components/experiment/ArticleRenderer.vue client/tests/experiment-flow.test.cjs
  git commit -m "feat: restore between-paragraph comments"
  ```

## Task 7: 接入固定 render_mode 与实验交互事件

**Files:**
- Modify: `client/src/components/experiment/ArticleRenderer.vue`
- Modify if needed: `client/src/components/experiment/ReadingStage.vue`
- Modify if needed: `client/src/components/experiment/QuestionStage.vue`
- Test: `client/tests/experiment-flow.test.cjs`

**Interfaces:**
- Consumes: 服务端脱敏文章对象中的不透明 `render_mode`。
- Produces: 固定布局渲染和既有 `interaction` 事件对象；不改变阶段组件向 `event()` 传递的事件类型和 payload。

- [ ] **Step 1: 增加事件与固定条件回归断言**

  断言阶段组件继续绑定 `@interaction="recordInteraction"`，渲染器继续发出三类评论事件，且不存在任何参与者可修改布局的状态或控件。

- [ ] **Step 2: 运行失败测试（如有）**

  运行 `node tests/experiment-flow.test.cjs`，只保留由本次渲染改造引起的失败。

- [ ] **Step 3: 实现最小兼容调整**

  保持 `render_mode` 单向映射；必要时只调整 payload 以保留 `comment_index`、`segment_index`；不修改 SQLite 写入路径和数据库结构。

- [ ] **Step 4: 运行前端实验测试**

  ```bash
  npm run test:experiment
  ```
  预期：实验流程和参与者分配测试全部通过。

- [ ] **Step 5: 提交独立变更**

  ```bash
  git add client/src/components/experiment client/tests/experiment-flow.test.cjs
  git commit -m "refactor: keep experiment comment events and fixed layouts"
  ```

## Task 8: 确认参与者端不暴露研究者控制功能

**Files:**
- Modify if needed: `client/src/components/experiment/ArticleRenderer.vue`
- Test: `client/tests/experiment-flow.test.cjs`

**Interfaces:**
- Consumes: 原系统视觉核心中可能存在的控制栏/筛选状态概念，仅允许其展示层被迁移。
- Produces: 实验端无研究者控制栏、布局切换按钮、点赞/回复筛选滑杆、评论类型筛选、图表和高频词开关。

- [ ] **Step 1: 写控制功能隐藏失败断言**

  检查实验渲染器和实验页面源码不包含原系统控制组件导入、控制按钮文字或交互入口；允许评论统计作为只读展示。

- [ ] **Step 2: 运行测试确认失败或通过**

  运行前端实验测试；若已通过，保留断言作为回归保护，不做无关改动。

- [ ] **Step 3: 移除任何迁移过程中带入的控制入口**

  只删除参与者端不可用的控制逻辑，不删除评论展示和实验事件。

- [ ] **Step 4: 运行测试确认通过**

  运行 `npm run test:experiment`。

- [ ] **Step 5: 提交独立变更（仅有修改时）**

  ```bash
  git add client/src/components/experiment client/tests/experiment-flow.test.cjs
  git commit -m "test: keep researcher controls hidden in experiment UI"
  ```

## Task 9: 验证 CRA 隐藏与允许查看阶段展示

**Files:**
- Modify if needed: `client/src/components/experiment/QuestionStage.vue`
- Test: `client/tests/experiment-flow.test.cjs`

**Interfaces:**
- Consumes: `QuestionStage.vue` 的 `group` 阶段判断和 `ArticleRenderer`。
- Produces: `cra` 阶段没有文章/评论可见 DOM；`aca`、`ctia`、评论定位阶段保留文章/评论显示；答题过程中不能通过返回操作重新打开 CRA 内容。

- [ ] **Step 1: 写可见性回归断言**

  断言 `QuestionStage.vue` 对 `group !== 'cra'` 才挂载文章面板，且 CRA 页面保留四道评论识别题，不重新挂载文章渲染器。

- [ ] **Step 2: 运行测试确认当前行为**

  运行前端实验测试；若失败，定位到阶段条件而非渲染器样式。

- [ ] **Step 3: 实现最小可见性修复**

  只修正 CRA/非 CRA 的挂载条件和不可返回约束，保持题目内容、顺序和事件名称不变。

- [ ] **Step 4: 运行测试确认通过**

  运行 `npm run test:experiment`。

- [ ] **Step 5: 提交独立变更（仅有修改时）**

  ```bash
  git add client/src/components/experiment/QuestionStage.vue client/tests/experiment-flow.test.cjs
  git commit -m "test: preserve hidden article during CRA"
  ```

## Task 10: 全量验证、构建和本地浏览器检查

**Files:**
- No planned source changes; only verification artifacts/logs if needed.

**Interfaces:**
- Consumes: 完成的实验渲染器和既有本地服务。
- Produces: 可审计的测试、preflight、生产构建和浏览器检查结果。

- [ ] **Step 1: 运行前端实验测试**

  ```bash
  cd /Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client
  npm run test:experiment
  ```

- [ ] **Step 2: 运行服务端测试**

  ```bash
  cd /Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue
  python3 -m pytest -q server/tests
  ```

- [ ] **Step 3: 运行数据库 preflight**

  ```bash
  python3 server/scripts/preflight.py --db /tmp/commentscope-local-test.sqlite3
  ```

- [ ] **Step 4: 构建生产前端**

  ```bash
  cd client
  npm run build
  ```

- [ ] **Step 5: 使用本地浏览器检查四种布局和 CRA**

  在 `http://127.0.0.1:8888/` 中检查：一个 `baseline`（P01–P24 中映射为 `layout_a`）条件、一个 `cs` 条件、一个 `se` 条件、一个 `be` 条件，以及 CRA 阶段。确认文章段落和评论外观恢复、评论交互可操作、交互事件仍写入、CRA 中文章与评论不存在。

- [ ] **Step 6: 汇总验证结果并在完成前复查差异**

  检查 `git diff` 只包含本次渲染改造相关文件；不处理工程历史路径迁移产生的大量无关删除/未跟踪状态；按照 verification-before-completion skill 以命令输出为依据报告结果。

- [ ] **Step 7: 提交最终整合变更（如仍有未提交的本次修改）**

  ```bash
  git add client/src/components/experiment client/tests/experiment-flow.test.cjs docs/superpowers/plans/2026-09-12-original-comment-rendering.md
  git commit -m "feat: restore original experiment article and comment rendering"
  ```
