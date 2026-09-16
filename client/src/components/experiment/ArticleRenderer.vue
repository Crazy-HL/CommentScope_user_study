<template>
  <div class="article-container article-renderer">
    <div
      :class="[
        isBaselineLayout ? 'baseline-layout' : 'main-content',
        {
          'has-annotation-panel': hasAnnotationPanel,
          'has-global-comments': globalComments.length > 0,
          'is-baseline-layout': isBaselineLayout
        }
      ]">
      <aside v-if="globalComments.length" class="panel global-comments-panel">
        <div class="panel-header">
          <h4>Overall Article Comments ({{ globalComments.length }})</h4>
        </div>
        <div class="panel-content">
          <article
            v-for="item in visibleGlobalComments"
            :key="`global-${item.index}`"
            class="comment-item global-comment-item"
            @click="note('comment_click', item.index)">
            <div class="comment-user">
              <img
                :src="item.comment.user_avatar || defaultAvatar"
                class="avatar"
                alt=""
                @error="handleAvatarError" />
              <span class="username">{{ item.comment.user_nickname || "" }}</span>
            </div>
            <div class="comment-text">{{ item.comment.text }}</div>
            <div class="comment-stats">
              <span class="like-count" title="Likes"><svg class="icon" viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><path fill="currentColor" d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" /></svg> {{ formatNumber(item.comment.like_count) }}</span>
              <span class="reply-count" title="Replies"><svg class="icon" viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><path fill="currentColor" d="M12 3c5.514 0 10 3.592 10 8.007 0 4.917-5.144 7.961-9.91 7.961-1.937 0-3.384-.397-4.394-.644-1 .613-1.595 1.037-4.272 1.82.535-1.277.723-2.215.725-3.292C3.484 16.541 2 13.975 2 11.007 2 6.592 6.486 3 12 3zm0-2C5.373 1 0 5.373 0 11c0 2.042.808 3.945 2.278 5.391.239.276.283.673.117.988-.288.555-.555 1.064-.763 1.554.302-.11.744-.266 1.326-.558.379-.19.857-.207 1.24-.039.96.42 2.079.635 3.253.635 6.086 0 11-4.015 11-9 0-5.627-5.373-10-11-10z" /></svg> {{ formatNumber(item.comment.reply_count) }}</span>
            </div>
          </article>
        </div>
      </aside>

      <article
        class="panel article-panel"
        :class="{ 'baseline-article-panel': isBaselineLayout }"
        :data-layout="mode"
        ref="articleContainer">
        <h1 class="article-title">{{ article.title }}</h1>

        <div v-if="hasMeta" class="article-meta">
          <span v-if="article.user_nickname" class="author">By: {{ article.user_nickname }}</span>
          <span v-if="article.created_time" class="publish-time">Published: {{ formatTime(article.created_time) }}</span>
          <span v-if="article.updated_time" class="update-time">Updated: {{ formatTime(article.updated_time) }}</span>
        </div>

        <div class="article-content" :class="{ 'baseline-article-content': isBaselineLayout }">
          <template v-if="isBaselineLayout">
            <p
              v-for="paragraph in baselineParagraphs"
              :key="`baseline-paragraph-${paragraph.index}`"
              class="baseline-paragraph">
              {{ paragraph.text }}
            </p>
          </template>

          <template v-else>
            <div
              v-for="paragraph in articleStructure"
              :key="`paragraph-${paragraph.index}`"
              class="paragraph-block">
              <div class="paragraph-text">
                <template
                  v-for="sentence in paragraph.sentences"
                  :key="sentence.index">
                  <span class="sentence-wrapper">
                    <span
                      :id="`sentence-${sentence.index}`"
                      class="sentence"
                      :class="{ 'has-comment': hasSentenceComments(sentence.index), selected: activeSentence === sentence.index }"
                      :role="hasSentenceComments(sentence.index) ? 'button' : undefined"
                      :tabindex="hasSentenceComments(sentence.index) ? 0 : undefined"
                      @click="hasSentenceComments(sentence.index) ? toggleSentence(sentence.index) : undefined"
                      @keydown.enter.prevent="hasSentenceComments(sentence.index) ? toggleSentence(sentence.index) : undefined"
                      @keydown.space.prevent="hasSentenceComments(sentence.index) ? toggleSentence(sentence.index) : undefined">
                      {{ sentence.text }}<sup
                        v-if="mode === 'cs' && hasSentenceComments(sentence.index)"
                        class="annotation-marker">{{ commentsForSentence(sentence.index).length }}</sup>
                    </span>

                    <!-- The original system embeds comments as ordinary text, not cards. -->
                    <span
                      v-if="mode === 'se' && showInlineComments && topComment(sentence.index)"
                      class="inline-comment embedded-comment-neutral"
                      role="button"
                      tabindex="0"
                      :aria-label="`查看评论：${topComment(sentence.index).text}`"
                      @click.stop="toggleSentence(sentence.index)"
                      @keydown.enter.prevent="toggleSentence(sentence.index)"
                      @keydown.space.prevent="toggleSentence(sentence.index)">
                      【{{ topComment(sentence.index).text }}】
                    </span>
                  </span>

                  <!-- Between-Line comments stay in normal flow, so the following article text is pushed below them. -->
                  <div
                    v-if="mode === 'be' && showInlineComments && topComment(sentence.index)"
                    class="absolute-comment embedded-comment-neutral"
                    role="button"
                    tabindex="0"
                    :title="topComment(sentence.index).text"
                    :aria-label="`查看评论：${topComment(sentence.index).text}`"
                    @click.stop="toggleSentence(sentence.index)"
                    @keydown.enter.prevent="toggleSentence(sentence.index)"
                    @keydown.space.prevent="toggleSentence(sentence.index)">
                    {{ topComment(sentence.index).text }}
                  </div>
                </template>
              </div>

              <!-- 段落评论入口暂时对参与者隐藏；段落评论数据和展开逻辑保留，便于后续恢复。 -->
              <div
                v-if="showParagraphComments && expandedParagraphs[paragraph.index] && paragraphHasComments(paragraph.index)"
                class="paragraph-comments-body">
                <article
                  v-for="item in commentsForParagraph(paragraph.index)"
                  :key="`paragraph-comment-${item.index}`"
                  class="paragraph-comment-item"
                  @click="note('comment_click', item.index)">
                  <div class="comment-user">
                    <img
                      :src="item.comment.user_avatar || defaultAvatar"
                      class="avatar"
                      alt=""
                      @error="handleAvatarError" />
                    <span class="username">{{ item.comment.user_nickname || "" }}</span>
                  </div>
                  <div class="comment-text">{{ item.comment.text }}</div>
                  <div class="comment-stats">
                    <span class="like-count" title="Likes"><svg class="icon" viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><path fill="currentColor" d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" /></svg> {{ formatNumber(item.comment.like_count) }}</span>
                    <span class="reply-count" title="Replies"><svg class="icon" viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><path fill="currentColor" d="M12 3c5.514 0 10 3.592 10 8.007 0 4.917-5.144 7.961-9.91 7.961-1.937 0-3.384-.397-4.394-.644-1 .613-1.595 1.037-4.272 1.82.535-1.277.723-2.215.725-3.292C3.484 16.541 2 13.975 2 11.007 2 6.592 6.486 3 12 3zm0-2C5.373 1 0 5.373 0 11c0 2.042.808 3.945 2.278 5.391.239.276.283.673.117.988-.288.555-.555 1.064-.763 1.554.302-.11.744-.266 1.326-.558.379-.19.857-.207 1.24-.039.96.42 2.079.635 3.253.635 6.086 0 11-4.015 11-9 0-5.627-5.373-10-11-10z" /></svg> {{ formatNumber(item.comment.reply_count) }}</span>
                  </div>
                </article>
              </div>
            </div>
          </template>
        </div>

        <div class="article-footer">
          <div class="stats">
            <span v-if="article.voteup_count !== undefined" class="vote-count">Likes: {{ formatNumber(article.voteup_count) }}</span>
            <span v-if="article.comment_count !== undefined" class="comment-count">Comments: {{ formatNumber(article.comment_count) }}</span>
          </div>
          <a v-if="article.content_url" :href="article.content_url" target="_blank" rel="noopener" class="original-link">Read Original</a>
        </div>

        <section v-if="isBaselineLayout" class="baseline-comments">
          <h2 class="baseline-comments-title">Comments ({{ filteredComments.length }})</h2>
          <div v-if="filteredComments.length" class="baseline-comment-list">
            <article
              v-for="item in filteredComments"
              :key="`baseline-${item.index}`"
              class="baseline-comment-item comment-item"
              @click="note('comment_click', item.index)">
              <img
                :src="item.comment.user_avatar || defaultAvatar"
                class="avatar"
                alt=""
                @error="handleAvatarError" />
              <div class="baseline-comment-body">
                <div class="baseline-comment-user">{{ item.comment.user_nickname || "" }}</div>
                <div class="baseline-comment-text">{{ item.comment.text }}</div>
                <div class="baseline-comment-stats">
                  <span>Likes: {{ formatNumber(item.comment.like_count) }}</span>
                  <span>Replies: {{ formatNumber(item.comment.reply_count) }}</span>
                </div>
              </div>
            </article>
          </div>
          <div v-else class="baseline-empty-comments">No comments</div>
        </section>
      </article>

      <aside
        v-if="hasAnnotationPanel"
        class="panel annotation-panel"
        ref="annotationPanel">
        <div class="panel-header">
          <h4>Sentence-related Comments ({{ commentsForSentence(activeSentence).length }})</h4>
          <button type="button" class="close-btn" aria-label="Close comments" @click="closeAnnotation">×</button>
        </div>
        <div class="panel-content">
          <article
            v-for="item in commentsForSentence(activeSentence)"
            :key="`annotation-${item.index}`"
            class="annotation-item"
            @click="note('comment_click', item.index)">
            <div class="annotation-user">
              <img
                :src="item.comment.user_avatar || defaultAvatar"
                class="avatar"
                alt=""
                @error="handleAvatarError" />
              <span class="username">{{ item.comment.user_nickname || "" }}</span>
            </div>
            <div class="annotation-text">{{ item.comment.text }}</div>
            <div class="annotation-stats">
              <span class="like-count" title="Likes"><svg class="icon" viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><path fill="currentColor" d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" /></svg> {{ formatNumber(item.comment.like_count) }}</span>
              <span class="reply-count" title="Replies"><svg class="icon" viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><path fill="currentColor" d="M12 3c5.514 0 10 3.592 10 8.007 0 4.917-5.144 7.961-9.91 7.961-1.937 0-3.384-.397-4.394-.644-1 .613-1.595 1.037-4.272 1.82.535-1.277.723-2.215.725-3.292C3.484 16.541 2 13.975 2 11.007 2 6.592 6.486 3 12 3zm0-2C5.373 1 0 5.373 0 11c0 2.042.808 3.945 2.278 5.391.239.276.283.673.117.988-.288.555-.555 1.064-.763 1.554.302-.11.744-.266 1.326-.558.379-.19.857-.207 1.24-.039.96.42 2.079.635 3.253.635 6.086 0 11-4.015 11-9 0-5.627-5.373-10-11-10z" /></svg> {{ formatNumber(item.comment.reply_count) }}</span>
            </div>
          </article>
        </div>
      </aside>
    </div>

    <div
      v-if="!isBaselineLayout"
      class="connection-container"
      ref="connectionContainer"
      aria-hidden="true">
      <svg v-if="hasAnnotationPanel" class="connection-line" :style="connectionStyle">
        <line x1="0" y1="0" x2="100%" y2="0" stroke="#FF5722" stroke-width="2" stroke-dasharray="4,2" />
      </svg>
    </div>
  </div>
</template>

<script>
import { defineComponent } from "vue";
import ParagraphCommentTrigger from "./ParagraphCommentTrigger.vue";

const LAYOUTS = Object.freeze({
  layout_a: "baseline",
  layout_b: "cs",
  layout_c: "se",
  layout_d: "be"
});

const SENTENCE_BOUNDARY = /[^。！？；.!?\n]+[。！？；.!?]?/g;
const DECIMAL_DOT = "\uE000";
const DEFAULT_PARAGRAPH_RANGES = Object.freeze([
  { start: 0, end: 3 },
  { start: 4, end: 21 },
  { start: 22, end: 33 },
  { start: 34, end: 52 },
  { start: 53, end: 63 },
  { start: 64, end: 66 }
]);

export default defineComponent({
  name: "ArticleRenderer",
  components: { ParagraphCommentTrigger },
  props: {
    article: { type: Object, required: true }
  },
  emits: ["interaction"],
  data() {
    return {
      activeSentence: null,
      showInlineComments: true,
      showParagraphComments: true,
      likeThreshold: 0,
      replyThreshold: 0,
      expandedParagraphs: {},
      connectionStyle: { left: "0px", top: "0px", width: "0px", transform: "rotate(0deg)", transformOrigin: "0 0" },
      defaultAvatar: "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0iI2NjYyIgZD0iTTEyLDJBMTAsMTAgMCAwLDAgMiwxMkExMCwxMCAwIDAsMCAxMiwyMkExMCwxMCAwIDAsMCAyMiwxMkExMCwxMCAwIDAsMCAxMiwyTTEyLDRBNyA3IDAgMCwxIDE5LDExQTcgNyAwIDAsMSAxMiwxOEE3LDcgMCAwLDEgNSwxMUE3LDcgMCAwLDEgMTIsNE0xMiw2QTUsNSAwIDAsMCA3LDExQTUsNSAwIDAsMCAxMiwxNkE1LDUgMCAwLDAgMTcsMTFBNSw1IDAgMCwwIDEyLDZNMTIsOEEzLDMgMCAwLDEgMTUsMTFBNCw4IDAgMCwxIDEyLDE1QTQsNCAwIDAsMSA5LDExQTMsMyAwIDAsMSAxMiw4WiIvPjwvc3ZnPg=="
    };
  },
  computed: {
    mode() {
      return LAYOUTS[this.article.render_mode] || "baseline";
    },
    isBaselineLayout() {
      return this.mode === "baseline";
    },
    hasAnnotationPanel() {
      return !this.isBaselineLayout && this.activeSentence !== null && this.commentsForSentence(this.activeSentence).length > 0;
    },
    hasMeta() {
      return Boolean(this.article.user_nickname || this.article.created_time || this.article.updated_time);
    },
    normalizedComments() {
      return (this.article.comments || []).map((comment, index) => ({
        index,
        comment: {
          ...comment,
          text: String(comment.text ?? comment.content ?? ""),
          like_count: Number(comment.like_count ?? comment.voteup_count ?? 0),
          reply_count: Number(comment.reply_count ?? comment.sub_comment_count ?? 0)
        }
      }));
    },
    sentences() {
      const text = String(this.article.body ?? this.article.content_text ?? "").trim();
      // Keep decimal values such as 0.67% inside one sentence, matching the
      // server-side splitter used to resolve preconfigured anchors.
      const protectedText = text.replace(/(\d)\.(?=\d)/g, `$1${DECIMAL_DOT}`);
      const matches = protectedText.match(SENTENCE_BOUNDARY) || [];
      return (matches.length ? matches : [protectedText])
        .map((value, index) => ({ text: value.replaceAll(DECIMAL_DOT, ".").trim(), index }))
        .filter(item => item.text);
    },
    paragraphRanges() {
      const ranges = DEFAULT_PARAGRAPH_RANGES.map(range => ({ ...range }));
      const lastRangeEnd = ranges.reduce((max, range) => Math.max(max, range.end), -1);
      if (lastRangeEnd < this.sentences.length - 1) {
        const rangeStart = lastRangeEnd + 1;
        ranges.push({ start: rangeStart, end: this.sentences.length - 1 });
      }
      return ranges;
    },
    articleStructure() {
      return this.paragraphRanges.map((range, index) => ({
        index,
        sentences: this.sentences.slice(range.start, Math.min(range.end + 1, this.sentences.length))
      })).filter(item => item.sentences.length);
    },
    baselineParagraphs() {
      return this.articleStructure.map(paragraph => ({
        index: paragraph.index,
        text: paragraph.sentences.map(sentence => sentence.text).join(" ")
      }));
    },
    anchoredComments() {
      const lastSentence = this.sentences.length - 1;
      return this.normalizedComments.map(item => {
        // The server resolves each preconfigured anchor against the exact
        // sentence list sent to this component. Never infer an anchor from the
        // comment order or from an early/middle/late position band: that makes a
        // semantically unrelated comment appear attached to a sentence.
        const linkedSentence = Array.isArray(item.comment.link)
          ? item.comment.link.find(value => Number.isInteger(Number(value)) && Number(value) >= 0 && Number(value) <= lastSentence)
          : undefined;
        const rawSentence = item.comment.anchor_sentence_index
          ?? item.comment.sentence_index
          ?? item.comment.sentenceIndex
          ?? (linkedSentence !== undefined ? linkedSentence : null);
        const parsedSentence = Number(rawSentence);
        const sentenceIndex = Number.isInteger(parsedSentence) && parsedSentence >= 0 && parsedSentence <= lastSentence
          ? parsedSentence
          : null;
        const paragraphIndex = this.articleStructure.findIndex(paragraph =>
          sentenceIndex !== null && paragraph.sentences.some(sentence => sentence.index === sentenceIndex));
        const explicitParagraph = Number(item.comment.paragraph_index ?? item.comment.paragraphIndex);
        return {
          ...item,
          sentenceIndex,
          paragraphIndex: Number.isInteger(explicitParagraph) && explicitParagraph >= 0
            ? explicitParagraph
            : paragraphIndex >= 0 ? paragraphIndex : null
        };
      });
    },
    globalComments() {
      return this.anchoredComments.filter(item => item.comment.global === true || item.comment.scope === "global" || (Array.isArray(item.comment.link) && (item.comment.link.length === 0 || item.comment.link[0] === -1)));
    },
    visibleGlobalComments() {
      return this.globalComments.filter(item => this.isAboveThreshold(item));
    },
    filteredComments() {
      return this.anchoredComments.filter(item => !this.isGlobal(item) && this.isAboveThreshold(item));
    },
    maxLikeCount() {
      return Math.max(0, ...this.anchoredComments.map(item => item.comment.like_count));
    },
    maxReplyCount() {
      return Math.max(0, ...this.anchoredComments.map(item => item.comment.reply_count));
    }
  },
  watch: {
    activeSentence() {
      this.$nextTick(this.updateConnectionLine);
    },
    likeThreshold() {
      this.activeSentence = null;
    },
    replyThreshold() {
      this.activeSentence = null;
    }
  },
  mounted() {
    window.addEventListener("resize", this.updateConnectionLine);
    window.addEventListener("scroll", this.updateConnectionLine, true);
  },
  beforeUnmount() {
    window.removeEventListener("resize", this.updateConnectionLine);
    window.removeEventListener("scroll", this.updateConnectionLine, true);
  },
  methods: {
    isGlobal(item) {
      return item.comment.global === true || item.comment.scope === "global" || (Array.isArray(item.comment.link) && (item.comment.link.length === 0 || item.comment.link[0] === -1));
    },
    isAboveThreshold(item) {
      return item.comment.like_count >= this.likeThreshold && item.comment.reply_count >= this.replyThreshold;
    },
    commentsForSentence(index) {
      return this.anchoredComments.filter(item => item.sentenceIndex === index && !this.isGlobal(item) && this.isAboveThreshold(item));
    },
    commentsForParagraph(index) {
      return this.anchoredComments.filter(item => item.paragraphIndex === index && !this.isGlobal(item) && this.isAboveThreshold(item));
    },
    paragraphHasComments(index) {
      return this.commentsForParagraph(index).length > 0;
    },
    hasSentenceComments(index) {
      return this.commentsForSentence(index).length > 0;
    },
    topComment(index) {
      return this.commentsForSentence(index)[0]?.comment || null;
    },
    toggleSentence(index) {
      if (!this.hasSentenceComments(index)) return;
      this.activeSentence = this.activeSentence === index ? null : index;
      this.note(this.activeSentence === index ? "comment_open" : "comment_close", index);
    },
    closeAnnotation() {
      this.activeSentence = null;
      this.note("comment_close", null);
    },
    toggleParagraph(index) {
      this.$set ? this.$set(this.expandedParagraphs, index, !this.expandedParagraphs[index]) : (this.expandedParagraphs[index] = !this.expandedParagraphs[index]);
      this.note("paragraph_toggle", { paragraph_index: index, expanded: Boolean(this.expandedParagraphs[index]) });
    },
    note(type, payload = {}) {
      this.$emit("interaction", { type, payload: typeof payload === "number" ? { comment_index: payload } : payload });
    },
    updateConnectionLine() {
      if (!this.hasAnnotationPanel || !this.$refs.annotationPanel || !this.$refs.connectionContainer) return;
      this.$nextTick(() => {
        const sentence = document.getElementById(`sentence-${this.activeSentence}`);
        if (!sentence) return;
        const sentenceRect = sentence.getBoundingClientRect();
        const panelRect = this.$refs.annotationPanel.getBoundingClientRect();
        const containerRect = this.$refs.connectionContainer.getBoundingClientRect();
        const endX = panelRect.left;
        const endY = panelRect.top + panelRect.height / 2;
        const startX = sentenceRect.right;
        const startY = sentenceRect.top + sentenceRect.height / 2;
        const length = Math.sqrt((endX - startX) ** 2 + (endY - startY) ** 2);
        const angle = Math.atan2(endY - startY, endX - startX) * 180 / Math.PI;
        const nextStyle = {
          left: `${startX - containerRect.left}px`,
          top: `${startY - containerRect.top}px`,
          width: `${length}px`,
          transform: `rotate(${angle}deg)`,
          transformOrigin: "0 0"
        };
        if (Object.keys(nextStyle).some(key => nextStyle[key] !== this.connectionStyle[key])) this.connectionStyle = nextStyle;
      });
    },
    handleAvatarError(event) {
      if (event?.target && event.target.src !== this.defaultAvatar) event.target.src = this.defaultAvatar;
    },
    formatNumber(value) {
      const number = Number(value);
      return Number.isFinite(number) ? number.toLocaleString("en-US") : "0";
    },
    formatTime(value) {
      if (!value) return "";
      const date = new Date(value);
      return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString();
    }
  }
});
</script>

<style scoped>
.article-container { position: relative; width: 100%; max-width: 2500px; margin: 0 auto; padding: 16px; box-sizing: border-box; }
.baseline-layout { width: 100%; }
.main-content { display: grid; grid-template-columns: minmax(0, 1fr); grid-template-areas: "article"; gap: 12px; width: 100%; }
.main-content.has-global-comments { grid-template-columns: 220px minmax(0, 1fr); grid-template-areas: "global article"; }
/* 侧边栏浮动定位，不挤占文章宽度 */
.main-content.has-annotation-panel { grid-template-columns: minmax(0, 1fr); grid-template-areas: "article"; }
.main-content.has-global-comments.has-annotation-panel { grid-template-columns: 220px minmax(0, 1fr); grid-template-areas: "global article"; }
.panel { box-sizing: border-box; padding: 14px; height: fit-content; border-radius: 8px; background: #fff; box-shadow: 0 2px 10px rgba(0,0,0,.1); }
.global-comments-panel { grid-area: global; position: sticky; top: 120px; max-height: calc(100vh - 140px); overflow-y: auto; }
.article-panel { grid-area: article; position: sticky; top: 120px; max-height: calc(100vh - 140px); overflow-y: auto; }
.baseline-article-panel { position: static; max-height: none; overflow: visible; }
/* 侧边栏固定定位，浮动在视口右侧空白区域，不影响文章宽度 */
.annotation-panel {
  position: fixed;
  right: 20px;
  top: 120px;
  width: 300px;
  max-height: calc(100vh - 180px);
  overflow-y: auto;
  z-index: 20;
  box-shadow: 0 4px 20px rgba(0,0,0,.15);
}
.article-title { margin: 0 0 10px; color: #222; font-size: 24px; line-height: 1.3; }
.article-meta { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 16px; color: #6b7280; font-size: 13px; }
.article-content { color: #333; font-size: 16px; line-height: 1.7; }
.baseline-paragraph { margin: 0 0 1em; text-indent: 2em; line-height: 1.7; white-space: pre-wrap; }
.paragraph-block { margin-bottom: .2em; }
.paragraph-text { position: relative; margin: 0 0 1em; text-indent: 2em; line-height: 1.7; }
.sentence-wrapper { position: static; }
.sentence { display: inline; padding: 0 1px 2px; border-radius: 3px; white-space: pre-wrap; transition: background .2s, border .2s; }
.sentence.has-comment { border-bottom: 1.5px dotted rgba(0,123,255,.7); cursor: pointer; }
.sentence.has-comment:hover, .sentence.selected { border-bottom-style: solid; border-bottom-color: rgba(0,86,179,.8); background: rgba(255,236,179,.6); }
.annotation-marker { margin-left: 2px; color: #007bff; font-size: .7em; font-weight: 700; }
.inline-comment {
  display: inline;
  font-size: 0.85em;
  margin-left: 0.5em;
  cursor: pointer;
}
.inline-comment.embedded-comment-neutral {
  color: #4f6f82;
}
.absolute-comment {
  display: block;
  position: static;
  margin: 0.15em 0 0.15em 2em;
  max-width: calc(100% - 2em);
  font-size: 0.78em;
  color: #555;
  background: none;
  padding: 0;
  pointer-events: all;
  cursor: pointer;
  line-height: 1.5;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  z-index: 5;
}
.embedded-comment-neutral {
  color: #4f6f82;
}
.paragraph-comments-body { margin: .5em 0 1em 2em; padding: 12px; border-left: 3px solid #b9d8e4; background: #f8fafb; }
.panel-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #eee; }
.panel-header h4 { margin: 0; color: #333; font-size: 15px; }
.panel-content { display: flex; flex-direction: column; gap: 12px; }
.comment-item, .annotation-item, .paragraph-comment-item { position: relative; margin-bottom: 12px; padding: 11px; border-top: 1px solid #eee; border-bottom: 1px solid #eee; border-radius: 6px; background: #f9f9f9; transition: box-shadow .2s, transform .2s; cursor: pointer; }
.comment-item:hover, .annotation-item:hover, .paragraph-comment-item:hover { box-shadow: 0 2px 8px rgba(0,0,0,.1); transform: translateY(-1px); }
.comment-user, .annotation-user { display: flex; align-items: center; margin-bottom: 7px; }
.avatar { width: 24px; height: 24px; margin-right: 8px; border-radius: 50%; object-fit: cover; background: #f0f0f0; }
.username { color: #333; font-size: 13px; font-weight: 700; }
.comment-text, .annotation-text { color: #333; font-size: 13px; line-height: 1.55; overflow-wrap: anywhere; white-space: pre-wrap; }
.comment-stats, .annotation-stats { display: flex; align-items: center; gap: 12px; margin-top: 8px; color: #999; font-size: 11px; }
.like-count, .reply-count { display: inline-flex; align-items: center; gap: 4px; }
.like-count { color: #ff4757; }
.reply-count { color: #57606f; }
.close-btn { border: 0; color: #999; background: none; cursor: pointer; font-size: 20px; }
.close-btn:hover { color: #333; }
.article-footer { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding-top: 15px; border-top: 1px solid #eee; color: #666; font-size: 13px; }
.stats span { margin-right: 15px; }
.original-link { color: #0084ff; text-decoration: none; }
.baseline-comments { margin-top: 20px; padding-top: 20px; border-top: 1px solid #e5e7eb; }
.baseline-comments-title { margin: 0 0 4px; color: #333; font-size: 18px; }
.baseline-comment-list { display: flex; flex-direction: column; }
.baseline-comment-item { display: flex; gap: 12px; width: 100%; margin: 0; padding: 16px 0; border: 0; border-bottom: 1px solid #e5e7eb; border-radius: 0; background: transparent; text-align: left; cursor: pointer; }
.baseline-comment-item:hover { box-shadow: none; transform: none; background: #fafafa; }
.baseline-comment-body { min-width: 0; flex: 1; }
.baseline-comment-user { margin-bottom: 6px; color: #333; font-size: 14px; font-weight: 600; }
.baseline-comment-text { color: #333; font-size: 14px; line-height: 1.55; white-space: pre-wrap; overflow-wrap: anywhere; }
.baseline-comment-stats { display: flex; gap: 16px; margin-top: 8px; color: #8a8f98; font-size: 13px; }
.baseline-empty-comments { padding: 24px 0 8px; color: #8a8f98; text-align: center; }
.connection-container { position: absolute; top: 0; left: 0; z-index: 10; width: 100%; height: 100%; pointer-events: none; overflow: visible; }
.connection-line { position: absolute; height: 2px; background: transparent; filter: drop-shadow(0 0 2px rgba(255,87,34,.5)); }
@media (max-width: 1400px) {
  /* 中等屏幕：侧边栏宽度略减，仍浮动在右侧 */
  .annotation-panel { width: 260px; right: 12px; }
}
@media (max-width: 1180px) {
  .main-content.has-global-comments { grid-template-columns: 200px minmax(0, 1fr); }
  .global-comments-panel { display: none; }
  .annotation-panel { width: 240px; right: 8px; }
}
@media (max-width: 900px) {
  /* 小屏幕：侧边栏回退到正常流，堆叠在文章下方，避免覆盖 */
  .main-content, .main-content.has-global-comments, .main-content.has-annotation-panel, .main-content.has-global-comments.has-annotation-panel {
    grid-template-columns: minmax(0, 1fr);
    grid-template-areas: "article" "global" "annotation";
  }
  .global-comments-panel, .article-panel { position: static; max-height: none; }
  .global-comments-panel { display: block; }
  .annotation-panel {
    position: static !important;
    width: 100%;
    max-height: none;
    margin-top: 12px;
    box-shadow: 0 2px 10px rgba(0,0,0,.1);
  }
}
@media (max-width: 640px) {
  .article-container { padding: 8px 0; }
  .article-title { font-size: 22px; }
  .article-content { font-size: 16px; }
  .article-footer { align-items: flex-start; flex-direction: column; }
}
</style>
