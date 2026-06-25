---
name: feishu-agent
description: 飞书（Feishu/Lark）全栈集成 — 开放平台 API 直连 + Gateway WebSocket 双向通信，覆盖消息收发、Bot 配置、用户权限管理、审批通知
version: 1.1.0
author: andymao
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [feishu, lark, messaging, gateway, bot, api, websocket]
    related_skills: [feishu-openapi, feishu-integration-guide, feishu-doc-manager, feishu-voice-reply]
    requires_toolsets: [terminal, web]
    config:
      - key: platforms.feishu.enabled
        description: 飞书平台开关
        default: true
        prompt: 启用飞书平台?
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
    required_for: Gateway WebSocket 模式
  - name: FEISHU_DOMAIN
    prompt: 域名 (国内 feishu / 海外 lark)
    required_for: API 域名
  - name: FEISHU_ALLOWED_USERS
    prompt: 允许与 Bot 通信的用户 open_id 列表（逗号分隔）
    required_for: 用户权限管控
  - name: FEISHU_HOME_CHANNEL
    prompt: 默认发送消息的 open_id
    required_for: send_message 自动路由
---

# 飞书全栈集成（Feishu Agent）

飞书（Lark）与 Hermes Agent 的全栈集成方案。覆盖从凭证配置、API 测试、Gateway WebSocket 连接到日常消息收发和权限管理的完整生命周期。

## When to Use

- 配置或排查飞书 Bot 连接时
- 通过飞书发送消息（文本/图片/文件/富文本卡片）
- 让飞书用户能与 Hermes Agent 双向对话
- 管理飞书 Bot 的用户白名单和群聊策略
- 将飞书文档与 Hermes 知识库联动

## 架构概览

```
┌──────────────┐     ┌─────────────────────┐     ┌──────────────┐
│  飞书客户端   │ ←─→ │  Hermes Gateway      │ ←─→ │  LLM + Tools  │
│  (PC/手机)    │     │  (WebSocket 长连接)   │     │  (推理与执行)   │
└──────────────┘     └─────────────────────┘     └──────────────┘
       │                      │
       │              ┌───────┴────────┐
       │              │ lark-oapi SDK   │
       └──────────────│ (REST API 直连)  │
                      └────────────────┘
```

两种集成模式：
| 模式 | 方向 | 适用场景 |
|------|------|----------|
| **API 直连** | Hermes → 飞书 | 主动推送消息、文档管理 |
| **Gateway WebSocket** | 飞书 ↔ Hermes | 双向对话、实时交互 |

## Quick Reference

### 核心命令

```bash
# 验证凭证有效性
source ~/.hermes/.env
python3 -c "
import requests
r = requests.post('https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
    json={'app_id': '$FEISHU_APP_ID', 'app_secret': '$FEISHU_APP_SECRET'})
print('OK' if r.json().get('code') == 0 else 'FAIL: ' + r.json().get('msg',''))
"

# 获取 Bot 信息
python3 -c "
import requests
r = requests.post('https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
    json={'app_id': '$FEISHU_APP_ID', 'app_secret': '$FEISHU_APP_SECRET'})
token = r.json()['tenant_access_token']
r2 = requests.get('https://open.feishu.cn/open-apis/bot/v3/info',
    headers={'Authorization': f'Bearer {token}'})
print(r2.json().get('bot',{}).get('app_name','?'))
"

# 发送文本消息
source ~/.hermes/.env 2>/dev/null
~/.hermes/venv/bin/python3 ~/.hermes/skills/feishu-openapi/scripts/feishu_client.py \
  send-text "ou_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" "消息内容"

# 搜索群聊
~/.hermes/venv/bin/python3 ~/.hermes/skills/feishu-openapi/scripts/feishu_client.py \
  search-chat "群名关键词"
```

### Gateway 管理

```bash
systemctl --user start hermes-gateway.service    # 启动
systemctl --user stop hermes-gateway.service     # 停止
systemctl --user restart hermes-gateway.service  # 重启
systemctl --user status hermes-gateway.service   # 状态
journalctl --user -u hermes-gateway.service -f   # 实时日志
```

### 飞书相关日志过滤

```bash
journalctl --user -u hermes-gateway.service --no-pager -n 100 | grep -iE "lark|feishu|飞书"
tail -50 ~/.hermes/logs/gateway.log | grep -i "lark\|feishu"
```

## Procedure

### 1. 前提准备

1. 在 [飞书开发者后台](https://open.feishu.cn/app) 创建自建应用
2. 获取 `App ID` 和 `App Secret`
3. 添加必要权限（`im:message:send_as_bot`、`im:chat:readonly` 等）
4. **发布应用**（开发版本不代表上线，需创建版本并申请发布）
5. 在飞书搜索 Bot 名称并添加好友

### 2. 环境配置

将以下变量追加到 `~/.hermes/.env`（不要直接修改，用 echo `>>`）：

```bash
cat >> ~/.hermes/.env << 'EOF'
FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FEISHU_CONNECTION_MODE=websocket
FEISHU_DOMAIN=feishu
FEISHU_ALLOW_ALL_USERS=false
FEISHU_ALLOWED_USERS=ou_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FEISHU_HOME_CHANNEL=ou_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FEISHU_GROUP_POLICY=disabled
EOF
```

### 3. 安装 SDK

```bash
~/.hermes/venv/bin/pip install lark-oapi
```

### 4. 验证凭证

确认 APP_ID 和 APP_SECRET 有效（见 Quick Reference 章节）。

### 5. 首次部署：发现用户 open_id

**这是最常见的踩坑点** — 需要 open_id 来配置权限，但需要先收到消息才知道 open_id。

解法：临时开放所有用户 → 启动 Gateway → 在飞书发消息 → 从日志捕获 open_id → 收紧配置。

详见 `feishu-integration-guide` skill 的「首次部署：发现用户 open_id」章节。

### 6. 启用 feishu 平台并启动 Gateway

```bash
hermes config set platforms.feishu.enabled true
systemctl --user start hermes-gateway.service
sleep 10
journalctl --user -u hermes-gateway.service --no-pager -n 30 | grep -i "lark.*connected"
```

### 7. 日常使用

- **飞书发消息给 Bot** → Gateway 自动接收并进入 Hermes 会话
- **Hermes 主动推送到飞书** → 在会话中执行 `send_message`
- **调用 API 发送** → 使用 `feishu-openapi` 技能中的 `feishu_client.py` 脚本

## Pitfalls

### open_id 跨应用不通用

同一用户在不同飞书自建应用下的 open_id 不同。从一台机器复制到另一台机器的 open_id 无效，每次新部署都要重新发现。

### Gateway 启动但不响应飞书消息

最常见原因：
1. `FEISHU_ALLOWED_USERS` 未配置或配置了错误的 open_id → 日志显示 `Unauthorized user`
2. Bot 未在飞书端被用户添加 → 日志显示 `User/Bot not in chat`
3. 应用未发布（开发版本不对外）→ Gateway 连上但无事件推送

排查：
```bash
journalctl --user -u hermes-gateway.service --no-pager -n 50 | grep -i "lark\|feishu\|unauthorized\|error"
```

### API 直连正常但 Gateway 收不到消息

- 确认 `.env` 中有 `FEISHU_CONNECTION_MODE=websocket`
- Gateway 重启需要 5-10 秒 WebSocket 握手，检查日志中的 `connected to wss://`
- 飞书开放平台 → 事件订阅 → 确认 WebSocket 事件已添加（`im.message.receive_v1`）

### 群聊消息收不到

- `FEISHU_GROUP_POLICY` 需设为 `open`
- Bot 必须被拉入目标群聊
- 群聊消息在飞书 API 中需要 `im:chat:readonly` 权限

### 凭证泄露风险

`.env` 包含 APP_SECRET，该文件已通过 Hermes 默认的 `600` 权限保护。不要将其提交到 Git 或分享。

## 关联技能

| 技能 | 用途 |
|------|------|
| `feishu-openapi` | lark-oapi SDK 使用、API 直连发消息/图片/文件 |
| `feishu-integration-guide` | 详细配置步骤、凭证说明、问题排查（1:1 替换本技能的前身） |
| `feishu-doc-manager` | 飞书文档管理（创建/读取/编辑文档） |
| `feishu-voice-reply` | 文字转飞书语音消息发送 |

## Verification

部署完成后验证：
1. `journalctl` 中有 `[Lark] connected to wss://...` 日志 ✅
2. 从飞书客户端给 Bot 发消息，Hermes 有响应 ✅
3. 在 Hermes 会话中执行 `send_message` 飞书用户能收到 ✅
4. `hermes doctor` 不报飞书相关错误 ✅
