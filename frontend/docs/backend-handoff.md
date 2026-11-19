# 前端接口交接（建议稿，未冻结）

以用户截图为产品依据。戴晨羲对接双人沟通和翻译；周颖对接故事、模拟与服务整合。建议使用同域 `/api`；路径均集中在 `src/api/client.ts`。

| 请求 | 请求体 | 响应 data |
| --- | --- | --- |
| POST /communication/rooms | role: child 或 parent | roomId, inviteCode |
| POST /communication/rooms/join | inviteCode, role | roomId, inviteCode |
| GET /communication/rooms/:roomId/messages | 无 | Message[] |
| POST /communication/rooms/:roomId/messages | role, text, clientMessageId | Message |
| POST /practice/start | sceneId | Practice |
| POST /practice/reply | sessionId, text, clientMessageId | Practice |
| POST /practice/exit | sessionId | 成功状态 |

Message: `{id: string, role: 'child' | 'parent', original: string, translated: string}`。
Practice: `{sessionId: string, reply: string, turn: number, done: boolean, feedback?: string}`。

可返回对象本身或 `{data: ...}`。非 2xx 提取 `message` 或 `error.message`；安全分流 `{status:'safety_redirect', data:{message:string}}` 中止本次呈现并显示提示，目前未有后端安全样例可验收。下一轮联调须落实独立的安全分流锁定状态，不得将这一错误提示等同完整安全功能。

## 需要后端共同确认

- 房间鉴权、角色凭证、邀请码过期、对方在线状态及退出接口。当前只有 roomId 的建议稿不能用于公开生产。
- 消息采用轮询还是 WebSocket、翻译预览与最终发送是否分为两步、消息去重与翻译失败是否保留原文。当前真实模式确认的是提交原话；若需要翻译后再次确认，应先扩展为 preview/confirm 两阶段接口。
- 正式故事使用固定内容还是生成内容；故事 JSON、正式音频路径与内容审核。
- 模拟场景 ID、每轮状态、结束反馈、异常码与安全分流。

这些接口不是已交付的后端。前端默认演示模式，真实接口必须单独联调验证后交付。

## 登录与形象选择新增合同（未与后端联调）

- 演示模式：预设 `demo_child` / `demo_parent`，页面显示演示登录，不注册真实用户、不发送密码。登录状态仅在当前标签页的 sessionStorage 中保存演示身份和引导完成标志。
- 真实模式：`POST /api/auth/login`，请求 `{account, password, role}`，预期返回 `{data:{user:{id,name,role}, accessToken}}`。仅完整成功响应后进入，失败保留在登录页。真实 token 只保存在内存，刷新需重新登录；后端需要最终确定认证合同、失效和退出策略。
- 其他真实 API 请求会携带 `Authorization: Bearer <accessToken>`。前端路由守卫仅控制页面体验，后端必须独立验证登录状态、角色和房间访问权限。
- 孩子首次进入形象选择，家长直接进入首页。确认后通过共享状态同步所有 Pet；“我的”可换形象或退出。
- 当前形象 ID 仅作为本机展示偏好存入 localStorage，不保存密码、token、原话或模拟对话，也不声称已同步账号。后续如需跨设备，增加用户资料读取与更新接口。

## 沟通消息的孩子头像

Message 增加可选 `senderCompanionId`，值为 `lamp | star | cloud | sprout | lantern`。
孩子发送请求时携带自己的形象 ID，后端需验证该用户身份和形象 ID，并在消息写入、发送响应与消息列表中返回。家长消息不需要此字段。

客户端根据每条消息中的发送者形象 ID 渲染，而非家长设备的本地偏好。缺失或未知 ID 回退为默认小灯，不接受消息传入任意图片 URL。当前按发送时 ID 保留历史消息头像，换形象只影响后续发送的消息。

演示模式下，孩子自己的消息使用实际选中形象；家长可手动查看明确标注的“小星”预设来信，仅验证头像显示，不代表真实设备互通。
