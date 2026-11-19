# 话外完整源码：每人使用自己的 API

本包包含 Python 后端和 Vue 前端，无附带密钥、账号、聊天记录或数据库。每位使用者在自己的电脑创建账号、填写自己的模型服务信息。费用由其 API 账户承担。本包不是已经上线的公共网站。

## 环境

安装 Python 3.11 或更新版本，以及 Node.js 22.12 或更新版本。Python 后端只用标准库，不需要 pip。前端首次安装依赖需要联网。

## 1. 创建账号

解压后在本目录打开终端，逐条执行：

```
python server.py --create-user child01 --role child --name 孩子
python server.py --create-user parent01 --role parent --name 家长
```

按提示输入至少 12 位密码；输入不显示字符。同一个账号只需创建一次。不要重复运行创建命令。

## 2. 接入自己的 API 并启动后端

```
python start_backend.py
```

按提示输入：完整 Chat Completions 接口 URL、模型 ID、API Key。默认地址为并行平台的 `https://llmapi.paratera.com/v1/chat/completions`，模型填写控制台提供的精确 ID。其他供应商需要支持同样的 JSON 协议和 Bearer 鉴权，例如请求含 model/messages，响应含 choices[0].message.content；并非所有 API 都兼容。请以供应商文档为准，输入完整路径，不只是主页或 Base URL。

密钥不显示、不写入配置文件，仅由后端进程使用；不要把密钥放进前端 VITE_ 环境变量。程序会将沟通原话、练习内容发送到你所配置的服务，请只使用可信服务。

## 3. 启动前端

Windows 双击 `start-frontend.cmd`，或另开终端：

```
cd frontend
npm.cmd ci
npm.cmd run dev -- --host 127.0.0.1
```

macOS/Linux 使用 `npm` 代替 `npm.cmd`。打开终端显示的 Local 地址。保持两个终端打开。前端已经启用真实接口，通过 Vite 将 /api 转发给本机 8000 端口。

## 4. 验证

用普通窗口登录 child01、无痕窗口登录 parent01；各自选择正确身份。孩子创建房间，家长输入邀请码，发送消息。双方必须连接同一个后端：两台电脑各自启动本包，会得到两套互不共享的数据库，不能通过邀请码互通。跨电脑沟通需要另行部署共享服务。

401/403 通常需要核查密钥、模型权限；余额不足请检查供应商控制台。502 的详细提示显示在页面。后端启动不代表 API 已验证成功，发送消息才会真实调用并产生用量。

## 开发与限制

运行 `python -m unittest discover -s . -v` 执行后端测试（模型使用替身）。在 frontend 执行 `npm.cmd run build` 检查类型并构建。

数据库首次运行自动创建为 huawai.sqlite3，请勿将含私人信息的数据库转发。源码与测试提供本地联调能力，尚未做真实平台端到端验证、完整危机分流和生产安全验收，不应直接暴露到公网。故事保持固定内容；没有自助注册或找回密码。
