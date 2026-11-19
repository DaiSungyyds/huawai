# Sites 部署记录

已于 2026 年 10 月 26 日发布： https://huawai-family-demo.wangpai206.chatgpt.site

- 2026 年 10 月 26 日已按用户要求改为公开访问，有链接的人可访问，无需 GPT 账号；网页内部仍为演示登录。
- 使用静态演示构建，真实注册认证、双设备消息和 AI 服务未接入。
- 源码部署目录：`sites/huawai-demo`，站点身份存于该目录 `.openai/hosting.json`，更新时必须复用。
- 本次发布 commit：`7b78a6608805d625d4607bfe100328767b2ace19`。
- 部署状态、站点及版本 ID 见 `.work/deploy/sites-deployment.json`。
- 后续在 `frontend` 开发后，将源码及重新构建的 dist 同步到部署目录，再用 Sites 更新同一站点。
