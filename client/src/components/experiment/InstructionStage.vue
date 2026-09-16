<template>
  <main class="stage-shell">
    <section class="stage-card">
      <p class="step">第 {{ articleOrder }} 篇，共 4 篇</p>
      <h1>阅读说明</h1>
      <p>接下来请像平时一样自然阅读文章及相关评论。阅读完成后，你将依次回答：</p>
      <ol>
        <li>阅读判断 4 题</li>
        <li>文章理解 2 题</li>
        <li>评论理解 2 题</li>
        <li>信息定位 2 题</li>
        <li>阅读体验评价</li>
      </ol>
      <p class="hint">题目提交后不能修改，也不能回到已提交题目。请在准备好后开始。</p>
      <button type="button" :disabled="loading" @click="$emit('continue')">{{ loading ? "正在加载…" : "开始阅读" }}</button>
    </section>
  </main>
</template>

<script setup>
defineProps({ articleOrder: { type: Number, required: true }, loading: { type: Boolean, default: false } });
defineEmits(["continue"]);
</script>

<style scoped>
.stage-shell { min-height: calc(100vh - 62px); display: grid; place-items: center; padding: 30px 18px; background: #f5f8fa; }
.stage-card { width: min(680px, 100%); padding: 34px; border: 1px solid #dbe5ec; border-radius: 16px; background: #fff; box-shadow: 0 12px 36px rgba(37,64,88,.08); color: #263f56; }
.step { color: #2b7a78; font-weight: 800; }
h1 { margin-top: 6px; color: #17324d; }
p, li { line-height: 1.8; }
.hint { padding: 13px 15px; border-left: 4px solid #d6a84b; background: #fff9ea; }
button { float: right; min-width: 140px; padding: 13px 20px; border: 0; border-radius: 9px; color: #fff; background: #236b78; font-weight: 800; cursor: pointer; }
button:disabled { opacity: .55; }
</style>
