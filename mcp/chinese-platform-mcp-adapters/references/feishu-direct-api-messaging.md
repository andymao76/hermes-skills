# 飞书直接 API 消息发送（绕过 send_message）

## 背景

当 Feishu 已通过 Hermes Gateway 连接（WebSocket），但 `send_message(action='list')` 中不显示飞书目标时，可以直接通过飞书 Open API 发送消息。

## 前置条件

- 飞书 App ID 和 App Secret（配置在 `~/.hermes/.env` 的 `FEISHU_APP_ID` / `FEISHU_APP_SECRET`）
- 目标用户的 `open_id`（可通过飞书开放平台控制台获取）

## API 工作流

### 步骤 1：获取 tenant_access_token

```bash
curl -s -X POST 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal' \
  -H 'Content-Type: application/json' \
  -d '{"app_id":"<APP_ID>","app_secret":"<APP_SECRET>"}'
```

返回：`{"code":0,"tenant_access_token":"t-g1046af1...","expire":7200}`

### 步骤 2：发送文本消息

```bash
curl -s -X POST 'https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id' \
  -H 'Authorization: Bearer <TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{
    "receive_id": "ou_xxxxx",
    "msg_type": "text",
    "content": "{\"text\":\"消息内容\"}"
  }'
```

注意 `content` 字段是**二次序列化的 JSON 字符串**（内层的 JSON 需要被转义为字符串）。

### 步骤 3：验证

返回 `{"code":0,"data":{"message_id":"om_xxxxx"}}` 表示发送成功。

## 从 execute_code 中调用（推荐）

```python
import json, requests

# 获取 token
r = requests.post('https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
    json={"app_id": "cli_xxx", "app_secret": "xxx"})
token = r.json()['tenant_access_token']

# 发送消息
payload = {
    "receive_id": "ou_xxx",
    "msg_type": "text",
    "content": json.dumps({"text": "消息内容"})
}
r = requests.post(
    'https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id',
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    json=payload
)
print(r.json())
# → {"code": 0, "data": {"message_id": "om_xxx"}}
```

## 注意事项

- Token 有效期 2 小时，过期需重新获取
- `receive_id_type` 可选 `open_id`（推荐）、`user_id`、`union_id`、`chat_id`（群聊）
- 飞书国内版端点：`open.feishu.cn`
- 飞书国际版（Lark）端点：`open.larksuite.com`
- 文本消息的 `content` 字段是 JSON 字符串，不是对象本身——这是飞书 API 的特性

## 优先使用 send_message（关键发现）

**`send_message` 原生支持飞书**，即使飞书不出现在 `send_message(action='list')` 的目标列表中。飞书是 bot-to-user 模式，channel_directory 可能一直为空，但这不影响发送。

### 格式

```
target="feishu:ou_xxx"        # 发给个人（open_id）
target="feishu:chat_xxx"      # 发给群聊
```

支持的前缀（来自 `_FEISHU_TARGET_RE` 正则）：
- `ou_` — 用户 open_id（个人 DM 用这个）
- `oc_` — 群聊 open_chat_id
- `on_` — 其他 open_id 格式
- `chat_` — 群聊 chat_id
- `open_` — 其他 open ID

### 为什么飞书不在 list 结果中？

因为飞书不像 Discord/Telegram 那样有频道发现机制——它是 bot 主动发送到指定用户。`send_message(list)` 只返回 channel_directory 中已注册的条目，飞书的这个列表始终为空。**这不影响发送。**

### 示例

```python
send_message(target="feishu:ou_a74c0eb0ff0f216d5036c2300a213d22",
             message="测试消息")
# → {"success": true, "platform": "feishu", "chat_id": "ou_xxx", "message_id": "om_xxx"}
```

### 实现原理

`_send_feishu()` 函数（在 `send_message_tool.py` 中）每次调用时**新建一个 FeishuAdapter 实例**并直接构建 lark client，不依赖 gateway 的运行中 adapter。所以即使 gateway 尚未启动或 adapter 未注册到 channel_directory，也能独立发送。

## 直接 API 方式（当 send_message 不可用时）

如果 `send_message` 工具本身不可用（例如在 subagent 中但未加载 send_message 工具集），才回退到直接 API 方式。

## 关联资源

- [[feishu-lark-connection-guide]] — Hermes Gateway 接入方案
- 飞书 Open API 文档：`https://open.feishu.cn/document/server-docs/im-v1/message/create`
