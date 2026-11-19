<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import type { Message } from '../api/client'
import ChatMessage from './ChatMessage.vue'
import Icon from './Icon.vue'
const props = defineProps<{
  messages: Message[]
  role: 'child' | 'parent'
  invite: string
  mock: boolean
  busy: boolean
  translated: string
  error: string
  notice: string
  translatedDraft: string
  translateStep: 'input' | 'translating' | 'edit'
}>()
const draft = defineModel<string>('draft', { required: true })
const confirmed = defineModel<boolean>('confirmed', { required: true })
const emit = defineEmits<{
  send: []
  translate: []
  cancelTranslate: []
  leave: []
  copyInvite: []
  useExample: []
  incoming: []
  cancel: []
  dismissError: []
  dismissNotice: []
  'update:translatedDraft': [value: string]
}>()
const log = ref<HTMLElement | null>(null)
const input = ref<HTMLTextAreaElement | null>(null)
const editInput = ref<HTMLTextAreaElement | null>(null)
const toolsOpen = ref(false)
const unread = ref<string[]>([])
const count = computed(() => Array.from(draft.value).length)
const editCount = computed(() => Array.from(props.translatedDraft).length)
let following = true
let disposed = false
let resizeObserver: ResizeObserver | undefined

function onEditInput(e: Event) {
  emit('update:translatedDraft', (e.target as HTMLTextAreaElement).value)
}
function atBottom() {
  const el = log.value
  return !el || el.scrollHeight - el.clientHeight - el.scrollTop <= 56
}
function onScroll() {
  following = atBottom()
  if (following) unread.value = []
}
function latest() {
  const el = log.value
  if (el) el.scrollTop = el.scrollHeight
  following = true
  unread.value = []
}
function fitInput() {
  const el = input.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = `${Math.min(96, Math.max(52, el.scrollHeight))}px`
}
function fitEditInput() {
  const el = editInput.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = `${Math.min(120, Math.max(60, el.scrollHeight))}px`
}
watch(() => props.messages.map(m => m.id), async (ids, previous = []) => {
  const old = new Set(previous)
  const newMessages = props.messages.filter(m => !old.has(m.id))
  if (!newMessages.length) return
  const shouldFollow = following || newMessages.some(m => m.role === props.role)
  const previousTop = log.value?.scrollTop ?? 0
  if (!shouldFollow) {
    unread.value = [...new Set([...unread.value, ...newMessages.filter(m => m.role !== props.role).map(m => m.id)])]
  }
  await nextTick()
  if (disposed) return
  if (shouldFollow) latest()
  else if (log.value) log.value.scrollTop = previousTop
}, { flush: 'pre' })
watch(draft, async () => { await nextTick(); fitInput() })
watch(() => props.translatedDraft, async () => { await nextTick(); fitEditInput() })
onMounted(async () => {
  await nextTick()
  if (disposed) return
  latest()
  fitInput()
  resizeObserver = new ResizeObserver(() => { if (following) latest() })
  if (log.value) resizeObserver.observe(log.value)
})
onUnmounted(() => { disposed = true; resizeObserver?.disconnect() })
</script>

<template>
  <section class="room-panel mobile-chat" aria-label="亲子沟通对话">
    <header class="chat-room-bar">
      <div>
        <strong>{{ role === 'parent' ? '和孩子聊聊' : '和家长聊聊' }}</strong>
        <span>{{ mock ? '本机演示 · 未连接另一台设备' : '沟通空间' }}</span>
      </div>
      <button class="text-button" @click="emit('leave')">退出沟通</button>
    </header>
    <div class="chat-room-meta">
      <button class="code" aria-label="复制邀请码" @click="emit('copyInvite')">邀请码 {{ invite }} ⧉</button>
      <span>当前身份：{{ role === 'child' ? '孩子' : '家长' }}</span>
    </div>
    <div class="chat-message-area">
      <div ref="log" class="chat-log" role="log" aria-label="消息记录" aria-live="polite" aria-relevant="additions" tabindex="0" @scroll.passive="onScroll">
        <div v-if="!messages.length" class="empty-chat">
          <Icon name="chat" :size="34"/>
          <h3>从一句真心话开始</h3>
          <p>可以先说说感受，再说说你的期待。</p>
          <p v-if="mock" class="hint">用下方"带入示例"试一试。</p>
        </div>
        <ChatMessage v-for="message in messages" :key="message.id" :message="message" :viewer-role="role"/>
      </div>
      <button v-if="unread.length" class="new-message-button" @click="latest">{{ unread.length }} 条新消息 <span aria-hidden="true">↓</span></button>
    </div>
    <div v-if="error" class="chat-feedback chat-feedback--error" role="alert">
      <span>{{ error }}</span>
      <button class="text-button" @click="emit('dismissError')">关闭</button>
    </div>
    <div v-if="notice" class="chat-feedback" role="status">
      <span>{{ notice }}</span>
      <button class="text-button" @click="emit('dismissNotice')">知道了</button>
    </div>

    <!-- 转译编辑模式 -->
    <form v-if="translateStep === 'edit'" class="composer composer-edit" @submit.prevent="emit('send')">
      <div class="composer-fields">
        <div class="edit-header">
          <span class="edit-label">✏️ 转译完成，确认或修改后发送</span>
          <button type="button" class="text-button" @click="emit('cancelTranslate')">重新输入</button>
        </div>
        <div class="edit-original">
          <small>你的原话</small>
          <p>{{ draft }}</p>
        </div>
        <label for="edited">你可以修改转译结果</label>
        <textarea id="edited" ref="editInput" :value="translatedDraft" @input="onEditInput" rows="3" placeholder="转译结果…" :disabled="busy"></textarea>
        <small class="edit-hint">如果转译不准确，可以直接修改后再发送</small>
      </div>
      <div class="composer-bottom">
        <small>{{ editCount }} / 500</small>
        <button v-if="busy" type="button" class="secondary" @click="emit('cancel')">取消</button>
        <button v-else type="submit" class="primary" :disabled="!translatedDraft.trim() || editCount > 500">确认发送 ↑</button>
      </div>
    </form>

    <!-- 普通输入模式 -->
    <form v-else class="composer" @submit.prevent="translateStep === 'input' && draft.trim() ? emit('translate') : emit('send')">
      <div class="composer-fields">
        <div v-if="mock" class="chat-demo-tools">
          <button type="button" class="text-button" @click="emit('useExample')">＋ 带入{{ role === 'child' ? '孩子' : '家长' }}示例</button>
          <button type="button" class="text-button" :aria-expanded="toolsOpen" @click="toolsOpen = !toolsOpen">演示工具 {{ toolsOpen ? '⌃' : '⌄' }}</button>
        </div>
        <div v-if="mock && toolsOpen" class="chat-tools-panel">
          <p>使用固定示例，不生成真实 AI 回应。可模拟来信检查滚动提醒，不会连接另一台设备。</p>
          <button type="button" class="secondary" @click="emit('incoming')">模拟一条{{ role === 'parent' ? '孩子' : '家长' }}来信</button>
        </div>
        <label class="sr-only" for="raw">想说的原话</label>
        <textarea id="raw" ref="input" v-model="draft" :readonly="mock" :disabled="busy || translateStep === 'translating'" rows="2" placeholder="写下你想让对方听见的话…" @input="fitInput"></textarea>
      </div>
      <div class="composer-bottom">
        <small>{{ count }} / 500{{ mock ? ' · 预设演示' : '' }}</small>
        <div class="composer-actions">
          <button v-if="busy" type="button" class="secondary" @click="emit('cancel')">
            {{ translateStep === 'translating' ? '取消转译' : '取消发送' }}
          </button>
          <template v-else>
            <button v-if="translateStep === 'translating'" type="button" class="primary" disabled>正在转译…</button>
            <button v-else type="submit" class="primary" :disabled="!draft.trim() || count > 500">
              {{ mock ? '确认发送 ↑' : '转译并预览 →' }}
            </button>
          </template>
        </div>
      </div>
    </form>
  </section>
</template>
