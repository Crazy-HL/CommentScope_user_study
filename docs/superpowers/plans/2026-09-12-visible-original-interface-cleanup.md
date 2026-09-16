# Visible Original Interface Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore the original system's actually visible article/comment interface inside the experiment flow, while deleting prototype features that were disabled before the experiment.

**Architecture:** Keep the experiment flow and server payload unchanged. Make `ArticleRenderer.vue` the experiment-only adapter for the original visible renderer: it receives the server-provided fixed `render_mode`, renders the original three-column article/comment layout and four embedding modes, and emits interaction events. Keep participant controls that were visible in the original UI (sentence/paragraph comment toggles, Like/Reply sliders, layout buttons), but make layout buttons display-only/disabled so the assigned condition cannot change. Remove disabled comment classification, pie charts, high-frequency words, and related code from the experiment renderer.

**Tech Stack:** Vue 3, Vue CLI, Node contract tests, Tornado/Python experiment API.

## Global Constraints

- Do not change P01–P24 allocation, article order, question data, SQLite schema, or CRA hiding behavior.
- Do not expose `internal_id`, `internal_anchor`, `render_mode`, condition codes, or answer keys in participant-facing text.
- Preserve event emission through `interaction` for comment clicks, panel open/close, control changes, and layout-control attempts.
- CRA must continue to render no article or comment DOM; ACA, CTIA, and location must render the article and comments.
- Preserve the existing backup and do not restore deleted node_modules or unrelated prototype files.
- The disabled prototype features are comment classification/type legend, pie chart, high-frequency-word highlighting/legend, and their controls/calculations.

---

### Task 1: Lock the visible-interface contract

**Files:**
- Modify: `client/tests/experiment-flow.test.cjs`
- Create: no new production files

**Interfaces:**
- The test reads `client/src/components/experiment/ArticleRenderer.vue` as a static contract.
- The renderer must contain visible control/layout/sidebar class names and must not contain disabled-feature identifiers.

- [ ] **Step 1: Add failing assertions**

Add assertions for `control-panel`, `CommentToggles` or equivalent sentence/paragraph controls, `layout-switcher`, `like-slider`, `reply-slider`, `global-comments-panel`, `annotation-panel`, `ParagraphCommentTrigger`, and active/disabled layout controls. Add negative assertions for `commentClassification`, `keywordHighlight`, `ChartLegend`, `HighFrequencyWords`, `type-pie-chart`, and comment-type labels.

- [ ] **Step 2: Run the focused contract test**

Run:

```bash
cd /Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client
node tests/experiment-flow.test.cjs
```

Expected: FAIL because the current renderer lacks the original visible control/sidebar contract and still contains disabled-feature remnants.

---

### Task 2: Replace the simplified renderer with the visible original renderer adapter

**Files:**
- Modify: `client/src/components/experiment/ArticleRenderer.vue`
- Reference only: `/Users/hl/Desktop/Comments_Annotations_backups/CommentScope-pre-experiment-2026-09-11_225707/source/client/src/components/ArticleContent.vue`

**Interfaces:**
- Props: `{ article: Object }`.
- Emits: `interaction` with `{ type: string, payload: object }`.
- `article.render_mode` remains the only source of the assigned layout.

- [ ] **Step 1: Implement the visible control bar**

Render sentence-comment and paragraph-comment toggles, Like/Reply range sliders, and four layout buttons. Bind the toggles/sliders to local state and emit `control_change` events. Mark the assigned layout button active and disabled; all layout buttons must not mutate `article.render_mode` or local mode.

- [ ] **Step 2: Implement the original three-column structure**

Render the global comments panel on the left when global comments exist, article content in the center, and the sentence annotation panel on the right when a sentence is selected. Keep original avatars, usernames, comment text, Likes/Replies, close button, panel borders, and connection line behavior.

- [ ] **Step 3: Implement all four visible embedding modes**

Use the existing mapping `layout_a -> baseline`, `layout_b -> cs`, `layout_c -> se`, `layout_d -> be`. Preserve baseline comment list, CS sentence marker and right-side panel, SE sentence-end inline comment, and BE absolute between-line comment. Preserve paragraph comment trigger and expandable paragraph comment body.

- [ ] **Step 4: Delete disabled feature paths**

Remove imports, props, state, computed values, templates, styles, and methods for comment classification, type labels/colors, pie charts, high-frequency words, legends, and keyword highlighting. Do not remove generic comment rendering or the visible Like/Reply/paragraph controls.

- [ ] **Step 5: Run the focused contract test and build**

Run:

```bash
cd /Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client
node tests/experiment-flow.test.cjs
npm run build
```

Expected: contract checks pass and Vue production build exits 0.

---

### Task 3: Verify experiment-stage integration

**Files:**
- Inspect: `client/src/components/experiment/ReadingStage.vue`
- Inspect: `client/src/components/experiment/QuestionStage.vue`
- Modify only if a regression is proven: those same files

**Interfaces:**
- Reading stage continues to record renderer `interaction` events and reading/scroll events.
- CRA continues to omit `ArticleRenderer`; non-CRA question stages continue to include it.

- [ ] **Step 1: Run frontend experiment tests**

```bash
cd /Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client
npm run test:experiment
npm run test:experiment-flow
```

- [ ] **Step 2: Run server tests and preflight**

```bash
cd /Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue
python3 -m pytest -q server/tests
python3 server/scripts/preflight.py --db /tmp/commentscope-local-test.sqlite3
```

- [ ] **Step 3: Check the diff for scope control**

```bash
git status --short
 git diff -- client/src/components/experiment/ArticleRenderer.vue client/tests/experiment-flow.test.cjs
```

Confirm no backup, formal database, allocation, question, or unrelated deleted dependency files are changed by this task.

---

### Task 4: Browser verification

**Files:**
- No production changes unless browser verification exposes a regression.

- [ ] **Step 1: Start the local client/server using the repository's documented command**

Use the existing local project start command and confirm `http://127.0.0.1:8888/` loads.

- [ ] **Step 2: Check one article for each layout**

Verify the visible original structure and interactions for baseline, CS, SE, and BE. Confirm controls remain visible, layout buttons are non-switching, sliders and sentence/paragraph toggles work, and comment clicks emit events.

- [ ] **Step 3: Check CRA**

After clicking “完成阅读并答题”, confirm article text and all comments are absent from the DOM and no back navigation is offered.
