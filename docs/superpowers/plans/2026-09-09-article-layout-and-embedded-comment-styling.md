# Article Layout and Embedded Comment Styling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give embedded comments a single neutral color while classification is disabled, widen the article at 1280 × 720, reduce oversized typography, and constrain the top filter sliders.

**Architecture:** Keep the existing feature-flag system and semantic-color code intact. Add conditional presentation classes in `ArticleContent.vue`, use an annotation-state class to switch between two- and three-column grids, and lock the agreed visual values with the existing source-level Node regression test.

**Tech Stack:** Vue 3 single-file component, scoped CSS, Node.js `assert`, Vue CLI production build, in-app browser verification.

## Global Constraints

- Target viewport is 1280 × 720 desktop.
- Comment classification and keyword highlighting remain disabled by hidden internal feature flags.
- Existing classification and keyword-highlight implementation must not be deleted.
- The neutral embedded-comment color is exactly `#4f6f82` and carries no semantic meaning.
- No user-visible feature or appearance switch is added.
- Do not stage, commit, clean, or otherwise include unrelated repository changes; the repository currently contains a migrated untracked project copy and widespread unrelated deletions.

---

### Task 1: Add failing visual-regression source assertions

**Files:**
- Modify: `client/tests/feature-flags.test.cjs`
- Test: `client/tests/feature-flags.test.cjs`

**Interfaces:**
- Consumes: source text from `src/components/ArticleContent.vue`.
- Produces: regression assertions for `embedded-comment-neutral`, `has-annotation-panel`, the neutral color, grid widths, typography, and slider dimensions.

- [ ] **Step 1: Append exact failing assertions**

Add these assertions before the existing `console.log`:

```js
assert.match(
	article,
	/:class="\{\s*'has-annotation-panel':\s*activeSentence !== null &&\s*hasComments\(activeSentence\)\s*\}"/
);
assert.match(
	article,
	/:class="featureFlags\.commentClassification\s*\?\s*`comment-type-\$\{getCommentType\([\s\S]*?\)\}`\s*:\s*'embedded-comment-neutral'"/
);
assert.match(
	article,
	/class="absolute-comment"[\s\S]*?:class="\{\s*'embedded-comment-neutral':\s*!featureFlags\.commentClassification\s*\}"/
);
assert.match(article, /\.embedded-comment-neutral\s*\{[\s\S]*?color:\s*#4f6f82;/);
assert.match(
	article,
	/\.main-content\s*\{[\s\S]*?grid-template-columns:\s*260px\s+minmax\(0,\s*1fr\);/
);
assert.match(
	article,
	/\.main-content\.has-annotation-panel\s*\{[\s\S]*?grid-template-columns:\s*230px\s+minmax\(0,\s*1fr\)\s+230px;/
);
assert.match(article, /\.article-title\s*\{[\s\S]*?font-size:\s*28px;/);
assert.match(article, /\.article-content\s*\{[\s\S]*?font-size:\s*16px;/);
assert.match(
	article,
	/\.comment-text,\s*\.annotation-text\s*\{[\s\S]*?font-size:\s*14px;[\s\S]*?line-height:\s*1\.55;/
);
assert.match(
	article,
	/\.filter-sliders-compact\s*\{[\s\S]*?flex:\s*0 0 170px;[\s\S]*?width:\s*170px;/
);
assert.match(
	article,
	/\.slider-compact\s*\{[\s\S]*?width:\s*110px;[\s\S]*?flex:\s*0 0 110px;/
);
```

- [ ] **Step 2: Run the regression test and verify RED**

Run:

```bash
cd client && npm run test:feature-flags
```

Expected: FAIL on the first new assertion because `has-annotation-panel` and the new styling do not yet exist.

- [ ] **Step 3: Inspect the failure**

Confirm the failure is an assertion mismatch for the newly requested behavior, not a syntax error in the test.

---

### Task 2: Implement neutral comment styling and state-aware layout

**Files:**
- Modify: `client/src/components/ArticleContent.vue:139-300`
- Modify: `client/src/components/ArticleContent.vue:1017-1535`
- Test: `client/tests/feature-flags.test.cjs`

**Interfaces:**
- Consumes: `featureFlags.commentClassification`, `activeSentence`, and `hasComments(index)`.
- Produces: conditional classes `embedded-comment-neutral` and `has-annotation-panel`; CSS rules for the approved dimensions and typography.

- [ ] **Step 1: Bind the main-grid state class**

Change the main-content opening element to:

```vue
<div
	class="main-content"
	:class="{
		'has-annotation-panel':
			activeSentence !== null && hasComments(activeSentence)
	}">
```

- [ ] **Step 2: Bind the neutral class to Sentence-End comments**

Replace the current Sentence-End `:class` expression with:

```vue
:class="featureFlags.commentClassification
	? `comment-type-${getCommentType(sentenceData.topComment)}`
	: 'embedded-comment-neutral'"
```

This preserves all original semantic classes when classification is restored.

- [ ] **Step 3: Bind the neutral class to Between-Line comments**

Add this binding to the `.absolute-comment` element:

```vue
:class="{
	'embedded-comment-neutral': !featureFlags.commentClassification
}"
```

- [ ] **Step 4: Apply the approved embedded-comment and typography CSS**

Update or add these declarations:

```css
.paragraph-text {
	line-height: 1.7;
}

.absolute-comment {
	font-size: 0.78em;
}

.embedded-comment-neutral {
	color: #4f6f82;
}

.article-title {
	font-size: 28px;
}

.article-content {
	font-size: 16px;
}

.comment-text,
.annotation-text {
	font-size: 14px;
	line-height: 1.55;
}
```

Keep the existing `.inline-comment.comment-type-1` through `.comment-type-5` declarations unchanged.

- [ ] **Step 5: Replace the desktop grid with state-aware columns**

Use these desktop rules:

```css
.main-content {
	display: grid;
	grid-template-columns: 260px minmax(0, 1fr);
	gap: 20px;
	width: 100%;
	max-width: 2500px;
	margin: 0 auto;
}

.main-content.has-annotation-panel {
	grid-template-columns: 230px minmax(0, 1fr) 230px;
}
```

Remove the obsolete `@media (max-width: 1400px)` three-column override because it would overwrite the new state-aware grid at the 1280px target width.

Inside the existing `@media (max-width: 1200px)` rule, retain the two-column responsive grid and explicitly map the panels:

```css
.global-comments-panel {
	grid-area: global;
}
.article-panel {
	grid-area: article;
}
.annotation-panel {
	grid-area: annotation;
}
```

The existing `@media (max-width: 768px)` single-column template then stacks the named areas correctly.

- [ ] **Step 6: Constrain the top slider group**

Update the compact filter styles to:

```css
.filter-sliders-compact {
	display: flex;
	flex-direction: column;
	gap: 4px;
	flex: 0 0 170px;
	width: 170px;
	padding: 0 4px;
	min-width: 0;
}

.filter-group-compact {
	gap: 4px;
}

.slider-compact {
	width: 110px;
	flex: 0 0 110px;
}

.filter-value-compact {
	min-width: 24px;
}
```

Keep all existing range track, thumb, gradient, hover, accessibility, and `v-model` behavior.

- [ ] **Step 7: Run the regression test and verify GREEN**

Run:

```bash
cd client && npm run test:feature-flags
```

Expected: `feature flag regression checks passed` with exit code 0.

- [ ] **Step 8: Review only the intended file changes**

Run:

```bash
git diff -- client/src/components/ArticleContent.vue client/tests/feature-flags.test.cjs
```

Expected: only the conditional classes, layout/typography/slider CSS, and regression assertions described above. Do not stage or commit because of the repository migration state.

---

### Task 3: Build and visually verify all layouts

**Files:**
- Verify: `client/src/components/ArticleContent.vue`
- Verify: `client/tests/feature-flags.test.cjs`

**Interfaces:**
- Consumes: running frontend at `http://localhost:8080/` and backend at `http://localhost:8888/`.
- Produces: measured and visual evidence that the approved design works at 1280 × 720.

- [ ] **Step 1: Run the production build**

Run:

```bash
cd client && npm run build
```

Expected: exit code 0. Existing Browserslist freshness and bundle-size warnings are acceptable; compile errors are not.

- [ ] **Step 2: Reload the running page at 1280 × 720**

Use the in-app browser, reload `http://localhost:8080/`, and set or confirm a 1280 × 720 viewport.

- [ ] **Step 3: Measure the default Sentence-End layout**

Verify computed styles and dimensions:

- `.article-content` font size is `16px`.
- `.article-title` font size is `28px`.
- `.slider-compact` width is approximately `110px`.
- `.inline-comment.embedded-comment-neutral` resolves to `rgb(79, 111, 130)`.
- With no active detail panel, `.main-content` has two columns and `.article-panel` is substantially wider than the previous approximately `585px`; expected panel width is around `929px` at the current page padding and gap.

- [ ] **Step 4: Verify the active-detail three-column state**

Click a sentence with comments and verify:

- `.main-content` gains `has-annotation-panel`.
- The right sentence-related comments panel appears.
- Computed columns are approximately `230px 709px 230px` at the target viewport.
- The article remains readable and no panel overlaps.

- [ ] **Step 5: Verify Between-Line and Click-to-Show**

Switch to Between-Line and verify positioned embedded comments use the same neutral blue-gray color and remain legible. Switch to Click-to-Show and verify sentence selection and the right detail panel still work.

- [ ] **Step 6: Capture a final browser screenshot and inspect it**

Confirm visually that the wider article, smaller type, shorter sliders, and neutral comment color improve screenshot balance without reintroducing semantic classification or keyword highlighting.

- [ ] **Step 7: Run the final verification commands together**

Run:

```bash
cd client && npm run test:feature-flags && npm run build
```

Expected: regression checks pass and build exits 0.
