import { session } from '../state/session'
export const isMock = import.meta.env.VITE_USE_MOCK !== 'false'
const base = (import.meta.env.VITE_API_BASE || '/api').replace(/\/$/, '')
export interface TranslateResult { original: string; translated: string; safetyAlert?: boolean; riskLevel?: 'none' | 'medium' | 'high' }
export interface Message { id: string; role: 'child' | 'parent'; original: string; translated: string; senderCompanionId?: string; pending?: boolean; safetyAlert?: boolean; riskLevel?: 'none' | 'medium' | 'high' }
export interface Room { roomId: string; inviteCode: string }
export interface Practice { sessionId: string; reply: string; turn: number; done: boolean; feedback?: string }
export async function request<T>(path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  const timeout = AbortSignal.timeout(30000)
  const response = await fetch(`${base}${path}`, { method: body === undefined ? 'GET' : 'POST', headers: { 'Content-Type': 'application/json', ...(session.token ? { Authorization: `Bearer ${session.token}` } : {}) }, body: body === undefined ? undefined : JSON.stringify(body), signal: signal ? AbortSignal.any([signal, timeout]) : timeout })
  const payload = await response.json().catch(() => null)
  if (!response.ok) throw new Error(payload?.message || payload?.error?.message || `服务暂时不可用（${response.status}）`)
  if (payload?.status === 'safety_redirect') throw new Error(payload?.data?.message || '请暂停练习，联系你信任的成年人。')
  return (payload?.data ?? payload) as T
}
// 以下为前端建议合同，尚未与两位后端成员冻结；真实接口集中在此适配。
export const api = {
  createRoom: (role: string, signal: AbortSignal) => request<Room>('/communication/rooms', { role }, signal),
  joinRoom: (inviteCode: string, role: string, signal: AbortSignal) => request<Room>('/communication/rooms/join', { inviteCode, role }, signal),
  // 转译接口：只做转译，不保存消息
  translate: (text: string, signal: AbortSignal) => request<TranslateResult>('/translate', { text }, signal),
  // 发送消息：支持传入自定义的 translated 文本
  send: (roomId: string, role: string, text: string, clientMessageId: string, signal: AbortSignal, senderCompanionId?: string, translated?: string) => request<Message>(`/communication/rooms/${encodeURIComponent(roomId)}/messages`, { role, text, clientMessageId, translated, ...(role === 'child' && senderCompanionId ? { senderCompanionId } : {}) }, signal),
  messages: (roomId: string, signal: AbortSignal) => request<Message[]>(`/communication/rooms/${encodeURIComponent(roomId)}/messages`, undefined, signal),
  practiceStart: (sceneId: string, signal: AbortSignal) => request<Practice>('/practice/start', { sceneId }, signal),
  practiceReply: (sessionId: string, text: string, clientMessageId: string, signal: AbortSignal) => request<Practice>('/practice/reply', { sessionId, text, clientMessageId }, signal),
  practiceExit: (sessionId: string) => request('/practice/exit', { sessionId }),
  deleteUserData: (signal?: AbortSignal) => request<{ ok: boolean; message: string }>('/user/data', undefined, signal),
}

// 删除用户数据的特殊请求（使用 DELETE 方法）
export async function deleteUserData(signal?: AbortSignal): Promise<{ ok: boolean; message: string }> {
  const timeout = AbortSignal.timeout(30000)
  const response = await fetch(`${base}/user/data`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
      ...(session.token ? { Authorization: `Bearer ${session.token}` } : {})
    },
    signal: signal ? AbortSignal.any([signal, timeout]) : timeout
  })
  const payload = await response.json().catch(() => null)
  if (!response.ok) throw new Error(payload?.message || `服务暂时不可用（${response.status}）`)
  return payload?.data ?? payload
}
