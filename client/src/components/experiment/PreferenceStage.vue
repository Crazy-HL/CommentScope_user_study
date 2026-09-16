<template>
  <main class="survey-page">
    <section class="survey-card">
      <h1>四种界面偏好排序</h1>
      <p>请分别选择第 1 至第 4 名。每一种界面只能出现一次。</p>
      <form @submit.prevent="submit">
        <label v-for="rank in 4" :key="rank" class="rank-row">
          <span>第 {{ rank }} 名</span>
          <select v-model="ranking[rank - 1]" required>
            <option value="" disabled>请选择界面</option>
            <option v-for="option in options" :key="option.value" :value="option.value" :disabled="ranking.includes(option.value) && ranking[rank - 1] !== option.value">{{ option.label }}</option>
          </select>
        </label>
        <label class="reason">选择第 1 名的主要原因
          <textarea v-model.trim="reason" rows="4" required></textarea>
        </label>
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" :disabled="!valid || submitting">{{ submitting ? "正在保存…" : "提交排序" }}</button>
      </form>
    </section>
  </main>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { PREFERENCE_OPTIONS } from "../../experiment/experimentConfig";
const props = defineProps({ api: { type: Object, required: true }, sessionId: { type: String, required: true } });
const emit = defineEmits(["completed"]);
const options = PREFERENCE_OPTIONS;
const ranking = reactive(["", "", "", ""]);
const reason = ref("");
const submitting = ref(false);
const error = ref("");
const valid = computed(() => new Set(ranking).size === 4 && ranking.every(Boolean) && reason.value.length > 0);
async function submit() {
  if (!valid.value || submitting.value) return;
  submitting.value = true; error.value = "";
  try {
    await props.api.submitPreference(props.sessionId, [...ranking], ranking[0], reason.value);
    emit("completed");
  } catch (requestError) { error.value = requestError.message; submitting.value = false; }
}
</script>

<style scoped>
.survey-page { min-height: calc(100vh - 62px); display: grid; place-items: center; padding: 26px 18px; background: #f4f7f9; }
.survey-card { width: min(700px, 100%); padding: 36px; border: 1px solid #d9e4ea; border-radius: 16px; background: #fff; }
h1 { color: #17324d; }.rank-row { display: grid; grid-template-columns: 100px 1fr; gap: 15px; align-items: center; margin: 15px 0; font-weight: 700; color: #294257; }
select, textarea { width: 100%; box-sizing: border-box; padding: 11px; border: 1px solid #b8c8d2; border-radius: 8px; font: inherit; }
.reason { display: block; margin-top: 24px; color: #294257; font-weight: 700; }.reason textarea { margin-top: 8px; resize: vertical; }
button { display: block; margin: 22px 0 0 auto; padding: 13px 20px; border: 0; border-radius: 9px; color: #fff; background: #236b78; font-weight: 800; }
button:disabled { opacity: .5; }.error { color: #8b1e2d; }
</style>
