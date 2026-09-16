# CommentScope Experiment System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有评论展示原型改造成可上线进行24人单一用户实验的 Vue + Tornado + SQLite 系统，严格执行四种评论呈现条件、固定 P01–P24 分配、逐题不可回退流程、断点续做和完整数据采集。

**Architecture:** 参与者端使用 Vue 单页流程，所有实验材料、参与者分配和正确答案由服务端配置/数据库控制。Tornado 提供会话、题目、事件、答案提交、恢复、导出和管理接口；SQLite 保存原始事件与结构化结果，前端不接收答案表。四种条件共用同一材料，只替换评论呈现器：TE、CS、SE、BL。

**Tech Stack:** Vue 3, Vue CLI, Axios, Tornado, Python 3, SQLite3, pytest/unittest, Node test runner.

## Global Constraints

- 实验参与者固定为 `P01`–`P24`，每个编号预先绑定一个拉丁方组别、文章顺序、条件和题目。
- 每个参与者完成4篇不同文章；每篇文章只体验一种条件；每篇文章 × 每种条件正好6人。
- 每篇文章使用同一正文、10条评论、点赞数、子评论数和人工正文锚点；不实时抓取、不自动定位。
- 参与者端不得显示内部评论编号、正文锚点、组别、实验条件名或正确答案。
- CRA 4题、ACA 2题、CTIA 2题、评论定位2题均逐题显示、提交后进入下一题、不可返回修改。
- 题目开始时间必须在题目实际显示后记录；每次事件/提交立即持久化。
- 支持中断恢复；已提交题目只读；同一参与者编号不能被两个活动会话同时占用。
- 正式数据与预测试/重置数据分离，预测试数据不得混入正式分析导出。
- NASA-TLX 六项、RC、CA、偏好排序和4道必填半结构化访谈由参与者直接填写并保存。
- SQLite 数据文件位于服务器持久目录；导出 CSV/JSON；提供数据库备份和受保护的重置/状态接口。
- 任何业务代码删除前先完成当前实际系统目录的完整快照和校验记录。

## File Map

- Create: `server/experiment_config.py` — P01–P24 固定分配、流程阶段、条件名称的服务端配置。
- Create: `server/experiment_materials.py` — 将四份 Markdown 材料转换/固化为安全的文章、评论、题目和答案数据。
- Create: `server/database.py` — SQLite schema、连接、迁移、原子写入、查询和导出数据访问层。
- Create: `server/experiment_service.py` — 会话占用、恢复、流程推进、答案判定和指标汇总业务逻辑。
- Modify: `server/server.py` — 替换旧通用接口，接入实验 API、导出、备份和受保护管理接口。
- Create: `server/scripts/import_materials.py` — 将研究者材料导入 SQLite 的一次性/幂等脚本。
- Create: `server/scripts/backup_database.py` — SQLite 在线备份脚本。
- Create: `server/tests/test_experiment_config.py` — 拉丁方分配和流程配置测试。
- Create: `server/tests/test_database.py` — schema、幂等写入、断点恢复和并发占用测试。
- Create: `server/tests/test_api.py` — API 的逐题、答案安全、导出和重置测试。
- Replace: `client/src/App.vue` — 实验入口和阶段路由。
- Create: `client/src/experiment/experimentApi.js` — 实验 API 客户端。
- Create: `client/src/experiment/experimentStore.js` — 当前会话、文章阶段和恢复状态。
- Create: `client/src/experiment/experimentConfig.js` — 仅包含参与者可见的展示文案和阶段常量，不包含答案。
- Create: `client/src/components/experiment/ParticipantPicker.vue` — P01–P24 下拉选择和占用错误提示。
- Create: `client/src/components/experiment/InstructionStage.vue` — 实验说明。
- Create: `client/src/components/experiment/ReadingStage.vue` — 自然阅读、计时、滚动轨迹和评论事件采集。
- Create: `client/src/components/experiment/QuestionStage.vue` — 单题显示、提交、不可回退、题目计时。
- Create: `client/src/components/experiment/WorkloadStage.vue` — NASA-TLX、RC、CA。
- Create: `client/src/components/experiment/PreferenceStage.vue` — 四条件偏好排序。
- Create: `client/src/components/experiment/InterviewStage.vue` — 4道必填半结构化访谈题。
- Create: `client/src/components/experiment/ArticleRenderer.vue` — 根据当前条件选择 TE/CS/SE/BL 展示器。
- Create: `client/src/components/experiment/ProgressHeader.vue` — 只显示文章序号/阶段进度，不暴露条件。
- Modify: `client/src/components/ArticleContent.vue` — 若保留部分渲染代码，仅抽取/适配实验 renderer；移除研究原型控制栏和分析功能。
- Remove from active build: `ChartLegend.vue`, `CommentStats.vue`, `CommentToggles.vue`, `HighFrequencyWords.vue`, `HighFrequencyLegend.vue`, `ParagraphCommentTrigger.vue`, `Embedded mode/*`, copy 组件、分类/高频词相关代码和旧测试入口；这些文件先由完整备份保留。
- Create: `client/tests/experiment-flow.test.cjs` — 参与者流程与不可回退测试。
- Create: `client/tests/participant-allocation.test.cjs` — P01–P24 展示映射契约测试。
- Modify: `client/package.json` — 测试脚本和必要依赖。
- Create: `README_EXPERIMENT.md` — 自有服务器部署、备份、导出、重置、预测试和正式实验操作说明。

## Task 1: Create and verify the pre-change backup

**Files:**
- Create outside active source: `/Users/hl/Desktop/Comments_Annotations_backups/CommentScope-pre-experiment-2026-09-11/`
- Read-only source: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/`
- Create: `docs/superpowers/plans/2026-09-11-experiment-system-implementation.md`

- [ ] Record current path, Git HEAD, Git status summary, file manifest and SHA-256 manifest.
- [ ] Make an exact source snapshot of the current confirmed system directory, including current source, data, configs, built assets and existing tests; exclude only transient lock files if the snapshot process cannot copy them.
- [ ] Write a README in the backup explaining that it is the pre-experiment baseline and must not be edited.
- [ ] Verify the backup manifest matches the source manifest and record the archive checksum.
- [ ] Only after verification, create a local `codex/experiment-system-2026-09-11` branch or a clearly documented in-place checkpoint if the existing dirty Git state prevents a safe branch checkpoint.

## Task 2: Establish server-side experiment configuration and material contracts

**Files:**
- Create: `server/experiment_config.py`
- Create: `server/experiment_materials.py`
- Create: `server/tests/test_experiment_config.py`
- Read: `/Users/hl/CommentScope__CHI_2027_/experiment_design_clean_2026-09-11/01_实验设计指导稿.md`
- Read: `/Users/hl/CommentScope__CHI_2027_/experiment_design_clean_2026-09-11/02_A02_文章与题目.md`
- Read: `/Users/hl/CommentScope__CHI_2027_/experiment_design_clean_2026-09-11/03_A03_文章与题目.md`
- Read: `/Users/hl/CommentScope__CHI_2027_/experiment_design_clean_2026-09-11/04_A04_文章与题目.md`
- Read: `/Users/hl/CommentScope__CHI_2027_/experiment_design_clean_2026-09-11/05_A07_文章与题目.md`
- Read: `/Users/hl/CommentScope__CHI_2027_/experiment_design_clean_2026-09-11/答案表.md`

- [ ] Write failing tests for all 24 participants, four groups of six, Latin-square balance, article order, and one condition per article.
- [ ] Write failing material-contract tests for 4 articles, 10 comments each, 4 CRA items, 2 ACA items, 2 CTIA items, 2 location items, and exactly one answer per item.
- [ ] Implement immutable server-side participant allocation and material parsing/validation.
- [ ] Ensure participant payloads omit `group_id`, condition labels, internal comment IDs, anchors and answers while server-side records retain them.
- [ ] Run the focused server tests and confirm they pass.

## Task 3: Add SQLite schema, event logging and session recovery

**Files:**
- Create: `server/database.py`
- Create: `server/experiment_service.py`
- Create: `server/tests/test_database.py`

- [ ] Write failing tests for session creation, exclusive participant lock, heartbeat/release, resume after interruption, immutable submitted answers, raw event ordering, formal/pilot separation, and derived metrics.
- [ ] Implement tables for sessions, article_sessions, events, question_items, responses, workload_surveys, preferences and interviews with UTC timestamps and indexes.
- [ ] Implement transaction-safe idempotent event/response writes keyed by client event IDs or server request IDs.
- [ ] Implement scroll trace storage and normalized scroll distance calculation as `sum(abs(deltaScrollY)) / documentHeight`.
- [ ] Implement session resume at the last incomplete stage without reopening submitted items.
- [ ] Run focused tests and verify SQLite survives close/reopen.

## Task 4: Replace Tornado endpoints with experiment APIs

**Files:**
- Modify: `server/server.py`
- Create: `server/scripts/import_materials.py`
- Create: `server/scripts/backup_database.py`
- Create: `server/tests/test_api.py`

- [ ] Write failing API tests for participant list, session start/resume, safe article payload, event ingestion, response submission, survey/interview submission, finish, export and protected reset.
- [ ] Implement JSON request validation and explicit error responses for invalid participant IDs, stale sessions, duplicate submissions and malformed payloads.
- [ ] Implement endpoints that never return correct answers or internal metadata to participants.
- [ ] Implement CSV/JSON exports with raw events and analysis-ready tables, plus pilot/formal filtering.
- [ ] Implement token-protected researcher operations using an environment variable, with no hard-coded secret.
- [ ] Implement one-command material import and SQLite backup using the SQLite backup API.
- [ ] Run all server tests.

## Task 5: Build the participant UI and four controlled renderers

**Files:**
- Replace: `client/src/App.vue`
- Create: `client/src/experiment/experimentApi.js`
- Create: `client/src/experiment/experimentStore.js`
- Create: `client/src/experiment/experimentConfig.js`
- Create: `client/src/components/experiment/ParticipantPicker.vue`
- Create: `client/src/components/experiment/InstructionStage.vue`
- Create: `client/src/components/experiment/ReadingStage.vue`
- Create: `client/src/components/experiment/QuestionStage.vue`
- Create: `client/src/components/experiment/WorkloadStage.vue`
- Create: `client/src/components/experiment/PreferenceStage.vue`
- Create: `client/src/components/experiment/InterviewStage.vue`
- Create: `client/src/components/experiment/ArticleRenderer.vue`
- Create: `client/src/components/experiment/ProgressHeader.vue`
- Modify: `client/src/components/ArticleContent.vue` or replace with renderer-specific focused components.
- Remove from active build: unused prototype controls, analytics visuals, keyword/classification components, copy components and test-only entry points.
- Create: `client/tests/experiment-flow.test.cjs`
- Create: `client/tests/participant-allocation.test.cjs`

- [ ] Write failing tests for participant picker, phase order, one-question display, no back navigation, disabled duplicate submit, required surveys/interviews, and resume state.
- [ ] Implement the participant picker and server session start/resume flow.
- [ ] Implement reading stage instrumentation: visible start time, completion time, scroll trace, document height, normalized distance, comment open/close/click events, unload/visibility interruption.
- [ ] Implement TE, CS, SE and BL renderers using the same normalized article/comment material and condition-specific presentation only.
- [ ] Implement question stage with CRA/ACA/CTIA/location labels hidden from participants, one item at a time, submit acknowledgements and server-side scoring.
- [ ] Implement NASA-TLX six dimensions, RC, CA, preference ranking and required four free-text interview answers.
- [ ] Implement reconnect/resume hydration and a clear completion state.
- [ ] Run client tests and production build.

## Task 6: Remove unused active code and document operations

**Files:**
- Remove from active build: prototype-only components and imports identified in Task 5.
- Modify: `client/src/api/index.js` or replace with experiment API client.
- Create: `README_EXPERIMENT.md`
- Create: `.env.example`

- [ ] Confirm every removed component is present in the pre-change backup before deleting it from the active build.
- [ ] Remove old generic article/comments endpoints, live crawl/analysis paths, layout switcher and participant-facing debug controls.
- [ ] Add deployment instructions for Tornado, Vue build serving, persistent SQLite directory, backup schedule, admin token, pilot reset and formal export.
- [ ] Add a preflight command that validates materials, participant balance, schema and writable data directory.
- [ ] Run lint/build/test checks after cleanup.

## Task 7: End-to-end verification and release readiness

**Files:**
- Modify tests/docs only as needed from previous tasks.
- Create: `server/tests/test_preflight.py` if needed.

- [ ] Run server unit/API tests, client tests and production build.
- [ ] Run a scripted P01–P24 allocation check and verify every article-condition cell has six participants.
- [ ] Execute a pilot walkthrough covering all four conditions, interruption/resume, duplicate session prevention, all question types, surveys, preference and interview completion.
- [ ] Verify exported CSV/JSON contains the required fields from the guidance document and excludes answer leakage from participant payloads.
- [ ] Verify SQLite backup restore into a clean file and compare row counts/checksums.
- [ ] Inspect the final Git diff, confirm no source deletion occurred before backup verification, and report exact backup path, tests and deployment steps.

## Verification Commands

- `cd /Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/server && python3 -m unittest discover -s tests -v`
- `cd /Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client && npm test -- --runInBand`
- `cd /Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client && npm run build`
- `cd /Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/server && python3 scripts/preflight.py`

