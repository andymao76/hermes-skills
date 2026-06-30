---
name: feishu-integration-guide
description: 飞书（Feishu/Lark）对接完整指南 — API直连 + Gateway WebSocket 双向通信的配置方法、凭证说明、问题排查
category: productivity
tags:
  - feishu
  - lark
  - websocket
  - gateway
  - webhook
  - api
required_environment_variables:
  - name: FEISHU_APP_ID
    prompt: 飞书 App ID（自建应用）
    help: 在 https://open.feishu.cn/app 查看
    required_for: 所有飞书 API 调用
  - name: FEISHU_APP_SECRET
    prompt: 飞书 App Secret
    help: 在 https://open.feishu.cn/app 查看
    required_for: 所有飞书 API 调用
  - name: FEISHU_CONNECTION_MODE
    prompt: 连接模式 (websocket/api)
    default: websocket
    required_for: Gateway WebSocket 双向通信
  - name: FEISHU_DOMAIN
    prompt: 域名 (feishu 国内 / lark 海外)
    default: feishu
    required_for: API 域名
  - name: FEISHU_ALLOW_ALL_USERS
    prompt: 是否允许所有用户与 Bot 通信 (true/false)
    default: false
    required_for: 首次部署时发现用户 open_id
  - name: FEISHU_ALLOWED_USERS
    prompt: 允许通信的用户 open_id 列表（逗号分隔）
    required_for: 用户权限白名单
  - name: FEISHU_HOME_CHANNEL
    prompt: 默认消息发送目标的 open_id
    required_for: send_message(target="feishu")
---

# 飞书对接完整指南

## 概述

飞书集成覆盖三种方式，按推荐优先级排列：

| 方式 | 说明 | 状态 |
|------|------|------|
| ① 开放平台 API | 通过 `lark-oapi` SDK 直接调用 REST API 发消息 | ✅ 可用 |
| ② Gateway WebSocket | Hermes Gateway 直连飞书消息推送，双向通信 | ✅ 可用 |
| ③ feishu-hermes 桥服务 | Node.js + Cloudflare Tunnel Webhook 中转 | ❌ 未部署 |

---

## 方式一：开放平台 API（主动发送）

### 凭证配置

`.env` 文件中：

```ini
FEISHU_APP_ID=cli_aaa6b15aa6b85cdc
FEISHU_APP_SECRET=<完整密钥>
FEISHU_DOMAIN=feishu
FEISHU_ALLOW_ALL_USERS=false
FEISHU_ALLOWED_USERS=ou_6cc19b25d1617ca7c486bd69e9ba9ede
FEISHU_GROUP_POLICY=open
FEISHU_HOME_CHANNEL=ou_6cc19b25d1617ca7c486bd69e9ba9ede
```

### 发送测试消息

```bash
# 方式A：手动设环境变量
export FEISHU_APP_ID="cli_aaa6b15aa6b85cdc"
export FEISHU_APP_SECRET="<你的密钥>"

python3 ~/.hermes/skills/feishu-openapi/scripts/feishu_client.py send-text \
  "ou_6cc19b25d1617ca7c486bd69e9ba9ede" \
  "消息内容"

# 方式B：从 .env 读取（推荐）
source ~/.hermes/.env 2>/dev/null
cd ~/.hermes/skills/feishu-openapi/scripts
python3 feishu_client.py send-text \
  "ou_6cc19b25d1617ca7c486bd69e9ba9ede" \
  "消息内容"
```

### 常用命令

```bash
# 搜索群聊
python3 feishu_client.py search-chat <关键词>

# 发送文本
python3 feishu_client.py send-text <open_id> <消息内容>

# 发送图片
python3 feishu_client.py send-image <open_id> <图片路径>

# 查群成员
python3 feishu_client.py chat-members <chat_id>

# 上传文件
python3 feishu_client.py upload-file <文件路径> <文件类型> [文件名]
```

### 已知凭证

| 项目 | 值 |
|------|-----|
| APP_ID | `cli_aaa6b15aa6b85cdc` |
| 用户 open_id | `ou_6cc19b25d1617ca7c486bd69e9ba9ede` |
| 群聊 chat_id | `oc_a5a593e6822e69661878ae5c2124be35` |
| tenant_key | `1ba0ef13fe875758` |

### SDK

```bash
# lark-oapi 已安装
# 代码位置：
~/.hermes/skills/feishu-openapi/scripts/feishu_client.py
```

---

## 方式二：Gateway WebSocket（双向通信）

### 配置步骤

**前置关键步骤：飞书开发者后台配置事件订阅**

WebSocket 连上后飞书不会自动推送消息。必须订阅接收消息事件：
1. 打开 [飞书开发者后台](https://open.feishu.cn/app) → 点击你的应用
2. 左侧导航 → **事件与回调** → **添加事件**
3. 搜索并添加 `im.message.receive_v1`（接收用户消息）
4. 确认下方 **配置 WebSocket 事件** 已勾选
5. **发布** → **创建新版本** → **发布**

>  没有此步骤，WebSocket 连上了也收不到任何消息。这是双向通信最常见遗漏。

1. **.env 配置飞书连接参数**（已配）

```ini
FEISHU_CONNECTION_MODE=websocket
FEISHU_APP_ID=cli_aaa6b15aa6b85cdc
FEISHU_APP_SECRET=<完整密钥>
FEISHU_DOMAIN=feishu
```

2. **config.yaml 启用飞书平台**（已配）

```bash
hermes config set platforms.feishu.enabled true
```

3. **重启 Gateway**

```bash
systemctl --user restart hermes-gateway.service
```

4. **验证连接**

```bash
# 检查日志确认 WebSocket 已连接
journalctl --user -u hermes-gateway.service --no-pager -n 30 | grep "Lark.*connected"

# 正常输出示例：
# [Lark] [2026-06-12 21:55:19] [INFO] connected to wss://msg-frontier.feishu.cn/ws/v2?...
```

### 验证可用目标

```bash
# 在 Hermes 中执行：
send_message(action='list')
# 应看到 feishu 平台出现
```

### 限制说明

- Bot 必须先在飞书客户端中被用户或群聊添加，才能通过 Gateway 发送消息
- 用户需要先给 Bot 发一条消息建立对话关系
- 首次 `send_message` 到 chat_id 可能报错 `[230002] Bot/User can NOT be out of the chat`，此时需先通过 API 方式发送，或让用户主动联系 Bot

### 日志查看

```bash
# 实时跟踪
journalctl --user -u hermes-gateway.service -f --no-pager

# 查看飞书相关日志
journalctl --user -u hermes-gateway.service --no-pager -n 100 | grep -i "lark\|feishu"
```

---

## 方式三：feishu-hermes 桥服务（Webhook，未部署）

### 架构

```
飞书开放平台 → Webhook → Cloudflare Tunnel → feishu-hermes (port 3010) → hermes CLI
```

### 部署步骤

```bash
# 1. 创建项目目录
mkdir -p ~/feishu-hermes && cd ~/feishu-hermes

# 2. 初始化
npm init -y
npm install express axios dotenv

# 3. 创建 server.js（参考 feishu-integration skill 中的模板）
# 4. 配置 .env
# 5. 启动
node server.js &
```

### 添加主动发送端点

在 server.js 中添加：

```javascript
app.post("/feishu/send", async (req, res) => {
  const { receive_id, receive_id_type, text } = req.body;
  if (!receive_id || !text) {
    return res.status(400).json({ code: 400, msg: "receive_id and text are required" });
  }
  const token = await getTenantAccessToken();
  const idType = receive_id_type || "open_id";
  const result = await axios.post(
    `https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=${idType}`,
    { receive_id, msg_type: "text", content: JSON.stringify({ text }) },
    { headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" } }
  );
  res.json(result.data);
});
```

---

## 首次部署：发现用户 open_id（先有鸡还是先有蛋）

飞书 Bot 的 open_id 需要用户给 Bot 发消息后才知道，但 Gateway 又需要 open_id 配置才能放行。按以下步骤解决：

### 步骤

1. **在 .env 临时开放所有用户权限**：
```bash
cat >> ~/.hermes/.env << 'EOF'
FEISHU_CONNECTION_MODE=websocket
FEISHU_ALLOW_ALL_USERS=true
FEISHU_DOMAIN=feishu
FEISHU_GROUP_POLICY=disabled
EOF
```

2. **确保 feishu 已启用**：
```bash
hermes config set platforms.feishu.enabled true
```

3. **安装 lark-oapi SDK**（API 直连需要）：
```bash
~/.hermes/venv/bin/pip install lark-oapi
```

4. **启动 Gateway**：
```bash
systemctl --user start hermes-gateway.service
sleep 10
journalctl --user -u hermes-gateway.service --no-pager -n 30 | grep -i "lark\|feishu\|connected"
```
预期看到：`[Lark] connected to wss://msg-frontier.feishu.cn/ws/v2?...`

5. **在飞书客户端给 Bot 发一条消息**（如"你好"）

6. **从日志中捕获 open_id**：
```bash
journalctl --user -u hermes-gateway.service --no-pager -n 50 | grep -oP 'open_id["\\s:]+ou_[a-zA-Z0-9]+' | head -1
```
或者在 Hermes 会话中用 `memory` 查询（使用知识库）。

7. **收紧 .env 配置**，替换为实际 open_id：
```bash
# 编辑 .env 将 FEISHU_ALLOW_ALL_USERS=true 改为
FEISHU_ALLOW_ALL_USERS=false
FEISHU_ALLOWED_USERS=ou_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FEISHU_HOME_CHANNEL=ou_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

8. **重启 Gateway**：
```bash
systemctl --user restart hermes-gateway.service
```

### 备选方案：用 API 验证凭证

不启动 Gateway，先确认凭证有效：
```bash
source ~/.hermes/.env
python3 -c "
import requests
r = requests.post('https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
    json={'app_id': '$FEISHU_APP_ID', 'app_secret': '$FEISHU_APP_SECRET'})
data = r.json()
if data.get('code') == 0:
    token = data['tenant_access_token']
    r2 = requests.get('https://open.feishu.cn/open-apis/bot/v3/info',
        headers={'Authorization': f'Bearer {token}'})
    print('Bot:', r2.json().get('bot', {}).get('app_name', 'unknown'))
    print('状态: 凭证有效 ✅')
else:
    print('凭证无效:', data.get('msg'))
"
```

### Pitfall：open_id 跨应用不通用

- Bot 的 `open_id` 和用户的 `open_id` 不同
- 同一用户在不同飞书自建应用下 open_id 也不同
- 从腾讯云同步的 `feishu-integration-guide` 中记录的 open_id（如 `ou_6cc19b25d1617ca7c486bd69e9ba9ede`）是腾讯云那边的 APP_ID 下的，不能直接用于本地其他 APP_ID
- 每次新部署都要重新发现 open_id

---

## 常见问题

### Q: API 返回 `code: 10014/10003, msg: app secret invalid / invalid param`

**排查流程（按顺序执行）：**

1. **用 curl 直接测试凭证**（绕过 SDK，确认问题在凭证还是代码）：
```bash
curl -s -X POST 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal' \
  -H 'Content-Type: application/json' \
  -d '{"app_id":"你的APP_ID","app_secret":"你的APP_SECRET"}'
```
   - `code: 0` → 凭证有效，问题在 SDK/网关配置
   - `code: 10014` → APP_SECRET 错误或不完整
   - `code: 10003` → APP_ID 或 APP_SECRET 格式无效

2. **用 hexdump 检查 .env 文件是否被截断**（security.redact_secrets 会掩盖输出）：
```bash
grep "^FEISHU_APP_SECRET" ~/.hermes/.env | xxd
```
   确认 `=` 后面的内容完整无截断。如果看到 `***` 或 `...` 之类的截断标记，说明文件本身已损坏。

3. **确保 APP_ID 与 APP_SECRET 匹配**：
   - 飞书自建应用的 APP_ID 和 APP_SECRET 是一一对应的
   - 如果有两套飞书 Bot（如本地 + 腾讯云），**不能交叉使用**— 本地的 APP_ID 必须配本地的 APP_SECRET
   - 去 [飞书开发者后台](https://open.feishu.cn/app) → 点击对应的应用 → 凭证与基础信息，重新复制完整的 App Secret

4. **确认 open_id 属于当前 APP_ID**：
   - 同一用户在不同自建应用下的 open_id **不同**（open_id 是应用级非用户级）
   - 从腾讯云或别处抄来的 open_id 不能直接用于本地的 Bot

5. **修复后立即验证**：
```bash
# 修复 .env（确保先删掉损坏的行）
sed -i '/^FEISHU_APP_SECRET/d' ~/.hermes/.env
echo 'FEISHU_APP_SECRET=你的完整密钥' >> ~/.hermes/.env

# 加载验证
source ~/.hermes/.env
curl -s -X POST 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal' \
  -H 'Content-Type: application/json' \
  -d "{\"app_id\":\"$FEISHU_APP_ID\",\"app_secret\":\"$FEISHU_APP_SECRET\"}" | python3 -c "import sys,json; d=json.load(sys.stdin); print('✅ 有效' if d.get('code')==0 else f'❌ {d.get(\"msg\")}')"
```

### Q: Gateway 报 `Platform 'LightClawBot' config validation failed`
- 这是 lightclawbot 问题，不影响飞书
- 原因是缺少 `LIGHTCLAW_API_KEY` 环境变量

### Q: 看到"invalid appid or secret"错误，是飞书的问题吗？
- **先看错误来源**。错误前缀是 `[QQBot:...]` 的是 QQ Bot 的报错，**不影响飞书**
- 飞书相关错误前缀是 `[Lark]`。排障时用 `grep "Lark"` 过滤日志，不要被其他平台的报错干扰
- 确认飞书连接正常：搜索 `Lark.*connected` 看到 `connected to wss://msg-frontier.feishu.cn/ws/v2?...` 即正常

### Q: 我有两个飞书 Bot（如本地 + 腾讯云），会冲突吗？
- **不会冲突**。不同 APP_ID 是独立的飞书自建应用，各有独立的 WebSocket 连接、消息队列和权限
- 同一用户在不同 Bot 下的 open_id **不同**（open_id 是应用级而非用户级），这是飞书的设计
- 两套 `.env` 的 FEISHU_APP_ID / FEISHU_APP_SECRET 不要混用，各自独立维护
- 在飞书客户端中看到的是两个不同身份的 Bot 在回复，不是系统冲突

### Q: send_message 报 `Bot/User can NOT be out of the chat`
- Bot 尚未加入目标群聊或未与该用户建立对话
- 解决方案：在飞书客户端给 Bot 发一条消息，或在群聊中添加 Bot

### Q: Gateway WebSocket 连接失败
- 检查 `.env` 中 `FEISHU_APP_ID` 和 `FEISHU_APP_SECRET` 是否正确
- 重启 Gateway：`systemctl --user restart hermes-gateway.service`
- 查看日志：`journalctl --user -u hermes-gateway.service --no-pager -n 50`

### Q: WebSocket 连不上，日志显示 timeout（使用代理时）
- **根因**：Clash Verge（`verge-mihomo`）等代理可能无法转发飞书 WebSocket（`msg-frontier.feishu.cn`）的 WSS 连接
- **排查**：检查代理是否正常转发飞书：
  ```bash
  curl -s --connect-timeout 5 -x http://127.0.0.1:7897 https://open.feishu.cn
  ```
  如果 HTTP 000 或超时，说明代理无法转发飞书
- **解决**：将 `.feishu.cn` 加入 NO_PROXY，让飞书直连：
  ```bash
  cat ~/.config/systemd/user/hermes-gateway.service.d/proxy.conf
  sed -i 's/NO_PROXY=\(.*\)/NO_PROXY=\1,.feishu.cn/' \
    ~/.config/systemd/user/hermes-gateway.service.d/proxy.conf
  systemctl --user daemon-reload
  systemctl --user restart hermes-gateway.service
  ```

### Q: Gateway restart/stop 命令卡住（deactivating 状态）
- **根因**：Gateway 优雅关闭时某些 MCP 连接未及时响应 SIGTERM
- **解决**：强制 SIGKILL：
  ```bash
  systemctl --user kill -s SIGKILL hermes-gateway.service
  sleep 2
  systemctl --user reset-failed hermes-gateway.service
  systemctl --user start hermes-gateway.service
  ```

### Q: 配了 Gateway WebSocket 后 Bot 仍不回消息（老桥接干扰）
- **根因**：旧的 feishu-hermes 桥接服务（方式三，cloudflared + Node.js 3010）可能在后台运行，占用了飞书消息通道
- **排查**：`ps aux | grep -E "cloudflared|feishu-hermes" | grep -v grep`
- **解决**：停掉老服务：`pkill -f "feishu-hermes" 2>/dev/null && pkill -f "cloudflared.*3010" 2>/dev/null`

### Q: WebSocket 已连上，日志显示 connected，但 Bot 收不到用户消息
- **根因**：未在飞书开发者后台订阅 `im.message.receive_v1` 事件
- **解决**：
  1. 打开 [飞书开发者后台](https://open.feishu.cn/app) → 点击你的应用
  2. **事件与回调** → **添加事件** → 搜索 `im.message.receive_v1` → 添加
  3. 确认 **配置 WebSocket 事件** 已勾选
  4. **发布** 新版本
- **验收**：重启 Gateway 后，在飞书给 Bot 发消息，日志中出现 `[Lark] receive message` 即正常

### Q: 发送图片/文件时报错 code 99991672（Access denied）
- **根因**：Bot 缺少 `im:resource:upload` 或 `im:resource` 权限
- **解决**：
  1. 打开 [飞书开发者后台](https://open.feishu.cn/app) → 点击你的应用
  2. **权限管理** → 搜索 `im:resource` → 开启
  3. **发布** 新版本
- **验证**：重新调用 `send-image` 或上传文件接口
- **注意**：文本消息只需 `im:message:send_as_bot`，图片和文件需要额外 `im:resource` 权限

---

## Cron 定时任务推送

飞书可作为 Hermes cron 任务的推送目标。推送格式及完整配置参见 `references/cron-delivery.md`。

## 参考链接

- [飞书开放平台文档](https://open.feishu.cn/document)
- [lark-oapi Python SDK](https://github.com/larksuite/oapi-sdk-python)
- [飞书开发者后台](https://open.feishu.cn/app)
- 系统脚本：`~/.hermes/skills/feishu-openapi/scripts/feishu_client.py`
- 凭证排查完整流程：`references/credential-troubleshooting.md`
- Gateway 代理排障：`references/gateway-proxy-troubleshooting.md`
