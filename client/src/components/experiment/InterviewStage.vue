<template>
  <main class="interview-page">
    <section class="interview-card">
      <h1>使用体验反馈</h1>
      <p>请填写以下 4 个问题。所有问题均为 required（必填），请尽量描述具体体验。</p>
      <form @submit.prevent="submit">
        <label v-for="(question, index) in questions" :key="index">
          <span>{{ index + 1 }}. {{ question }}</span>
          <textarea v-model.trim="answers[`q${index + 1}`]" rows="5" required></textarea>
        </label>
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" :disabled="!valid || submitting">{{ submitting ? "正在保存…" : "提交并完成实验" }}</button>
      </form>
    </section>
  </main>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { INTERVIEW_QUESTIONS } from "../../experiment/experimentConfig";
const props = defineProps({ api: { type: Object, required: true }, sessionId: { type: String, required: true } });
const emit = defineEmits(["completed"]);
const questions = INTERVIEW_QUESTIONS;
const answers = reactive({ q1: "", q2: "", q3: "", q4: "" });
const startedAt = Date.now();
const submitting = ref(false);
const error = ref("");
const valid = computed(() => Object.values(answers).length === 4 && Object.values(answers).every(value => value.trim().length > 0));
async function submit() {
  if (!valid.value || submitting.value) return;
  submitting.value = true; error.value = "";
  try { await props.api.submitInterview(props.sessionId, { ...answers }, startedAt); emit("completed"); }
  catch (requestError) { error.value = requestError.message; submitting.value = false; }
}
</script>

<style scoped>
.interview-page { min-height: calc(100vh - 62px); padding: 28px 18px; background: #f4f7f9; }
.interview-card { width: min(820px, 100%); margin: auto; padding: 36px; border: 1px solid #d9e4ea; border-radius: 16px; background: #fff; }
h1 { color: #17324d; }.interview-card > p { color: #607586; }
label { display: block; margin: 24px 0; color: #294257; font-weight: 700; line-height: 1.6; }
textarea { width: 100%; box-sizing: border-box; margin-top: 8px; padding: 12px; border: 1px solid #b8c8d2; border-radius: 8px; font: inherit; resize: vertical; }
button { display: block; margin-left: auto; padding: 13px 20px; border: 0; border-radius: 9px; color: #fff; background: #236b78; font-weight: 800; }
button:disabled { opacity: .5; }.error { color: #8b1e2d; }
</style>
