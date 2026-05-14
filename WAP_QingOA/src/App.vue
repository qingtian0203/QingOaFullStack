<script setup lang="ts">
import { onMounted, ref } from "vue";
import { login, resolveToken } from "./api";

const checking = ref(true);
const authenticated = ref(false);
const username = ref("konglingjia");
const password = ref("123456");
const error = ref("");

onMounted(async () => {
  document.documentElement.classList.toggle("app-webview", Boolean(window.QingOA?.getToken));
  authenticated.value = Boolean(await resolveToken());
  checking.value = false;
});

async function submitLogin() {
  error.value = "";
  try {
    await login(username.value.trim(), password.value);
    authenticated.value = true;
  } catch (err) {
    error.value = err instanceof Error ? err.message : "登录失败";
  }
}
</script>

<template>
  <div v-if="checking" class="screen-center">
    <div class="spinner" />
    <p>正在打开流程中心</p>
  </div>

  <main v-else-if="!authenticated" class="login-page">
    <section class="login-card">
      <p class="eyebrow">QingOA WAP</p>
      <h1>流程中心</h1>
      <p class="muted">浏览器调试模式使用轻量登录，App 内会自动走 JS Bridge。</p>

      <form data-testid="wap-login-form" class="login-form" @submit.prevent="submitLogin">
        <input
          v-model="username"
          data-testid="wap-login-username"
          autocomplete="username"
          placeholder="账号"
        />
        <input
          v-model="password"
          data-testid="wap-login-password"
          autocomplete="current-password"
          type="password"
          placeholder="密码"
        />
        <button data-testid="wap-login-submit" type="submit">登录流程中心</button>
      </form>
      <p v-if="error" class="error">{{ error }}</p>
    </section>
  </main>

  <RouterView v-else />
</template>
