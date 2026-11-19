import { computed, ref } from 'vue'
export const companions = [
  { id: 'lamp', name: '小灯', kind: '暖心台灯', description: '亮一盏小灯，让心里的话慢慢说。', src: '/static/pet/lamp-mascot-v1.png', color: '#f4ecd5' },
  { id: 'star', name: '小星', kind: '星星抱枕', description: '一点点勇气，也有自己的光。', src: '/static/pet/companion-star.png', color: '#f7edd1' },
  { id: 'cloud', name: '小云', kind: '云朵靠垫', description: '想歇一歇的时候，就慢一点。', src: '/static/pet/companion-cloud.png', color: '#eaf0f1' },
  { id: 'sprout', name: '小芽', kind: '小芽花盆', description: '每一次表达，都是一点新的成长。', src: '/static/pet/companion-sprout.png', color: '#edf0df' },
  { id: 'lantern', name: '小暖', kind: '纸灯笼', description: '把想说的话，放进温暖的光里。', src: '/static/pet/companion-lantern.png', color: '#f4e7dc' },
] as const
export type CompanionId = typeof companions[number]['id']
const preferenceKey = 'huawai.companion.v1'
function savedChoice(): CompanionId {
  try { const id = localStorage.getItem(preferenceKey); return companions.find(c => c.id === id)?.id ?? 'lamp' } catch { return 'lamp' }
}
export const selectedCompanionId = ref<CompanionId>(savedChoice())
export const selectedCompanion = computed(() => companions.find(c => c.id === selectedCompanionId.value) ?? companions[0])
export function selectCompanion(id: CompanionId) {
  selectedCompanionId.value = id
  try { localStorage.setItem(preferenceKey, id) } catch { /* Selection still works in memory. */ }
}
