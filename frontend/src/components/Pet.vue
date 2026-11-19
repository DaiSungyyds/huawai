<script setup lang="ts">
import { selectedCompanion } from '../state/companions'
defineProps<{ wave?: boolean }>()
</script>

<template>
  <span class="pet lamp-mascot" :class="{ 'lamp-mascot--greeting': wave }" role="img" :aria-label="`${selectedCompanion.name}，${selectedCompanion.kind}`">
    <span class="lamp-mascot__glow" aria-hidden="true"></span>
    <img class="lamp-mascot__image" :src="selectedCompanion.src" alt="" width="1024" height="1024" decoding="async">
  </span>
</template>

<style scoped>
.lamp-mascot { position: relative; display: inline-block; isolation: isolate; vertical-align: middle; }
.lamp-mascot__image { position: relative; display: block; width: 100%; height: 100%; object-fit: contain; transform-origin: 50% 85%; animation: lamp-breathe 4.8s ease-in-out infinite; }
.lamp-mascot__glow { position: absolute; inset: 8% 10% 20%; border-radius: 50%; background: radial-gradient(ellipse, #f7dc8e55 0%, #ffe9ac1a 48%, transparent 72%); animation: lamp-light 4.8s ease-in-out infinite; pointer-events: none; }
.lamp-mascot--greeting .lamp-mascot__image { animation: lamp-greeting 5s ease-in-out infinite; }
@keyframes lamp-breathe { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-3px); } }
@keyframes lamp-greeting { 0%, 65%, 100% { transform: rotate(0); } 15%, 40% { transform: rotate(-2deg); } 28%, 53% { transform: rotate(2deg); } }
@keyframes lamp-light { 0%, 100% { opacity: .55; } 50% { opacity: 1; } }
@media (prefers-reduced-motion: reduce) { .lamp-mascot__image, .lamp-mascot__glow { animation: none; } }
</style>
