# Article Layout and Embedded Comment Styling Design

**Date:** 2026-09-09  
**Status:** Awaiting written-spec review  
**Target viewport:** 1280 × 720 desktop screenshot

## Goal

Improve screenshot readability by visually distinguishing comments embedded in the article without restoring semantic classification colors, widening the article column, reducing oversized typography, and shortening the top filter sliders.

## Scope

This change only affects presentation in `client/src/components/ArticleContent.vue` and regression checks in the client test suite. Existing comment-classification and keyword-highlight code remains intact and hidden behind the existing internal feature flags.

## Embedded Comment Styling

When `featureFlags.commentClassification` is `false`:

- Sentence-End embedded comments use one neutral blue-gray color: `#4f6f82`.
- Between-Line embedded comments use the same neutral blue-gray color.
- The color communicates “commentary” only and must not vary by `comment_type`.
- Semantic type labels remain hidden.
- Existing five semantic colors and their CSS classes remain unchanged so classification can be restored later by switching the feature flag back to `true`.

The embedded comment styling should remain visually secondary to the article body. It should not introduce a strong filled background or another legend.

## Responsive Layout

The main grid becomes state-aware:

- When the sentence-detail panel is closed, the page uses two effective columns: a fixed-width overall-comments panel of approximately `260px` and an article column that consumes the remaining width.
- When the sentence-detail panel is open, the page uses three columns: approximately `230px`, a flexible article column, and approximately `230px`.
- At the 1280 × 720 target viewport, the article should be substantially wider than the current approximately `585px` width.
- Existing small-screen breakpoints continue to stack panels rather than forcing narrow desktop columns.
- No empty grid track should be reserved for the conditional right detail panel when it is not displayed.

A state class on `.main-content` will identify whether the detail panel is open. This keeps the behavior explicit and avoids relying on fragile selectors tied to conditional DOM structure.

## Typography

- Article body font size changes from `20px` to `16px`.
- Normal paragraph line height changes from `1.8` to `1.7`.
- The enlarged Between-Line layout retains extra vertical spacing, adjusted only if necessary to keep positioned comments from colliding.
- Article title changes from `34px` to `28px`.
- Overall and sentence-detail comment text changes from `20px` to `14px` with a readable line height near `1.55`.
- Metadata, usernames, counters, and control labels retain their current hierarchy unless a minor spacing adjustment is required by the narrower side columns.

## Top Controls

- The like/reply filter container no longer grows to occupy all remaining horizontal space.
- Its overall width is approximately `170px`.
- Each range input is approximately `110px`, with the numeric value still visible.
- The controls remain keyboard-accessible and retain their current labels, values, and filtering behavior.
- At smaller widths, the existing wrapping behavior remains available.

## Feature Restoration Compatibility

No classification or keyword-highlight implementation is deleted. When `commentClassification` is restored to `true`:

- Existing per-type classes continue to provide their original semantic colors.
- Existing type labels, legends, filters, borders, and charts can reappear as currently implemented.
- The new neutral embedded-comment color applies only when classification is disabled.

## Testing and Verification

Add source-level regression assertions before production changes to verify:

1. A neutral embedded-comment class is present only when classification is disabled.
2. The state-aware main-grid class is bound to sentence-detail visibility.
3. CSS contains the agreed neutral color and constrained slider dimensions.
4. CSS contains the reduced article, title, and side-comment font sizes.
5. Existing feature-flag regression checks continue to pass.

After implementation:

- Run the regression test and production build.
- Reload the running application at `http://localhost:8080/`.
- Measure computed dimensions at 1280 × 720.
- Visually verify Sentence-End, Between-Line, and Click-to-Show layouts.
- Confirm the article expands when the detail panel is closed and transitions to three columns when it opens.
- Confirm embedded comments have a single blue-gray color while semantic type colors remain inactive.

## Non-Goals

- Removing or rewriting the existing classification system.
- Adding a user-visible appearance or feature-flag switch.
- Changing comment filtering logic or API data.
- Redesigning the content, navigation, or article structure.
- Adding a screenshot-export feature.
