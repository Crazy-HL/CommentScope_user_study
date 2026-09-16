<template>
  <main class="center-page">
    <section class="card picker-card">
      <p class="eyebrow">CommentScope</p>
      <h1>评论阅读实验</h1>
      <p class="lead">请选择研究者分配给你的参与者编号。编号范围为 P01–P24。</p>
      <label for="participant-select">参与者编号</label>
      <select id="participant-select" v-model="selected" :disabled="loading">
        <option value="" disabled>请选择</option>
        <option v-for="item in selectableParticipants" :key="item.participant_id" :value="item.participant_id" :disabled="!item.available">
          {{ item.participant_id }}{{ item.resumable ? "（继续实验）" : item.available ? "" : "（使用中）" }}
        </option>
      </select>
      <p v-if="completedCount > 0" class="completed-notice">已有 {{ completedCount }} 名参与者完成实验，不在列表中显示。</p>
      <p v-if="error" class="error" role="alert">{{ error }}</p>
      <button type="button" :disabled="!selected || loading" @click="begin">{{ loading ? "正在进入…" : selectedItem?.resumable ? "继续实验" : "进入实验" }}</button>
      <p class="notice">请勿与他人共用编号。实验中断后，请使用同一浏览器继续。</p>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { PARTICIPANT_IDS } from "../../experiment/experimentConfig";

const props = defineProps({
  api: { type: Object, required: true },
  clientInstanceId: { type: String, required: true },
});
const emit = defineEmits(["started"]);
const selected = ref("");
const loading = ref(false);
const error = ref("");
const participants = ref(PARTICIPANT_IDS.map(participant_id => ({ participant_id, available: true })));
const selectedItem = computed(() => participants.value.find(item => item.participant_id === selected.value));
// 过滤掉已完成实验的参与者，不在下拉框显示
const selectableParticipants = computed(() => participants.value.filter(item => !item.completed));
const completedCount = computed(() => participants.value.filter(item => item.completed).length);

async function loadParticipants() {
  try {
    const payload = await props.api.listParticipants(props.clientInstanceId);
    if (Array.isArray(payload.participants)) participants.value = payload.participants;
  } catch (_) {
    // The fixed list remains usable if the availability request is temporarily unavailable.
  }
}

onMounted(() => {
  loadParticipants();
});

async function begin() {
  if (!selected.value || loading.value) return;
  loading.value = true;
  error.value = "";
  try {
    const payload = await props.api.startSession(selected.value, props.clientInstanceId);
    emit("started", payload);
  } catch (requestError) {
    error.value = requestError.code === "participant_locked"
      ? "这个编号正在另一台设备或另一个浏览器中使用，请联系研究者。"
      : requestError.message;
  } finally {
    loading.value = false;
  }
}

</script>

<style scoped>
.center-page { min-height: 100vh; display: grid; place-items: center; padding: 24px; background: linear-gradient(145deg, #edf5fa, #f8fbfd 55%, #eef7f2); }
.card { width: min(520px, 100%); padding: 38px; border: 1px solid #d8e4ec; border-radius: 18px; background: #fff; box-shadow: 0 18px 60px rgba(36,69,94,.12); }
.eyebrow { margin: 0; color: #2b7a78; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; }
h1 { margin: 8px 0 12px; font-size: clamp(30px, 5vw, 42px); color: #17324d; }
.lead, .notice { color: #5b7083; line-height: 1.7; }
label { display: block; margin: 26px 0 8px; font-weight: 700; color: #263f56; }
select, button { width: 100%; min-height: 48px; border-radius: 10px; font: inherit; }
select { padding: 0 13px; border: 1px solid #aebfcd; background: white; }
button { margin-top: 18px; border: 0; color: white; background: #236b78; font-weight: 800; cursor: pointer; }
button:disabled { opacity: .55; cursor: not-allowed; }
.error { padding: 10px 12px; color: #8b1e2d; background: #fff0f1; border-radius: 8px; }
.notice { margin: 18px 0 0; font-size: 13px; }
.completed-notice { margin: 8px 0 0; color: #6b7f8f; font-size: 12px; }
</style>
