<script setup lang="ts">
defineProps<{ kind: 'chat' | 'book' | 'practice' }>()
</script>
<template>
  <svg class="feature-art" viewBox="0 0 260 150" fill="none" aria-hidden="true">
    <template v-if="kind === 'chat'">
      <ellipse cx="130" cy="134" rx="75" ry="6" fill="#b9a080" opacity=".12"/>
      <g transform="rotate(-8 105 60)"><rect x="39" y="23" width="121" height="76" rx="20" fill="#fffdf7" stroke="#c5ab8b" stroke-width="1.5"/><path d="m63 97-6 16 25-14" fill="#fffdf7"/><path d="m63 97-6 16 25-14" stroke="#c5ab8b" stroke-width="1.5"/><path d="M62 47h68M62 60h46" stroke="#d5c4af" stroke-width="5" stroke-linecap="round"/></g>
      <g transform="rotate(6 171 99)"><rect x="122" y="69" width="99" height="57" rx="17" fill="#a0b49b" stroke="#789174" stroke-width="1.5"/><path d="m198 123 8 13-25-11" fill="#a0b49b"/><path d="m198 123 8 13-25-11" stroke="#789174" stroke-width="1.5"/><path d="m150 94 8 8 19-19" stroke="#fffdf7" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></g>
      <path d="m208 30 2-7 3 7 7 2-7 3-3 7-2-7-7-3 7-2Z" fill="#dca564"/>
    </template>
    <template v-else-if="kind === 'book'">
      <ellipse cx="130" cy="134" rx="77" ry="6" fill="#789174" opacity=".12"/>
      <path d="m130 51-65-15-12 80 77 16 77-16-12-80-65 15Z" fill="#94aa8f" stroke="#71876e" stroke-width="1.5"/>
      <path d="M130 46C107 29 80 26 61 29l-7 78c30-2 55 5 76 20 21-15 46-22 76-20l-7-78c-19-3-46 0-69 17Z" fill="#fffdf5" stroke="#b9b8a2" stroke-width="1.5"/>
      <path d="M130 47v78M77 49c14 1 25 5 36 10M75 64c14 1 25 5 36 10M73 80c14 1 25 5 36 10" stroke="#d8d8c3" stroke-width="3" stroke-linecap="round"/>
      <path d="m164 51 5 10 11 2-8 8 2 11-10-6-10 6 2-11-8-8 11-2 5-10Z" fill="#edcc80" stroke="#d3b16a"/>
      <path d="m175 19 3-8 3 8 8 3-8 3-3 8-3-8-8-3 8-3Z" fill="#e4c47d"/><path d="M150 91h32" stroke="#dedcc8" stroke-width="3" stroke-linecap="round"/>
    </template>
    <template v-else>
      <ellipse cx="131" cy="135" rx="72" ry="6" fill="#a2aabc" opacity=".15"/>
      <g transform="rotate(-10 106 81)"><rect x="66" y="23" width="99" height="108" rx="11" fill="#edf0f5" stroke="#a6b3c5" stroke-width="1.5"/><path d="M85 48h47M85 62h32" stroke="#bfcad8" stroke-width="4" stroke-linecap="round"/></g>
      <g transform="rotate(8 156 86)"><rect x="112" y="39" width="89" height="91" rx="11" fill="#fffdf5" stroke="#b8b5a7" stroke-width="1.5"/><circle cx="157" cy="80" r="19" fill="#e9c77f"/><path d="m149 80 6 6 11-13" stroke="#fffdf5" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><path d="M137 112h40" stroke="#ded9c9" stroke-width="3" stroke-linecap="round"/></g>
      <path d="m47 48 2-7 3 7 7 2-7 3-3 7-2-7-7-3 7-2Z" fill="#b4c1ce"/>
    </template>
  </svg>
</template>
