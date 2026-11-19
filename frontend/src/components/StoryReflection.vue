<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import Pet from './Pet.vue'
import { selectedCompanion } from '../state/companions'
import Icon from './Icon.vue'
const emit = defineEmits<{ practice: [text: string] }>()
const feeling = ref(''), need = ref(''), expression = ref(''), composed = ref(false), copyStatus = ref('')
const resultPanel = ref<HTMLElement | null>(null)
async function revealResult() {
  await nextTick()
  resultPanel.value?.focus({ preventScroll: true })
  resultPanel.value?.scrollIntoView({ block: 'nearest', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' })
}
const complete = computed(() => !!feeling.value && !!need.value)
const feelingResponse: Record<string, string> = {
  '想念': '你看见了小鹿的想念。想和在乎的人靠近，是可以说出来的。',
  '有点失落': '你留意到了小鹿的失落。等不到电话时，心里空一点也很自然。',
  '担心打扰': '你发现小鹿在担心打扰。可以先问问对方什么时候方便，不必把话一直藏起来。',
  '不确定': '暂时说不清感受也没关系，我们可以先从小鹿希望发生什么开始。',
}
const needResponse: Record<string, string> = {
  '约时间聊聊': '约一个双方方便的时间，会让这份期待更具体。',
  '被认真听见': '比起立刻得到答案，小鹿也许更希望有人认真听完。',
  '一点陪伴': '一点陪伴不一定要很久，也可以是分享今天的一件小事。',
  '不确定': '需要也可以慢慢想。先试着说“我想和你聊聊”，就已经迈出了一步。',
}
const response = computed(() => [feelingResponse[feeling.value], needResponse[need.value]].filter(Boolean).join(''))
function compose() {
  if (!complete.value) return
  const starts: Record<string,string> = {
    '想念': '我有点想你们了。', '有点失落': '没能和你们聊上，我有一点失落。',
    '担心打扰': '我想和你们聊聊，又有点担心打扰你们。', '不确定': '我还不太知道怎么形容现在的感受。',
  }
  const requests: Record<string,string> = {
    '约时间聊聊': '我们可以约一个方便的时间，聊聊今天的事吗？',
    '被认真听见': '你们方便的时候，可以认真听我说说今天的事吗？',
    '一点陪伴': '你们方便的时候，可以陪我聊一小会儿吗？',
    '不确定': '我想先和你们聊一聊，可以吗？',
  }
  expression.value = starts[feeling.value] + requests[need.value]
  composed.value = true; copyStatus.value = ''; void revealResult()
}
function skip() {
  feeling.value = ''; need.value = ''
  // Selection watchers run synchronously; then show a neutral, unselected example.
  expression.value = '我想和你们说说今天的事，我们可以找个方便的时间聊聊吗？'
  composed.value = true; copyStatus.value = ''; void revealResult()
}
watch([feeling, need], () => { composed.value = false; expression.value = ''; copyStatus.value = '' }, { flush: 'sync' })
async function copy() {
  try { await navigator.clipboard.writeText(expression.value.trim()); copyStatus.value = '已复制这句话。' }
  catch { copyStatus.value = '复制未成功，请在输入框中长按或选中文字手动复制。' }
}
</script>

<template>
  <section class="reflection" aria-labelledby="reflection-title">
    <div class="reflection-heading"><h3 id="reflection-title">陪小鹿想一想</h3><span class="reflection-step">{{ composed ? '把感受说出来' : '先发现感受与需要' }}</span></div>
    <p id="feeling-question">你觉得小鹿可能有什么感受？没有标准答案。</p>
    <div class="chips" role="group" aria-labelledby="feeling-question"><button v-for="item in ['想念', '有点失落', '担心打扰', '不确定']" :key="item" :aria-pressed="feeling === item" :class="{ selected: feeling === item }" @click="feeling = item">{{ item }}</button></div>
    <p id="need-question">小鹿可能希望得到什么？</p>
    <div class="chips" role="group" aria-labelledby="need-question"><button v-for="item in ['约时间聊聊', '被认真听见', '一点陪伴', '不确定']" :key="item" :aria-pressed="need === item" :class="{ selected: need === item }" @click="need = item">{{ item }}</button></div>
    <p class="hint">这些是对故事角色的理解，不代表你的个人情况。</p>
    <div v-if="response" class="reflection-response" aria-live="polite"><Pet/><div><strong>{{ selectedCompanion.name }}想说</strong><p>{{ response }}</p></div></div>
    <div v-if="!composed" class="reflection-next"><p class="reflection-progress" role="status">{{ complete ? '感受和需要都找到了，接下来帮小鹿说一句话吧。' : feeling ? '再选一个小鹿可能的需要，就可以整理一句话。' : need ? '再选一种可能的感受，也可以选“不确定”。' : '选一选，小灯会陪你把感受整理成一句话。' }}</p><div class="reading-actions"><button class="primary" :disabled="!complete" @click="compose">帮小鹿整理一句话 <Icon name="arrow" :size="18"/></button><button class="text-button" @click="skip">跳过选择，看看表达示例</button></div></div>
    <section v-else ref="resultPanel" tabindex="-1" class="story-expression" aria-labelledby="expression-title">
      <div class="expression-heading"><Icon name="sparkle" :size="21"/><h3 id="expression-title">原来，可以这样说</h3></div>
      <p>这是一句给小鹿的表达示例。你可以改成更贴近故事的说法。</p>
      <label for="story-expression">帮小鹿说的话</label><textarea id="story-expression" v-model="expression" rows="4" aria-describedby="expression-note"></textarea>
      <p id="expression-note" class="hint">本地预设内容组合，不是 AI 分析；不会自动发送给任何人。</p>
      <p v-if="Array.from(expression).length > 500" class="expression-error" role="alert">请把这句话缩短到 500 字以内，再去练习。</p>
      <div class="reading-actions"><button class="primary" :disabled="!expression.trim() || Array.from(expression).length > 500" @click="emit('practice', expression.trim())">帮小鹿练习这句话 <Icon name="arrow" :size="18"/></button><button class="secondary" :disabled="!expression.trim()" @click="copy">复制这句话</button></div>
      <p v-if="copyStatus" class="hint" role="status">{{ copyStatus }}</p>
    </section>
  </section>
</template>
