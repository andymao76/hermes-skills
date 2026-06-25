# Gemini 作为翻译引擎配置

## 概述

Google Gemini 通过 OpenAI 兼容端点接入 Hermes，可作为翻译引擎使用。
相比 DeepL，Gemini 支持系统指令（可指定翻译风格、术语表、语境），适合需要上下文感知的翻译场景。

## 配置方式

已通过 `hermes config` 配置为 provider：

```yaml
providers:
  gemini:
    api_key_env: GEMINI_API_KEY
    base_url: https://generativelanguage.googleapis.com/v1beta/openai
    default: gemini-2.5-flash
    model: gemini-2.5-flash
```

### Key 存储

Key 存储在 `~/.hermes/.env`：
```
GEMINI_API_KEY=AIzaSy...
```

### Key 写入注意事项

**与 DeepL 相同**：`write_file` 工具会检测并替换 API Key 类字符串。使用终端 heredoc 或 Python 写入 `.env`。

### 代理要求

Gemini API (`generativelanguage.googleapis.com`) 需要代理访问（127.0.0.1:7897）。
Hermes 框架不会自动为 provider 请求走代理，需要在 `config.yaml` 的 `mcp_servers` 或脚本中手动设置 `HTTPS_PROXY`。

## 使用方式

### 切换 provider 翻译

```bash
# 在 Hermes 对话中
/model gemini
# 然后发送翻译请求
```

### 直接 API 调用（脚本中）

```python
import os, json, urllib.request

os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7897"

# 读 Key
with open(os.path.expanduser("~/.hermes/.env")) as f:
    for l in f:
        if "GEMINI" in l:
            key = l.strip().split("=", 1)[1]
            break

url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
data = json.dumps({
    "model": "gemini-2.5-flash",
    "messages": [
        {"role": "system", "content": "你是技术翻译专家。保留所有缩写不翻译。"},
        {"role": "user", "content": "待翻译文本"}
    ],
    "max_tokens": 2000
}).encode()

req = urllib.request.Request(url, data=data, headers={
    "Authorization": "Bearer " + key,
    "Content-Type": "application/json"
})
with urllib.request.urlopen(req, timeout=30) as r:
    result = json.loads(r.read())
    print(result["choices"][0]["message"]["content"])
```

## 支持模型

当前使用 `gemini-2.5-flash`（快速、免费层）。
其他可选: `gemini-2.5-pro`（高质量，需付费）

## 测试验证

```bash
python3 -c "
import os, json, urllib.request
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7897'
with open(os.path.expanduser('~/.hermes/.env')) as f:
    key = [l.split('=',1)[1] for l in f if 'GEMINI' in l][0].strip()
url = 'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions'
data = json.dumps({'model':'gemini-2.5-flash','messages':[{'role':'user','content':'用中文回复：API有效吗？'}],'max_tokens':50}).encode()
req = urllib.request.Request(url, data=data, headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
print(json.loads(urllib.request.urlopen(req).read())['choices'][0]['message']['content'])
"
# 期望输出: API有效。/是的，API有效。
```

## 翻译质量特征

| 维度 | Gemini | DeepL | 说明 |
|------|--------|-------|------|
| 术语保留 | ★★★★ | ★★★★★ | Gemini 有时会翻译一些缩写 |
| 上下文感知 | ★★★★★ | ★★★ | Gemini 支持系统指令指定语境 |
| 速度 | 快 | 快 | 两者都在秒级 |
| 中文输出 | 自然 | 自然 | 无明显差异 |
| 规范用语 | ★★★★ | ★★★★★ | DeepL 对 "shall"/"should" 处理更好 |

## 常见问题

### Q: max_tokens 太小导致空回复

症状: `finish_reason: "length"` 但 `completion_tokens: 0`

解决: 增大 `max_tokens` 到至少 100+。20 以下可能出现生成内容被截断到 0 token 的情况。

### Q: 403 / 认证失败

检查:
- Key 是否完整（无多余空格/换行）
- 端点是否正确 (`/v1beta/openai` 不是 `/v1`)
- 是否需要代理
