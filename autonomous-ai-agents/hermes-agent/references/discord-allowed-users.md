# DISCORD_ALLOWED_USERS: Discord 机器人用户权限白名单

## 问题

在 Discord 服务器中，其他成员 @andymaobot 或发消息，**机器人完全不回复**，但机器人本身在线、网关运行正常。

## 根因

`~/.hermes/.env` 中配置了 `DISCORD_ALLOWED_USERS` 白名单，只允许指定的 Discord 用户 ID 与机器人交互：

```
DISCORD_ALLOWED_USERS=848476942923726859
```

不在白名单中的用户发消息，Hermes gateway 自动忽略，不进入会话循环。

## 排查步骤

```bash
# 1. 检查是否设置了白名单
grep DISCORD_ALLOWED_USERS ~/.hermes/.env

# 2. 如果设置了，确认当前用户的 Discord ID 是否在其中
#    获取自己的 Discord ID：Discord → 设置 → 高级 → 开发者模式 → 右键用户名 → 复制 ID
```

## 解决方案

### 方案 A：添加特定用户（推荐）

```bash
# 逗号分隔多个用户 ID
sed -i 's/DISCORD_ALLOWED_USERS=848476942923726859/DISCORD_ALLOWED_USERS=848476942923726859,新用户ID1,新用户ID2/' ~/.hermes/.env
```

### 方案 B：完全移除限制（开放给所有人）

```bash
sed -i '/DISCORD_ALLOWED_USERS/d' ~/.hermes/.env
```

## 生效

修改 `.env` 后必须重启 gateway：

```bash
hermes gateway restart
```

或从 gateway session 内 `/restart`。

## 与其他平台对比

| 平台 | 环境变量 | 说明 |
|------|---------|------|
| Discord | `DISCORD_ALLOWED_USERS` | 逗号分隔的 Discord 用户 ID |
| Telegram | `TELEGRAM_ALLOWED_USERS` | 逗号分隔的 Telegram 用户 ID（控制 DM，群组用 `allowed_chats`） |
| WhatsApp | `WHATSAPP_ALLOWED_USERS` | 逗号分隔的手机号 |
| WeChat | `WEIXIN_ALLOWED_USERS` | 逗号分隔的微信 ID |

## 注意

- `DISCORD_ALLOWED_USERS` 仅限制**谁可以向机器人发送消息**，不限制机器人向谁发送。
- `send_message(target="discord")` 不受此变量限制——机器人可以主动向任何频道/用户发消息。
- 此变量只在 `.env` 中生效，`config.yaml` 的 `discord.allowed_channels` 控制的是频道白名单（空字符串 = 全部允许），两者是独立维度。
