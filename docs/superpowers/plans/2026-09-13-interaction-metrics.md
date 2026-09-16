# 文章与题目交互指标记录 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Record and aggregate meaningful article-level and question-level interactions without changing the participant-facing experiment flow.

**Architecture:** Keep `events` as the raw event ledger, extend it with article order and stage, and add article-block summary columns in SQLite. The reading component sends throttled scroll samples and typed comment interactions; the question component sends option-selection events and submits counts alongside the existing response. When an article remains visible during ACA, CTIA, or LOCATION, QuestionStage also records scroll samples and attaches per-question scroll summaries; CRA reports zero because its article is hidden. Existing databases are migrated idempotently at startup.

**Tech Stack:** Vue 3, Axios, Tornado/Python, SQLite, Node contract tests, Python unittest.

## Global Constraints

- Do not change P01–P24 allocation, article order, question data, or CRA hiding behavior.
- Do not record meaningless global document clicks; record only experiment-related interactions.
- Preserve existing fields and support existing SQLite files through idempotent migrations.
- Keep raw events and derived counts; do not replace raw event history with aggregates.

---

### Task 1: Lock the persistence contract with failing tests

**Files:**
- Modify: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/server/tests/test_database.py` (create if absent)
- Modify: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client/tests/experiment-flow.test.cjs`

**Interfaces:**
- The database tests instantiate `ExperimentDatabase` against a temporary SQLite path.
- The client contract test reads Vue source as text.

- [ ] **Step 1: Add Python assertions for new schema columns and updates**

Assert that a new database has `article_sessions.scroll_event_count`, `total_scroll_distance_px`, `max_scroll_y`, `comment_click_count`, `comment_open_count`, `comment_close_count`, and `paragraph_toggle_count`; `events.article_order` and `events.stage`; and `responses.option_click_count`, `option_change_count`, `scroll_event_count`, `total_scroll_distance_px`, and `max_scroll_y`. Insert an event with order/stage metadata and assert it is returned. Call `update_reading` with new summary fields and assert they persist. Insert a response with counts and assert they persist.

- [ ] **Step 2: Run the focused Python test and verify it fails**

Run:

```bash
cd /Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue
python3 -m unittest server.tests.test_database -v
```

Expected: FAIL because the new columns and method parameters do not yet exist.

- [ ] **Step 3: Add client source assertions**

Assert that `ReadingStage.vue` emits `stage: "reading"`, sends `scroll_event_count`, `total_scroll_distance_px`, `max_scroll_y`, and typed comment counts; assert that `QuestionStage.vue` emits `question_option_change`, tracks option clicks/changes, and sends both counts to `submitResponse`.

- [ ] **Step 4: Run the focused client test and verify it fails**

Run:

```bash
cd /Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client
node tests/experiment-flow.test.cjs
```

Expected: FAIL on the new source-contract assertions.

### Task 2: Add SQLite migrations and persistence APIs

**Files:**
- Modify: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/server/database.py`
- Modify: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/server/experiment_service.py`
- Modify: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/server/server.py` only if request parsing needs new fields
- Test: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/server/tests/test_database.py`

**Interfaces:**
- `ExperimentDatabase.log_event(..., article_order=0, stage=None)` stores structured context and remains backward-compatible for old callers.
- `ExperimentDatabase.update_reading(..., scroll_event_count=0, total_scroll_distance_px=0, max_scroll_y=0, comment_counts=None)` persists article-level reading summaries.
- `ExperimentDatabase.insert_response(..., option_click_count=1, option_change_count=0)` persists question interaction summaries.
- `ExperimentService.log_event` and `finish_reading` pass the new optional values through.

- [ ] **Step 1: Implement idempotent column migration**

After `executescript(SCHEMA)`, inspect `PRAGMA table_info` and execute `ALTER TABLE ... ADD COLUMN` only for missing columns. Use defaults that allow existing rows to load: integer counts `0`, distances `0`, and nullable event context.

- [ ] **Step 2: Implement structured raw-event context**

Extend the `events` insert with `article_order` and `stage`; decode them in `list_events`. Keep payload JSON unchanged for compatibility.

- [ ] **Step 3: Implement article summary persistence**

Extend `update_reading` to persist scroll and typed comment counts, keeping `comment_interaction_count` as the sum/legacy field supplied by the client.

- [ ] **Step 4: Implement question summary persistence**

Extend `responses` insert and service/request handling to persist `option_click_count` and `option_change_count`, defaulting old requests to one click and zero changes.

- [ ] **Step 5: Run the focused Python test and verify it passes**

Run:

```bash
cd /Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue
python3 -m unittest server.tests.test_database -v
```

Expected: PASS with no failures.

### Task 3: Record reading-stage scroll and typed comment interactions

**Files:**
- Modify: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client/src/components/experiment/ReadingStage.vue`
- Modify: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client/src/components/experiment/ArticleRenderer.vue`
- Modify: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client/src/experiment/experimentApi.js` only if the API payload needs explicit fields
- Test: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client/tests/experiment-flow.test.cjs`

**Interfaces:**
- Reading event payloads include `stage: "reading"`.
- Scroll state tracks sampled event count, total pixel distance, and maximum Y.
- Article renderer emits typed payloads with `comment_index` or `paragraph_index`.

- [ ] **Step 1: Add the minimal reading metrics state**

Track `scrollEventCount`, `maxScrollY`, and typed comment counters. Increment scroll distance on every native scroll event; increment event count only when the existing 180 ms throttle emits a raw `scroll` event. Flush a pending scroll sample before finishing so the final movement is not lost.

- [ ] **Step 2: Add stage and typed interaction payloads**

Add `stage: "reading"` to reading events. Ensure `comment_click`, `comment_open`, `comment_close`, and `paragraph_toggle` carry their existing indices and are counted separately before sending.

- [ ] **Step 3: Send article-level summary fields on finish**

Send `scroll_event_count`, `total_scroll_distance_px`, `max_scroll_y`, and all typed comment counts to `finishReading`, while retaining `normalized_scroll_distance` and `comment_interaction_count`.

- [ ] **Step 4: Run the focused client contract test and verify it passes**

Run:

```bash
cd /Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client
node tests/experiment-flow.test.cjs
```

Expected: PASS for reading metric assertions.

### Task 4: Record question option clicks and changes

**Files:**
- Modify: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client/src/components/experiment/QuestionStage.vue`
- Modify: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/server/database.py` if response compatibility refinement is needed
- Test: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client/tests/experiment-flow.test.cjs`

**Interfaces:**
- Each question starts with `optionClickCount = 0`, `optionChangeCount = 0`, and no selected option.
- Selecting an option increments click count; selecting a different option after a prior selection increments change count.
- `submitResponse` receives both counts.
- `question_option_change` raw event contains the question identity, stage, item index, and selected option.

- [ ] **Step 1: Track option selection metrics**

Use an explicit handler on each radio input/label instead of relying only on `v-model`, so every participant option click is counted and the previous selection is available for change detection.

- [ ] **Step 2: Emit question interaction events**

Send `question_option_change` with `stage` equal to the current group and include `question_type`, `question_id`, `item_index`, `selected_option`, and the elapsed time since display.

- [ ] **Step 3: Submit counts with the final response**

Pass `option_click_count` and `option_change_count` to the API. Reset counts when the next question is displayed.

- [ ] **Step 4: Run focused client and Python tests**

Run:

```bash
cd /Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client
node tests/experiment-flow.test.cjs
cd ..
python3 -m unittest server.tests.test_database -v
```

Expected: PASS.

### Task 5: Verify compatibility and inspect database output

**Files:**
- Modify: no production files unless verification finds a concrete failure
- Test: existing client and server test suites

- [ ] **Step 1: Run all experiment tests**

```bash
cd /Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client
npm run test:experiment
cd ..
python3 -m unittest discover -s server/tests -v
```

Expected: all tests pass.

- [ ] **Step 2: Build the client**

```bash
cd /Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client
npm run build
```

Expected: Vue production build exits with code 0.

- [ ] **Step 3: Verify SQLite schema and sample aggregation**

Create a temporary database, insert one reading event, two question option-change events, one response, and one article summary. Query the new columns and assert the values match the sent metrics.

- [ ] **Step 4: Report exact changed files and any remaining limitations**

Do not claim all-click tracking: the implementation records meaningful experiment controls only, not arbitrary page clicks.
