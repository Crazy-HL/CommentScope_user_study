# Academic Chart Style Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended; not required) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the administrator paper-analysis charts closely reproduce the supplied CommentScope Matplotlib figure while preserving real-data and in-memory demo-data behavior.

**Architecture:** Keep the charts as responsive Vue/SVG components rather than raster images, but consolidate the overall comparison into one figure-like two-panel SVG and implement the same statistical/display rules as the reference script. Keep condition values as TE, CS, SE, BL in application data; only the display order is adapted in the chart layer.

**Tech Stack:** Vue 3, SVG, JavaScript, CSS, existing Vue build/test scripts.

## Global Constraints

- Do not change participant-facing article/comment presentation or experiment flow.
- Do not write demo data to SQLite or include it in exports.
- Do not change database condition codes; preserve TE, CS, SE, BL.
- Keep the ordinary administrator overview page intact.
- Keep the existing summary API and empty-data handling.
- Use seconds for chart coordinates while accepting the existing millisecond time data.
- Use the supplied reference ordering as far as the current condition vocabulary permits: BL, SE, TE, CS.

### Task 1: Add chart contract tests

**Files:**
- Modify: `client/tests/admin-dashboard.test.cjs`

- [ ] **Step 1: Add failing source-contract assertions**

Assert that the academic chart components contain the required figure structure and behavior: a combined two-panel overall SVG, continuous coolwarm color mapping for overall plots, fixed 50-second time ticks, dynamic t-based CI, equal-value accuracy spreading, and a figure-level task legend.

- [ ] **Step 2: Run the focused test and verify it fails**

Run: `node client/tests/admin-dashboard.test.cjs`
Expected: FAIL because the current implementation still has two separate overall panels, fixed condition colors, and index-only jitter.

### Task 2: Replace the overall academic chart layout and statistics

**Files:**
- Modify: `client/src/components/admin/AdminAcademicOverallChart.vue`
- Modify: `client/src/components/admin/admin.css`

- [ ] **Step 1: Implement one figure-like two-panel SVG**

Render completion time and overall accuracy as adjacent panels with one shared condition axis, alternating row bands, left-side condition labels only, and top color ramps. Keep all observed points, black center statistics, and CI/error-bar marks.

- [ ] **Step 2: Implement reference-equivalent transforms**

Convert time milliseconds to seconds before scaling, use 50-second tick generation, use a dynamic Student-t critical-value approximation keyed to sample size, use continuous coolwarm interpolation for overall points, and spread equal accuracy values symmetrically around each row.

- [ ] **Step 3: Keep empty and partial data safe**

Do not render invalid coordinates for missing observations; retain the existing empty-state behavior in the parent page.

### Task 3: Align the task-level academic chart

**Files:**
- Modify: `client/src/components/admin/AdminAcademicTaskChart.vue`
- Modify: `client/src/components/admin/admin.css`

- [ ] **Step 1: Implement the reference task layout**

Use the three task categories on the x-axis, place four conditions around each category, render participant points plus mean and CI, and put the legend centered above the plotting area.

- [ ] **Step 2: Match reference colors and axes**

Use four discrete coolwarm samples for conditions, fixed 0.00–1.00 y-axis ticks, compact figure-like spacing, and the supplied task labels.

### Task 4: Verify integration and visual output

**Files:**
- No production files added.

- [ ] **Step 1: Run focused and regression tests**

Run:
- `node client/tests/admin-dashboard.test.cjs`
- `npm run test:experiment`
- `npm run build`
- `python3 -m pytest -q server/tests`

- [ ] **Step 2: Inspect the running analysis page**

Open `/admin/analysis?v=20260913-academic-style-final`, confirm the page renders with demo data, and check that the chart uses the combined overall figure and reference-style task figure without console errors.
