# Open WebUI 0.9.6 + Hermes Bridge 整合

## 架构

```
浏览器 (Open WebUI :3000)
    ↕ HTTP (OpenAI 兼容 API)
Hermes Bridge (:9099) — FastAPI 代理
    ↕ subprocess
Hermes CLI — `hermes chat -q`
    ↕ API
DeepSeek / SiliconFlow
```

## 核心发现

### 1. Open WebUI 的外部连接不能持久化到数据库

Open WebUI 0.9.6 的外部 OpenAI 兼容连接（`OPENAI_API_BASE_URLS`、`OPENAI_API_KEYS`）是**运行时配置**——通过环境变量或 `/api/v1/configs/connections` API 设置，存储在内存中。重启后丢失。

**解决：** 启动脚本 `~/.hermes/scripts/open-webui.sh` 中通过 API 自动重新配置外部连接。

### 2. Open WebUI 管理员账户密码重置

Open WebUI 使用 SQLite 数据库存储用户凭证。可直接更新 auth 表：

```python
import bcrypt, sqlite3
hashed = bcrypt.hashpw(b"newpassword", bcrypt.gensalt(rounds=12))
db = sqlite3.connect("/path/to/webui.db")
db.execute("UPDATE auth SET password = ? WHERE email = ?", (hashed.decode(), "user@email.com"))
```

密码存储在 bcrypt 哈希中，不可反向解析。

### 3. 外部模型通过 Hermes Bridge 可用

- `siliconflow` → SiliconFlow 国际站 Qwen/Qwen3.6-35B-A3B（需代理 127.0.0.1:7897，延迟高）
- `deepseek-chat` → DeepSeek API（国内直连，速度快，推荐默认）

### 4. 通过 API 配置外部连接的 Python 工作流

```python
import requests
base = "http://localhost:3000"
# 登录
r = requests.post(f"{base}/api/v1/auths/signin", json={"email":"...","password":"..."})
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
# 配置外部连接
r = requests.post(f"{base}/api/v1/configs/connections", headers=headers, json={
    "ENABLE_DIRECT_CONNECTIONS": True,
    "ENABLE_BASE_MODELS_CACHE": True,
    "OPENAI_API_BASE_URLS": "http://localhost:9099/v1",
    "OPENAI_API_KEYS": "",
})
# 测试对话
r = requests.post(f"{base}/api/v1/chat/completions", headers=headers, json={
    "model": "siliconflow",
    "messages": [{"role": "user", "content": "hello"}],
    "stream": False,
}, timeout=60)
```

## Telegram 授权排查

### 现象

Bot 在 gateway 日志中显示 `Unauthorized user: 7090273400 (Andy M) on telegram`。

### 根因

`~/.hermes/.env` 中的 `TELEGRAM_ALLOWED_USERS` 填成了 **Bot ID**（`8819964718`）而不是 **用户 Telegram ID**（`7090273400`）。

### 授权机制

`gateway/run.py` 中的 `_is_user_authorized()` 检查顺序：
1. 平台级 allow-all 变量（如 `TELEGRAM_ALLOW_ALL_USERS=true`）
2. 环境变量 allowlists：`TELEGRAM_ALLOWED_USERS`（私聊 DM）、`TELEGRAM_GROUP_ALLOWED_CHATS`（群组）
3. DM pairing 批准列表
4. 全局 allow-all（`GATEWAY_ALLOW_ALL_USERS`）
5. 默认：拒绝

**关键：** `TELEGRAM_ALLOWED_USERS` 是 env var 驱动的（从 `.env` 读取），不来自 `config.yaml` 的 `telegram.allowed_chats` 段。`allowed_chats` 只控制群组消息白名单，不控制 DM 授权。

### 修复

```bash
sed -i 's/TELEGRAM_ALLOWED_USERS=OLD_BOT_ID/TELEGRAM_ALLOWED_USERS=CORRECT_USER_ID/' ~/.hermes/.env
systemctl --user restart hermes-gateway
```
