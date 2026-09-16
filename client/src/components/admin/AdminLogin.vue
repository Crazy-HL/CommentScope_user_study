<template>
  <main class="admin-login-page">
    <section class="admin-login-card" aria-labelledby="admin-login-title">
      <div class="admin-kicker">CommentScope · Researcher access</div>
      <h1 id="admin-login-title">管理员后台</h1>
      <p class="admin-login-intro">登录后查看实验进度、论文分析指标和数据完整性。</p>
      <form class="admin-login-form" @submit.prevent="submit">
        <label>
          用户名
          <input v-model="username" autocomplete="username" required placeholder="请输入管理员用户名" />
        </label>
        <label>
          密码
          <input v-model="password" autocomplete="current-password" type="password" required placeholder="请输入管理员密码" />
        </label>
        <p v-if="error" class="admin-error" role="alert">{{ error }}</p>
        <button class="admin-primary-button" type="submit" :disabled="loading">
          {{ loading ? "正在登录…" : "登录后台" }}
        </button>
      </form>
    </section>
  </main>
</template>

<script setup>
import { ref } from "vue";
import adminApi from "../../admin/adminApi";

const emit = defineEmits(["authenticated"]);
const username = ref("");
const password = ref("");
const loading = ref(false);
const error = ref("");

async function submit() {
  loading.value = true;
  error.value = "";
  try {
    const result = await adminApi.login(username.value.trim(), password.value);
    password.value = "";
    emit("authenticated", result.username);
  } catch (requestError) {
    error.value = requestError.status === 401 ? "用户名或密码错误。" : requestError.message;
  } finally {
    loading.value = false;
  }
}
</script>
