# Open WebUI 离线数据库操作

当无法使用浏览器访问 Open WebUI 管理面板时，可通过 SQLite 直接管理。

## 数据库路径

```
~/open-webui/.venv/lib/python3.12/site-packages/open_webui/data/webui.db
```

## 关键表

| 表名 | 列 | 用途 |
|------|-----|------|
| `user` | id, name, email, role | 用户信息 |
| `auth` | id, email, password | bcrypt 加密密码 |
| `config` | id (INTEGER), data (JSON), version, created_at, updated_at | 应用配置 |
| `api_key` | id, user_id, key, data, expires_at... | API 密钥 |

## 常用操作

### 修改管理员密码

```python
import sqlite3, bcrypt
db = sqlite3.connect('webui.db')
hashed = bcrypt.hashpw(b'新密码', bcrypt.gensalt(rounds=12))
db.execute('UPDATE auth SET password = ? WHERE email = ?', (hashed.decode(), 'admin@example.com'))
db.commit()
```

### 设置默认模型

```python
import sqlite3, json
db = sqlite3.connect('webui.db')
row = db.execute('SELECT id, data FROM config WHERE id = 1').fetchone()
config = json.loads(row[1])
config['default_models'] = 'deepseek-chat'
db.execute('UPDATE config SET data = ? WHERE id = 1', (json.dumps(config),))
db.commit()
```

### 配置外部连接（运行时 API）

Open WebUI 的外部 OpenAI 兼容连接不持久化到 SQLite，重启后丢失。
启动后需通过 API 重新配置：

```bash
# 获取 token
TOKEN=$(curl -s -X POST http://localhost:3000/api/v1/auths/signin \
  -H "Content-Type: application/json" \
  -d '{"email":"...","password":"..."}' | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")

# 设置外部连接
curl -s -X POST http://localhost:3000/api/v1/configs/connections \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ENABLE_DIRECT_CONNECTIONS":true,"OPENAI_API_BASE_URLS":"http://localhost:9099/v1","OPENAI_API_KEYS":""}'
```

### 查看用户列表

```bash
python3 -c "
import sqlite3
db = sqlite3.connect('~/open-webui/.venv/lib/python3.12/site-packages/open_webui/data/webui.db')
for u in db.execute('SELECT id, name, email, role FROM user').fetchall():
    print(f'{u[1]} ({u[2]}) — {u[3]}')
"
```

## Pitfalls

- **外部连接不持久化**：Open WebUI 0.9.6 的 OpenAI 兼容连接是运行时状态，重启后必须通过 API 重新配置。`open-webui.sh` 的 start 脚本已包含自动重配置逻辑。
- **bcrypt rounds=12**：需匹配 Open WebUI 的 bcrypt 参数（`gensalt(rounds=12)`），否则密码不生效。
- **配置缓存**：修改 `config` 表后必须重启 Open WebUI 才能生效。
- **端口冲突**：`[Errno 98] address already in use` → 用 `ss -tlnp | grep <端口>` 找到旧进程 PID，`kill -9` 强制杀掉，再用 `ss -tlnp | grep <端口>` 确认释放。
- **Hermes Bridge 僵尸进程**：PID 文件存在但进程不响应时，用 `ss -tlnp | grep 9099` 找到实际绑定进程再 kill。
- **config.data 字段是 JSON 字符串**：更新时需要用 `json.dumps()` 序列化，不能直接写字符串。
- **token 过期**：Open WebUI 的 API token 约 4 周过期，过期后需要重新登录获取。
