# 校园网测试指南

## 你的网络情况

当前 IP：101.5.11.75（公网 IP）
校园网做了 NAT，设备之间不能直连。

## 推荐方案：cpolar 内网穿透

### 1. 注册 cpolar

访问 https://www.cpolar.com 注册账号（免费）

### 2. 安装 cpolar

```powershell
# Windows 下载安装
# https://www.cpolar.com/download

# 或用 scoop
scoop install cpolar
```

### 3. 配置认证

```powershell
cpolar authtoken <你的token>
```

### 4. 启动后端

```powershell
cd D:\Tsinghua\Project\huawai-source\huawai

# 监听所有网卡
$env:HUAWAI_HOST = "0.0.0.0"
$env:LLM_API_KEY = "sk-C1CNC9CZ7esF6y4x5yTQ8g"
$env:LLM_MODEL = "Qwen3.7-Plus"
python server.py
```

### 5. 启动前端

```powershell
cd frontend
npm run dev
```

### 6. 创建隧道

```powershell
# 后端隧道
cpolar http 8000

# 前端隧道（另一终端）
cpolar http 5174
```

会显示类似：
```
Tunnel status: online
Forwarding:  https://abc123.cpolar.cn -> 127.0.0.1:8000
```

### 7. 测试

- 手机浏览器打开前端隧道地址
- 另一台设备也打开同样地址
- 即可双端测试

## 备选方案：手机热点

如果只是临时测试：

1. 手机开热点
2. 电脑连接热点
3. 另一台设备也连接热点
4. 查看电脑 IP（应该是 192.168.x.x）
5. 另一台设备访问 http://电脑IP:5174

## 备选方案：宿舍路由器

如果有小路由器：

1. 校园网网线接路由器 WAN 口
2. 两台设备连路由器 WiFi
3. 查看电脑 IP（192.168.x.x）
4. 启动服务时设置 HUAWAI_HOST=0.0.0.0
5. 另一台设备访问 http://电脑IP:5174
