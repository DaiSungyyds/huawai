<script setup lang="ts">
import { computed, ref } from 'vue'
import { companions, selectedCompanionId, selectCompanion, type CompanionId } from '../state/companions'
import Icon from './Icon.vue'
const emit = defineEmits<{ complete: [] }>()
const candidate = ref<CompanionId>(selectedCompanionId.value)
const preview = computed(() => companions.find(c => c.id === candidate.value)!)
function confirm() { selectCompanion(candidate.value); emit('complete') }
</script>
<template>
  <section class="picker-page">
    <p class="eyebrow">选一个喜欢的开始</p><h1>谁来陪你练习表达？</h1><p class="subtitle">只是喜欢就很好。之后可以在“我的”里更换。</p>
    <div class="companion-preview" :style="{background:preview.color}" aria-live="polite"><span class="preview-orbit"></span><img :key="preview.id" :src="preview.src" :alt="preview.kind" width="240" height="240"><h2>{{ preview.name }}<span>{{ preview.kind }}</span></h2><p>{{ preview.description }}</p></div>
    <div class="companion-options" role="group" aria-label="选择表达伙伴"><button v-for="item in companions" :key="item.id" :class="{selected:candidate === item.id}" :aria-pressed="candidate === item.id" :aria-label="`${item.name}，${item.kind}`" @click="candidate = item.id"><span class="companion-option-art" :style="{background:item.color}"><img :src="item.src" alt="" width="104" height="104"><span v-if="candidate === item.id" class="choice-tick"><Icon name="check" :size="15"/></span></span><strong>{{ item.name }}</strong><span>{{ item.kind }}</span></button></div>
    <div class="picker-confirm"><button class="primary" @click="confirm">就选{{ preview.name }}，一起开始<Icon name="arrow" :size="18"/></button><p>形象只改变展示，不影响功能和回应。</p></div>
  </section>
</template>
