<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'
import Pet from './Pet.vue'
import Icon from './Icon.vue'
import { request, isMock } from '../api/client'
import { signIn, type User } from '../state/session'
const emit = defineEmits<{ complete: [] }>()
const role = ref<'child' | 'parent'>('child'), account = ref(isMock ? 'demo_child' : ''), password = ref(isMock ? 'demo1234' : '')
const busy = ref(false), error = ref('')
let controller: AbortController | undefined
watch(role, value => { error.value = ''; if (isMock) account.value = `demo_${value}` })
onUnmounted(() => controller?.abort())
async function login() {
  if (busy.value) return
  error.value = ''
  if (!account.value.trim() || !password.value) { error.value = '请填写账号和密码。'; return }
  busy.value = true; controller = new AbortController()
  try {
    if (isMock) signIn({ id: `demo-${role.value}`, name: role.value === 'child' ? '小朋友' : '家长', role: role.value })
    else {
      const data = await request<{ user: User; accessToken: string }>('/auth/login', { account: account.value.trim(), password: password.value, role: role.value }, controller.signal)
      if (!data.user || !['child', 'parent'].includes(data.user.role) || typeof data.user.id !== 'string' || typeof data.user.name !== 'string' || !data.accessToken) throw new Error('登录返回格式不完整，请联系服务提供者。')
      signIn(data.user, data.accessToken)
    }
    password.value = ''; emit('complete')
  } catch (e) { if (!controller.signal.aborted) error.value = e instanceof Error ? e.message : '暂时无法登录，请稍后再试。' }
  finally { busy.value = false }
}
</script>
<template>
  <div class="login-page">
    <div class="login-brand"><span class="brand-mark"><Icon name="lamp" :size="28"/></span><strong>话外</strong><span class="mode-tag">{{ isMock ? '本地演示登录' : '账号登录' }}</span></div>
    <div class="login-welcome"><Pet :wave="true"/><span class="login-bubble">你好，很高兴见到你。</span></div>
    <div class="login-intro"><p class="eyebrow">从这里，慢慢靠近</p><h1>欢迎来到话外</h1><p>让想说的话，被好好听见。</p></div>
    <form class="login-form" @submit.prevent="login">
      <div class="role-selector" role="group" aria-label="登录身份"><button type="button" :aria-pressed="role === 'child'" :class="{selected:role === 'child'}" :disabled="busy" @click="role = 'child'"><Icon name="sun" :size="20"/>我是孩子</button><button type="button" :aria-pressed="role === 'parent'" :class="{selected:role === 'parent'}" :disabled="busy" @click="role = 'parent'"><Icon name="heart" :size="20"/>我是家长</button></div>
      <label for="login-account">{{ isMock ? '演示账号' : '账号' }}</label><input id="login-account" v-model="account" :readonly="isMock" :disabled="busy" :autocomplete="isMock ? 'off' : 'username'" autocapitalize="none" spellcheck="false" placeholder="请输入账号" maxlength="128">
      <label for="login-password">{{ isMock ? '演示密码' : '密码' }}</label><input id="login-password" v-model="password" type="password" :readonly="isMock" :disabled="busy" :autocomplete="isMock ? 'off' : 'current-password'" placeholder="请输入密码" maxlength="128">
      <p v-if="isMock" class="login-demo-note">当前使用预设演示账号，不注册或验证真实账号，请勿输入个人账号密码。</p>
      <p v-if="error" class="error-banner" role="alert">{{ error }}</p>
      <button class="primary login-submit" :disabled="busy">{{ busy ? '正在登录…' : isMock ? '使用演示账号进入' : '登录' }}<Icon name="arrow" :size="19"/></button>
      <p class="login-next">{{ role === 'child' ? '进入后，挑一位你喜欢的表达伙伴。' : '进入后，开启一次和孩子的沟通。' }}</p>
    </form>
    <p class="login-footer">认真对待每一份感受，尊重每一次表达。</p>
  </div>
</template>
