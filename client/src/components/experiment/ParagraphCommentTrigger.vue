<!-- ParagraphCommentTrigger.vue -->
<template>
	<span
		class="paragraph-comment-trigger"
		:title="isExpanded ? '折叠段落评论' : '展开段落评论'"
		@click.stop="$emit('toggle')">
		<svg class="trigger-icon" viewBox="0 0 24 24" width="24" height="24">
			<path
				fill="currentColor"
				d="M17,11H7V9H17V11M21,6V8H3V6H21M17,15H7V13H17V15Z" />
		</svg>
		<sup class="comment-count-badge">{{ commentCount }}</sup>
	</span>
</template>

<script setup>
	defineProps({
		commentCount: {
			type: Number,
			required: true
		},
		isExpanded: {
			type: Boolean,
			default: false
		}
	});

	defineEmits(["toggle"]);
</script>

<style scoped>
	.paragraph-comment-trigger {
		display: inline-block;
		margin-left: 0.5em;
		padding: 2px 4px;
		border-radius: 4px;
		cursor: pointer;
		transition: all 0.2s ease;
		vertical-align: middle; /* 调整垂直对齐 */
		line-height: 1;
		color: #495057; /* 默认字体颜色更柔和 */
	}

	.paragraph-comment-trigger:hover {
		background-color: #f8f9fa; /* 更轻的 hover 背景 */
	}

	.trigger-icon {
		color: #0d6efd; /* 改成蓝色 */
		vertical-align: middle;
	}

	.comment-count-badge {
		font-size: 0.75em;
		color: #e03131; /* 改成醒目的红色 */
		font-weight: bold;
		vertical-align: super;
		margin-left: 2px;
	}
</style>
