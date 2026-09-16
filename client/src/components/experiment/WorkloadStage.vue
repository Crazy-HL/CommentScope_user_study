<template>
  <main class="survey-page">
    <section class="survey-card">
      <p class="eyebrow">文章 {{ articleOrder }} / 4</p>
      <h1>阅读体验评价</h1>
      <p class="intro">请根据刚才的实际体验作答。所有项目均为必填。</p>
      <form @submit.prevent="submit">
        <div v-for="item in nasaItems" :key="item.key" class="scale-item">
          <label :for="item.key">{{ item.label }} <strong>{{ values[item.key] }}</strong></label>
          <input :id="item.key" v-model.number="values[item.key]" type="range" min="1" max="7" step="1" required />
          <div class="ends"><span>1 = 很低</span><span>7 = 很高</span></div>
        </div>
        <div v-for="item in ratingItems" :key="item.key" class="rating-item">
          <label :for="item.key">{{ item.label }}</label>
          <select :id="item.key" v-model.number="values[item.key]" required>
            <option value="" disabled>请选择 1–7</option>
            <option v-for="score in 7" :key="score" :value="score">{{ score }}</option>
          </select>
          <small>1 = 非常不同意，7 = 非常同意</small>
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" :disabled="!valid || submitting">{{ submitting ? "正在保存…" : "提交评价" }}</button>
      </form>
    </section>
  </main>
</template>

<script setup>
import { computed, reactive, ref } from "vue";

const props = defineProps({ api: { type: Object, required: true }, sessionId: { type: String, required: true }, articleOrder: { type: Number, required: true } });
const emit = defineEmits(["completed"]);
const nasaItems = [
  { key: "mental_demand", label: "脑力需求：完成任务需要多少思考和注意？" },
  { key: "physical_demand", label: "操作需求：完成任务需要多少点击、滚动等操作？" },
  { key: "temporal_demand", label: "时间压力：完成任务时感到多大的时间压力？" },
  { key: "performance", label: "自我表现困难程度：完成任务时，你觉得自己的表现有多困难？" },
  { key: "effort", label: "努力程度：为了完成任务，你付出了多少努力？" },
  { key: "frustration", label: "挫败程度：过程中感到多大程度的烦躁、紧张或不安？" }
];
const ratingItems = [
  { key: "reading_continuity", label: "这种界面能保持连续阅读。" },
  { key: "comment_accessibility", label: "这种界面便于找到和阅读相关评论。" }
];
const values = reactive({ mental_demand: 4, physical_demand: 4, temporal_demand: 4, performance: 4, effort: 4, frustration: 4, reading_continuity: "", comment_accessibility: "" });
const submitting = ref(false);
const error = ref("");
const valid = computed(() => ratingItems.every(item => Number(values[item.key]) >= 1 && Number(values[item.key]) <= 7));

async function submit() {
  if (!valid.value || submitting.value) return;
  submitting.value = true;
  error.value = "";
  try {
    await props.api.submitWorkload(props.sessionId, props.articleOrder, { ...values });
    emit("completed");
  } catch (requestError) {
    error.value = requestError.message;
    submitting.value = false;
  }
}
</script>

<style scoped>
.survey-page { min-height: calc(100vh - 62px); padding: 28px 18px; background: #f4f7f9; }
.survey-card { width: min(780px, 100%); margin: auto; padding: 34px; border: 1px solid #d9e4ea; border-radius: 16px; background: #fff; }
.eyebrow { color: #2b7a78; font-weight: 800; }
h1 { color: #17324d; }.intro, small { color: #607586; }
.scale-item, .rating-item { margin: 24px 0; padding-bottom: 20px; border-bottom: 1px solid #edf1f4; }
label { display: block; margin-bottom: 10px; color: #294257; font-weight: 700; line-height: 1.5; }
input[type="range"] { width: 100%; accent-color: #277587; }
.ends { display: flex; justify-content: space-between; color: #718391; font-size: 12px; }
select { min-width: 150px; padding: 9px; border: 1px solid #b8c8d2; border-radius: 8px; }
small { margin-left: 10px; }
button { display: block; margin-left: auto; padding: 13px 20px; border: 0; border-radius: 9px; color: #fff; background: #236b78; font-weight: 800; }
button:disabled { opacity: .5; }.error { color: #8b1e2d; }
</style>
