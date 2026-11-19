<script setup lang="ts">
import Icon from './Icon.vue'
import FeatureArt from './FeatureArt.vue'
defineEmits<{ create: []; join: [] }>()
</script>
<template>
  <section class="parent-home">
    <div class="page-heading"><p class="eyebrow">话外 · 家长端</p><h1>听见孩子，也让孩子听见你。</h1><p class="subtitle">从一次耐心的倾听开始，把彼此想说的话说清楚。</p></div>
    <section class="parent-welcome"><span class="pill"><Icon name="heart" :size="17"/> 给彼此一点理解的空间</span><FeatureArt kind="chat"/><h2>开启一次亲子沟通</h2><p>你和孩子进入同一个空间，借助表达翻译，更好地理解彼此。</p><button class="primary" @click="$emit('create')">创建沟通空间<Icon name="arrow" :size="19"/></button><p class="hint">创建后，将邀请码分享给孩子。</p></section>
    <button class="parent-join panel" @click="$emit('join')"><span class="parent-join-icon"><Icon name="chat" :size="26"/></span><span><strong>孩子已经发来邀请码？</strong><span>输入邀请码，加入这次沟通。</span></span><Icon name="arrow" :size="21"/></button>
    <section class="parent-tips"><h2>开始前，给彼此一点时间</h2><div><span>01</span><p>先听完孩子想说的话，再表达自己的想法。</p></div><div><span>02</span><p>翻译是帮助理解的参考，你仍可以保留自己的表达。</p></div><div><span>03</span><p>每一条消息，都由你确认后再发送。</p></div></section>
  </section>
</template>
