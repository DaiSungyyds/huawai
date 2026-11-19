# 话外项目优化方案

## 一、问题诊断与现状分析

### 1.1 已识别问题

| 问题 | 位置 | 当前状态 | 优先级 |
|------|------|----------|--------|
| 原话可见性控制缺失 | `ChatMessage.vue:17` | 双方均可查看对方原话 | P0 |
| "消息同步中断"提示 | `App.vue:82` | 轮询失败时显示 | P1 |
| 改写延迟约1分钟 | `server.py:65` + `paratera.py` | 同步阻塞调用 | P0 |
| 发送前确认流程 | `ChatRoom.vue:62-67` | 已有确认框，但体验待优化 | P1 |
| 安全边界机制 | 全局 | 部分实现，需补全 | P0 |

---

## 二、具体优化方案

### 2.1 原话可见性控制（P0）

**问题描述**：当前 `ChatMessage.vue` 第17行对所有用户显示"看看原话"折叠区域，预期效果是：
- 孩子发送的消息：孩子可看原话，家长不可看
- 家长发送的消息：家长可看原话，孩子不可看

**解决方案**：

```vue
<!-- ChatMessage.vue 修改 -->
<template>
  <article class="chat-message" :class="{ 'chat-message--own': own }">
    <!-- ... 头像部分保持不变 ... -->
    <div class="message" :class="{own}">
      <small>{{ message.role === 'child' ? '孩子' : '家长' }} · 确认后的表达</small>
      <p>{{ message.translated }}</p>
      <!-- 只有消息发送者本人可以看到原话 -->
      <details v-if="own"><summary>看看原话</summary>{{ message.original }}</details>
    </div>
  </article>
</template>
```

**修改文件**：`frontend/src/components/ChatMessage.vue`

**验证方法**：
1. 用两个浏览器分别登录孩子和家长账号
2. 孩子发送消息后，孩子端应能看到"看看原话"
3. 家长端收到消息后，不应看到"看看原话"选项

---

### 2.2 移除"消息同步中断"提示（P1）

**问题描述**：`App.vue:82` 在轮询失败时显示"消息同步暂时中断"，影响用户体验。

**解决方案**：静默处理轮询失败，仅在连续多次失败后提示。

```typescript
// App.vue 修改
let pollFailCount = 0
poll = setInterval(async () => {
  if (syncBusy) return
  syncBusy = true
  try {
    const items = await api.messages(result.roomId, AbortSignal.timeout(10000))
    if (syncId === roomEpoch) messages.value = items
    pollFailCount = 0  // 成功则重置计数
  } catch {
    pollFailCount++
    // 连续5次失败（约12.5秒）后才提示
    if (syncId === roomEpoch && pollFailCount >= 5) {
      notice.value = '连接似乎断开了，可以尝试重新进入沟通。'
    }
  } finally {
    syncBusy = false
  }
}, 2500)
```

**修改文件**：`frontend/src/App.vue`

---

### 2.3 降低改写延迟（P0）

**问题诊断**：
1. 服务端 `paratera.py` 使用同步 HTTP 请求，超时25秒
2. 服务端使用全局 `LOCK` 串行处理所有请求
3. 前端等待服务端改写完成后才显示任何反馈

**优化方案（分层实施）**：

#### 方案 A：前端流式体验优化（推荐优先实施）

让用户在输入时就能看到"正在处理"的状态，而不是等待1分钟后突然出现结果。

```typescript
// App.vue - 发送流程优化
async function send() {
  if (!confirmed.value || !draft.value.trim() || Array.from(draft.value).length > 500) return
  const originalText = draft.value.trim()

  // 立即显示"正在处理"状态
  const tempId = 'pending-' + crypto.randomUUID()
  const pendingMsg: Message = {
    id: tempId,
    role: role.value,
    original: originalText,
    translated: '正在为你润色表达…',
    pending: true,
    ...(role.value === 'child' ? { senderCompanionId: selectedCompanion.value.id } : {})
  }
  messages.value.push(pendingMsg)
  draft.value = ''
  confirmed.value = false

  await run(async (signal, id) => {
    try {
      const message: Message = isMock
        ? { id: crypto.randomUUID(), role: role.value, original: originalText, translated: translated.value, ...(role.value === 'child' ? { senderCompanionId: selectedCompanion.value.id } : {}) }
        : await api.send(room.value, role.value, originalText, crypto.randomUUID(), signal, role.value === 'child' ? selectedCompanion.value.id : undefined)

      if (id !== epoch) return
      // 替换 pending 消息为真实消息
      const idx = messages.value.findIndex(m => m.id === tempId)
      if (idx >= 0) messages.value[idx] = message
      else messages.value.push(message)
    } catch (e) {
      // 失败时移除 pending 消息
      messages.value = messages.value.filter(m => m.id !== tempId)
      throw e
    }
  })
}
```

#### 方案 B：后端异步化 + 流式响应

```python
# server.py - 使用异步处理
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)

async def async_chat(messages):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, chat, messages)

# 或者使用流式响应
def chat_stream(messages):
    """流式返回改写结果"""
    # 修改 paratera.py 支持 stream=True
    # 逐块返回，前端逐字显示
    pass
```

#### 方案 C：优化 LLM 调用参数

```python
# paratera.py - 降低 max_tokens 和 timeout
body = json.dumps({
    'model': model,
    'messages': messages,
    'stream': False,
    'max_tokens': 200,  # 从800降低，改写不需要太长
    'temperature': 0.7
}).encode()

# 超时从25秒降低
with urllib.request.urlopen(req, timeout=15) as response:
```

#### 方案 D：前端预翻译 + 后端确认

```typescript
// 使用本地轻量级模型或规则做预翻译
// 后端返回后替换为正式翻译
function quickLocalRewrite(text: string): string {
  // 简单的语气词替换、标点调整等
  return text
    .replace(/你们总是/g, '有时候')
    .replace(/都不/g, '可能')
    // ... 更多规则
}
```

**推荐实施顺序**：A → C → B（D 为可选增强）

---

### 2.4 发送前确认转译流程优化（P1）

**当前状态**：已有确认框，但体验可以优化。

**优化方案**：转译完成后自动放入聊天框，用户可编辑后确认发送。

```vue
<!-- ChatRoom.vue - 优化确认流程 -->
<template>
  <!-- ... -->
  <form class="composer" @submit.prevent="emit('send')">
    <div class="composer-fields">
      <!-- 转译预览区域 - 可编辑 -->
      <div v-if="translated && !busy" class="translation-preview">
        <label for="edited">转译后的表达（可修改）</label>
        <textarea
          id="edited"
          v-model="editedTranslation"
          rows="3"
          placeholder="转译结果将显示在这里…"
        ></textarea>
        <small class="hint">如果转译不准确，可以直接修改后再发送</small>
      </div>

      <!-- 原话输入框 -->
      <label class="sr-only" for="raw">想说的原话</label>
      <textarea
        id="raw"
        ref="input"
        v-model="draft"
        :disabled="busy"
        rows="2"
        placeholder="写下你想让对方听见的话…"
        @input="fitInput"
      ></textarea>
    </div>

    <div class="composer-bottom">
      <small>{{ count }} / 500</small>
      <button v-if="busy" type="button" class="secondary" @click="emit('cancel')">取消</button>
      <button v-else class="primary" :disabled="!canSend">
        {{ busy ? '处理中…' : '确认发送 ↑' }}
      </button>
    </div>
  </form>
</template>

<script setup lang="ts">
const editedTranslation = ref('')

// 监听转译结果，自动填入编辑框
watch(() => props.translated, (newVal) => {
  if (newVal && !props.busy) {
    editedTranslation.value = newVal
  }
})

const canSend = computed(() => {
  return props.confirmed && props.draft.trim() && count.value <= 500
})
</script>
```

**后端修改**：支持前端传入自定义的转译文本

```python
# server.py - 允许前端覆盖转译结果
if method=='POST':
    text=field(b,'text')
    client=field(b,'clientMessageId',128)
    # 如果前端提供了自定义转译，直接使用
    custom_translated = b.get('customTranslated')
    if custom_translated and isinstance(custom_translated, str) and custom_translated.strip():
        translated = custom_translated.strip()
    else:
        translated=chat([...])
    # ... 其余逻辑
```

---

## 三、安全边界与风险应对机制评估

### 3.1 现有机制

| 机制 | 位置 | 状态 |
|------|------|------|
| 心理支持弹窗 | `App.vue:191` | ✅ 已实现 |
| 练习场景安全提示 | `server.py:78` | ✅ 已实现 |
| 不提供心理诊断声明 | `App.vue:191` | ✅ 已实现 |
| 退出沟通功能 | `ChatRoom.vue:48` | ✅ 已实现 |

### 3.2 缺失机制与补全方案

#### 3.2.1 心理风险识别（缺失）

**需要实现**：
1. **关键词检测**：识别自伤、自杀、暴力等高风险词汇
2. **情绪分析**：检测极端负面情绪
3. **风险分级响应**

```python
# server.py - 添加安全风险检测
SAFETY_KEYWORDS = {
    'high': ['自杀', '不想活', '自残', '割腕', '去死', '跳楼'],
    'medium': ['抑郁', '焦虑', '失眠', '厌食', '孤独', '绝望'],
    'low': ['难过', '伤心', '生气', '委屈']
}

def check_safety_risk(text: str) -> dict:
    """返回风险等级和建议"""
    text_lower = text.lower()
    for level, keywords in SAFETY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return {
                'risk': level,
                'action': 'show_support_modal' if level == 'high' else 'gentle_reminder',
                'message': get_safety_message(level)
            }
    return {'risk': 'none', 'action': 'continue'}

# 在消息处理前检查
safety_result = check_safety_risk(text)
if safety_result['risk'] == 'high':
    return {'status': 'safety_redirect', 'message': '请先联系信任的人或拨打心理援助热线：400-161-5888'}
```

#### 3.2.2 危机干预转介（部分实现）

**需要补全**：

```vue
<!-- App.vue - 增强支持弹窗 -->
<div v-if="help" class="modal-backdrop" @click.self="help = false">
  <section class="support-modal" role="dialog" aria-modal="true">
    <button class="modal-close" @click="help = false">×</button>
    <span class="feature-icon"><Icon name="heart" :size="25"/></span>
    <h2>你可以找一个信任的人</h2>

    <!-- 新增：分级支持资源 -->
    <div class="support-level">
      <h3>如果你现在很痛苦</h3>
      <p>试着联系信任的家长、老师、学校辅导人员。</p>
    </div>

    <div class="support-level support-level--urgent">
      <h3>如果你正在危机中</h3>
      <p><strong>24小时心理援助热线</strong></p>
      <p class="hotline">400-161-5888</p>
      <p class="hotline">北京心理危机研究与干预中心：010-82951332</p>
      <p>如果你正面临即时危险，请拨打 110 或前往最近医院急诊。</p>
    </div>

    <div class="support-level">
      <h3>如果你想找人聊聊</h3>
      <p>• 12355 青少年服务热线</p>
      <p>• 学校心理咨询室</p>
      <p>• 社区心理辅导站</p>
    </div>

    <button class="primary" @click="help = false">先照顾好自己</button>
    <small>话外用于沟通支持与练习，不提供心理诊断。如有需要，请寻求专业帮助。</small>
  </section>
</div>
```

#### 3.2.3 用户隐私保护（需加强）

**现有问题**：
1. SQLite 数据库文件包含私人对话，仅依赖操作系统权限
2. 前端 localStorage 可能存储敏感信息
3. 缺少数据加密和自动清理机制

**补全方案**：

```python
# server.py - 添加数据保护措施
import sqlite3

# 1. 数据库连接时设置加密（如果使用 SQLCipher）
# 2. 添加消息自动过期机制
def cleanup_old_messages(days=30):
    """清理30天前的消息"""
    cutoff = time.time() - (days * 86400)
    c.execute('DELETE FROM messages WHERE id IN (SELECT id FROM messages WHERE CAST(json_extract(data, "$.timestamp") AS REAL) < ?)', (cutoff,))

# 3. 添加用户数据导出和删除接口
if path=='/api/user/data' and method=='DELETE':
    # 用户请求删除所有个人数据
    c.execute('DELETE FROM messages WHERE user=?', (u['id'],))
    c.execute('DELETE FROM practices WHERE user=?', (u['id'],))
    c.execute('DELETE FROM tokens WHERE user=?', (u['id'],))
    return {'ok': True, 'message': '数据已删除'}
```

```typescript
// frontend - 添加隐私保护提示
// session.ts - 退出时清除所有本地数据
export function signOut() {
  session.user = undefined
  session.token = undefined
  localStorage.removeItem('huawai-session')
  localStorage.removeItem('huawai-companion')
  // 清除所有可能的缓存
  sessionStorage.clear()
}
```

---

## 四、实施计划

### 阶段一（1-2天）：核心问题修复 ✅ 已完成

| 任务 | 文件 | 状态 |
|------|------|------|
| 修复原话可见性 | `ChatMessage.vue` | ✅ 完成 |
| 移除同步中断提示 | `App.vue` | ✅ 完成 |
| 添加 pending 状态显示 | `App.vue`, `ChatMessage.vue` | ✅ 完成 |
| 优化 LLM 调用参数 | `paratera.py` | ✅ 完成 |

### 阶段二（2-3天）：体验优化 ⏳ 部分完成

| 任务 | 文件 | 状态 |
|------|------|------|
| 转译结果可编辑 | `ChatRoom.vue` | ⏳ 待实施 |
| 后端支持自定义转译 | `server.py` | ⏳ 待实施 |
| 流式响应实现 | `paratera.py` + `server.py` | ⏳ 待实施 |

### 阶段三（3-5天）：安全机制补全 ✅ 已完成

| 任务 | 文件 | 状态 |
|------|------|------|
| 关键词风险检测 | `server.py` | ✅ 完成 |
| 增强支持弹窗 | `App.vue`, `style.css` | ✅ 完成 |
| 数据清理机制 | `server.py` | ✅ 完成 |
| 用户数据删除接口 | `server.py`, `client.ts` | ✅ 完成 |
| 退出时清除本地数据 | `session.ts` | ✅ 完成 |

---

## 五、验证清单

### 功能验证

- [ ] 孩子发送消息后，孩子端可看原话，家长端不可看
- [ ] 家长发送消息后，家长端可看原话，孩子端不可看
- [ ] 轮询失败时不再显示"消息同步中断"
- [ ] 发送消息后立即显示"正在处理"状态
- [ ] 转译完成后可在输入框中修改再发送
- [ ] 包含高风险关键词时触发支持弹窗

### 安全验证

- [ ] 输入自伤相关词汇时显示危机干预资源
- [ ] 退出登录后本地不保留任何对话数据
- [ ] 数据库文件权限正确设置
- [ ] 支持弹窗中的热线电话号码正确可拨打

### 性能验证

- [ ] 改写延迟降低到15秒以内
- [ ] 前端无明显卡顿
- [ ] 轮询不会造成明显流量消耗

---

## 六、风险与备选方案

| 风险 | 影响 | 备选方案 |
|------|------|----------|
| Paratera API 响应慢 | 用户体验差 | 考虑切换到更快的模型或本地部署 |
| 关键词检测误报 | 正常对话被拦截 | 使用更精准的 NLP 模型而非关键词 |
| 流式响应兼容性问题 | 部分浏览器不支持 | 保持轮询，优化进度显示 |

---

**文档版本**：v1.1
**创建日期**：2026-11-19
**最后更新**：2026-11-19
**状态**：阶段一、三已完成，阶段二待实施

## 七、已完成修改清单

### 已修改文件

| 文件 | 修改内容 |
|------|----------|
| `frontend/src/components/ChatMessage.vue` | 原话仅发送者可见，pending 状态样式 |
| `frontend/src/App.vue` | 移除同步中断提示，pending 消息状态，安全风险处理，增强支持弹窗 |
| `frontend/src/api/client.ts` | Message 接口扩展，deleteUserData API |
| `frontend/src/state/session.ts` | 退出时清除本地数据 |
| `frontend/src/style.css` | pending 动画，支持弹窗样式 |
| `server.py` | 安全风险检测，数据清理机制，用户数据删除接口 |
| `paratera.py` | 优化 LLM 调用参数（max_tokens: 300, timeout: 15s） |

### 功能验证清单

- [ ] 孩子发送消息后，孩子端可看原话，家长端不可看
- [ ] 家长发送消息后，家长端可看原话，孩子端不可看
- [ ] 轮询失败时不再立即显示"消息同步中断"
- [ ] 发送消息后立即显示"正在为你润色表达…"状态
- [ ] 包含高风险关键词时触发支持弹窗
- [ ] 退出登录后本地数据被清除
