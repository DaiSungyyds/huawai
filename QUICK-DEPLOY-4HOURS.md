# 4小时快速部署计划

## 目标
让异地组员能访问测试亲子对话功能

## 时间线

| 时间 | 任务 |
|------|------|
| 0:00-0:30 | 注册 cpolar + 安装 |
| 0:30-0:45 | 启动服务 + 创建隧道 |
| 0:45-1:00 | 测试验证 |
| 1:00-4:00 | 组员测试 + 收集反馈 |

## 步骤

### 1. 注册 cpolar（5分钟）

访问 https://www.cpolar.com
- 微信扫码登录
- 进入控制台，复制 authtoken

### 2. 安装 cpolar（5分钟）

```powershell
# 下载安装包
# https://www.cpolar.com/download

# 安装后配置
cpolar authtoken <你的token>
```

### 3. 启动后端（2分钟）

```powershell
cd D:\Tsinghua\Project\huawai-source\huawai

$env:HUAWAI_HOST = "0.0.0.0"
$env:LLM_API_KEY = "sk-C1CNC9CZ7esF6y4x5yTQ8g"
$env:LLM_MODEL = "Qwen3.7-Plus"
python server.py
```

### 4. 启动前端（2分钟）

```powershell
cd frontend
npm run dev
```

### 5. 创建隧道（5分钟）

新开两个终端：

```powershell
# 终端1：后端隧道
cpolar http 8000

# 终端2：前端隧道
cpolar http 5174
```

会显示：
```
Forwarding:  https://xxxxx.cpolar.cn -> 127.0.0.1:8000
Forwarding:  https://yyyyy.cpolar.cn -> 127.0.0.1:5174
```

### 6. 测试（10分钟）

手机浏览器打开前端隧道地址，测试：
- 登录
- 创建房间
- 发送消息
- 查看转译

### 7. 分享给组员（10分钟）

把前端隧道地址发给组员，让他们：
- 浏览器打开
- 用 testchild / testpass123456 登录测试

## 备选方案：如果 cpolar 不行

### ngrok（国际版）

```powershell
# 注册 https://ngrok.com
# 下载 ngrok
ngrok config add-authtoken <token>
ngrok http 5174
```

### 花生壳（国内）

```powershell
# 下载 https://hsk.oray.com/download
# 注册配置即可
```

## 注意事项

1. 隧道地址每次重启会变（免费版）
2. 免费版有流量限制（每天1G够用）
3. 电脑不能休眠，否则隧道断开

## 4小时后

- 收集组员反馈
- 记录问题
- 决定是否继续优化
