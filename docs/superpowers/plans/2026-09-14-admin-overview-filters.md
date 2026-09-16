# Admin Overview Filters Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修正普通总览页的偏好/访谈目标数量，并让管理员能够按参与者、文章、条件和数据类型筛选查看完整实验统计。

**Architecture:** 复用现有 `/api/admin/summary` 统计接口和 `AdminStats` 的条件过滤机制，扩展返回的参与者级完成计数，并在 `AdminOverview.vue` 中增加筛选状态、进度明细和指标明细表。筛选条件通过查询参数传递，普通总览与论文分析共享同一数据口径。

**Tech Stack:** Vue 3 Composition API, Axios, Python SQLite statistics layer, Node source-contract tests, pytest.

## Global Constraints

- 正式实验目标为 24 名参与者、96 个文章实验区块、960 条逐题回答。
- 偏好排序、偏好理由、访谈均为参与者级数据，目标数量是 24，不是 96。
- 统计默认排除已重置会话。
- 普通总览展示可筛选的完整统计概览；论文图表仍保留在 `/admin/analysis`。
- 不引入横向滚动条；保留现有管理员视觉风格。

### Task 1: Extend summary counts and filters

**Files:**
- Modify: `server/admin_stats.py`
- Test: `server/tests/test_admin_stats.py`

- [ ] Add tests for participant-level preference/interview counts and filtered summary behavior.
- [ ] Run the focused pytest tests and observe the expected failure.
- [ ] Return separate `preference_submitted`, `preference_reason_submitted`, and `interviews` counts, plus expected targets, while preserving existing response keys.
- [ ] Support `article_order` and expose filter metadata/options needed by the overview page.
- [ ] Run focused pytest tests again and verify they pass.

### Task 2: Add overview filters and complete metric table

**Files:**
- Modify: `client/src/components/admin/AdminOverview.vue`
- Modify: `client/src/components/admin/admin.css`
- Test: `client/tests/admin-dashboard.test.cjs`

- [ ] Add source-contract tests for corrected denominators, filter controls, and all-metric rendering.
- [ ] Run the source-contract test and observe the expected failure.
- [ ] Add reactive filters and reload summary with query parameters when filters change.
- [ ] Replace the combined preference/interview card with correctly denominated cards.
- [ ] Add response, survey, preference, interview, and metric detail sections with `n`, mean, median, SD, and observations.
- [ ] Add responsive CSS that keeps the overview readable without page-level horizontal overflow.
- [ ] Run client source tests and verify they pass.

### Task 3: Verify integration

**Files:**
- No additional production files.

- [ ] Run server tests.
- [ ] Run client experiment and admin source checks.
- [ ] Build the Vue client.
- [ ] Start or reuse the local server and inspect `/admin` with the filters and corrected target counts.
