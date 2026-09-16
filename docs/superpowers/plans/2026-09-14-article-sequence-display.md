# 管理员文章编号与顺序筛选实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将管理员页面的文章展示编号改为 `01–04`，并实现完整文章顺序与文章位置的清晰筛选。

**Architecture:** 内部 SQLite/API 继续使用真实 `article_id` 和 `article_order`；前端通过固定展示映射渲染文章编号。新增 `article_sequence` API 筛选参数，由后端映射到现有 `GROUP_ALLOCATIONS` 的 `group_id`，而 `article_order` 保留为文章位置筛选。

**Tech Stack:** Vue 3 Composition API, Python SQLite statistics layer, pytest, Node source-contract tests.

## Global Constraints

- 展示编号：`01=A02`、`02=A03`、`03=A04`、`04=A07`。
- 合法完整顺序仅为 `01-02-03-04`、`02-03-04-01`、`03-04-01-02`、`04-01-02-03`。
- 不修改数据库内部文章编号，不破坏历史数据关联。
- 不引入 `mode = pilot`。
- 选择参与者后，详情按 participant_id 展示完整四篇文章数据。
- 遵循 TDD：先写失败测试并确认失败，再写最小实现。

## Task 1: 固化后端顺序筛选契约

**Files:**
- Modify: `server/admin_stats.py`
- Modify: `server/tests/test_admin_stats.py`

- [ ] 为四个合法 `article_sequence` 增加筛选测试，并断言对应参与者/分组范围。
- [ ] 为非法序列增加测试，断言 `ValueError`。
- [ ] 增加组合筛选测试，确认序列筛选与 `article_order`、`article_id`、`condition` 可组合。
- [ ] 运行后端相关测试，确认新测试先失败。
- [ ] 在 `normalize_filters` 增加 `article_sequence` 与固定合法值校验。
- [ ] 在 `_article_rows` 增加 `group_id` 约束，并把 `article_sequence` 纳入返回 scope/filter options（如现有接口需要）。
- [ ] 运行后端相关测试，确认通过且旧测试不回归。

## Task 2: 固化前端显示和筛选契约

**Files:**
- Modify: `client/src/components/admin/AdminOverview.vue`
- Modify: `client/src/components/admin/AdminParticipantDetails.vue`
- Modify: `client/tests/admin-dashboard.test.cjs`

- [ ] 增加源码契约测试，要求文章展示映射、四个完整顺序、独立文章位置筛选和新文案存在。
- [ ] 运行客户端测试，确认新测试先失败。
- [ ] 在普通总览页增加 `articleDisplayLabels`、`articleSequenceOptions` 和 `articlePositionOptions`。
- [ ] 将文章下拉框改为显示 `01–04`，值仍传 `A02/A03/A04/A07`。
- [ ] 将“文章顺序”改为完整顺序组合，新增“文章位置”使用 `article_order`。
- [ ] 修改筛选摘要，使其显示展示编号和完整箭头顺序，不显示原始编号。
- [ ] 在参与者详情中统一通过映射渲染文章编号和顺序。
- [ ] 更新模拟总览数据的筛选兼容逻辑（如果其使用与真实 API 相同的筛选参数）。
- [ ] 运行客户端源码测试。

## Task 3: 集成验证

**Files:**
- No additional production files.

- [ ] 运行 `python3 -m pytest -q server/tests`。
- [ ] 运行 `node client/tests/admin-dashboard.test.cjs`。
- [ ] 运行 `npm --prefix client run build`。
- [ ] 重启本地服务，检查 `/admin`。
- [ ] 验证四个顺序筛选、四个位置筛选、文章展示编号和参与者详情完整性。
- [ ] 检查 `/admin/analysis` 不出现新的路由或筛选错误。
