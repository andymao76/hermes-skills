# IM 平台故障模式速查

## Telegram

| 症状 | 可能原因 | 处理 |
|------|---------|------|
| `httpx.ConnectError: All connection attempts failed` | Gateway 重启中 / 代理临时中断 | 等待 Gateway 稳定后自动恢复，检查 `journalctl -u hermes-gateway` |
| `Timed out` | Telegram API 超时（国内网络波动） | 临时问题，无需操作 |
| 日志无 `Connecting to telegram...` | Gateway 重启后尚未轮到 Telegram | 等 60s 后检查，Telegram 连接约需 30s |

## WhatsApp

| 症状 | 可能原因 | 处理 |
|------|---------|------|
| `Code 408` 反复重连 | WebSocket 未走代理 / 网络受限 | 应用 Baileys 代理补丁：`bash ~/.hermes/skills/devops/hermes-whatsapp-bridge/scripts/apply-proxy-patch.sh` |
| `Code 440` (conflict → replaced) | 多个 bridge 实例同时运行 | 杀多余的 `bridge.js` 进程 |
| `Code 515` | WhatsApp 请求重启（配对新 session 后常见） | 自动重连，等待 1-3s |
| `whatsapp connect timed out after 30s` | Gateway 30s 等待超时（但 bridge 仍在后台重连） | 检查 `~/hermes/whatsapp/bridge.log` 确认桥接状态 |

## Discord

| 症状 | 可能原因 | 处理 |
|------|---------|------|
| Gateway 日志完全无 Discord 行 | `DISCORD_ENABLED: false` | 改为 `true` 后重启 Gateway |
| `discord connect timed out after 30s` | WebSocket 连接超时 | 检查代理是否正常，Bot API 消息发送仍可用（绕过 WebSocket） |
| `paused after 10 consecutive failures` | 连续失败后被暂停 | 重启 Gateway 或运行 `hermes gateway restart` |

## 微信 (Weixin)

| 症状 | 可能原因 | 处理 |
|------|---------|------|
| `iLink sendmessage rate limited` | 发送频率过高 | 等待 30s 冷却，自动恢复 |
| `Cannot connect to host ilinkai.weixin.qq.com` | DNS 解析失败 / 网络问题 | 检查代理和 DNS |

## QQ Bot

| 症状 | 可能原因 | 处理 |
|------|---------|------|
| `invalid appid or secret` (code 100016) | AppID 或 Client Secret 无效 | 登录 q.qq.com 重新获取凭据 |
| QQ 开放平台无法扫码登录 | 浏览器无头模式不支持 QR 渲染 | 用户手动在终端打开浏览器登录 |
