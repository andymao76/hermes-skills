# 阿里百炼 Qwen-VL — 视觉分析的备用方案

当 SiliconFlow VLM 不可用或需要国内直连替代时，使用阿里百炼（Alibaba Cloud Bailian / DashScope）的 Qwen-VL 模型。

## 前提

- API key 在 `~/.hermes/config.yaml` 的 `custom_providers.bailian` 或 `providers.bailian` 中
- 或在 `~/.hermes/.env` 中为 `DASHSCOPE_API_KEY`
- 兼容 OpenAI 格式的端点：`https://dashscope.aliyuncs.com/compatible-mode/v1`
- **注意**：该 API key 之前可能欠费（qwen-plus），但 **Qwen3-VL-Plus 独立计费且可用**

## 可用视觉模型（已验证）

| 模型 ID | 说明 | 推荐 |
|---------|------|:----:|
| `qwen3-vl-plus` | 主力视觉模型，综合最优 | ⭐ |
| `qwen3-vl-flash` | 轻量快速响应 | |
| `qwen-vl-ocr` | 文字识别专用 | |
| `qwen2.5-vl-72b-instruct` | 高端长上下文（已停用，改用 qwen3-vl-plus） | ❌ |

## 调用示例

### 快速分析（单图）

```python
import json, base64, requests, yaml, os

# 从 config.yaml 读取 key
with open(os.path.expanduser('~/.hermes/config.yaml')) as f:
    cfg = yaml.safe_load(f)

# Bailian 可能藏在 custom_providers 或 providers 下
api_key = ''
base_url = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
for src in [cfg.get('custom_providers', {}), cfg.get('providers', {})]:
    for k, v in src.items():
        if 'bai' in k.lower():
            api_key = v.get('api_key', '')
            base_url = v.get('base_url', base_url) or base_url
            break
    if api_key:
        break

# 必要时从 .env 补充
if not api_key or api_key.startswith('$'):
    with open(os.path.expanduser('~/.hermes/.env')) as f:
        for line in f:
            if 'DASHSCOPE_API_KEY' in line:
                p = line.strip().split('=', 1)
                if len(p) == 2 and p[1] and not p[1].startswith('$'):
                    api_key = p[1].strip("'\" ")
                    break

# 避免双写 compatible-mode
base_url = base_url.replace('compatible-mode/compatible-mode', 'compatible-mode')

# 编码图片
with open(img_path, 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()

headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
payload = {
    'model': 'qwen3-vl-plus',
    'messages': [{'role': 'user', 'content': [
        {'type': 'text', 'text': '请描述这张图片'},
        {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{b64}'}}
    ]}],
    'max_tokens': 1000, 'temperature': 0.1
}

r = requests.post(f'{base_url}/chat/completions', headers=headers, json=payload, timeout=60)
result = r.json()
if 'choices' in result:
    print(result['choices'][0]['message']['content'])
```

## 两个关键坑

### 1. API key 来源不统一
Bailian 的 key 可能在三个位置：
- `config.yaml → custom_providers.bailian.api_key`
- `config.yaml → providers.bailian.api_key`
- `~/.hermes/.env → DASHSCOPE_API_KEY`

**优先从 config.yaml 读**，回退到 .env。用 yaml.safe_load 而非正则，避免 key 截断。

### 2. base_url 双写问题
如果 config.yaml 写了 `base_url: https://dashscope.aliyuncs.com/compatible-mode/v1`，直接拼成 `{base_url}/chat/completions` 会得到双 `compatible-mode`。**必须去重**：
```python
base_url = base_url.replace('compatible-mode/compatible-mode', 'compatible-mode')
```

## 与 SiliconFlow 方案对比

| 维度 | SiliconFlow (CN) | 阿里百炼 |
|------|:---:|:---:|
| 端点 | api.siliconflow.cn/v1 | dashscope.aliyuncs.com/compatible-mode/v1 |
| 时延 | ~500ms | ~800-1500ms |
| 模型 | Qwen3-VL-32B-Instruct | qwen3-vl-plus |
| 可靠性 | 偶尔 503 | 偶尔 400（配额检查） |
| Key 位置 | config.yaml providers.siliconflow-cn | config.yaml providers/custom_providers 中带 bailian 的条目 |
| 代理 | 无需 | 无需 |

**最佳实践：** 优先 SiliconFlow 国内站，失败时自动 fallback 到阿里百炼 Qwen-VL。
