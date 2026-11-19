<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Pet from './components/Pet.vue'
import LoginPage from './components/LoginPage.vue'
import ParentHome from './components/ParentHome.vue'
import ChatRoom from './components/ChatRoom.vue'
import CompanionPicker from './components/CompanionPicker.vue'
import { session as authSession, signOut, finishCompanionSelection } from './state/session'
import { selectedCompanion } from './state/companions'
import StoryReflection from './components/StoryReflection.vue'
import Icon from './components/Icon.vue'
import FeatureArt from './components/FeatureArt.vue'
import { api, isMock, type Message } from './api/client'
const route = useRoute(), router = useRouter()
const page = computed(() => route.path)
function onLogin() { role.value = authSession.user?.role ?? 'child'; void router.replace(authSession.user?.role === 'child' ? '/companions' : '/') }
function onCompanionDone() { finishCompanionSelection(); void router.replace('/') }
function logout() { leaveRoom(); exitPractice(); stopAudio(); signOut(); void router.replace('/login') }
const isParent = computed(() => authSession.user?.role === 'parent')
const tabs = computed(() => isParent.value
  ? [{ path: '/', icon: 'home', text: '首页' }, { path: '/communication', icon: 'chat', text: '亲子沟通' }, { path: '/account', icon: 'heart', text: '我的' }]
  : [{ path: '/', icon: 'home', text: '今天' }, { path: '/communication', icon: 'chat', text: '沟通翻译' }, { path: '/stories', icon: 'book', text: '小灯故事' }, { path: '/practice', icon: 'practice', text: '场景练习' }])
const keyboardOpen = ref(false)
const viewportHeight = ref('100dvh'), viewportTop = ref('0px')
function updateKeyboard() {
  viewportHeight.value = `${window.visualViewport?.height ?? window.innerHeight}px`
  viewportTop.value = `${window.visualViewport?.offsetTop ?? 0}px`
  const typing = document.activeElement?.matches('input, textarea')
  keyboardOpen.value = !!typing && !!window.visualViewport && window.visualViewport.height < window.innerHeight - 120
}
function onFocusChange() { requestAnimationFrame(updateKeyboard) }
onMounted(() => {
  updateKeyboard()
  window.addEventListener('resize', updateKeyboard)
  window.visualViewport?.addEventListener('scroll', updateKeyboard)
  window.visualViewport?.addEventListener('resize', updateKeyboard)
  document.addEventListener('focusin', onFocusChange)
  document.addEventListener('focusout', onFocusChange)
})
onUnmounted(() => {
  window.removeEventListener('resize', updateKeyboard)
  window.visualViewport?.removeEventListener('scroll', updateKeyboard)
  window.visualViewport?.removeEventListener('resize', updateKeyboard)
  document.removeEventListener('focusin', onFocusChange)
  document.removeEventListener('focusout', onFocusChange)
})
const busy = ref(false), error = ref(''), notice = ref(''), help = ref(false)
let controller: AbortController | undefined, poll: ReturnType<typeof setInterval> | undefined
let epoch = 0
let roomEpoch = 0
let syncBusy = false
let pollFailCount = 0
const role = ref<'child' | 'parent'>(authSession.user?.role ?? 'child'), room = ref(''), invite = ref(''), code = ref(''), draft = ref(''), confirmed = ref(false)
// 转译编辑流程状态
const translatedDraft = ref('')  // 用户可编辑的转译结果
const translateStep = ref<'input' | 'translating' | 'edit'>('input')  // 当前步骤
const messages = ref<Message[]>([])
const sampleChild = '你们总是很忙，都不听我说话。'
const sampleParent = '我不是不想听，最近工作实在太忙了。'
const sample = computed(() => role.value === 'child' ? sampleChild : sampleParent)
const translated = computed(() => role.value === 'child' ? '我有点想你们，也希望被认真听见。我们能约一个时间，好好聊聊吗？' : '我很在乎你，最近忙碌让你觉得被忽略了。我想找个时间认真听你说。')
const storyOpen = ref(false)
const practiceSeed = ref('')
const scene = ref('missing'), started = ref(false), session = ref(''), turns = ref(0), reply = ref(''), practiceText = ref(''), feedback = ref('')
const conversation = ref<{ role: string; text: string }[]>([])
const scenes = [ { id: 'missing', icon: 'chat', title: '想和爸妈聊一会儿', label: '表达想念', desc: '想念在外工作的父母，却又怕打扰他们。' }, { id: 'phone', icon: 'phone', title: '商量手机使用时间', label: '说出边界', desc: '想有自己的安排，也希望听听彼此的担心。' }, { id: 'friend', icon: 'friend', title: '和朋友说开小误会', label: '修复关系', desc: '有一点委屈，想把心里的话说清楚。' } ]
const currentScene = computed(() => scenes.find(s => s.id === scene.value)!)
function cancel() { epoch++; controller?.abort(); busy.value = false }
async function run(job: (signal: AbortSignal, id: number) => Promise<void>) {
  cancel(); const id = epoch; controller = new AbortController(); busy.value = true; error.value = ''; notice.value = ''
  try { await job(controller.signal, id) } catch (e) { if (id === epoch && !controller.signal.aborted) error.value = e instanceof Error ? e.message : '连接失败，请稍后重试。' } finally { if (id === epoch) busy.value = false }
}
async function enter(join = false) {
  if (join && !/^[A-Za-z0-9]{6,12}$/.test(code.value.trim())) { error.value = '请输入 6–12 位字母或数字邀请码。'; return }
  await run(async (signal, id) => {
    const result = isMock ? { roomId: 'demo-room', inviteCode: 'LIGHT6' } : await (join ? api.joinRoom(code.value.trim(), role.value, signal) : api.createRoom(role.value, signal))
    if (id !== epoch) return
    room.value = result.roomId; invite.value = result.inviteCode; draft.value = ''; messages.value = []
    if (!isMock) {
      const syncId = ++roomEpoch
      pollFailCount = 0
      poll = setInterval(async () => {
        if (syncBusy) return
        syncBusy = true
        try { const items = await api.messages(result.roomId, AbortSignal.timeout(10000)); if (syncId === roomEpoch) { messages.value = items; pollFailCount = 0 } }
        catch { pollFailCount++; if (syncId === roomEpoch && pollFailCount >= 8) notice.value = '连接似乎断开了，可以尝试重新进入沟通。' }
        finally { syncBusy = false }
      }, 2500)
    }
  })
}
function leaveRoom() {
  role.value = authSession.user?.role ?? 'child'
  roomEpoch++; clearInterval(poll); cancel()
  room.value = ''; messages.value = []; draft.value = ''; confirmed.value = false
  translatedDraft.value = ''; translateStep.value = 'input'
}

// 转译函数：调用 AI 转译，结果放入 translatedDraft 供用户编辑
async function translate() {
  if (!draft.value.trim() || Array.from(draft.value).length > 500) return
  const originalText = draft.value.trim()

  await run(async (signal, id) => {
    translateStep.value = 'translating'
    error.value = ''
    try {
      const response = isMock
        ? { original: originalText, translated: translated.value }
        : await api.translate(originalText, signal)

      if (id !== epoch) return

      // 检查安全风险警报
      if (response.safetyAlert && response.riskLevel === 'high') {
        translateStep.value = 'input'
        help.value = true
        error.value = response.message || '我们注意到你可能需要帮助。'
        return
      }

      // 转译结果放入可编辑区域
      translatedDraft.value = response.translated
      translateStep.value = 'edit'
    } catch (e) {
      translateStep.value = 'input'
      // 提供更友好的错误提示
      const msg = e instanceof Error ? e.message : ''
      if (msg.includes('超时') || msg.includes('timeout')) {
        error.value = '转译请求超时，请检查网络后点击"转译并预览"重试。'
      } else if (msg.includes('连接失败') || msg.includes('502')) {
        error.value = '模型服务暂时不可用，请稍后再试。'
      } else {
        throw e
      }
    }
  })
}

// 取消转译编辑，回到输入状态
function cancelTranslate() {
  translatedDraft.value = ''
  translateStep.value = 'input'
}

// 发送函数：使用 translatedDraft 作为转译结果
async function send() {
  if (!draft.value.trim() || Array.from(draft.value).length > 500) return
  const originalText = draft.value.trim()
  // 如果有编辑后的转译结果，使用它；否则让后端重新转译
  const finalTranslated = translatedDraft.value.trim() || undefined
  const tempId = 'pending-' + crypto.randomUUID()

  // 立即显示 pending 消息
  const pendingMsg: Message = {
    id: tempId,
    role: role.value,
    original: originalText,
    translated: finalTranslated || '正在发送…',
    pending: !finalTranslated,
    ...(role.value === 'child' ? { senderCompanionId: selectedCompanion.value.id } : {})
  }
  messages.value.push(pendingMsg)

  await run(async (signal, id) => {
    try {
      const response = isMock
        ? { id: crypto.randomUUID(), role: role.value, original: originalText, translated: finalTranslated || translated.value, ...(role.value === 'child' ? { senderCompanionId: selectedCompanion.value.id } : {}) }
        : await api.send(room.value, role.value, originalText, crypto.randomUUID(), signal, role.value === 'child' ? selectedCompanion.value.id : undefined, finalTranslated)

      if (id !== epoch) return

      // 检查安全风险警报
      if ('safetyAlert' in response && response.safetyAlert && response.riskLevel === 'high') {
        messages.value = messages.value.filter(m => m.id !== tempId)
        help.value = true
        error.value = response.message || '我们注意到你可能需要帮助。'
        return
      }

      const message: Message = response as Message
      const idx = messages.value.findIndex(m => m.id === tempId)
      if (idx >= 0) messages.value[idx] = message
      else if (!messages.value.some(m => m.id === message.id)) messages.value.push(message)

      if (message.riskLevel === 'medium') {
        notice.value = '如果你感到困扰，可以随时点击"寻找现实中的支持"。'
      }

      // 发送成功，清空状态
      draft.value = ''
      translatedDraft.value = ''
      translateStep.value = 'input'
      confirmed.value = false
    } catch (e) {
      messages.value = messages.value.filter(m => m.id !== tempId)
      throw e
    }
  })
}
function previewIncomingMessage() {
  if (!isMock) return
  const sender = role.value === 'parent' ? 'child' : 'parent'
  messages.value.push({ id: `demo-incoming-${crypto.randomUUID()}`, role: sender, original: sender === 'child' ? sampleChild : sampleParent, translated: sender === 'child' ? '我有点想你们，也希望被认真听见。我们能约一个时间，好好聊聊吗？' : '我很在乎你，最近忙碌让你觉得被忽略了。我想找个时间认真听你说。', ...(sender === 'child' ? { senderCompanionId: 'star' } : {}) })
}
function useExample() { draft.value = sample.value; confirmed.value = false }
async function openParentRoom() { await router.push('/communication'); await nextTick(); await enter() }
async function joinParentRoom() { await router.push('/communication'); await nextTick(); document.getElementById('invite')?.focus() }
async function copy(text: string) { try { await navigator.clipboard.writeText(text); notice.value = '已复制，可以分享给对方。' } catch { notice.value = '复制未成功，请长按文字手动复制。' } }
function storyToCommunication() { router.push('/communication'); notice.value = '故事可以帮助你找到感受。进入沟通前，请自己决定想说什么。' }
async function storyToPractice(text: string) {
  await router.push('/practice')
  await nextTick()
  scene.value = 'missing'
  practiceSeed.value = text
}
async function startPractice() {
  await run(async (signal, id) => {
    const data = isMock ? { sessionId: 'demo-practice', reply: '最近你过得怎么样？有什么想和我聊聊的吗？', turn: 0, done: false } : await api.practiceStart(scene.value, signal)
    if (id !== epoch) return
    started.value = true; session.value = data.sessionId; practiceText.value = practiceSeed.value; turns.value = 0; feedback.value = ''; conversation.value = [{ role: '对方', text: data.reply }]
  })
}
async function practiceSend() {
  if (!practiceText.value.trim() || turns.value >= 2 || Array.from(practiceText.value).length > 500) return
  await run(async (signal, id) => {
    const text = practiceText.value.trim()
    const data = isMock ? { sessionId: session.value, reply: turns.value === 0 ? '谢谢你愿意说出来。你希望我们怎么安排呢？' : '我听明白了，我们可以一起商量一个合适的时间。', turn: turns.value + 1, done: turns.value === 1, feedback: '你尝试表达了自己的感受，也提出了具体的期待。下次可以再问问对方的想法。' } : await api.practiceReply(session.value, text, crypto.randomUUID(), signal)
    if (id !== epoch) return
    conversation.value.push({ role: '我', text }, { role: '对方', text: data.reply }); turns.value = data.turn; practiceText.value = ''; if (data.done) feedback.value = data.feedback || '练习结束。可以想一想哪句话最贴近你的心意。'
  })
}
function exitPractice() { practiceSeed.value = ''; if (session.value && !isMock) void api.practiceExit(session.value).catch(() => {}); cancel(); started.value = false; session.value = ''; conversation.value = []; practiceText.value = ''; feedback.value = ''; turns.value = 0 }
function stopAudio() { if ('speechSynthesis' in window) speechSynthesis.cancel(); reply.value = '' }
function readStory() { if (!('speechSynthesis' in window)) { notice.value = '当前设备不支持朗读，可以继续阅读故事。'; return } if (reply.value) { stopAudio(); return } const text = document.querySelector('.story-text')?.textContent || ''; const speech = new SpeechSynthesisUtterance(text); speech.lang = 'zh-CN'; speech.rate = 0.9; speech.onend = () => { reply.value = '' }; speech.onerror = () => { reply.value = ''; notice.value = '当前设备无法朗读，可以继续阅读故事。' }; reply.value = 'playing'; speechSynthesis.speak(speech) }
watch(draft, () => { confirmed.value = false })
watch(page, () => { leaveRoom(); exitPractice(); stopAudio(); error.value = ''; notice.value = ''; storyOpen.value = false })
onUnmounted(() => { leaveRoom(); exitPractice(); stopAudio() })
</script>

<template>
  <div class="app-shell" :class="{ 'keyboard-open': keyboardOpen, 'chat-active': page === '/communication' && !!room }" :style="{ '--viewport-height': viewportHeight, '--viewport-top': viewportTop }">
    <LoginPage v-if="!authSession.user" @complete="onLogin"/>
    <CompanionPicker v-else-if="page === '/companions'" @complete="onCompanionDone"/>
    <template v-else>
    <aside class="sidebar">
      <RouterLink to="/" class="brand"><span class="brand-mark"><Icon name="lamp" :size="29"/></span><span>话外<small>让心意慢慢靠近</small></span></RouterLink>
      <div class="nav-caption">你的小小表达空间</div>
      <nav><RouterLink v-for="tab in tabs" :key="tab.path" :to="tab.path" :class="{ active: page === tab.path }"><Icon class="nav-icon" :name="tab.icon"/>{{ tab.text }}<span v-if="page === tab.path" class="nav-dot"></span></RouterLink></nav>
      <div class="sidebar-note"><Icon class="tiny-sun" name="sun" :size="30"/><p>每一种感受，<br>都值得被好好听见。</p><small>从一句话开始，就很好。</small></div>
      <button class="support-link" @click="help = true"><Icon name="heart" :size="16"/> 寻找现实中的支持 <Icon name="diagonal" :size="14"/></button>
    </aside>
    <main>
      <header class="topbar"><span>{{ page === '/account' ? '我的' : tabs.find(t => t.path === page)?.text || '今天' }} <span class="breadcrumb"> / &nbsp; 话外</span></span><div class="topbar-right"><span class="mode-tag"><i></i>{{ isMock ? '预设演示数据' : '真实接口模式' }}</span><button class="avatar account-entry" aria-label="我的账号" @click="router.push('/account')"><img v-if="authSession.user?.role === 'child'" :src="selectedCompanion.src" alt=""><Icon v-else name="heart" :size="18"/></button></div></header>
      <div class="content" :key="page">
        <template v-if="page === '/account'">
          <div class="page-heading"><p class="eyebrow">你的小小空间</p><h1>你好，{{ authSession.user?.name }}</h1><p class="subtitle">当前身份：{{ authSession.user?.role === 'child' ? '孩子' : '家长' }}</p></div>
          <section v-if="authSession.user?.role === 'child'" class="account-companion panel"><Pet/><h2>我的表达伙伴 · {{ selectedCompanion.name }}</h2><p>{{ selectedCompanion.description }}</p><button class="primary" @click="router.push('/companions')">更换伙伴 <Icon name="arrow" :size="18"/></button></section>
          <section class="panel account-settings"><p>{{ isMock ? '当前为本地演示登录，不代表真实账号认证。' : '当前为账号登录模式。' }}</p><p class="hint">只在本机保存形象偏好，不保存沟通原文。退出会清空当前会话。</p><button class="secondary full" @click="logout">退出登录</button></section>
        </template>
        <ParentHome v-else-if="page === '/' && isParent" @create="openParentRoom" @join="joinParentRoom"/>
        <template v-else-if="page === '/'">
          <div class="greeting"><div><p class="eyebrow"><span></span> 留一点空间，给心里的话</p><h1>有些话，<span>可以慢慢说。</span></h1><p class="subtitle">你好，欢迎来到话外。今天，想从哪里开始？</p></div><span class="date-note"><Icon name="sun" :size="18"/> 不着急，我们一起</span></div>
          <section class="hero"><div class="hero-copy"><span class="pill"><span class="warm-dot"></span> {{ selectedCompanion.name }}在这里，陪你慢慢说</span><h2>让心里的话，<br>被<span class="highlight-word">好好听见。</span></h2><p>也许是一点想念，也许是一点委屈。<br>从认识感受开始，让彼此靠近一点。</p><button class="primary" @click="router.push('/communication')">开始一次沟通 <Icon name="arrow" :size="19"/></button><span class="hero-footnote">从一句话开始，就很好。</span></div><div class="hero-art"><span class="hero-halo"></span><span class="orbit orbit-one"></span><span class="orbit orbit-two"></span><Icon class="spark spark-one" name="sparkle" :size="26"/><Icon class="spark spark-two" name="sparkle" :size="18"/><span class="pet-bubble">每一种感受，都有它的光。</span><Pet :wave="true"/><span class="ground"></span><span class="art-caption"><i></i> XIAODENG / 你的小小表达伙伴</span></div></section>
          <div class="section-heading"><div><p class="eyebrow">FIND YOUR OWN WAY</p><h2>今天，想从哪里开始？</h2></div><span>按你的节奏，自由选择</span></div>
          <section class="feature-grid">
            <RouterLink to="/communication" class="feature-card peach"><div class="card-top"><span class="feature-icon"><Icon name="chat"/></span><span class="card-index">01 / CONNECT</span></div><FeatureArt kind="chat"/><h3>亲子沟通翻译</h3><p>在同一个空间里，把想说的话<br>说清楚，把彼此的心意听明白。</p><span class="card-bottom">一起聊一聊 <Icon name="arrow" :size="20"/></span></RouterLink>
            <RouterLink to="/stories" class="feature-card sage"><div class="card-top"><span class="feature-icon"><Icon name="book"/></span><span class="card-index">02 / DISCOVER</span></div><FeatureArt kind="book"/><h3>小灯故事</h3><p>走进一个小故事，<br>也许会遇见和你相似的感受。</p><span class="card-bottom">听一个故事 <Icon name="arrow" :size="20"/></span></RouterLink>
            <RouterLink to="/practice" class="feature-card lavender"><div class="card-top"><span class="feature-icon"><Icon name="practice"/></span><span class="card-index">03 / PRACTICE</span></div><FeatureArt kind="practice"/><h3>模拟场景练习</h3><p>在安心的练习里试着开口，<br>为现实中的对话多准备一点。</p><span class="card-bottom">先练习一下 <Icon name="arrow" :size="20"/></span></RouterLink>
          </section>
          <section class="gentle-note"><span class="note-icon"><Icon name="sun" :size="27"/></span><div><strong>不需要一次就说得很好</strong><p>你可以先听故事，也可以直接沟通，或者只练习一句话。这里没有规定的顺序。</p></div><span class="note-decoration">～</span></section>
        </template>
        <template v-else-if="page === '/communication'">
          <div v-if="!room" class="page-heading"><p class="eyebrow">CONNECT · 听见彼此</p><h1>把心里的话，好好说。</h1><p class="subtitle">孩子与家长进入同一次沟通，让表达更清楚，让理解更靠近。</p></div>
          <div v-if="!room" class="workspace two-columns"><section class="panel"><h2>和对方进入同一次沟通</h2><div class="logged-role"><Icon :name="authSession.user?.role === 'child' ? 'sun' : 'heart'" :size="22"/><span>当前以{{ authSession.user?.role === 'child' ? '孩子' : '家长' }}身份沟通</span></div><h3>开启一个沟通空间</h3><p class="muted">创建后，把邀请码分享给对方。</p><button class="primary" :disabled="busy" @click="enter()">{{ busy ? '正在准备…' : '创建沟通空间 ↗' }}</button><div class="divider">或加入对方的空间</div><label for="invite">沟通邀请码</label><input id="invite" v-model="code" placeholder="输入对方分享的邀请码" maxlength="12" :disabled="busy"><button class="secondary full" :disabled="busy" @click="enter(true)">加入沟通</button></section><section v-if="!isParent" class="companion-panel"><Pet/><h3>先听见，再理解。</h3><p>说出你的感受，也给对方一点表达的空间。<br>每条消息由你确认后发出。</p><p v-if="isMock" class="demo-explain">当前使用预设消息演示，不会连接另一台设备。双端通信将在接入后端后启用。</p></section><section v-else class="parent-room-note panel"><Icon name="heart" :size="25"/><h3>先听见，再回应。</h3><p>可以先确认孩子想表达什么，再说出你的感受和期待。</p><p v-if="isMock" class="demo-explain">当前为本机预设消息演示。连接孩子的真实设备，需要接入后端。</p></section></div>
          <ChatRoom v-else :messages="messages" :role="role" :invite="invite" :mock="isMock" :busy="busy" :translated="translated" :error="error" :notice="notice" :translated-draft="translatedDraft" :translate-step="translateStep" v-model:draft="draft" v-model:confirmed="confirmed" @send="send" @translate="translate" @cancel-translate="cancelTranslate" @update:translated-draft="translatedDraft = $event" @leave="leaveRoom" @copy-invite="copy(invite)" @use-example="useExample" @incoming="previewIncomingMessage" @cancel="cancel" @dismiss-error="error = ''" @dismiss-notice="notice = ''"/>
        </template>
        <template v-else-if="page === '/stories'">
          <div class="page-heading"><p class="eyebrow">DISCOVER · 走进一个故事</p><h1>在故事里，遇见感受。</h1><p class="subtitle">不急着说自己。先陪小灯，看看故事里的那个小伙伴。</p></div>
          <section v-if="!storyOpen" class="story-cover"><div class="story-illustration"><span class="moon">☾</span><span class="star-a">✧</span><span class="star-b">✦</span><Pet/><span class="story-land"></span></div><div class="story-description"><span class="pill">原创示例 · 约 2 分钟阅读</span><h2>等电话的小灯</h2><p>小灯把想说的话写在纸上，一张又一张。<br>今晚，远方的电话会响起来吗？</p><div class="story-tags"><span>想念</span><span>表达需要</span><span>亲子关系</span></div><button class="primary" @click="storyOpen = true">打开这个故事 ↗</button><small class="muted block">暂用固定故事演示；故事来源方案由团队确认。</small></div></section>
          <section v-else class="panel reading-panel"><button class="text-button" @click="storyOpen = false; stopAudio()">← 返回故事列表</button><div class="reading-title"><span class="eyebrow">小灯的故事 · 01</span><h2>等电话的小灯</h2><button class="secondary" @click="readStory">{{ reply ? '■ 停止朗读' : '▷ 设备语音朗读' }}</button><p class="hint">使用设备自带语音，音色和可用性因设备而异。</p></div><div class="story-text"><p>窗台上的小灯亮起来了。小鹿坐在桌边，把今天想说的话写在一张纸上：美术课画了星星，操场边开了小花，还有午饭时没讲完的笑话。</p><p>爸爸妈妈在很远的地方工作。小鹿拿起电话，又轻轻放下。“他们会不会很忙呢？”纸上的字越来越多，心里却有一点空。</p><p>小灯晃了晃暖暖的光。“想念可以说出来呀。你不用猜他们什么时候有空，也不用假装自己不想念。”</p><p>小鹿想了想，在纸上写下：“我有点想你们了。我们可以约一个时间，聊聊今天的事吗？”</p><p>那天，电话没有立刻响起。但小鹿发现，自己终于知道想说什么了。窗边的小灯，还在安安静静地亮着。</p></div><StoryReflection @practice="storyToPractice"/><div class="reading-actions"><button class="secondary" @click="storyToCommunication">我自己也有话想说 ↗</button><button class="text-button" @click="storyOpen = false; stopAudio()">读完了，返回故事</button></div></section>
        </template>
        <template v-else-if="page === '/practice'">
          <div class="page-heading"><p class="eyebrow">PRACTICE · 给开口一点勇气</p><h1>先在这里，试着说一次。</h1><p class="subtitle">这是模拟练习，角色不是真实家人或朋友。你可以随时结束。</p></div>
          <section v-if="practiceSeed && !started" class="story-practice-context" aria-label="从故事带入的练习"><strong>这次，先帮故事里的小鹿练习</strong><p>你刚整理的这句话已带过来，开始后可以继续修改：</p><blockquote>{{ practiceSeed }}</blockquote><p class="hint">这是角色表达，不代表你的个人经历。练习回应仍为当前模式的演示内容。</p><button class="text-button" @click="practiceSeed = ''">清除这句话，自己选择场景</button></section><template v-if="!started"><div class="scene-grid"><button v-for="s in scenes" :disabled="!!practiceSeed && s.id !== 'missing'" class="scene-card" :class="{ selected: scene === s.id }" @click="scene = s.id"><span class="feature-icon"><Icon :name="s.icon" :size="28"/></span><span class="scene-label">{{ s.label }}</span><h3>{{ s.title }}</h3><p>{{ s.desc }}</p><span class="scene-choice">{{ scene === s.id ? '已选择 ✓' : '选择场景 ↗' }}</span></button></div><section class="practice-intro"><div class="practice-pet"><Pet/></div><div><h3>不用完美表达，只要开始就好。</h3><p>{{ isMock ? '演示仅开放“想和爸妈聊一会儿”，提供两轮固定角色回应。' : `将进入「${currentScene.title}」模拟对话。` }}</p></div><button class="primary" :disabled="busy || (isMock && scene !== 'missing')" @click="startPractice">{{ busy ? '准备中…' : '开始练习 ↗' }}</button></section></template>
          <section v-else class="panel practice-chat"><div class="room-heading"><div><strong>{{ practiceSeed ? '帮小鹿练习表达' : currentScene.title }}</strong><p>模拟角色 · 已完成 {{ turns }} / 2 轮</p><div class="turn-progress" aria-hidden="true"><i :class="{ complete: turns >= 1 }"></i><i :class="{ complete: turns >= 2 }"></i></div></div><button class="text-button" @click="exitPractice">结束并退出</button></div><p v-if="isMock" class="demo-explain">预设演示：角色回复固定，不会根据你输入的内容生成回应。</p><div class="chat-log" aria-live="polite"><article v-for="(m, i) in conversation" :key="i" class="message" :class="{ own: m.role === '我' }"><small>{{ m.role === '我' ? '我' : '练习角色' }}</small><p>{{ m.text }}</p></article></div><div v-if="feedback" class="feedback"><span>✦ 这次练习的小收获</span><p>{{ feedback }}</p><p class="hint">{{ isMock ? '以上为预设反馈示例，并非对你输入的评估。' : '选择适合你的建议即可。' }}</p><button class="primary" @click="router.push('/communication')">准备和对方聊聊 ↗</button><button class="text-button" @click="exitPractice">重新选择场景</button></div><form v-else class="composer" @submit.prevent="practiceSend"><label for="practice">你想怎么回答？</label><textarea id="practice" v-model="practiceText" rows="3" placeholder="试着表达你的感受和期待…" :disabled="busy"></textarea><div class="composer-bottom"><small>{{ Array.from(practiceText).length }} / 500</small><button class="primary" :disabled="busy || !practiceText.trim() || Array.from(practiceText).length > 500">{{ busy ? '等待回应…' : '发送 ↑' }}</button></div></form></section>
        </template>
        <div v-if="busy && !room" class="status-bar" role="status">正在连接，请稍等… <button class="text-button" @click="cancel">取消</button></div>
        <div v-if="error && !room" class="error-banner" role="alert">{{ error }} <button class="text-button" @click="error = ''">关闭</button></div>
        <div v-if="notice && !room" class="notice-banner" role="status">{{ notice }} <button class="text-button" @click="notice = ''">知道了</button></div>
        <footer><span>话外 · 让每一份心意，都有回响</span><button @click="help = true">需要一点现实中的支持？ ↗</button></footer>
      </div>
    </main>
    <nav class="mobile-nav"><RouterLink v-for="tab in tabs" :to="tab.path" :class="{ active: page === tab.path }"><Icon :name="tab.icon" :size="23"/>{{ tab.text }}</RouterLink></nav>
    <div v-if="help" class="modal-backdrop" @click.self="help = false"><section class="support-modal" role="dialog" aria-modal="true" aria-labelledby="support-title"><button class="modal-close" aria-label="关闭" @click="help = false">×</button><span class="feature-icon"><Icon name="heart" :size="25"/></span><h2 id="support-title">我们注意到你可能正在经历很困难的时刻。请先暂停一下，联系你信任的人聊聊。</h2><div class="support-section support-section--urgent"><p class="hotline">北京市心理援助热线：010-82951332</p><p class="hotline">全国青少年心理咨询热线：12355</p></div><button class="primary" @click="help = false">先照顾好自己</button><small>话外用于沟通支持与练习，不提供心理诊断。如有需要，请寻求专业帮助。</small></section></div>
    </template>
  </div>
</template>
