const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const read = rel => fs.readFileSync(path.join(root, rel), "utf8");

const app = read("src/App.vue");
const picker = read("src/components/experiment/ParticipantPicker.vue");
const question = read("src/components/experiment/QuestionStage.vue");
const interview = read("src/components/experiment/InterviewStage.vue");
const renderer = read("src/components/experiment/ArticleRenderer.vue");

assert.match(picker, /P01/);
assert.match(picker, /P24/);
assert.match(picker, /select/);
assert.match(picker, /listParticipants\(props\.clientInstanceId\)/);
assert.match(picker, /resumable/);
assert.match(app, /ParticipantPicker/);
assert.match(app, /ReadingStage/);
assert.match(app, /QuestionStage/);
assert.match(app, /WorkloadStage/);
assert.match(app, /PreferenceStage/);
assert.match(app, /InterviewStage/);
assert.match(question, /itemStartMs/);
assert.match(question, /submit/);
assert.match(question, /questions/);
assert.match(question, /ArticleRenderer/);
assert.match(question, /group !== ["\']cra["\']/);
assert.match(question, /["']A["'], ["']B["']/);
assert.doesNotMatch(question, /(?:>\s*(?:back|previous|返回|上一题)\s*<)|(?:aria-label=["'][^"']*(?:back|previous|返回|上一题))/i);
assert.match(interview, /required/);
assert.match(interview, /4/);
assert.match(renderer, /layout_a\s*:\s*["']baseline["']/);
assert.match(renderer, /layout_b\s*:\s*["']cs["']/);
assert.match(renderer, /layout_c\s*:\s*["']se["']/);
assert.match(renderer, /layout_d\s*:\s*["']be["']/);
assert.doesNotMatch(renderer, /layout_a\s*:\s*["']te["']/);
for (const className of [
  "article-container",
  "article-title",
  "article-meta",
  "article-content",
  "paragraph-block",
  "paragraph-text",
  "article-footer",
  "baseline-comments",
  "baseline-comment-item",
  "comment-item",
  "comment-user",
  "comment-text",
  "comment-stats"
]) {
  assert.match(renderer, new RegExp(className.replaceAll("-", "\\-")));
}
// The experiment renderer keeps the assigned embedding layout fixed and removes
// researcher-facing controls from the participant view.
for (const className of [
  "global-comments-panel",
  "main-content",
  "article-panel",
  "annotation-panel",
  "connection-container",
  "paragraph-comments-body",
  "paragraph-comment-item",
  "comment-item",
  "comment-user",
  "comment-text",
  "comment-stats",
  "avatar",
  "baseline-comments",
  "baseline-comment-item",
  "inline-comment",
  "absolute-comment"
]) {
  assert.match(renderer, new RegExp(className.replaceAll("-", "\\-")));
}
assert.match(renderer, /showInlineComments/);
for (const hiddenControl of [
  "control-panel",
  "control-panel-inner",
  "layout-switcher",
  "layout-btn",
  "filter-sliders-compact",
  "like-slider",
  "reply-slider",
  "setControl",
  "sliderStyle"
]) {
  assert.doesNotMatch(renderer, new RegExp(hiddenControl.replaceAll("-", "\\-")));
}
assert.doesNotMatch(renderer, /[◌☷♥↩]/);
assert.match(renderer, /d="M12 21\.35l-1\.45-1\.32C5\.4 15\.36 2 12\.28 2 8\.5/);
assert.match(renderer, /d="M12 3c5\.514 0 10 3\.592 10 8\.007/);
assert.match(renderer, /d="M12 3c5\.514 0 10 3\.592 10 8\.007[^"]*1\.326-\.558/);
assert.doesNotMatch(renderer, /1\.326-\.635 6\.086/);
assert.match(renderer, /import ParagraphCommentTrigger from ["']\.\/ParagraphCommentTrigger\.vue["'];/);
// The paragraph trigger is temporarily hidden from participants, while its
// component import and expand/collapse logic remain available for later use.
assert.doesNotMatch(renderer, /<ParagraphCommentTrigger[\s\S]*:comment-count=[\s\S]*:is-expanded=[\s\S]*@toggle="toggleParagraph\(paragraph\.index\)"/);
assert.match(renderer, /toggleParagraph\(index\)/);
assert.match(renderer, /class="paragraph-comments-body"/);
assert.doesNotMatch(renderer, /段落评论（|隐藏段落评论/);
assert.doesNotMatch(renderer, /<span[^>]*class="paragraph-comment-trigger"/);
assert.match(renderer, /data-layout|assignedLayout|mode/);
assert.match(renderer, /comment_close/);
assert.match(renderer, /comment_click/);
assert.match(renderer, /mode === ['"]se['"]/);
assert.match(renderer, /class="inline-comment(?:\s|")/);
assert.match(renderer, /mode === ['"]be['"]/);
assert.match(renderer, /class="absolute-comment(?:\s|")/);
// Between-Line comments use normal document flow. The sentence wrapper stays
// static, so no paragraph-relative coordinates can place a comment over text.
assert.match(renderer, /\.sentence-wrapper\s*\{[^}]*position:\s*static;/);
assert.match(renderer, /\.paragraph-text\s*\{[^}]*position:\s*relative;/);
// The original renderer preserves its six researcher-defined paragraph bands.
// Sentence/comment placement must consume the server's researcher-resolved anchor.
// It must never invent an anchor from comment order or position bands.
assert.match(renderer, /anchor_sentence_index/);
assert.doesNotMatch(renderer, /bands\s*=\s*\{\s*early/);
assert.doesNotMatch(renderer, /index\s*\+\s*1\)\s*\/\s*\(this\.normalizedComments\.length\s*\+\s*1\)/);
assert.match(renderer, /parsedSentence[\s\S]*\? parsedSentence[\s\S]*: null/);
assert.match(renderer, /DEFAULT_PARAGRAPH_RANGES/);
assert.match(renderer, /start:\s*0,\s*end:\s*3/);
assert.match(renderer, /start:\s*64,\s*end:\s*66/);
// Fixed legacy ranges must be extended so every source sentence (and its anchored
// comments) remains visible, including A02/A03/A04 tails beyond sentence 66.
assert.match(renderer, /paragraphRanges/);
assert.match(renderer, /lastRangeEnd[\s\S]*sentences\.length\s*-\s*1/);
assert.match(renderer, /rangeStart[\s\S]*lastRangeEnd\s*\+\s*1/);
assert.doesNotMatch(renderer, /if\s*\(paragraphs\.length\s*>\s*1\)/);
// Like/Reply indicators in comment cards use the original SVG icons, not replacement glyphs.
assert.match(renderer, /class=\"like-count\"[^>]*>[\\s\\S]*<svg class=\"icon\"/);
assert.match(renderer, /class=\"reply-count\"[^>]*>[\\s\\S]*<svg class=\"icon\"/);
assert.match(renderer, /mode === ['"]cs['"]/);
assert.match(renderer, /annotation-panel/);

// These features were disabled in the pre-experiment visible system and must be deleted,
// not merely hidden again.
for (const disabledFeature of [
  "commentClassification",
  "keywordHighlight",
  "ChartLegend",
  "HighFrequencyWords",
  "HighFrequencyLegend",
  "type-pie-chart",
  "Statement",
  "Question",
  "Exclamation",
  "Suggestion",
  "Sarcasm",
  "高频词",
  "researcher"
]) {
  assert.doesNotMatch(renderer, new RegExp(disabledFeature, "i"));
}

// Sentence-End and Between-Line must retain the pre-experiment system's
// lightweight text embedding. They are not comment cards, bubbles, or avatars.
assert.match(renderer, /class="inline-comment(?:\s|\")[\s\S]*?【\{\{\s*topComment\(sentence\.index\)\.text\s*\}\}】/);
assert.match(renderer, /class="absolute-comment(?:\s|\")[\s\S]*?\{\{\s*topComment\(sentence\.index\)\.text\s*\}\}/);
assert.match(renderer, /\.inline-comment\s*\{[^}]*display:\s*inline;/);
assert.match(renderer, /\.inline-comment\s*\{[^}]*font-size:\s*0?\.85em;/);
assert.match(renderer, /\.inline-comment\s*\{[^}]*margin-left:\s*0?\.5em;/);
assert.match(renderer, /\.absolute-comment\s*\{[^}]*background:\s*none;/);
assert.match(renderer, /\.absolute-comment\s*\{[^}]*padding:\s*0;/);
// Between-Line comments must participate in normal flow so they cannot cover
// the following article line; their compact line-height preserves the original text style.
assert.match(renderer, /\.absolute-comment\s*\{[^}]*position:\s*static;/);
assert.match(renderer, /\.absolute-comment\s*\{[^}]*display:\s*block;/);
assert.match(renderer, /\.absolute-comment\s*\{[^}]*line-height:\s*1\.5;/);
// The flow-based Between-Line implementation must not retain the old oversized
// paragraph line-height; that extra line box is what made comments sit too low.
assert.doesNotMatch(renderer, /paragraph-text\.high-line-height/);
assert.doesNotMatch(renderer, /high-line-height['"]\s*\}/);
assert.match(renderer, /\.absolute-comment\s*\{[^}]*margin:\s*0\.15em\s+0\s+0\.15em\s+2em;/);
assert.doesNotMatch(renderer, /element\.style\.top/);
assert.match(renderer, /\.absolute-comment\s*\{[^}]*white-space:\s*nowrap;/);
assert.match(renderer, /\.absolute-comment\s*\{[^}]*text-overflow:\s*ellipsis;/);
for (const removedCardSurface of [
  "embedded-comment-inline",
  "embedded-comment-icon",
  "embedded-comment-card",
  "embedded-comment-card-body",
  "embedded-comment-card-header",
  "embedded-comment-author",
  "inline-comment-label",
  "inline-comment-text"
]) {
  assert.doesNotMatch(renderer, new RegExp(removedCardSurface));
}

const readingStage = fs.readFileSync(path.join(root, "src/components/experiment/ReadingStage.vue"), "utf8");
assert.match(readingStage, /stage:\s*["']reading["']/);
assert.match(readingStage, /scrollEventCount/);
assert.match(readingStage, /total_scroll_distance_px/);
assert.match(readingStage, /max_scroll_y/);
assert.match(readingStage, /comment_click_count/);
assert.match(readingStage, /comment_open_count/);
assert.match(readingStage, /comment_close_count/);
assert.match(readingStage, /paragraph_toggle_count/);
assert.match(readingStage, /if\s*\(scrollTimer\)\s*await\s+flushScrollSample/);

const questionStage = fs.readFileSync(path.join(root, "src/components/experiment/QuestionStage.vue"), "utf8");
assert.match(questionStage, /question_option_change/);
assert.match(questionStage, /optionClickCount/);
assert.match(questionStage, /optionChangeCount/);
assert.doesNotMatch(questionStage, /v-model="selectedOption"/);
assert.match(questionStage, /:checked="selectedOption === option.key"/);
assert.match(questionStage, /option_click_count/);
assert.match(questionStage, /option_change_count/);
assert.match(questionStage, /scroll_event_count/);
assert.match(questionStage, /total_scroll_distance_px/);
assert.match(questionStage, /max_scroll_y/);

console.log("experiment flow contract checks passed");
