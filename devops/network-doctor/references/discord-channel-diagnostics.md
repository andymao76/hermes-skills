# Discord 频道诊断参考

## 修复记录：2026-06-11 Discord 404 Unknown Channel + Home Channel 配置错位

### 故障现象

```
# Gateway 日志
ERROR [...] [Discord] Failed to send Discord message: 404 Not Found (error code: 10003): Unknown Channel

# send_message 工具报错
Discord send failed:       # 空错误信息
No home channel set for discord  # 即便 config.yaml 已设置
```

### 根因分析

**Root Cause 1 — Home Channel ID 错误：**

配置的 `DISCORD_HOME_CHANNEL` 频道 ID 与实际 Discord #综合 频道不符。

| 配置值（错误） | 实际值（正确） |
|---------------|--------------|
| `1511985583709491200` | `1511985583709491244` |

后 4 位不同，应是从 Discord 复制时手误。

**Root Cause 2 — 配置写在 config.yaml 但 Gateway 读的是 .env：**

| 配置位置 | 作用域 | 读取方式 |
|----------|--------|----------|
| `config.yaml` 的 `DISCORD_HOME_CHANNEL: ...` | CLI Agent 会话 | `hermes config set` 写入此处 |
| `~/.hermes/.env` 的 `DISCORD_HOME_CHANNEL=...` | Gateway 进程（systemd） | `os.getenv("DISCORD_HOME_CHANNEL")` |

Gateway 启动时通过 `load_hermes_dotenv()` 加载 `.env` 到 `os.environ`，**不读取 `config.yaml` 的平键值**。所以只改 `config.yaml` 对 Gateway 无效。

**Root Cause 3 — send_message 工具在当前 Agent 会话中失败：**

即使 `.env` 已修正，当前 Agent 会话的 `os.environ` 在启动时已加载完毕。`send_message` 工具的 `_standalone_send()` 读取的是进程级环境变量，需 `/exit` 重新会话。

### 修复步骤

#### Step 1: 确认 Discord Bot Token 有效

```bash
DISCORD_TOKEN=*** DISCORD_BOT_TOKEN ~/.hermes/.env | cut -d= -f2-)
curl -s -o /dev/null -w "HTTP %{http_code} | %{time_total}s\n" \
  --max-time 10 -x http://127.0.0.1:7897 \
  "https://discord.com/api/v10/users/@me" \
  -H "Authorization: Bot $DISCORD_TOKEN"
```

期望 `HTTP 200`。

#### Step 2: 验证 Home Channel ID

```bash
DISCORD_TOKEN=*** DISCORD_BOT_TOKEN ~/.hermes/.env | cut -d= -f2-)
CHANNEL_ID=1511985583709491244  # 替换为要验证的 ID
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  --max-time 10 -x http://127.0.0.1:7897 \
  "https://discord.com/api/v10/channels/${CHANNEL_ID}" \
  -H "Authorization: Bot $DISCORD_TOKEN"
```

- `HTTP 200` → 频道存在
- `HTTP 404` → 频道 ID 错误（最常见）

#### Step 3: 同步配置到两个位置

```bash
# 1) config.yaml（用于 CLI Agent 的 send_message 工具）
hermes config set DISCORD_HOME_CHANNEL 1511985583709491244

# 2) .env（用于 Gateway 进程 — 关键！容易被忘）
echo 'DISCORD_HOME_CHANNEL=1511985583709491244' >> ~/.hermes/.env

# 验证
grep DISCORD_HOME_CHANNEL ~/.hermes/config.yaml
grep DISCORD_HOME_CHANNEL ~/.hermes/.env
```

#### Step 4: 重启 Gateway

Gateway 的 SIGTERM 优雅关闭经常**卡在 deactivating**（子进程连接未断开），需要用 SIGKILL：

```bash
systemctl --user kill -s SIGKILL hermes-gateway.service
sleep 5
systemctl --user status hermes-gateway.service   # 确认 auto-restart 后 active
```

#### Step 5: 验证投递

直接用 Discord REST API 验证（不依赖 Agent 会话的环境变量）：

```bash
DISCORD_TOKEN=*** DISCORD_BOT_TOKEN ~/.hermes/.env | cut -d= -f2-)
curl -s -m 15 -X POST \
  "https://discord.com/api/v10/channels/1511985583709491244/messages" \
  -H "Authorization: Bot $DISCORD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"✅ 测试消息"}' \
  -x http://127.0.0.1:7897
```

成功返回包含 `"id":"..."` 和 `"channel_id":"..."` 的 JSON。

### 经验总结

| 教训 | 说明 |
|------|------|
| 频道 ID 必须精确 | Discord 频道 ID 是 19 位整数，最后几位极易复制错 |
| 两处配置 | `config.yaml` 供 CLI Agent 用，`.env` 供 Gateway 用，缺一不可 |
| Gateway 优雅关闭常挂 | SIGKILL 强制杀后 systemd 自启，比等 graceful shutdown 快 |
| send_message 环境隔离 | 当前 Agent 会话的 `.env` 在启动时已加载，改 `.env` 后需 `/exit` 重连 |
| Discord 无连接日志 | 正常现象 — Discord adapter 不输出 "connected" 到 journalctl，无报错即正常 |

## 常见问题：Discord 发送消息失败

### 1. 验证 Discord Bot Token 有效

```bash
# 通过代理直连 Discord API 验证 token
DISCORD_TOKEN=$(grep DISCORD_BOT_TOKEN ~/.hermes/.env | cut -d= -f2-)
curl -s -o /dev/null -w "HTTP %{http_code} | %{time_total}s\n" \
  --max-time 10 \
  -x http://127.0.0.1:7897 \
  "https://discord.com/api/v10/users/@me" \
  -H "Authorization: Bot $DISCORD_TOKEN"
```
期望返回 `HTTP 200`。

### 2. 验证 Home Channel ID 正确

```bash
DISCORD_TOKEN=$(grep DISCORD_BOT_TOKEN ~/.hermes/.env | cut -d= -f2-)
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  --max-time 10 \
  -x http://127.0.0.1:7897 \
  "https://discord.com/api/v10/channels/${CHANNEL_ID}" \
  -H "Authorization: Bot $DISCORD_TOKEN"
```
- `HTTP 200` → 频道存在
- `HTTP 404` (error code 10003: Unknown Channel) → 频道 ID 错误
- `HTTP 403` → Bot 无权访问该频道

### 3. 发送测试消息

```bash
DISCORD_TOKEN=$(grep DISCORD_BOT_TOKEN ~/.hermes/.env | cut -d= -f2-)
curl -s -m 15 -X POST \
  "https://discord.com/api/v10/channels/${CHANNEL_ID}/messages" \
  -H "Authorization: Bot $DISCORD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"测试消息 ✅"}' \
  -x http://127.0.0.1:7897
```
成功返回包含 `"id":"..."` 和 `"channel_id":"..."` 的 JSON。

### 4. 检查 Gateway 日志中的 Discord 报错

```bash
journalctl --user -u hermes-gateway.service --since "5 min ago" --no-pager | grep -iE "discord|Unknown Channel"
```

常见错误：
- `error code: 10003: Unknown Channel` → Home channel ID 错误
- `error code: 50001: Missing Access` → Bot 未加入服务器或无权限
- `error code: 50013: Missing Permissions` → Bot 缺少发消息权限

### 5. Home Channel 配置同步检查

Discord Home Channel 需要在**两个地方**同时设置：

| 配置位置 | 作用域 | 检查命令 |
|----------|--------|----------|
| `config.yaml` | CLI Agent（send_message 工具） | `grep DISCORD_HOME_CHANNEL ~/.hermes/config.yaml` |
| `~/.hermes/.env` | Gateway 进程 | `grep DISCORD_HOME_CHANNEL ~/.hermes/.env` |

**Gateway 进程读取的是 `.env` 中的环境变量，不是 `config.yaml`。** 缺少任一个都会导致对应环境发送失败。

### 6. Gateway "卡在 deactivating" 无法重启

```bash
# 强制重启
systemctl --user kill -s SIGKILL hermes-gateway.service
sleep 5
systemctl --user status hermes-gateway.service
```

### 7. Home Channel 未设置时的备选发送

如果 Home Channel 未配置，可以临时指定频道名：
```bash
# 格式：discord:#频道名
hermes send -t 'discord:#综合' "消息内容"

# 或直接在 send_message 工具中使用
send_message(target="discord:#综合", message="...")
```
