---
name: discord-skillhub
description: Discord 操作参考 — 发送消息、反应、贴纸、投票、线程、钉选、搜索、权限、成员信息。
  Skillhub 导入版，来自 Clawdbot Discord Actions。
category: productivity
---

# Discord Actions（Skillhub 版）

来自 Clawdbot 生态的 Discord 操作参考。使用 `discord` 工具管理消息、反应、线程、投票和管理。

## 操作参考

### 反应

```json
{
  "action": "react",
  "channelId": "123",
  "messageId": "456",
  "emoji": "✅"
}
```

### 发送消息

```json
{
  "action": "sendMessage",
  "to": "channel:123",
  "content": "Hello from Hermes"
}
```

### 创建投票

```json
{
  "action": "poll",
  "to": "channel:123",
  "question": "Lunch?",
  "answers": ["Pizza", "Sushi", "Salad"],
  "allowMultiselect": false,
  "durationHours": 24
}
```

### 其他操作
- `threadCreate` / `threadList` / `threadReply`
- `pinMessage` / `listPins`
- `searchMessages`
- `permissions` / `memberInfo` / `roleInfo` / `channelInfo`

## Discord 写作风格

- 短小精悍，1-3 句
- 用 emoji 调节语气
- 不用 Markdown 表格（Discord 渲染为纯文本）
- `**bold**` 用于强调，`code` 用于技术术语
- 多个链接用 `<>` 包裹以抑制嵌入

> 注：这是 Skillhub 导入的 Discord 操作参考。Hermes Gateway 已经内置了 Discord 消息推送功能。
