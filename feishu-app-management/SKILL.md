---
name: feishu-app-management
description: 飞书应用管理 — 停用、删除、清理本地配置的完整流程
category: productivity
tags:
  - feishu
  - lark
  - app-management
  - cleanup
---

# 飞书应用管理

飞书应用生命周期管理：停用 API、删除应用、清理本地配置。

---

## 场景一：停用飞书应用（不删除）

通过飞书开放平台 API 将应用设置为 `enable: false`，Bot 停止响应，但应用保留。

### 前置条件

1. 应用的 **APP_ID** 和 **APP_SECRET**
2. 应用中已开通 `admin:app.enable:write` 权限

### 授权权限

如果尚未授权，访问以下链接（替换 `{app_id}`）：

```
https://open.feishu.cn/app/{app_id}/auth?q=admin:app.enable:write&op_from=openapi&token_type=tenant
```

### 执行停用

```python
import json, http.client

app_id = 'cli_xxx'
app_secret = 'xxx'

# Step 1: 获取 tenant_access_token
conn = http.client.HTTPSConnection('open.feishu.cn')
conn.request('POST', '/open-apis/auth/v3/tenant_access_token/internal',
    body=json.dumps({'app_id': app_id, 'app_secret': app_secret}),
    headers={'Content-Type': 'application/json'}
)
token = json.loads(conn.getresponse().read().decode())['tenant_access_token']

# Step 2: 停用应用（enable: false）
conn2 = http.client.HTTPSConnection('open.feishu.cn')
conn2.request('PUT', f'/open-apis/application/v6/applications/{app_id}/management',
    body=json.dumps({'enable': False}),
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
)
resp = conn2.getresponse()
result = json.loads(resp.read().decode())

if result.get('code') == 0:
    print('✅ 应用已停用')
else:
    print(f'❌ 失败: {result}')
```

### 重新启用

将请求体改为 `{"enable": true}` 即可恢复。

---

## 场景二：删除应用（在飞书开放平台删除）

### 手动删除步骤

1. 访问 [飞书开发者后台](https://open.feishu.cn/app)
2. 找到目标应用
3. 进入「应用详情」→「设置」→「删除应用」
4. 确认删除

### 删除后本地清理

应用删除后，需要清理本地 Hermes 配置：

```bash
# 1. 禁用飞书平台（Gateway 不再尝试连接）
hermes config set platforms.feishu.enabled false

# 2. 重启 Gateway
systemctl --user restart hermes-gateway.service

# 3. 验证飞书不再出现
send_message(action='list')
# 应不再显示 feishu 目标
```

### .env 凭证处理

`.env` 中的飞书凭证可以保留（不会造成影响），也可以手动移除：

```bash
# 查看当前飞书配置
grep FEISHU_ ~/.hermes/.env

# 如需清理，编辑 ~/.hermes/.env 删除 FEISHU_* 行
```

---

## 常见错误

| 错误码 | 含义 | 解决 |
|--------|------|------|
| `99991672` | 缺少 `admin:app.enable:write` 权限 | 点击错误信息中的授权链接开通 |
| `10014` | APP_SECRET 无效 | 检查密钥是否正确、是否截断 |
| `230002` | Bot 不在聊天中 | 需要先在飞书中添加 Bot 到群聊或发送消息 |

---

## 参考

- API 文档：https://open.feishu.cn/document/server-docs/application-v6/application/management
- 权限说明：`admin:app.enable:write` — 控制应用启停
