---
name: hermes-whatsapp-bridge
description: Hermes Agent WhatsApp Bridge 配置、排查、运维 — 二维码配对、断连恢复(Code 408/515)、Session 管理
version: 2.1.0
category: devops
tags: [hermes, whatsapp, bridge, baileys, messaging, gateway]
related_skills: [hermes-agent]
---

# Hermes Agent WhatsApp Bridge 运维 SKILL

## 触发场景

- WhatsApp 消息收不到 / 不回复
- 二维码不显示或配对失败
- Code 408（超时断连）或 Code 515（session 失效断连）
- Gateway 日志报 `whatsapp failed to connect`
- 依赖安装失败

## 诊断步骤

先执行快速诊断，收集关键信息：

```bash
# 1. 进程检查
ps aux | grep -i whatsapp | grep -v grep

# 2. Session 文件
ls -la ~/.hermes/whatsapp/session/
# 应有 creds.json 表示已配对，空目录表示未配对

# 3. 配置确认
grep WHATSAPP_ENABLED ~/.hermes/.env
grep -A5 "whatsapp" ~/.hermes/config.yaml

# 4. Gateway 日志
grep -i "whatsapp\|wa.*bridge\|Baileys\|paired" ~/.hermes/logs/gateway.log | tail -10

# 5. Bridge 日志
tail -30 ~/.hermes/whatsapp/bridge.log
```

## 常见问题与修复

### No creds.json — 从未配对

Gateway 日志报：
```
WhatsApp is enabled but not paired
(no creds.json at ~/.hermes/whatsapp/session/creds.json)
```

**修复：**
```bash
# 清除旧 session（如有）
rm -rf ~/.hermes/whatsapp/session/*

# 启动配对，终端显示二维码
hermes whatsapp
```

手机操作：WhatsApp → 设置 → 已链接设备 → 扫描终端二维码。

配对成功后 `~/.hermes/whatsapp/session/creds.json` 自动生成。

### Code 408 — 超时断连

bridge.log 显示：
```
⚠️  Connection closed (reason: 408). Reconnecting in 3s...
```

**三种可能原因：**

**原因 A：session 过期** — session 被 WhatsApp 端撤销（换手机、多设备登出、长时间未用）。
**修复：** 重新配对。
```bash
rm -rf ~/.hermes/whatsapp/session/*
hermes whatsapp
```

**原因 B：网络受限（防火长城环境，中国大陆常见）** — Baileys 的 WebSocket 连接无法直连 WhatsApp 服务器。即使 `HTTP_PROXY` 已设置环境变量，Node.js WebSocket 库也不会自动读取它，导致连接永远超时，QR 码无法生成。
**修复：** 给 Baileys 配置 WebSocket 代理 agent。

**原因 C：Snap Node.js TLS 限制** — Ubuntu 24.04+ 的 `/usr/bin/node` 可能是 Snap 包的符号链接（`readlink -f $(which node)` 返回 `/usr/bin/snap`）。Snap-confined Node.js 在通过 `https-proxy-agent` 建立 TLS 连接时可能报 `"Client network socket disconnected before secure TLS connection was established"`。
- **症状：** `hermes whatsapp` 在终端运行正常，但 Gateway 启动的桥接进程反复 Code 408
- **验证：** 对比测试 `/usr/bin/node` vs `/snap/node/XXX/bin/node` 的 TLS 代理连通性
- **完全修复（移除 Snap Node 改用原生安装）：**
  ```bash
  sudo snap remove node
  # 安装官方 Node.js（nvm 或 nodesource）
  curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -
  sudo apt install -y nodejs
  ```
- **临时验证：** 手动 `node bridge.js --port 3999 --session ~/.hermes/whatsapp/session --mode self-chat` 如果直接运行能连通但 Gateway 自动启动不行，说明是 Snap 问题

**⚠️ Gateway 30s 超时 vs Bridge 持续重连：** Gateway 对桥接进程的等待超时是 30 秒（15s HTTP 健康检查 + 15s WhatsApp 连接状态），但桥接进程会无限重连直到成功。所以 Gateway 日志报 `whatsapp connect timed out after 30s` 后，桥接进程依然在后台重连，最终可能连通。要确认是否连上，直接查看桥接日志或发一条消息测试即可，不必等待 Gateway 状态。

```bash
# 1. 安装 https-proxy-agent
cd ~/.hermes/hermes-agent/scripts/whatsapp-bridge
npm install https-proxy-agent

# 2. 修改 bridge.js：导入代理 agent 并传入 makeWASocket
```
在 import 区添加：
```javascript
import { HttpsProxyAgent } from 'https-proxy-agent';
```

在 makeWASocket() 调用前添加：
```javascript
const PROXY_URL = process.env.HTTPS_PROXY || process.env.HTTP_PROXY || 'http://127.0.0.1:7897';
const proxyAgent = PROXY_URL ? new HttpsProxyAgent(PROXY_URL) : undefined;
```

在 makeWASocket 配置中添加：
```javascript
agent: proxyAgent,
fetchAgent: proxyAgent,
```
完整的 makeWASocket 配置如下（仅显示关键改动）：
```javascript
sock = makeWASocket({
    version,
    auth: state,
    logger,
    agent: proxyAgent,       // ← WebSocket 走代理
    fetchAgent: proxyAgent,  // ← 媒体上传/下载也走代理
    printQRInTerminal: false,
    browser: ['Hermes Agent', 'Chrome', '120.0'],
    ...
});
```

**验证：**
```bash
cd ~/.hermes/hermes-agent/scripts/whatsapp-bridge
node bridge.js --pair-only --session ~/.hermes/whatsapp/session --port 3001
```
应显示二维码字符画，等待手机扫码。

> ⚠️ `hermes update` 会覆盖 bridge.js 的修改，升级后需重新打补丁。

### Code 440 — 冲突/被替换 (Conflict)

bridge.log 显示：
```
⚠️  Connection closed (reason: 440). Reconnecting in 3s...
```
日志中附带 `stream:error` → `conflict` → `type: replaced`。

**原因：** 同一个 WhatsApp 账号同时在两个地方连接（例如 Gateway 的 bridge 和手动测试的 bridge 各占一个实例）。WhatsApp Multi-Device 只允许一个 WebSocket 连接活跃，新连接会把旧连接踢下线。

**修复：** 杀掉多余的桥接进程，只保留一个。
```bash
# 查看所有桥接进程
ps aux | grep bridge.js | grep -v grep

# 杀掉重复的进程（保留一个即可）
kill <重复的PID>

# 或杀掉所有后让 Gateway 自动重建
kill $(pgrep -f bridge.js)
sleep 3
# Gateway 会自动重启 bridge
```

**预防：** 不要同时运行 `hermes whatsapp`（配对模式）和 Gateway 自动启动的 bridge。配对完成后直接让 Gateway 接管即可。

### 二维码不显示
```bash
hermes whatsapp
```
如果仍不显示，检查终端是否支持 Unicode/QR 渲染。

### 依赖问题
WhatsApp Bridge 是 Hermes Gateway 内置的 Baileys 平台，无需额外 npm install。如遇到 Node.js 相关错误，确认 Node.js 版本：
```bash
node -v
```

## 配置参考

`.env` 中的 WhatsApp 变量：
```
WHATSAPP_ENABLED=true
WHATSAPP_MODE=self-chat
WHATSAPP_ALLOWED_USERS=+160****3546
```

`config.yaml` 中的 WhatsApp 配置：
```yaml
platforms:
  whatsapp:
    enabled: true
```

## 目录结构

```
~/.hermes/whatsapp/
├── bridge.log          # Bridge 运行日志，含连接/断连/重连记录
├── session/
│   ├── creds.json      # 配对凭据（核心 Session 文件）
│   └── ...             # Baileys 其他缓存文件
└── session.bak.*/      # 备份的旧 session
```

## Pitfalls

- Session 文件（creds.json）是唯一配对凭据，**不要删除**，否则需重新扫码
- 基于非官方 API（Baileys），存在被封风险
- Code 408 常见于 session 过期，重新配对即可，不要反复重启 Gateway
- Hermes Gateway 重启后会自动尝试连接 WhatsApp，但不会自动重新配对
- 频繁断连建议使用专门号码，不要用主号
