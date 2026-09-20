<template>
  <main class="survey-page">
    <section class="survey-card">
      <h1>四种界面偏好排序</h1>
      <p class="intro">请根据你的使用体验，将下方四种界面卡片拖入或点击填入排名槽位。每种界面只能出现一次。</p>

      <!-- 界面说明卡片（带示意图） -->
      <div class="interface-legend">
        <div v-for="option in options" :key="option.value" class="legend-card" :class="`legend-${option.value.toLowerCase()}`">
          <div class="legend-header">
            <span class="legend-badge" :class="`badge-${option.value.toLowerCase()}`">{{ option.value }}</span>
            <span class="legend-name">{{ option.fullName }}</span>
          </div>
          <img :src="option.image" :alt="option.fullName" class="legend-image" />
          <p class="legend-desc">{{ option.description }}</p>
        </div>
      </div>

      <form @submit.prevent="submit">
        <!-- 排名槽位 -->
        <div class="ranking-slots">
          <div
            v-for="rank in 4"
            :key="rank"
            class="rank-slot"
            :class="{ 'slot-filled': ranking[rank - 1], 'slot-empty': !ranking[rank - 1] }"
            @click="clearRank(rank - 1)">
            <div class="rank-label">第 {{ rank }} 名</div>
            <div v-if="ranking[rank - 1]" class="rank-card" :class="`card-${ranking[rank - 1].toLowerCase()}`">
              <img :src="getOptionImage(ranking[rank - 1])" class="rank-mini-image" />
              <span class="rank-badge" :class="`badge-${ranking[rank - 1].toLowerCase()}`">{{ ranking[rank - 1] }}</span>
              <span class="rank-name">{{ getOptionFullName(ranking[rank - 1]) }}</span>
              <span class="rank-remove">✕</span>
            </div>
            <div v-else class="rank-placeholder">点击下方界面卡片填入</div>
          </div>
        </div>

        <!-- 待选界面卡片（带示意图） -->
        <div class="available-cards">
          <div class="available-title">待选界面（点击填入排名）</div>
          <div class="available-grid">
            <div
              v-for="option in availableOptions"
              :key="option.value"
              class="available-card"
              :class="`card-${option.value.toLowerCase()}`"
              @click="selectNext(option.value)">
              <img :src="option.image" :alt="option.fullName" class="available-image" />
              <div class="available-info">
                <span class="available-badge" :class="`badge-${option.value.toLowerCase()}`">{{ option.value }}</span>
                <span class="available-name">{{ option.fullName }}</span>
              </div>
            </div>
          </div>
          <p v-if="!availableOptions.length" class="all-selected">所有界面已分配排名，点击已选卡片可取消重选。</p>
        </div>

        <label class="reason">选择第 1 名的主要原因
          <textarea v-model.trim="reason" rows="4" required placeholder="请简要说明你最喜欢这个界面的原因..."></textarea>
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

// 扩展选项，添加完整名称、示意图和详细说明
const options = PREFERENCE_OPTIONS.map(opt => ({
  ...opt,
  fullName: opt.value === "TE" ? "文末嵌入（TE）" :
            opt.value === "CS" ? "点击查看（CS）" :
            opt.value === "SE" ? "句末跟随（SE）" :
            "行间穿插（BL）",
  image: opt.value === "TE" ? "/images/te-schematic.png" :
         opt.value === "CS" ? "/images/cs-schematic.png" :
         opt.value === "SE" ? "/images/se-schematic.png" :
         "/images/bl-schematic.png",
  description: opt.value === "TE" ? "所有评论以卡片形式集中显示在文章末尾，阅读完正文后可查看评论。" :
               opt.value === "CS" ? "正文中有评论的位置会显示标记，点击标记可在侧边栏查看评论。" :
               opt.value === "SE" ? "评论紧跟在相关句子的末尾，与正文连续显示。" :
               "评论以独立段落的形式穿插在正文段落之间。"
}));

const ranking = reactive(["", "", "", ""]);
const reason = ref("");
const submitting = ref(false);
const error = ref("");

const availableOptions = computed(() => options.filter(opt => !ranking.includes(opt.value)));
const valid = computed(() => new Set(ranking).size === 4 && ranking.every(Boolean) && reason.value.length > 0);

function selectNext(value) {
  const emptyIndex = ranking.findIndex(r => !r);
  if (emptyIndex !== -1) {
    ranking[emptyIndex] = value;
  }
}
function clearRank(index) {
  ranking[index] = "";
}
function getOptionFullName(value) {
  const opt = options.find(o => o.value === value);
  return opt ? opt.fullName : value;
}
function getOptionImage(value) {
  const opt = options.find(o => o.value === value);
  return opt ? opt.image : "";
}

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
.survey-card { width: min(860px, 100%); padding: 32px; border: 1px solid #d9e4ea; border-radius: 16px; background: #fff; }
h1 { color: #17324d; margin: 0 0 8px; }
.intro { color: #607586; margin: 0 0 20px; line-height: 1.6; }

/* 界面说明卡片 */
.interface-legend { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 24px; }
.legend-card { padding: 12px; border-radius: 10px; border: 1px solid #e2eaed; background: #fafcfc; }
.legend-header { display: flex; align-items: center; gap: 6px; margin-bottom: 8px; }
.legend-name { font-weight: 700; color: #2c4a5e; font-size: 13px; }
.legend-image { width: 100%; height: auto; border-radius: 6px; margin-bottom: 8px; }
.legend-desc { margin: 0; font-size: 11px; color: #6b7f8f; line-height: 1.5; }

/* 颜色标签 */
.legend-badge, .rank-badge, .available-badge {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 32px; height: 22px; padding: 0 8px;
  border-radius: 5px; font-size: 11px; font-weight: 800; color: #fff;
}
.badge-te { background: #2b7a78; }
.badge-cs { background: #c0792e; }
.badge-se { background: #5a6fa8; }
.badge-bl { background: #8b5a8b; }

/* 排名槽位 */
.ranking-slots { display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }
.rank-slot {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 14px; border-radius: 10px;
  border: 2px dashed #d0dde5; background: #f7fafb;
  cursor: pointer; transition: all .2s; min-height: 56px;
}
.rank-slot.slot-filled { border-style: solid; border-color: transparent; background: #fff; padding: 8px 14px; }
.rank-slot.slot-empty:hover { border-color: #2b7a78; background: #f0f7f7; }
.rank-label { flex-shrink: 0; width: 60px; font-weight: 800; color: #2c4a5e; font-size: 14px; }
.rank-placeholder { color: #9fb0b8; font-size: 13px; }
.rank-card {
  flex: 1; display: flex; align-items: center; gap: 10px;
  padding: 6px 12px; border-radius: 8px; color: #fff;
}
.rank-mini-image { width: 40px; height: auto; border-radius: 4px; }
.rank-card.card-te { background: linear-gradient(135deg, #2b7a78, #1a5f5d); }
.rank-card.card-cs { background: linear-gradient(135deg, #c0792e, #a06020); }
.rank-card.card-se { background: linear-gradient(135deg, #5a6fa8, #45588a); }
.rank-card.card-bl { background: linear-gradient(135deg, #8b5a8b, #6e456e); }
.rank-name { flex: 1; font-weight: 700; font-size: 14px; }
.rank-remove { opacity: .7; font-size: 12px; }
.rank-card:hover .rank-remove { opacity: 1; }

/* 待选卡片 */
.available-cards { margin-bottom: 24px; padding: 14px; background: #f7fafb; border-radius: 10px; border: 1px solid #e2eaed; }
.available-title { font-size: 13px; font-weight: 700; color: #6b7f8f; margin-bottom: 10px; }
.available-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
.available-card {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  padding: 10px; border-radius: 8px; color: #fff;
  cursor: pointer; transition: transform .15s, box-shadow .15s;
}
.available-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,.15); }
.available-image { width: 100%; height: auto; border-radius: 6px; }
.available-info { display: flex; align-items: center; gap: 6px; }
.available-card.card-te { background: linear-gradient(135deg, #2b7a78, #1a5f5d); }
.available-card.card-cs { background: linear-gradient(135deg, #c0792e, #a06020); }
.available-card.card-se { background: linear-gradient(135deg, #5a6fa8, #45588a); }
.available-card.card-bl { background: linear-gradient(135deg, #8b5a8b, #6e456e); }
.available-name { font-weight: 700; font-size: 12px; }
.all-selected { margin: 8px 0 0; font-size: 12px; color: #2b7a78; }

.reason { display: block; margin-top: 20px; color: #294257; font-weight: 700; }
.reason textarea { margin-top: 8px; width: 100%; box-sizing: border-box; padding: 12px; border: 1px solid #b8c8d2; border-radius: 8px; font: inherit; resize: vertical; }
button { display: block; margin: 22px 0 0 auto; padding: 13px 24px; border: 0; border-radius: 9px; color: #fff; background: #236b78; font-weight: 800; cursor: pointer; }
button:disabled { opacity: .5; cursor: not-allowed; }
.error { color: #8b1e2d; }

@media (max-width: 768px) {
  .interface-legend { grid-template-columns: repeat(2, 1fr); }
  .available-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 600px) {
  .survey-card { padding: 20px; }
}
</style>
