# 照片内容验证工作流

从百度网盘下载照片后，用 SiliconFlow VLM 验证照片中是否有目标宠物/人物。

## 完整工作流

### 1. 从百度网盘下载候选照片

```python
# method=download 方式
params = urllib.parse.urlencode({
    'access_token': token, 'path': item['path']
})
url = f'https://pan.baidu.com/rest/2.0/xpan/file?method=download&{params}'
req = urllib.request.Request(url, headers={'User-Agent': 'pan.baidu.com'})
with urllib.request.urlopen(req, timeout=30) as resp:
    img_data = resp.read()
```

### 2. HEIC 格式转换

iPhone 备份中的 `.heic` 格式照片需转为 JPEG 才能被 VLM 识别：

```bash
convert input.heic output.jpg
```

ImageMagick 的 `convert` 命令可直接转换 HEIC → JPEG。

### 3. SiliconFlow VLM 内容验证

```python
import base64, json, yaml, tempfile, subprocess, os

# 获取 key
with open(os.path.expanduser('~/.hermes/config.yaml')) as f:
    key = yaml.safe_load(f)['providers']['siliconflow-cn']['api_key']

# 编码图片
with open(image_path, 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()

# 构建 payload
payload = json.dumps({
    'model': 'Qwen/Qwen3-VL-8B-Instruct',
    'messages': [{'role': 'user', 'content': [
        {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{b64}'}},
        {'type': 'text', 'text': '这张照片里有宠物狗吗？请用是或否开头描述画面。'}
    ]}],
    'max_tokens': 100, 'temperature': 0.1
})

# 写 tempfile → curl @file 发送
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    f.write(payload)
    tmp = f.name

result = subprocess.run([
    'curl', '-s', '--max-time', '30',
    'https://api.siliconflow.cn/v1/chat/completions',
    '-H', f'Authorization: Bearer ***    '-H', 'Content-Type: application/json',
    '-d', f'@{tmp}'
], capture_output=True, text=True)
os.unlink(tmp)

data = json.loads(result.stdout)
answer = data['choices'][0]['message']['content']
```

### 4. 判断逻辑

- 如果回答以"是"开头且包含"狗"或"犬" → 找到目标照片
- 否则 → 不是目标照片

## 关键陷阱

1. **HEIC 必须转换**：Qwen3-VL 不支持 HEIC 格式，必须先转 JPEG
2. **base64 嵌入 shell 会炸**：必须用 tempfile + curl @file 方式发送，base64 含 `+`、`/`、`=` 等特殊字符
3. **Screenshots vs 照片**：iPhone 备份中大量为工作截图（Discord/终端/AI文档），文件大小不是可靠判断依据。连 3MB 的 JPG 也可能是分辨率较高的截图
4. **timeout 处理**：VLM 处理大图可能较慢（30s+），`--max-time` 设 30-60s
5. **响应鲁棒性**：`json.loads(result.stdout)` 需要 try/except 防御
6. **命名目录省 AI 验证**：如果照片来自以宠物/人物命名的目录（如 `/2025-丢丢/丢丢/`），默认全部都是该目标的照片，不需要逐张 AI 验证。AI 验证只用于无分类的通用目录（如 iPhone 备份）
