# Telegram/消息平台图片分析管道

## 问题背景

用户通过 Telegram/Discord/微信等消息平台发送图片时，图片会自动保存到 `~/.hermes/image_cache/` 目录，文件名为 `img_<hash>.jpg`。

当当前模型（如 `deepseek-v4-flash`）**无原生视觉支持**时，`vision_analyze` 工具会失败：
```
Error code: 400 - 'unknown variant `image_url`, expected `text`'
```

## 解决方案：SiliconFlow CN Vision API 直连

### 标准工作流（CN 站，首选）

```
用户发图片 → ~/.hermes/image_cache/img_*.jpg → 写 Python 脚本 → SiliconFlow CN API → 返回分析
```

### 完整 Python 脚本模板

```python
import base64, json, os, yaml, subprocess, tempfile

# 1. 从 config 获取 SiliconFlow CN key（国内站直连，无需代理）
with open(os.path.expanduser('~/.hermes/config.yaml')) as f:
    config = yaml.safe_load(f)
api_key = config['providers']['siliconflow-cn']['api_key'].strip()

# 2. 读取图片并 base64 编码
img_path = '/home/andymao/.hermes/image_cache/img_<hash>.jpg'
with open(img_path, 'rb') as f:
    img_b64 = base64.b64encode(f.read()).decode('utf-8')

# 3. 构建请求 payload
payload = {
    'model': 'Qwen/Qwen3-VL-8B-Instruct',  # 或 32B 版更高精度
    'messages': [{
        'role': 'user',
        'content': [
            {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{img_b64}'}},
            {'type': 'text', 'text': '请详细描述这张图片的内容'}
        ]
    }],
    'max_tokens': 1024,
    'temperature': 0.1
}

# 4. 写入临时 JSON 文件（避开 shell 转义问题）
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    json.dump(payload, f)
    tmpfile = f.name

# 5. 用 curl @file 发送（urllib 偶发超时）
auth = 'Authorization: Bearer ' + api_key
result = subprocess.run(
    ['curl', '-s', '--max-time', '120',
     'https://api.siliconflow.cn/v1/chat/completions',
     '-H', auth,
     '-H', 'Content-Type: application/json',
     '-d', '@' + tmpfile],
    capture_output=True, text=True, timeout=130
)
os.unlink(tmpfile)

# 6. 解析结果
data = json.loads(result.stdout)
print(data['choices'][0]['message']['content'])
```

### 关键要点

| 要素 | 说明 |
|------|------|
| **API 端点** | `api.siliconflow.cn`（国内站，直连无需代理） |
| **推荐模型** | `Qwen/Qwen3-VL-8B-Instruct`（速度优先），`Qwen/Qwen3-VL-32B-Instruct`（精度优先） |
| **key 来源** | `config.yaml` → `providers.siliconflow-cn.api_key`（51 字符） |
| **JSON 文件 + curl @file** | **必须用此模式** — base64 字符串含 `+`/`/`/`=` 等字符，嵌入 shell 双引号会炸 |
| **超时** | SiliconFlow CN 视 API 约 2-10s，图片大则更长，设 `--max-time 120` |
| **多图分析** | content 数组可包含多条 image_url，模型自动对比理解 |
| **文件路径检查** | 先确认文件存在：`os.path.getsize(img_path)` |

### 可选：备用模型

- `Qwen/Qwen3-VL-8B-Instruct` — 响应最快（~2-5s），适合文字为主的截图
- `Qwen/Qwen3-VL-32B-Instruct` — 精度更高（~5-15s），复杂场景/医学影像
- `Qwen/Qwen3-VL-30B-A3B-Instruct` — MoE 版，性能与体积平衡

### 常见错误处理

| 错误 | 原因 | 修复 |
|------|------|------|
| `Model does not exist` | 模型名在 CN 站上不存在 | 检查模型 ID 是否包含 `Qwen/Qwen3-VL-` 前缀 |
| `curl: (28) Connection timed out` | 网络问题 | 检查 CN 域名是否可达；或改用国际站+代理 |
| `JSON decode error` | 响应非 JSON | 打印 `result.stdout[:300]` 检查错误页面 |
| `list index out of range` | API 返回空 choices | 检查 token 限额是否用完 |

---

### 备用方案：国际站 + 代理（CN 超时时降级）

当 `api.siliconflow.cn` 读超时时，降级到国际站 `api.siliconflow.com` + Clash 代理。

**核心要点：**

| 要素 | CN 站（首选） | 国际站（降级） |
|------|-------------|--------------|
| 端点 | `api.siliconflow.cn` | `api.siliconflow.com` |
| API Key | `providers.siliconflow-cn` | `providers.siliconflow` |
| 代理 | 直连（无需代理） | `127.0.0.1:7897` |
| 时延 | 500ms-3s | 2600ms-8s |
| 超时设 | `--max-time 120` | `--max-time 60` |

**Python 降级实现：**

```python
import base64, json, yaml, os, requests

with open(os.path.expanduser('~/.hermes/config.yaml')) as f:
    config = yaml.safe_load(f)

img_path = '/home/andymao/.hermes/image_cache/img_xxx.jpg'
with open(img_path, 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()

payload = {
    'model': 'Qwen/Qwen3-VL-8B-Instruct',
    'messages': [{'role': 'user', 'content': [
        {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{b64}'}},
        {'type': 'text', 'text': '请详细描述这张图片'}
    ]}],
    'max_tokens': 1024,
    'temperature': 0.1
}

headers = {
    'Authorization': f"Bearer {config['providers']['siliconflow']['api_key']}",
    'Content-Type': 'application/json'
}

proxies = {'http': 'http://127.0.0.1:7897', 'https': 'http://127.0.0.1:7897'}
resp = requests.post(
    'https://api.siliconflow.com/v1/chat/completions',
    json=payload, headers=headers, proxies=proxies, timeout=60
)

data = resp.json()
print(data['choices'][0]['message']['content'])
```

**降级自动切换脚本**：参见 `scripts/analyze_via_siliconflow.sh`（该脚本新增了 CN 超时后自动降级到 intl 的逻辑）"
