# Baileys WebSocket 代理补丁（防火长城环境）

## 背景

在中国大陆网络中，WhatsApp WebSocket 服务器（`wss://web.whatsapp.com`）被 DNS 污染和连接阻断。Baileys 使用 `ws` 库建立 WebSocket 连接，该库**不读取** Node.js 的 `HTTP_PROXY`/`HTTPS_PROXY` 环境变量，导致即使终端设置了代理，连接也永远超时（Code 408）。

## 补丁内容

### 1. 安装依赖

```bash
cd ~/.hermes/hermes-agent/scripts/whatsapp-bridge
npm install https-proxy-agent
```

### 2. 修改 bridge.js

**文件路径：** `~/.hermes/hermes-agent/scripts/whatsapp-bridge/bridge.js`

**改动一：添加 import**（第 32 行附近，在 `import qrcode` 和 `import { matchesAllowedUser }` 之间）

```javascript
import { HttpsProxyAgent } from 'https-proxy-agent';
```

**改动二：在 makeWASocket 调用前创建代理 agent**（第 204 行附近，`const { version } = await fetchLatestBaileysVersion()` 之后）

```javascript
const PROXY_URL = process.env.HTTPS_PROXY || process.env.HTTP_PROXY || 'http://127.0.0.1:7897';
const proxyAgent = PROXY_URL ? new HttpsProxyAgent(PROXY_URL) : undefined;
```

**改动三：在 makeWASocket 配置中添加 agent 选项**（在 `auth: state`、`logger` 之后）

```javascript
agent: proxyAgent,
fetchAgent: proxyAgent,
```

### 3. 验证

```bash
cd ~/.hermes/hermes-agent/scripts/whatsapp-bridge
timeout 30 node bridge.js --pair-only --session ~/.hermes/whatsapp/session --port 3001
```

成功输出：二维码字符画 + "Waiting for scan..."
失败输出：`⚠️  Connection closed (reason: 408)` — 说明代理仍有问题。

### 4. QQ 二维码显示（非必须）

bridge.js 中 `printQRInTerminal: false` 是 Baileys 内置的 QR 打印开关（已废弃被移除了），实际的 QR 码是通过 `qrcode.generate(qr, { small: true })` 在 `connection.update` 事件处理器中手动生成的（第 226-229 行）。所以 `printQRInTerminal: false` 不影响 QR 显示。

## 注意事项

- `hermes update` 会覆盖 bridge.js 的修改，升级后需要重新打补丁
- 补丁后运行 `hermes whatsapp` 配对时，子进程会自动继承当前 shell 的 `HTTP_PROXY` 环境变量
- Clash Verge (verge-mihomo) 的 7897 端口支持 HTTP CONNECT 隧道，可正常代理 WebSocket

## Snap Node.js TLS 问题

**症状：** Snap-confined Node.js（`/usr/bin/node → /usr/bin/snap`）通过 `https-proxy-agent` 建立 WebSocket 连接时报错：
```
Client network socket disconnected before secure TLS connection was established
```

**根因：** Snap 沙箱限制了对系统证书和网络套接字的访问，即使以 `classic` 模式安装也偶发。

**诊断：**
```bash
# 检查 node 是否为 Snap
readlink -f $(which node)
# 返回 /usr/bin/snap 即为 Snap 版本

# 测试 Snap Node TLS 代理连通性
/snap/node/XXX/bin/node -e "
const { HttpsProxyAgent } = await import('https-proxy-agent');
const WebSocket = (await import('ws')).default;
const a = new HttpsProxyAgent('http://127.0.0.1:7897');
const ws = new WebSocket('wss://echo.websocket.events', { agent: a, timeout: 10000 });
ws.on('open', () => console.log('OK'));
ws.on('error', e => console.log('FAIL:', e.message));
"
```

**验证（用非 Snap Node 对比）：**
```bash
cd ~/.hermes/hermes-agent/scripts/whatsapp-bridge
/usr/bin/node bridge.js --port 3999 --session ~/.hermes/whatsapp/session --mode self-chat
```
如果这条路能连通（显示 "✅ WhatsApp connected!"），则是 Snap 问题。

## Gateway 超时与桥接重连

Gateway 对 WhatsApp 桥接的等待超时逻辑：
1. Phase 1：HTTP 健康检查 → 每 1s 轮询 `/health`，最多 15 次
2. Phase 2：WhatsApp 连接状态 → 最多 15s
3. 总超时：**30 秒**

如果桥接进程启动后 WhatsApp WebSocket 连接时间超过 30 秒，Gateway 就会报 `whatsapp connect timed out after 30s` 并标记平台为失败。但桥接进程本身**不会退出**，会持续重连直到成功。

因此，出现 timeout 错误后，不要反复重启 Gateway。先检查桥接日志确认是否最终连上了：
```bash
tail -5 ~/.hermes/whatsapp/bridge.log
# 如果看到 "✅ WhatsApp connected!" 说明已连上
```
