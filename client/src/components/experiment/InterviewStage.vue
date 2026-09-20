<template>
  <main class="interview-page">
    <section class="interview-card">
      <h1>使用体验反馈</h1>
      <p>请填写以下 4 个问题。所有问题均为必填，请尽量描述具体体验。</p>
      <form @submit.prevent="submit">
        <!-- 第一题：带示意图的选择题 -->
        <div class="question-block">
          <span class="question-title">1. 在四种评论展示界面中，你最喜欢哪一种？</span>
          <div class="choice-grid">
            <div
              v-for="option in conditionOptions"
              :key="option.code"
              class="choice-card"
              :class="{ selected: selectedCondition === option.code }"
              @click="selectCondition(option.code)">
              <img :src="option.image" :alt="option.name" class="choice-image" />
              <div class="choice-name">{{ option.name }}</div>
              <div v-if="selectedCondition === option.code" class="check-mark">✓</div>
            </div>
          </div>
          <textarea
            v-model.trim="answers.q1"
            rows="3"
            placeholder="为什么喜欢这种？请简单描述原因。"
            required
            class="reason-textarea"></textarea>
        </div>

        <!-- 第2-4题：普通问答题 -->
        <label v-for="(question, index) in questions.slice(1)" :key="index + 2">
          <span>{{ index + 2 }}. {{ question }}</span>
          <textarea v-model.trim="answers[`q${index + 2}`]" rows="5" required></textarea>
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

// 四种界面选项
const conditionOptions = [
  { code: "TE", name: "文末嵌入（TE）", image: "/images/te-schematic.png" },
  { code: "CS", name: "点击查看（CS）", image: "/images/cs-schematic.png" },
  { code: "SE", name: "句末跟随（SE）", image: "/images/se-schematic.png" },
  { code: "BL", name: "行间穿插（BL）", image: "/images/bl-schematic.png" }
];

const selectedCondition = ref("");
const answers = reactive({ q1: "", q2: "", q3: "", q4: "" });
const startedAt = Date.now();
const submitting = ref(false);
const error = ref("");

function selectCondition(code) {
  selectedCondition.value = code;
}

const valid = computed(() => {
  return selectedCondition.value !== "" &&
    answers.q1.trim().length > 0 &&
    answers.q2.trim().length > 0 &&
    answers.q3.trim().length > 0 &&
    answers.q4.trim().length > 0;
});

async function submit() {
  if (!valid.value || submitting.value) return;
  submitting.value = true;
  error.value = "";
  try {
    // 把选择的界面编码也存到 q1 答案里，方便分析
    const finalAnswers = {
      ...answers,
      q1: `[选择: ${selectedCondition.value}] ${answers.q1}`
    };
    await props.api.submitInterview(props.sessionId, finalAnswers, startedAt);
    emit("completed");
  } catch (requestError) {
    error.value = requestError.message;
    submitting.value = false;
  }
}
</script>

<style scoped>
.interview-page { min-height: calc(100vh - 62px); padding: 28px 18px; background: #f4f7f9; }
.interview-card { width: min(820px, 100%); margin: auto; padding: 36px; border: 1px solid #d9e4ea; border-radius: 16px; background: #fff; }
h1 { color: #17324d; }
.interview-card > p { color: #607586; }

.question-block { margin: 24px 0; }
.question-title { display: block; margin-bottom: 16px; color: #294257; font-weight: 700; line-height: 1.6; }

.choice-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.choice-card {
  position: relative;
  border: 2px solid #d9e4ea;
  border-radius: 10px;
  padding: 12px 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  background: #fff;
}
.choice-card:hover { border-color: #8bb8d8; box-shadow: 0 2px 8px rgba(0,0,0,.08); }
.choice-card.selected { border-color: #236b78; background: #f0f7f8; }
.choice-image { width: 100%; height: auto; border-radius: 6px; margin-bottom: 8px; }
.choice-name { font-size: 13px; font-weight: 600; color: #294257; }
.check-mark {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #236b78;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
}

.reason-textarea {
  width: 100%;
  box-sizing: border-box;
  margin-top: 8px;
  padding: 12px;
  border: 1px solid #b8c8d2;
  border-radius: 8px;
  font: inherit;
  resize: vertical;
}

label { display: block; margin: 24px 0; color: #294257; font-weight: 700; line-height: 1.6; }
label span { display: block; margin-bottom: 8px; }
textarea { width: 100%; box-sizing: border-box; margin-top: 8px; padding: 12px; border: 1px solid #b8c8d2; border-radius: 8px; font: inherit; resize: vertical; }

button { display: block; margin-left: auto; padding: 13px 20px; border: 0; border-radius: 9px; color: #fff; background: #236b78; font-weight: 800; cursor: pointer; }
button:disabled { opacity: .5; cursor: not-allowed; }
.error { color: #8b1e2d; }

@media (max-width: 600px) {
  .choice-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
