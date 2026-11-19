import { reactive } from 'vue'
export interface User { id: string; name: string; role: 'child' | 'parent' }
const demo = import.meta.env.VITE_USE_MOCK !== 'false'
function restoreDemo(): User | null {
  if (!demo) return null
  try { const role = sessionStorage.getItem('huawai.demo.role'); return role === 'child' || role === 'parent' ? { id: `demo-${role}`, name: role === 'child' ? '小朋友' : '家长', role } : null } catch { return null }
}
function restoreReady(): boolean { try { return sessionStorage.getItem('huawai.demo.companionReady') === 'true' } catch { return false } }
export const session = reactive<{ user: User | null; token: string; companionReady: boolean }>({ user: restoreDemo(), token: '', companionReady: demo && restoreReady() })
export function signIn(user: User, token = '') {
  session.user = user; session.token = token; session.companionReady = user.role === 'parent'
  try { sessionStorage.removeItem('huawai.demo.companionReady') } catch { /* Optional demo state. */ }
  if (demo) { try { sessionStorage.setItem('huawai.demo.role', user.role) } catch { /* Tab memory still works. */ } }
}
export function finishCompanionSelection() {
  session.companionReady = true
  if (demo) { try { sessionStorage.setItem('huawai.demo.companionReady', 'true') } catch { /* In-memory state remains ready. */ } }
}
export function signOut() {
  session.user = null; session.token = ''; session.companionReady = false
  // 清除所有会话和本地存储数据
  try {
    sessionStorage.removeItem('huawai.demo.role')
    sessionStorage.removeItem('huawai.demo.companionReady')
    localStorage.removeItem('huawai-session')
    localStorage.removeItem('huawai-companion')
    // 清除所有可能的缓存
    sessionStorage.clear()
  } catch { /* No session is kept in memory. */ }
}
