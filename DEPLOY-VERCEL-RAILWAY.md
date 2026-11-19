# 部署到 Vercel + Railway

## 架构图

```
用户 → Vercel (前端) → Railway (后端) → Paratera API
```

## 第一步：部署后端到 Railway

### 1. 注册 Railway
- 访问 https://railway.app
- 用 GitHub 登录

### 2. 创建新项目
- 点击 "New Project"
- 选择 "Deploy from GitHub repo"
- 选择你的项目仓库（需要先推送到 GitHub）

### 3. 配置环境变量
在 Railway 项目的 "Variables" 中添加：

| 变量名 | 值 |
|--------|-----|
| LLM_API_KEY | 你的API密钥 |
| LLM_MODEL | Qwen3.7-Plus |
| LLM_CHAT_URL | https://llmapi.paratera.com/v1/chat/completions |
| HUAWAI_HOST | 0.0.0.0 |
| HOST | 0.0.0.0 |

### 4. 获取后端地址
- Railway 会自动分配一个域名，类似：
  `https://your-app-name.up.railway.app`
- 记下这个地址，后面要用

### 5. 创建测试用户
在 Railway 的 "Shell" 中运行：
```bash
python -c "
import secrets, hashlib, sqlite3
def password(p, s): return hashlib.scrypt(p.encode(), salt=bytes.fromhex(s), n=16384, r=8, p=1).hex()
conn = sqlite3.connect('huawai.sqlite3')
for i in range(1, 9):
    pair_id = f'{i:02d}'
    for role in ['child', 'parent']:
        account = f'{role}{pair_id}'
        salt = secrets.token_hex(16)
        pwd = password('test12345678', salt)
        conn.execute('DELETE FROM users WHERE account=?', (account,))
        conn.execute('INSERT INTO users(id, account, name, role, salt, password) VALUES(?,?,?,?,?,?)',
            (secrets.token_hex(16), account, f'{\"孩子\" if role==\"child\" else \"家长\"}{pair_id}', role, salt, pwd))
conn.commit()
conn.close()
print('Users created')
"
```

## 第二步：部署前端到 Vercel

### 1. 注册 Vercel
- 访问 https://vercel.com
- 用 GitHub 登录

### 2. 修改前端配置
编辑 `frontend/.env.production`：
```
VITE_USE_MOCK=false
VITE_API_BASE=https://your-railway-app.up.railway.app
```

把 `your-railway-app.up.railway.app` 替换为你的 Railway 地址。

### 3. 部署到 Vercel
- 点击 "New Project"
- 选择你的项目仓库
- 配置：
  - Framework Preset: Vite
  - Root Directory: frontend
  - Build Command: npm run build
  - Output Directory: dist

### 4. 获取前端地址
- Vercel 会分配一个域名，类似：
  `https://your-project.vercel.app`

## 第三步：测试

1. 打开 Vercel 地址
2. 用测试账号登录：
   - child01 / test12345678
   - parent01 / test12345678
3. 测试消息转译

## 注意事项

### Railway 免费版限制
- 每月 $5 额度（约 500 小时运行）
- 数据库是临时的，重启会丢失
- 如果需要持久化数据库，需要升级到付费版或使用外部数据库

### Vercel 免费版限制
- 每月 100GB 带宽
- 构建时间每月 6000 秒
- 对于小项目完全够用

### 国内访问
- Railway 和 Vercel 都在海外
- 国内访问可能较慢（1-3秒延迟）
- 但比 cpolar 稳定

## 成本

| 服务 | 免费版额度 | 超出后费用 |
|------|-----------|-----------|
| Railway | $5/月 | 按用量计费 |
| Vercel | 100GB 带宽 | $0.15/GB |

对于小规模测试，免费版完全够用。

## 故障排查

### 后端无法连接
- 检查 Railway 环境变量是否正确
- 查看 Railway 日志：`railway logs`

### 前端无法访问
- 检查 Vercel 构建是否成功
- 查看 Vercel 部署日志

### 转译失败
- 检查 Paratera API Key 是否有效
- 查看 Railway 后端日志
