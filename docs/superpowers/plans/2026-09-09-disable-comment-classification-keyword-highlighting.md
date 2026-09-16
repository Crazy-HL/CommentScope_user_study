# Disable Comment Classification and Keyword Highlighting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Use hidden internal feature flags to suspend comment classification and all keyword highlighting while preserving the existing implementation for later restoration.

**Architecture:** Add one front-end-only feature flag module as the source of truth. `ArticleContent.vue` will gate classification rendering, classification filtering, classification styling, and both highlighting paths; `CommentToggles.vue` will accept a visibility prop so the existing Frequent Words control remains in code but is not rendered. The Tornado API and JSON payload remain unchanged.

**Tech Stack:** Vue 3, Vue Single File Components, Vue CLI 5, Node.js assertion-based regression test, Tornado backend unchanged.

## Global Constraints

- The feature flags must exist only in code and must not appear as controls in the UI.
- Existing classification and highlighting components, functions, styles, and backend fields must not be deleted.
- `commentClassification` and `keywordHighlight` must default to `false`.
- Restoring either feature must require changing only its internal flag to `true`.
- Likes/replies filters, all comment modes, and Sentence-End/Between-Line/Click-to-Show layouts must remain functional.

---

## File Structure

- Create `client/src/config/featureFlags.js`: hidden, centralized immutable configuration.
- Create `client/tests/feature-flags.test.cjs`: source-level regression checks that prove the flags and all required UI/behavior gates exist without adding a test framework.
- Modify `client/package.json`: expose the regression test as `npm run test:feature-flags`.
- Modify `client/src/components/CommentToggles.vue`: preserve the Frequent Words control but render it only when its new visibility prop is true.
- Modify `client/src/components/ArticleContent.vue`: consume the flags and gate all classification and highlighting behavior.

---

### Task 1: Add the hidden feature-flag contract

**Files:**
- Create: `client/src/config/featureFlags.js`
- Create: `client/tests/feature-flags.test.cjs`
- Modify: `client/package.json`

**Interfaces:**
- Produces: named export `featureFlags`, an immutable object with Boolean properties `commentClassification` and `keywordHighlight`.
- Produces: npm script `test:feature-flags` that exits nonzero when the flags or required component gates are missing.

- [ ] **Step 1: Write the failing regression test**

Create `client/tests/feature-flags.test.cjs`:

```js
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const read = relativePath =>
  fs.readFileSync(path.join(root, relativePath), "utf8");

const flags = read("src/config/featureFlags.js");
const article = read("src/components/ArticleContent.vue");
const toggles = read("src/components/CommentToggles.vue");

assert.match(flags, /commentClassification:\s*false/);
assert.match(flags, /keywordHighlight:\s*false/);
assert.match(flags, /Object\.freeze/);
assert.match(article, /import\s*\{\s*featureFlags\s*\}/);
assert.match(article, /:show-high-frequency-control="featureFlags\.keywordHighlight"/);
assert.match(article, /featureFlags\.commentClassification/);
assert.match(article, /featureFlags\.keywordHighlight/);
assert.match(article, /!featureFlags\.commentClassification\s*\|\|/);
assert.match(article, /if\s*\(!featureFlags\.keywordHighlight\)\s*return content/);
assert.match(toggles, /v-if="showHighFrequencyControl"/);
assert.match(toggles, /showHighFrequencyControl:\s*\{/);

console.log("feature flag regression checks passed");
```

- [ ] **Step 2: Add the npm test command**

Add this script to `client/package.json` without changing the existing scripts:

```json
"test:feature-flags": "node tests/feature-flags.test.cjs"
```

- [ ] **Step 3: Run the test and verify the red state**

Run:

```bash
cd client && npm run test:feature-flags
```

Expected: FAIL with `ENOENT` for `src/config/featureFlags.js` because production configuration has not been added yet.

- [ ] **Step 4: Add the minimal hidden configuration**

Create `client/src/config/featureFlags.js`:

```js
export const featureFlags = Object.freeze({
  commentClassification: false,
  keywordHighlight: false
});
```

- [ ] **Step 5: Run the test again to expose the remaining missing gates**

Run:

```bash
cd client && npm run test:feature-flags
```

Expected: FAIL on the first missing assertion in `ArticleContent.vue` or `CommentToggles.vue`. This confirms the test is checking behavior integration rather than only configuration existence.

- [ ] **Step 6: Commit the contract and red integration test**

```bash
git add client/src/config/featureFlags.js client/tests/feature-flags.test.cjs client/package.json
git commit -m "test: define reversible feature flag contract"
```

---

### Task 2: Gate the existing classification and highlighting UI

**Files:**
- Modify: `client/src/components/CommentToggles.vue`
- Modify: `client/src/components/ArticleContent.vue`
- Test: `client/tests/feature-flags.test.cjs`

**Interfaces:**
- Consumes: `featureFlags.commentClassification: boolean` and `featureFlags.keywordHighlight: boolean` from Task 1.
- Produces: `CommentToggles` prop `showHighFrequencyControl: boolean`, defaulting to `true` to preserve compatibility.
- Produces: helper `getCommentBorderStyle(comment): object` that returns classification borders only when classification is enabled.
- Produces: helper `getCommentTooltip(comment, options): string` that omits Type metadata while classification is disabled.

- [ ] **Step 1: Preserve but hide the Frequent Words control**

In `CommentToggles.vue`, wrap the existing Frequent Words `.control-group` with:

```vue
<div v-if="showHighFrequencyControl" class="control-group">
```

Replace the current shorthand `defineProps` block with:

```js
defineProps({
  showInlineComments: Boolean,
  showParagraphComments: Boolean,
  showPieCharts: Boolean,
  showHighFrequencyWords: Boolean,
  showHighFrequencyControl: {
    type: Boolean,
    default: true
  }
});
```

Do not remove the existing checkbox, SVG, label, prop, or emit.

- [ ] **Step 2: Import and connect the hidden feature flags**

In `ArticleContent.vue`, add:

```js
import { featureFlags } from "@/config/featureFlags";
```

Pass the keyword flag into the existing toggle component:

```vue
<CommentToggles
  v-model:showInlineComments="showInlineComments"
  v-model:showParagraphComments="showParagraphComments"
  v-model:showPieCharts="showPieCharts"
  v-model:showHighFrequencyWords="showHighFrequencyWords"
  :show-high-frequency-control="featureFlags.keywordHighlight" />
```

- [ ] **Step 3: Gate classification controls and high-frequency legend**

Change the high-frequency legend condition to:

```vue
<HighFrequencyLegend
  v-if="featureFlags.keywordHighlight && showHighFrequencyWords"
  class="legend-item-compact" />
```

Wrap the existing `.comment-type-legend` and `ChartLegend` in a template gate, preserving their current contents:

```vue
<template v-if="featureFlags.commentClassification">
  <div class="comment-type-legend">
    <!-- preserve all five existing buttons -->
  </div>
  <ChartLegend
    :comments="allCommentsForLegend"
    class="chart-legend"
    :showPieChart="showPieCharts" />
</template>
```

- [ ] **Step 4: Disable both highlighting paths without deleting them**

At the beginning of `renderHighlightedContent`, after reading `content`, add:

```js
if (!featureFlags.keywordHighlight) return content;
```

For the existing `HighFrequencyWords` instance, keep the component but pass an empty keyword list and a false highlight value while disabled:

```vue
:wordsToHighlight="
  featureFlags.keywordHighlight
    ? getWordsToHighlight(sentenceData.originalIndex)
    : []
"
:showHighlight="featureFlags.keywordHighlight && showHighFrequencyWords"
```

This keeps sentence click behavior and comment markers intact while rendering ordinary sentence text.

- [ ] **Step 5: Stop classification from filtering comments**

Change the type condition in `getCommentsForSentence` to:

```js
(!featureFlags.commentClassification ||
  visibleCommentTypes.value[getCommentType(comment)]) &&
```

For every template condition that currently directly requires `visibleCommentTypes[getCommentType(...)]`, use the equivalent gate:

```vue
(!featureFlags.commentClassification ||
  visibleCommentTypes[getCommentType(comment)])
```

This preserves the old type visibility state but ignores it while classification is disabled.

- [ ] **Step 6: Remove visible type decoration through reversible helpers**

Add these helpers near the existing type helpers in `ArticleContent.vue`:

```js
const getCommentBorderStyle = (comment, width = 4) => {
  if (!featureFlags.commentClassification) return {};
  const border = `${width}px solid ${getTypeColor(comment)}`;
  return { borderLeft: border, borderRight: border };
};

const getCommentTooltip = (
  comment,
  { includeSentiment = false, includeStats = false } = {}
) => {
  const parts = [];
  if (includeSentiment) {
    parts.push(`Standpoint: ${getStandpointLabel(comment)}`);
    parts.push(`Emotion: ${getEmotionLabel(comment)}`);
  }
  if (featureFlags.commentClassification) {
    parts.push(`Type: ${getCommentTypeLabel(comment)}`);
  }
  if (includeStats) {
    parts.push(`Likes: ${formatNumber(comment.like_count)}`);
    parts.push(`Replies: ${formatNumber(comment.sub_comment_count)}`);
  }
  return parts.join(" | ");
};
```

Replace direct type-colored border bindings on global, paragraph, and annotation cards with `getCommentBorderStyle`; use width `3` for paragraph cards. Replace inline tooltip strings with `getCommentTooltip` calls so Type is omitted while disabled. Keep `getTypeColor` and `getCommentTypeLabel` unchanged.

- [ ] **Step 7: Hide embedded classification labels and classes**

Add `v-if="featureFlags.commentClassification"` to existing `.comment-type-tag` spans. Change embedded comment type class binding to return no type class while disabled:

```vue
:class="
  featureFlags.commentClassification
    ? `comment-type-${getCommentType(sentenceData.topComment)}`
    : null
"
```

Do not remove the existing labels, class names, color helpers, or CSS rules.

- [ ] **Step 8: Run the regression test and verify green**

Run:

```bash
cd client && npm run test:feature-flags
```

Expected:

```text
feature flag regression checks passed
```

- [ ] **Step 9: Build the production bundle**

Run:

```bash
cd client && npm run build
```

Expected: exit code 0 and `DONE  Build complete` or equivalent Vue CLI success output.

- [ ] **Step 10: Verify the running UI and API behavior**

With the backend on port 8888 and Vue dev server on port 8080:

```bash
curl -fsS http://localhost:8888/comments >/tmp/comments.json
curl -fsS http://localhost:8080/ >/tmp/article-ui.html
```

Then inspect the rendered page in the in-app browser and verify:

- no Frequent Words control or high-frequency legend;
- no five-category filter or category pie chart;
- no category tag, category border, or Type tooltip;
- no highlighted words in article text or comment text;
- comments, likes/replies filters, paragraph comments, and all three layouts remain usable.

- [ ] **Step 11: Commit the reversible UI change**

```bash
git add client/src/components/ArticleContent.vue client/src/components/CommentToggles.vue
git commit -m "feat: suspend classification and keyword highlighting"
```

---

## Self-Review Results

- Spec coverage: all eight acceptance criteria map to Task 2 Steps 1–10.
- Placeholder scan: all implementation and test steps are explicit; no unresolved markers remain.
- Type consistency: both flags are Boolean; `showHighFrequencyControl` is Boolean; helper names and signatures are consistent across the plan.
- Scope control: backend and JSON files are intentionally untouched.
