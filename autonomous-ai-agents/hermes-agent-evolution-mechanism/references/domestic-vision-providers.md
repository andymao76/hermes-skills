# 国内AI视觉模型调用参考

## 场景
Hermes 需要分析图片，但当前主力模型(DeepSeek)不支持视觉输入。
内置 `vision_analyze` 工具依赖session启动时配置的 `auxiliary.vision`，无法热切换。

## 方案：Python脚本直接调用国内视觉API

### 方案A：阿里百炼 Qwen3-VL-Plus（推荐首选）

**端点：** `https://dashscope.aliyuncs.com/compatible-mode/v1`
**Key位置：** `~/.hermes/.env` 中 `DASHSCOPE_API_KEY`
**推荐模型：** `qwen3-vl-plus`
**备选：** `qwen3-vl-flash`（更快更便宜）

```python
import json, base64, requests, os

# 从config.yaml或.env取key
api_key = "your-key"
base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

with open('image.jpg', 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()

headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
payload = {
    'model': 'qwen3-vl-plus',
    'messages': [{'role': 'user', 'content': [
        {'type': 'text', 'text': '描述这张图片'},
        {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{b64}'}}
    ]}],
    'max_tokens': 2000, 'temperature': 0.1
}
r = requests.post(f'{base_url}/chat/completions', headers=headers, json=payload, timeout=60)
result = r.json()
print(result['choices'][0]['message']['content'])
```

### 方案B：SiliconFlow Qwen3-VL（备选）

**端点（国内站）：** `https://api.siliconflow.cn/v1`
**端点（国际站）：** `https://api.siliconflow.com/v1`
**Key位置：** `~/.hermes/config.yaml` → `providers.siliconflow-cn.api_key`（国内站）
**注意：** SiliconFlow的key在config.yaml中，不在.env！

可用模型：
| 模型名 | 说明 |
|--------|------|
| `Qwen/Qwen3-VL-32B-Instruct` | 最佳精度 |
| `Qwen/Qwen3-VL-32B-Thinking` | 带思维链 |
| `Qwen/Qwen3-VL-8B-Instruct` | 轻量快速 |
| `Qwen/Qwen3-VL-30B-A3B-Instruct` | MoE架构 |

```python
import yaml
with open(os.path.expanduser('~/.hermes/config.yaml')) as f:
    cfg = yaml.safe_load(f)
sf = cfg['providers']['siliconflow-cn']
api_key = sf['api_key']
base_url = sf.get('base_url', 'https://api.siliconflow.cn/v1')
```

### 注意事项
- 百炼兼容OpenAI格式，直接替换base_url即可
- SiliconFlow model名需 vendor-prefix（如 `Qwen/` 前缀）
- 早期记忆标记"百炼欠费"已被纠正：qwen-plus文本模型可能欠费，但**vision模型单独计费可用**
- 批量调用时建议间隔0.3~0.5秒防限流
- 图片base64编码后增大~33%，大图注意payload
- HEIC格式需先转为jpg再传
