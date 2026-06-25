# Nous Research (inference-api) Provider 配置参考

## 概述

Nous Research 提供推理 API，可通过 Hermes 的 `nous` provider 使用。支持免费模型和付费模型。

## 端点

```
https://inference-api.nousresearch.com/v1
```

## 认证方式

使用 Bearer token（API key 前缀 `sk-nous-`，约 45-50 字符）：

```bash
# 测试模型列表（无需 credits）
curl --noproxy "*" \
  "https://inference-api.nousresearch.com/v1/models" \
  -H "Authorization: Bearer sk-nous-..."
```

## Hermes 配置步骤

### 1. 添加凭证

```bash
hermes auth add --type api-key --label "nous-portal" --api-key "sk-nous-..." nous
```

### 2. 配置 provider

```bash
hermes config set providers.nous.base_url "https://inference-api.nousresearch.com/v1"
hermes config set providers.nous.default "nvidia/nemotron-3-ultra:free"
hermes config set providers.nous.model "nvidia/nemotron-3-ultra:free"
hermes config set providers.nous.api_key_env ""
```

**说明**：`api_key_env: ''`（空字符串）让 Hermes 回退到凭证存储（credential store），而非从环境变量读取。

### 3. 验证配置

```yaml
nous:
    base_url: https://inference-api.nousresearch.com/v1
    default: nvidia/nemotron-3-ultra:free
    model: nvidia/nemotron-3-ultra:free
    api_key_env: ''
```

## 模型列表（部分）

| 模型 ID | 类型 | 价格 |
|---------|------|------|
| `nvidia/nemotron-3-ultra:free` | 免费 | $0 |
| `nvidia/nemotron-3-ultra-550b-a55b` | 付费 | $0.50/K input / $2.50/K output |
| `stepfun/step-3.7-flash:free` | 免费 | $0 |
| `qwen/qwen3.7-plus` | 付费 | $0.40/K input / $1.60/K output |
| `qwen/qwen3.7-max` | 付费 | $1.25/K input / $3.75/K output |
| `anthropic/claude-opus-4.8` | 付费 | $5/K input / $25/K output |
| `google/gemini-3.5-flash` | 付费 | $1.50/K input / $9/K output |
| `x-ai/grok-4.3` | 付费 | $1.25/K input / $2.50/K output |

## 免费模型命名约定

免费模型通过 `:free` 后缀标识，附加在标准模型名后：
- `nvidia/nemotron-3-ultra:free`
- `stepfun/step-3.7-flash:free`

## 测试连通性

### 免费模型（已验证可用）

```python
import urllib.request, json

req = urllib.request.Request(
    "https://inference-api.nousresearch.com/v1/chat/completions",
    data=json.dumps({
        "model": "nvidia/nemotron-3-ultra:free",
        "messages": [{"role": "user", "content": "Say hello"}],
        "max_tokens": 20
    }).encode(),
    headers={
        "Authorization": "Bearer sk-nous-...",
        "Content-Type": "application/json"
    }
)
with urllib.request.urlopen(req, timeout=30) as resp:
    result = json.loads(resp.read())
    print(result["choices"][0]["message"]["content"])
```

### 付费模型 — 低余额错误

当账户余额不足时，付费模型返回 HTTP 404：

```json
{
    "status": 404,
    "message": "Model 'nvidia/nemotron-3-ultra-550b-a55b' requires available credits. Your account balance is too low to use paid models — add credits at https://portal.nousresearch.com or pick a free model."
}
```

## 注意事项

- **不需要代理**：`--noproxy "*"` 可直接连接 `inference-api.nousresearch.com`
- **Portal URL**：`https://portal.nousresearch.com/orgs/{org_id}/api-keys` 查看/管理 API keys
- **充值地址**：`https://portal.nousresearch.com` 添加 credits
- **`hermes config set` 优先于直接编辑 config.yaml**：安全策略阻止直接写 config 和 .env 文件
- **免费模型已够测试连通性**：无需预先充值
