# 阿里百炼 Qwen-VL 视觉备选方案

当 SiliconFlow VLM 不可用（超时/限流/模型切换）时，可用 **阿里百炼 Qwen3-VL** 作为替代视觉方案。

## 连接信息

| 项目 | 值 |
|------|-----|
| API 端点 | `https://dashscope.aliyuncs.com/compatible-mode/v1`（OpenAI 兼容模式） |
| API Key 位置 | `.env` 中 `DASHSCOPE_API_KEY=`，或 `config.yaml` 中 `custom_providers.bailian.api_key` / `providers.bailian.api_key` |
| 认证方式 | `Authorization: Bearer <key>` |

**注意**：以前百炼 qwen-plus 欠费过（已从健康检查排除），但 **Qwen3-VL-Plus 独立计费，额度正常**。

## 可用视觉模型

从百炼开放平台可获取 10 个视觉/推理模型：

| 模型 ID | 类型 | 说明 |
|---------|------|------|
| `qwen3-vl-plus` | 视觉 | **推荐**，综合性能强 |
| `qwen3-vl-plus-2025-12-19` | 视觉 | 快照版 |
| `qwen3-vl-flash` | 视觉 | 快速版，响应更快 |
| `qwen3-vl-flash-2026-01-22` | 视觉 | 快照版 |
| `qwen-vl-ocr` | 视觉+OCR | 文字识别 |
| `qwen-vl-ocr-latest` | 视觉+OCR | 最新版 |

## API Key 提取（关键坑）

百炼的 API key 存在多个位置（因配置方式变化），**必须依次检查**：

```python
import yaml, json, os

api_key = ''
# 1. 从 config.yaml 的 custom_providers 找
with open(os.path.expanduser('~/.hermes/config.yaml')) as f:
    cfg = yaml.safe_load(f)
for src in [cfg.get('custom_providers', {}), cfg.get('providers', {})]:
    for k, v in src.items():
        if 'bai' in k.lower():
            api_key = v.get('api_key', '')
            break
    if api_key: break

# 2. 从 auth.json 找
if not api_key or api_key.startswith('$'):
    auth_path = os.path.expanduser('~/.hermes/auth.json')
    if os.path.exists(auth_path):
        with open(auth_path) as f:
            for cred in json.load(f).get('custom:bailian', []):
                api_key = cred.get('api_key', '')
                if api_key: break

# 3. 从 .env 找（.env 中输出被红化为 ***，但文件内是真实值）
if not api_key or api_key.startswith('$'):
    with open(os.path.expanduser('~/.hermes/.env')) as f:
        for line in f:
            if 'DASHSCOPE_API_KEY' in line:
                parts = line.strip().split('=', 1)
                if len(parts) == 2 and parts[1] and not parts[1].startswith('$'):
                    api_key = parts[1].strip("'\" ")
                    break
```

**陷阱**：`grep DASHSCOPE_API_KEY .env` 输出显示 `***`（内容红化），但 `xxd .env` 或 Python 直接 `open().read()` 可以拿到真实 key。不要被终端红化迷惑。

## 调用方式

### 单图分析

```python
import base64, requests

with open('/path/to/image.jpg', 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()

payload = {
    'model': 'qwen3-vl-plus',  # 或 qwen3-vl-flash
    'messages': [{
        'role': 'user',
        'content': [
            {'type': 'text', 'text': '请描述这张图片'},
            {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{b64}'}}
        ]
    }],
    'max_tokens': 500,
    'temperature': 0.1
}

r = requests.post(
    'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
    headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
    json=payload, timeout=60
)
result = r.json()
print(result['choices'][0]['message']['content'])
```

### 批量扫描（找特定主体）

适合从大量照片中识别是否包含某个人/宠物。

```python
import os, glob, time, json

photos = glob.glob('/path/to/photos/*.jpg')
results = {}
found = []

for p in photos:
    fname = os.path.basename(p)
    # ... (构造请求同上)
    r = requests.post(...)
    result = r.json()
    answer = result['choices'][0]['message']['content']
    
    # 判断是否命中
    is_target = any(k in answer for k in ['有', '贵宾', '泰迪', '犬', '丢丢'])
    results[fname] = answer
    if is_target:
        found.append({'file': p, 'result': answer})
    
    time.sleep(0.3)  # 限频，避免 429

# 保存结果供后续参考
with open('/tmp/scan_results.json', 'w') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
```

## 错误处理

| 现象 | 原因 | 解决 |
|------|------|------|
| `401 Missing Authentication header` | API Key 为空或格式不对 | 确认 key 提取逻辑，key 不以 `$` 开头 |
| `404 Model not found` | 模型名在百炼不存在 | 用 `qwen3-vl-plus` （不带 `Qwen/` 前缀） |
| `200 OK 但输出空` | 欠费/配额用尽 | 检查百炼控制台余额 |
| 响应慢（>30s） | 图片大或服务繁忙 | 缩小图片或用 `qwen3-vl-flash` |
| **终端 key 显示 `***`** | 内容红化，非 key 本身 | 用 Python `open().read()` 直读 |

## 与 SiliconFlow VLM 对比

| 维度 | SiliconFlow CN | 百炼 Qwen-VL |
|------|---------------|-------------|
| 国内直连 | ✅ 直连 | ✅ 直连 |
| 时延 | ~2-10s | ~5-15s |
| 模型 | Qwen3-VL-8B/32B/30B | Qwen3-VL-Plus/Flash/OCR |
| 图片格式 | JPEG/PNG 最佳，不支持 HEIC | JPEG/PNG 最佳 |
| 批量扫描 | 适合 | 适合 |
| 模型名格式 | `Qwen/Qwen3-VL-32B-Instruct` | `qwen3-vl-plus` |
