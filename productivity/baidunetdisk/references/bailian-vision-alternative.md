# 阿里百炼 Qwen-VL 视觉识别方案

当 SiliconFlow Qwen-VL 不可用或需要国内直连方案时的备用视觉识别后端。

## 配置

### API Key

百炼的 API Key 在 `config.yaml` 中配置，通过 `hermes auth` 凭证池管理：

```bash
hermes auth list custom:bailian
# → #1  bailian  api_key config:bailian
```

也可在 `.env` 中用 `DASHSCOPE_API_KEY` 设置。

### 端点（兼容 OpenAI 格式）

```
https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
```

### 可用视觉模型（2026-06 实测）

| 模型 | 用途 |
|------|------|
| `qwen3-vl-plus` | ✅ 通用视觉分析，主力 |
| `qwen3-vl-flash` | 轻量快捷，适合简单分类 |
| `qwen-vl-ocr` | 文字识别专用 |
| `qwen-vl-max` | 高精度，更慢 |

**推荐**: `qwen3-vl-plus` — 速度与准确率平衡最佳。

## API 调用模板

```python
import json, base64, requests

with open('/path/to/image.jpg', 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()

headers = {
    'Authorization': f'Bearer {YOUR_API_KEY}',
    'Content-Type': 'application/json',
}

payload = {
    'model': 'qwen3-vl-plus',
    'messages': [{
        'role': 'user',
        'content': [
            {'type': 'text', 'text': '请详细描述这张照片的内容。'},
            {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{b64}'}}
        ]
    }],
    'max_tokens': 1000,
    'temperature': 0.1
}

r = requests.post(
    'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
    headers=headers, json=payload, timeout=60
)
result = r.json()
if 'choices' in result:
    print(result['choices'][0]['message']['content'])
```

### API Key 获取（从 config.yaml 读取）

```python
import yaml, os
with open(os.path.expanduser('~/.hermes/config.yaml')) as f:
    cfg = yaml.safe_load(f)

api_key = ''
for src in [cfg.get('custom_providers', {}), cfg.get('providers', {})]:
    for k, v in src.items():
        if 'bai' in k.lower():
            api_key = v.get('api_key', '')
            break
    if api_key: break

if not api_key or api_key.startswith('$'):
    with open(os.path.expanduser('~/.hermes/.env')) as f:
        for line in f:
            if 'DASHSCOPE_API_KEY' in line:
                parts = line.strip().split('=', 1)
                if len(parts) == 2 and parts[1] and not parts[1].startswith('$'):
                    api_key = parts[1].strip("'\" ")
                    break
```

## 批量照片识别工作流

### 最佳提示词策略

**第一步：二分类快速筛选**
```
prompt = '这张照片里有贵宾犬/泰迪犬（叫丢丢）吗？回答"是"或"否"。'
max_tokens = 80  # 减少输出，加速
```

**第二步：确认后详细描述**
```
prompt = '请详细描述这只狗的外观、颜色、状态、姿势。'
max_tokens = 1000
```

### 图片格式处理

| 格式 | 处理方式 |
|:----:|----------|
| `.jpg` / `.jpeg` | 直接 base64 编码 |
| `.png` | 直接 base64 编码 |
| `.heic` | 需先转换：`heif-convert in.heic out.jpg` |
| `.heic_conv.jpg` | 已经转换好的 JPG，直接处理 |

### 批处理注意

- 每张间隔 **至少 0.3秒** 避免限流
- 每批建议 5 张
- 超时设置 45 秒/张
- 分批调用前先确认前一批结果

## 与 SiliconFlow 对比

| 特性 | SiliconFlow Qwen3-VL-32B | 百炼 Qwen3-VL-Plus |
|------|:------------------------:|:------------------:|
| API Key 位置 | config.yaml siliconflow-cn | config.yaml / .env bailian |
| 国内访问 | ✅ 直连 | ✅ 直连 |
| 单张时延 | ~500ms | ~800-1500ms |
| 识别准确率 | ✅ 优秀 | ✅ 优秀 |
| 高峰稳定性 | 偶有 429 | 稳定 |
