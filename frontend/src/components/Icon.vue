<script setup lang="ts">
withDefaults(defineProps<{ name: string; size?: number }>(), { size: 22 })
const paths: Record<string, string[]> = {
  home: ['m3 10 9-7 9 7', 'M5 9v11h5v-6h4v6h5V9'],
  chat: ['M21 11.5a8.5 8.5 0 0 1-8.5 8.5H5l-3 2v-8.5A8.5 8.5 0 0 1 10.5 5H13', 'M14 3h7v7h-4l-3 2V3', 'M7 12h5M7 15h8'],
  book: ['M12 6C9 3 5 3 2 4v15c3-1 7-1 10 2 3-3 7-3 10-2V4c-3-1-7-1-10 2Z', 'M12 6v15M5 8l4 1M5 12l4 1M15 9l4-1M15 13l4-1'],
  practice: ['M7 3h10a2 2 0 0 1 2 2v15H5V5a2 2 0 0 1 2-2Z', 'M9 2h6v4H9z', 'm9 12 2 2 4-4M9 17h6'],
  arrow: ['M5 12h14m-5-5 5 5-5 5'],
  diagonal: ['M6 18 18 6M6 6h12v12'],
  heart: ['M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z'],
  sun: ['M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8ZM12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5 19 19M5 19l1.5-1.5M17.5 6.5 19 5'],
  lamp: ['M8 3h8l4 10H4L8 3ZM12 13v7M7 21h10', 'M9 9h.01M15 9h.01M10 11h4'],
  phone: ['M7 3h10v18H7zM10 18h4M10 6h4'],
  friend: ['M9 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM3 20v-2a6 6 0 0 1 12 0v2M17 5a3 3 0 0 1 0 6M18 14a5 5 0 0 1 3 4v2'],
  check: ['m5 12 4 4L19 6'],
  sparkle: ['m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5L12 3Z'],
}
</script>
<template><svg :width="size" :height="size" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" class="icon"><path v-for="(d, index) in paths[name] || paths.sparkle" :key="index" :d="d" /></svg></template>
