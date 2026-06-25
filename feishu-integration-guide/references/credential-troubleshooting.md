# 飞书凭证排查与修复

## 常见错误码速查

| 错误码 | 含义 | 根因 |
|--------|------|------|
| `code: 0` | 成功 | — |
| `code: 10003` | invalid param | APP_ID 或 APP_SECRET 格式不正确/不存在 |
| `code: 10014` | app secret invalid | APP_SECRET 错误（多/少字符、过期、混用） |

## 完整排查流程

### 第 1 步：curl 直测凭证

绕过 SDK 和 Gateway，直接验证凭证是否有效：

```bash
curl -s -X POST 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal' \
  -H 'Content-Type: application/json' \
  -d '{"app_id":"cli_xxxxxxxxxxxxxxxxxxxx","app_secret":"xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}'
```

**期望结果**：`{"code": 0, "tenant_access_token": "t-...", "expire": 3600, "msg": "ok"}`

### 第 2 步：检查 .env 文件完整性

security.redact_secrets 会让 `grep`/`cat` 显示 `***` 掩盖密钥，**但文件的原始内容不变**。用 hexdump 确认：

```bash
grep "^FEISHU_APP_SECRET" ~/.hermes/.env | xxd
```

**正常输出示例**（密钥 28 字符左右）：
```
00000000: 4645 4953 4855 5f41 5050 5f53 4543 5245  FEISHU_APP_SECRE
00000010: 543d 7739 3744 4a4b 7151 694e 6568 4766  T=w97DJKqQiNehGf
00000020: 4c33 7741 6946 3050 4566 4351 5350 3541  L3wAiF0PEfCQSP5A
00000030: 3563 0a                                   5c.
```

**异常输出示例**（被截断）：
```
00000000: 4645 4953 4855 5f41 5050 5f53 4543 5245  FEISHU_APP_SECRE
00000010: 543d 7739 3744 4a4b 2e2e 2e35 4135 630a  T=w97DJK...5A5c.
```

### 第 3 步：修复 .env 文件

如果密钥被截断或损坏：

```bash
# 删除损坏的行
sed -i '/^FEISHU_APP_SECRET/d' ~/.hermes/.env

# 追加完整密钥（替换为实际的 APP_SECRET）
echo 'FEISHU_APP_SECRET=w97DJKqQiNehGfL3wAiF0PEfCQSP5A5c' >> ~/.hermes/.env
```

**注意**：不要用 `sed 's/^FEISHU_APP_SECRET=.*/FEISHU_APP_SECRET=新值/'` — 当新值包含特殊字符（`/`、`&`、`\`）时会失败。用 `echo >>` 追加更安全。

### 第 4 步：修复后验证

```bash
source ~/.hermes/.env 2>/dev/null
curl -s -X POST 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal' \
  -H 'Content-Type: application/json' \
  -d "{\"app_id\":\"$FEISHU_APP_ID\",\"app_secret\":\"$FEISHU_APP_SECRET\"}" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('✅ 有效' if d.get('code')==0 else f'❌ {d}')"
```

### 第 5 步：查 Bot 信息和发送测试消息

```bash
source ~/.hermes/.env 2>/dev/null
python3 -c "
import requests, json
r = requests.post('https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
    json={'app_id': '$FEISHU_APP_ID', 'app_secret': '$FEISHU_APP_SECRET'})
token = r.json()['tenant_access_token']
r2 = requests.get('https://open.feishu.cn/open-apis/bot/v3/info',
    headers={'Authorization': f'Bearer {token}'})
print('Bot:', r2.json().get('bot', {}).get('app_name', 'unknown'))

content = json.dumps({'text': '测试消息'})
r3 = requests.post(
    'https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id',
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
    json={'receive_id': 'ou_a74c0eb0ff0f216d5036c2300a213d22', 'msg_type': 'text', 'content': content})
print('发送结果:', '✅' if r3.json().get('code')==0 else '❌', r3.json().get('msg'))
"
```

## sed 常见陷阱

| 场景 | 问题 | 解决方案 |
|------|------|----------|
| 密钥含 `/` | `sed 's/旧/新/'` 中的 `/` 会中断替换 | 用 `echo >>` 追加，不要用 sed 替换 |
| 密钥含 `&` | sed 视 `&` 为"匹配到的文本"占位符 | 同上 |
| 密钥含 `\` | sed 视 `\` 为转义符 | 同上 |
| security.redact_secrets | 终端显示 `***` 但文件实际值完整 | 用 `xxd` 验证，不要相信 cat/grep 输出 |

## 通用建议

- **所有 API 调用先用 curl 直测**，不要先改代码再排查
- **`xxd` 是排查密钥截断的唯一可靠手段**（cat/grep 都受 redact 影响）
- **不要交叉使用不同 Bot 的凭证** — APP_ID 和 APP_SECRET 是一一对应的
- **不同 Bot 下同一用户的 open_id 不同** — 不能跨应用复用
