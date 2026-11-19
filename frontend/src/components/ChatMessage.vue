<script setup lang="ts">
import { computed } from 'vue'
import type { Message } from '../api/client'
import { companions } from '../state/companions'
import Icon from './Icon.vue'
const props = defineProps<{ message: Message; viewerRole: 'child' | 'parent' }>()
// Resolve only the sender's allowlisted ID. Never read this device's selected companion.
const companion = computed(() => companions.find(c => c.id === props.message.senderCompanionId) ?? companions[0])
const own = computed(() => props.message.role === props.viewerRole)
</script>
<template>
  <article class="chat-message" :class="{ 'chat-message--own': own, 'chat-message--pending': message.pending }">
    <div class="chat-avatar" :class="{ 'chat-avatar--parent': message.role === 'parent' }" :style="message.role === 'child' ? {background:companion.color} : undefined">
      <img v-if="message.role === 'child'" :src="companion.src" :alt="`孩子的头像：${companion.name}`" width="44" height="44">
      <Icon v-else name="heart" :size="23"/>
    </div>
    <div class="message" :class="{own}"><small>{{ message.role === 'child' ? '孩子' : '家长' }} · 确认后的表达</small><p :class="{ 'pending-text': message.pending }">{{ message.translated }}</p><details v-if="own && !message.pending"><summary>看看原话</summary>{{ message.original }}</details></div>
  </article>
</template>
