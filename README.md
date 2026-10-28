<div align="center">

# 💬 WeChat Bridge

**把微信 Bot 变成可编程的 HTTP 消息通道**

**Open-source Python bridge for pushing messages to WeChat via HTTP API, deployable with Docker.**

**轻量 · 数据主权 · 跨平台开箱即用**

[API 文档](docs/api-reference.md) · [部署指南](docs/deployment.md) · [上游项目](https://github.com/yuuouu/WeChat-Bridge)

<img src="docs/assets/banner.png" alt="WeChat Bridge" width="240">

</div>

---

> **关于本分支**：本仓库 fork 自 [yuuouu/WeChat-Bridge](https://github.com/yuuouu/WeChat-Bridge)（MIT License），基于上游 v1.4.0 维护。版本号形如 `v1.4.0-0.2`，即「上游版本号 - 本分支修订号」。与上游相比：
>
> - 移除遥测、匿名统计以及启动时的版本检查，不再向任何统计服务发送请求
> - 移除「通过微信远程操控 AI CLI」（Bridge Code Agent）模块
> - 移除内置 AI 助手、插件系统和 Webhook 消息转发，只保留对外推送微信消息和微信内置指令
> - 安装脚本、Docker 镜像和文档均指向本仓库
>
> 完整变更见 [更新日志](docs/CHANGELOG.md)。

WeChat Bridge 使用 HTTP API 把服务器、NAS 和自动化服务的通知发送到微信。收到的微信消息只记录在管理面板中，并响应少量内置指令（如 `/status`、`/pull`），不转发给外部服务，也不自动回复。

- [通过 HTTP API 发送微信消息](docs/api-reference.md)：接口参数、鉴权与调用示例
- [使用 Docker 或安装脚本部署微信 Bot](docs/deployment.md)：部署、升级与管理

---

## 快速开始

**macOS / Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/ggyy0124-cell/WeChat-Bridge/main/scripts/install.sh | bash
```

**Windows (PowerShell):**

```powershell
powershell -c "irm https://raw.githubusercontent.com/ggyy0124-cell/WeChat-Bridge/main/scripts/install.ps1 | iex"
```

**Docker:**

```bash
mkdir -p wechat-bridge && cd wechat-bridge

cat > docker-compose.yml <<EOF
services:
  wechat-bridge:
    image: ghcr.io/ggyy0124-cell/wechat-bridge:latest
    container_name: wechat-bridge
    restart: unless-stopped
    ports:
      - "5200:5200"
    volumes:
      - ./data:/data
    environment:
      - TZ=Asia/Shanghai
      - API_TOKEN=change-this-token
EOF

docker compose up -d
```

启动后打开 `http://localhost:5200`，如果设置了 `API_TOKEN` 先输入访问密码，然后扫码登录即可

更多部署、升级和原生运行方式见 [部署与管理指南](docs/deployment.md)

---

## 使用效果

<div align="center">
  <table>
    <tr>
      <td align="center"><img src="docs/assets/chat.png" alt="WeChat Bridge 聊天界面" width="500"></td>
      <td align="center"><img src="docs/assets/quota-limit.png" alt="10条配额风控机制" width="250"></td>
      <td align="center"><img src="docs/assets/daily-push.jpg" alt="日常签到与金价推送" width="250"></td>
      <td align="center"><img src="docs/assets/system-push.jpg" alt="系统报告与路由器状态推送" width="250"></td>
      <td align="center"><img src="docs/assets/markdown-render.png" alt="Markdown 文本渲染效果" width="250"></td>
    </tr>
    <tr>
      <td align="center"><em>Web 管理面板</em></td>
      <td align="center"><em>连续 10 条保护</em></td>
      <td align="center"><em>签到 / 金价 / 日常推送</em></td>
      <td align="center"><em>系统报告 / 服务监控 / 路由器状态</em></td>
      <td align="center"><em>Markdown 文本渲染</em></td>
    </tr>
  </table>
</div>

---

## 从任意网络发送到微信

本项目最核心的用法是把微信 Bot 变成一个 HTTP 推送网关

### 1. 本机或内网调用

```bash
curl -X POST http://localhost:5200/api/send \
  -H "Authorization: Bearer change-this-token" \
  -H "Content-Type: application/json" \
  -d '{"to": "好友名称或 user_id", "text": "Hello from server"}'
```

参数说明：

- `to`：目标联系人，在微信 Bot 中发送 `/uid` 可获取自己的 `user_id`
- `API_TOKEN`：接口访问密钥；设置后 `/api/send` 等接口必须携带 `Authorization: Bearer <TOKEN>` 或 URL 参数 `?token=<TOKEN>`，公网开放时务必设置
- `MARKDOWN_MODE=normalize`：可选，将 iStoreOS、青龙、Bark 等普通通知整理为 Markdown；不设置时默认按 Markdown 文本发送

如果不传 `to`，系统会尝试发送给通讯录里的第一个联系人；生产环境建议显式传入目标联系人或 `user_id`

### 2. 开放到公网调用

把 `5200` 端口通过反向代理、内网穿透或云服务器安全暴露为 HTTPS 域名，例如：

```text
https://bot.example.com -> http://127.0.0.1:5200
```

随后任何网络都可以调用：

```bash
curl -X POST https://bot.example.com/api/send \
  -H "Authorization: Bearer change-this-token" \
  -H "Content-Type: application/json" \
  -d '{"to": "好友名称或 user_id", "text": "来自公网的微信推送"}'
```

也可以用 GET，适合青龙面板、路由器插件、简单 Webhook：

```bash
curl "https://bot.example.com/api/send?token=change-this-token&to=好友名称&text=任务完成"
```

公网开放建议：

- 务必设置 `API_TOKEN`
- 优先使用 HTTPS
- 不要把无鉴权接口直接暴露到公网
- 更高安全要求下可叠加反向代理鉴权、IP 白名单、Cloudflare Access 或防火墙规则

---

## 典型使用场景

| 场景 | 推荐接入方式 |
|---|---|
| 服务器、NAS、软路由状态推送 | 定时任务或脚本调用 `POST /api/send` |
| 青龙面板、iStoreOS、OpenWrt 通知 | 配置自定义 Webhook URL 指向 `/api/send` 或 `/api/push` |
| Grafana、Uptime Kuma、GitHub 告警 | 调用 `/api/webhook/<type>`，自动格式化为微信友好文本 |
| 手机快捷指令、Tasker、云函数 | 公网 HTTPS 域名 + Bearer Token 调用 `/api/send` |

完整接口与平台示例见 [API 接口参考](docs/api-reference.md)

---

## 核心能力

- **标准 HTTP API**：`/api/send`、`/api/send_image`、`/api/push`、`/api/webhook`、`/api/contacts`、`/api/status`
- **内置指令**：在微信中发送 `/status`、`/pull`、`/mute` 等指令查看状态、补拉缓存消息、临时静默
- **Web 管理面板**：扫码登录、实时消息流、联系人缓存、图片收发、保活设置
- **桌面通知**：网页驻留后台时，可调用主流操作系统的原生系统通知
- **投递保护**：24h 窗口和连续 10 条限制下，自动缓存受阻消息，过期缓存自动标记丢弃，并支持 `/pull` 补拉
- **可见化状态**：Web UI 展示 `已缓存 / 已补拉 / 已丢弃 / 可能已送达` 等投递标签
- **API Token 鉴权**：支持 Bearer Token 或 `?token=`，适合公网和第三方集成
- **本地持久化**：SQLite WAL 模式保存消息、联系人、投递状态和配置，适合轻量设备长期运行

---

## 技术内核

WeChat Bridge 参考微信 openclaw 底层连接协议 **iLink** 的协议文档，以纯 Python **本地实现**了完整的协议栈——扫码登录、长轮询消息接收、文本 / 图片发送、媒体 AES-128-ECB 加密上传、"正在输入"状态下发，以及登录态持久化与自动续期，彻底脱离 openclaw npm 包，不依赖 Node.js 运行时。

这一设计带来三个结果：

- **零 Node.js 依赖**：纯 Python 单进程运行，轻量设备（路由器、NAS、树莓派）开箱即用
- **协议层可控**：消息类型、发送参数、会话游标完全在 Python 进程内管理，便于按需扩展
- **媒体原生支持**：自主实现 AES 加密 → CDN 上传管线，图片收发不依赖任何外部工具

---

## API 速览

```bash
# 发文本
curl -X POST http://localhost:5200/api/send \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"to": "好友名称或 user_id", "text": "Hello!"}'

# 发图片
curl -X POST http://localhost:5200/api/send_image \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "to=好友名称或 user_id" \
  -F "image=@photo.jpg"

# 健康检查
curl http://localhost:5200/api/status
```

完整 API、请求字段、Webhook 适配器、青龙面板和 iStoreOS 配置见 [API 接口参考](docs/api-reference.md)

---

## 微信侧限制

WeChat Bridge 基于腾讯 iLink Bot API，无法绕过官方接口限制：

| 限制项 | 影响 |
|---|---|
| 需主动发消息 | 只有用户先给 Bot 发过消息，系统才能获取 `user_id` 并主动发送 |
| 动态会话窗口 | 下发依赖最近入站消息的 `context_token`；有效期由 iLink 服务端控制，没有稳定的固定 TTL，失效后需要用户重新互动 |
| 连续 10 条限制 | Bot 连续发送 10 条消息后，若用户未回复，继续发送会被阻断；用户回复任意内容后计数重置 |

项目已把这些限制产品化处理：保活提醒、第 10 条末尾提醒、受阻消息缓存、`/pull` 补拉、投递状态标签，能降低丢消息概率，但不能突破接口规则。

从 1.4.0 起，Bridge 默认不再用本地“24 小时”计时器提前阻断发送，而是以 iLink 的实际业务响应为准。`ret=0` 只记录为“上游已受理、送达未确认”；如确需旧版保守策略，可设置 `ILINK_ENFORCE_LOCAL_SESSION_WINDOW=1`。

缓存消息不会无限期保留。默认清理策略是：普通缓存 72 小时后标记为 `DISCARDED`，行情、保活、设备上下线等时效消息 24 小时后标记为 `DISCARDED`，图片缓存保留 7 天。清理只改变投递状态，不物理删除历史记录；可通过 `PENDING_MESSAGE_TTL_HOURS`、`PENDING_TIME_SENSITIVE_TTL_HOURS`、`PENDING_MEDIA_TTL_HOURS` 调整，设置为 `0` 表示不自动过期。

---

## 微信可用指令

| 指令 | 说明 |
|---|---|
| `/help` | 显示帮助菜单 |
| `/status` | 查看服务状态、发送额度和配置 |
| `/uid` | 获取自己的用户 ID |
| `/keepalive [on\|off]` | 开启或关闭 23h 通道提醒 |
| `/mute 时长` | 临时静默，期间推送自动缓存（如 `/mute 2h`），回复任意内容解除 |
| `/pull` | 拉取当前缓存会话中的未送达消息 |

---

## 更多文档

| 文档 | 说明 |
|---|---|
| [部署与管理指南](docs/deployment.md) | 手动安装、Docker、版本升级 |
| [API 接口参考](docs/api-reference.md) | 完整 API、青龙面板 / iStoreOS 集成、Webhook 适配器 |
| [工作原理](docs/architecture.md) | iLink 协议桥接时序图与核心流程解析 |
| [安全策略](SECURITY.md) | 漏洞报告方式与部署安全清单 |
| [更新日志](docs/CHANGELOG.md) | 版本变更记录 |

---

## 隐私与数据收集

本项目**不包含任何遥测、匿名统计或版本检查**，不会向作者或任何第三方上报版本号、系统信息、运行状态或使用情况。

- **对外请求**：仅限腾讯 iLink 接口与微信 CDN（微信消息收发必需），不会把收到的微信消息转发给任何外部服务
- **安装脚本**：只从本仓库的 GitHub 地址下载源码，不经过任何第三方代理或统计服务
- **升级**：不会在启动时检查更新，请按 [部署指南](docs/deployment.md) 中的方式手动升级
- **数据留存**：微信登录凭据、消息记录和配置只保存在你自己的 `data/` 目录

---

<div align="center">
  <p>
    <img src="docs/assets/qrcode-tech-discussion.png" alt="加我进群技术讨论" width="88">
    <br><em>技术讨论</em>
  </p>
</div>

---

## 鸣谢

本项目在协议研究与底层实现上参考了以下开源项目：

- [openclaw-weixin](https://github.com/Tencent/openclaw-weixin/blob/main/README.zh_CN.md)
- [iLink Bot API 底层协议客户端实现](https://www.npmjs.com/package/@tencent-weixin/openclaw-weixin)

---

## License

MIT License - 自由使用、修改和分发
