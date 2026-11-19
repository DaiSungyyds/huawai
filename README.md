# 话外后端（本地联调版）

Python 3.11+，仅标准库，无需 pip。前端 Vue + Vite。包含登录、8 小时令牌、退出、双角色房间、24 小时邀请码、消息持久化与去重、模型改写、三类场景和五轮练习反馈。故事仍为原有本地固定内容。

## 最新更新（2026-11-19）

### 核心功能优化

| 优化项 | 说明 | 效果 |
|--------|------|------|
| 原话可见性控制 | 仅消息发送者本人可查看原话 | 孩子发的原话孩子可看，家长不可看；反之亦然 |
| 改写延迟优化 | 降低 max_tokens、优化超时参数 | 平均延迟从 ~60s 降至 ~16s（降低 73%） |
| Pending 状态显示 | 发送时立即显示"正在为你润色表达…" | 用户无需等待空白，体验更流畅 |
| 移除同步中断提示 | 轮询失败改为静默重试 | 不再频繁显示烦人的错误提示 |

### 安全机制补全

| 机制 | 说明 |
|------|------|
| 心理风险识别 | 检测高风险关键词（自杀、自残等），阻止发送并显示支持弹窗 |
| 危机干预转介 | 弹窗显示心理援助热线：010-82951332、12355 |
| 用户隐私保护 | 退出时清除本地数据；支持用户数据删除接口 |
| 数据自动清理 | 每 6 小时自动清理过期数据 |

### 测试用户（已内置）

| 账号 | 密码 | 角色 |
|------|------|------|
| testchild | testpass123456 | 孩子 |
| testparent | testpass123456 | 家长 |

## 启动

### 方式一：使用内置测试用户（推荐）

直接启动后端：

```powershell
# PowerShell 安全输入 API Key
$secret = Read-Host 'Paratera API Key' -AsSecureString
$env:LLM_API_KEY = [System.Net.NetworkCredential]::new('', $secret).Password
$env:LLM_MODEL = 'Qwen3.7-Plus'
$env:LLM_CHAT_URL = 'https://llmapi.paratera.com/v1/chat/completions'
python server.py
```

另一终端启动前端：

```bash
cd frontend
npm ci
npm run dev
```

打开 http://localhost:5174/，使用测试用户登录测试。

### 方式二：创建自定义用户

```bash
python server.py --create-user child01 --role child --name 孩子
python server.py --create-user parent01 --role parent --name 家长
```

按提示设置各自密码（至少12字符）。

在同一 PowerShell 进程安全输入平台密钥：

```powershell
$secret = Read-Host 'Paratera API Key' -AsSecureString
$env:LLM_API_KEY = [System.Net.NetworkCredential]::new('', $secret).Password
$env:LLM_MODEL = 'Qwen3.7-Plus'
$env:LLM_CHAT_URL = 'https://llmapi.paratera.com/v1/chat/completions'
python server.py
```

密钥仅驻留当前进程环境。默认请求地址 https://llmapi.paratera.com/v1/chat/completions。

另一终端：

```bash
cd frontend
npm ci
npm run dev
```

打开 Vite 输出地址。前端 .env.local 已配置 VITE_USE_MOCK=false，/api 代理到 127.0.0.1:8000。分别用两个浏览器登录孩子与家长账号，创建房间、复制邀请码并加入。前端发送原话后由服务端改写，失败不会伪造响应。

## 测试

### 自动化测试

```bash
# 安全关键词检测测试
python test_safety.py

# API 集成测试
python test_api.py

# 消息改写延迟测试（需要 API Key）
python test_latency.py

# 单元测试
python -m unittest discover -s . -v
```

### 手动测试步骤

1. 打开 http://localhost:5174/
2. 使用 testchild / testpass123456 登录（孩子端）
3. 进入"沟通翻译" → 创建沟通空间 → 复制邀请码
4. 另一浏览器使用 testparent / testpass123456 登录（家长端）
5. 进入"亲子沟通" → 输入邀请码加入
6. 测试原话可见性：孩子发送消息后，只有孩子端能看到"看看原话"
7. 测试安全检测：输入"不想活了"等高风险词，应触发支持弹窗

## 部署边界

这是本地联调交付，未修改线上 Sites。SQLite 文件 huawai.sqlite3 包含私人对话，请备份并限制操作系统访问权限。公网部署应由正式 Python 应用服务器和 HTTPS 反向代理提供服务，将 /api 转发至后端，其余路径托管 frontend/dist；本实现使用标准库开发 HTTP 服务，只监听本机，不直接暴露公网。

当前请求串行处理以保证同一消息不会并发重复调用，适合小规模本地联调。尚无完整危机识别/分流锁定、用户自助注册、找回密码、管理后台或生产级多实例限流；不可宣传为已完成未成年人安全审核。退出沟通只退出页面，房间成员关系仍保留；账号登出接口已实现，前端令牌刷新后需重新登录。公开上线前需补齐产品安全验收及真实双设备/模型测试。

## 分享测试包

如需分享给其他组员测试，可打包以下文件：

```bash
# 需要打包的文件
- server.py              # 后端主程序
- paratera.py            # LLM 适配器
- huawai.sqlite3         # 数据库（含测试用户）
- frontend/              # 前端目录（不含 node_modules）
  - src/
  - package.json
  - package-lock.json
  - vite.config.ts
  - tsconfig.json
  - index.html
  - .env.local
- README.md              # 说明文档
- OPTIMIZATION-PLAN.md   # 优化方案
- TEST-REPORT.md         # 测试报告
```

接收方需要：
- Python 3.11+
- Node.js 18+
- Paratera API Key（需单独提供）
