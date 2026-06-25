# Discord 404 Unknown Channel 排查实录

## 现象

Gateway 日志中反复出现：

```
ERROR [Discord] Failed to send Discord message: 404 Not Found (error code: 10003): Unknown Channel
```

Bot 确实在线（无连接失败日志），但每次尝试发送消息都报 404。

## 排查过程

### 1. 确认 Gateway 在线

```bash
systemctl --user status hermes-gateway.service
# → active (running), PID 1892
```

### 2. 检查 Discord Bot Token & 连接

```bash
# 验证 Gateway 进程中有 Discord 日志
journalctl --user -u hermes-gateway.service --since "1 hour ago" | grep -i discord
# → 有 ERROR 行，但无 connect failed / auth failed
```

### 3. 验证 Discord API 连通性（网络层）

```bash
curl -s -o /dev/null -w "HTTP %{http_code} | %{time_total}s" \
  --max-time 5 --socks5-hostname localhost:7897 \
  https://discord.com/api/v10/gateway
# → HTTP 200 | 0.188s  ✅ API 可达
```

### 4. 检查 Home Channel 配置

```bash
grep "DISCORD_HOME_CHANNEL" ~/.hermes/config.yaml
# → DISCORD_HOME_CHANNEL: 1511985583709491200
```

对比已知的正确频道 ID（#综合频道）：

| 字段 | 值 |
|------|-----|
| 已配置 | `1511985583709491200` |
| 正确值 | `1511985583709491244` |

只有最后 4 位不同（`1200` vs `1244`）—— 推测是复制粘贴时手误。

### 5. 修复

**两处同步，缺一不可：**

```bash
# 1) config.yaml — 供 CLI Agent 用
hermes config set DISCORD_HOME_CHANNEL 1511985583709491244

# 2) .env — 供 Gateway 进程用（关键！容易被忘）
echo 'DISCORD_HOME_CHANNEL=1511985583709491244' >> ~/.hermes/.env

# 验证
grep DISCORD_HOME_CHANNEL ~/.hermes/config.yaml
grep DISCORD_HOME_CHANNEL ~/.hermes/.env
```

**重启 Gateway（systemctl restart 可能卡住，用 SIGKILL）：**

```bash
systemctl --user kill -s SIGKILL hermes-gateway.service
sleep 5
systemctl --user status hermes-gateway.service
```

## 关键教训

- Discord Bot 能登录 ≠ 能发送消息。Bot 在线但 HOME_CHANNEL 错就会 404。
- 404 Unknown Channel 的根因几乎总是 **HOME_CHANNEL 频道 ID 错误**，而不是 Bot 掉线。
- 频道 ID 是 Discord 中的数字 ID（右键频道 → 复制 ID），不是频道名称。
- **④ Gateway 读取的是 `.env` 中的 `DISCORD_HOME_CHANNEL`，不是 config.yaml**。只改 config.yaml 对 Gateway 无效。两处都需要设置。
- 改完 `.env` 后当前 Agent 会话的 `send_message` 工具仍会失败 — 需 `/exit` 重连。
- **④ Gateway 的 systemctl restart 常卡在 "deactivating"** — 原因：Discord 客户端库或其他子进程不响应 SIGTERM。30 秒后应使用 SIGKILL。
- **④ Discord 日志无 "connected" 输出** — 与飞书不同，Discord adapter 不输出连接成功日志到 journal。无 ERROR 即正常。
- Gateway 在关闭过程中尝试发送消息也会触发 404 —— 这时的 404 不是配置问题，是 Gateway 正在关闭、Discord 连接已被部分销毁。
