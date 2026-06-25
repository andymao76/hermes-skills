---
name: vision-analysis-pipeline
description: "Hermes + SiliconFlow vision + markitdown 全链路：截图分析到知识库入库。覆盖 SSH 远程截图、vision_analyze 多源输入、markitdown 格式保全、知识库归档。"
category: "media"
triggers:
  - "分析截图"
  - "vision_analyze"
  - "远程截图工作流"
  - "SSH 截图分析"
  - "HEX/ASN.1 截图"
  - "markitdown 转存"
  - "截图入库"
---

# Vision Analysis Pipeline

## 链路总览

```
截图 (本地/远程/浏览器) → vision_analyze → 模型理解 → markitdown 存为 .md → 知识库入库
```

## 前置条件

### 1. SiliconFlow Vision 配置

在 `~/.hermes/config.yaml` 中：

```yaml
vision:
  provider: siliconflow
  model: Qwen/Qwen3-VL-30B-A3B-Instruct
  base_url: https://api.siliconflow.com/v1    # 留空则复用 siliconflow provider
  api_key: sk-xxx...                           # 留空则复用 siliconflow provider
  timeout: 120
```

备用模型（SiliconFlow CN）：`Qwen/Qwen3-VL-32B-Instruct`（精度更高）、`Qwen/Qwen3-VL-30B-A3B-Instruct`（MoE 平衡）、`Qwen/Qwen3-VL-8B-Instruct`（速度优先）
旧模型（已下线）：`Qwen/Qwen2-VL-72B-Instruct`（已从 SiliconFlow 下线）、`deepseek-ai/deepseek-vl2`（最多2张图）

### 2. MarkItDown

```bash
pip3 install markitdown
```

## 截图输入方式

### A. 本地路径（最常用）

直接调用 vision_analyze 工具即可。

### B. 浏览器截图（Hermes 开浏览器时）

调用 browser_vision 工具截图分析。

### C. SSH 远程通道（用户常用模式）

用户从 Windows SSH 登录 Linux 服务器，截图流程：

```powershell
# Windows 端：截完图 SCP 到服务器
scp C:\Users\xxx\Pictures\截图.png user@server:/home/andymao/temp-picture/
```

然后在对话中调用 vision_analyze 传入该路径。

**缺省分析目录**：`/home/andymao/temp-picture/`（已配置到 memory）

### D. Base64 行内编码（不用传文件）

```powershell
# Windows PowerShell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("截图.png")) | Set-Clipboard
```

直接粘贴到 Hermes 对话中即可。

## 截图分析要点

- **HEX 码流**：vision 模型直接识别 HEX 格式，对齐、缩进均保真
- **ASN.1 结构**：模型理解 BER/PER 编码的层级关系
- **表格/参数**：高分辨率模式下保留细节
- **detail 参数**：`high`（默认）按原始分辨率；`low` 统一缩放节省 token

## MarkItDown 存盘

### 命令行

```bash
markitdown report.pdf > ~/knowledge/research/report.md
markitdown spec.docx > ~/knowledge/spec.md
```

### Python API

```python
from markitdown import MarkItDown
md = MarkItDown()
result = md.convert("document.pdf")
with open("output.md", "w") as f:
    f.write(result.text_content)
```

### 知识库入库

转存到 knowledge 目录后执行 `enzyme refresh` 更新索引。

## 工作流模板

### 截图分析 → 知识库

1. 用户 SCP 截图到 `temp-picture/`
2. 调用 vision_analyze 分析内容（带具体问题）
3. 使用 markitdown 转为 markdown
4. 写入 `~/knowledge/research/`
5. 执行 `enzyme refresh` 更新索引

### 批量 PDF/文档入库

```bash
for f in *.pdf; do
  markitdown "$f" > ~/knowledge/research/"${f%.pdf}.md"
done
enzyme refresh
```

## 陷阱与注意事项

- **HEIC 格式图片**：iPhone 的 `.heic` 格式图片不能被 Qwen3-VL 直接处理。必须先转换为 JPEG：`convert input.heic output.jpg`（需要 ImageMagick）。同样 macOS 截图 `.png` 最通用
- **SiliconFlow 图片过期**：上传图片 1 小时后过期，视频 10 分钟，大文件需及时分析
- **429 频率限制**：SiliconFlow 有 API 限频，批量操作需加间隔
- **macOS 截图格式**：`.png` 最通用，`.webp` 支持更好（体积小）
- **SSH 无桌面环境**：不能直接 `gnome-screenshot`，必须从 Windows 传图
- **markitdown 对图片只保 EXIF**：不做 OCR，如需 OCR 需额外插件
- **DeepSeek VL2 限制**：最多 2 张图，超过自动缩至 384×384
- **auxiliary.vision 降级失败**：当 `auxiliary.vision.provider/model` 也指向无视觉模型（如 DeepSeek）时，`vision_analyze` 工具报 `unknown variant image_url`。即使切换配置（`hermes config set auxiliary.vision.provider openrouter`）也需新 session 才生效。必须在本 session 内直接用 Python 脚本调用第三方 API。
- **vision_analyze 不接受 Python requests/curl 失败**：当 API key 不在 os.environ 而藏在 config.yaml 中时，.env 中的 key 被输出红化为 `***`，Python 直接 `os.getenv()` 拿不到值。必须从 config.yaml 或 auth.json 中直接 yaml 解析提取。
- **deepseek-v4-flash / deepseek-v4-pro 无原生视觉支持**：这些模型通过 text 通道不支持 image_url 格式。vision_analyze 工具的降级通道（备用视觉模型）也可能因模型不兼容失败（报错 `unknown variant image_url`）。**必须使用 SiliconFlow VLM 直连方案**（见备用方案章节）。
- **Telegram/Discord 图片路径**：用户通过消息平台发送的图片自动保存到 `~/.hermes/image_cache/img_*.jpg`。`vision_analyze` 接受本地路径参数，但如果当前模型无视觉支持，会报错。此时应直接使用 SiliconFlow VLM 直连方案处理 cache 目录下的图片。详见 `references/telegram-image-pipeline.md`。
- **SiliconFlow CN API 可能超时**：`api.siliconflow.cn` 偶发读超时（尤其大图或高峰时段）。不能全靠 CN 端点。必须准备 **国际站 + 代理降级方案**（见备用方案→方案三）。
- **大图预缩放避免超时**：图片 >150KB 时，base64 后约 200KB+ 的请求体容易触发 CN 端点读超时（`Read timed out`）。建议发送前用 PIL 缩放至宽度 1200px（保持比例），quality=85，可显著减少超时概率。判断逻辑：先 `os.path.getsize()` 检查文件大小，>150KB 则 resize 后再发送。
- **两个不同的 API Key**：`config.yaml` 中 `providers.siliconflow`（国际站）和 `providers.siliconflow-cn`（国内站）是**不同的 key**。CN key 对 intl 端点无效，反之亦然。降级时必须切换 key 来源。
- **Python requests 代理配置必须用 dict**：`proxies={'http': 'http://127.0.0.1:7897', 'https': 'http://127.0.0.1:7897'}`。字符串形式会导致 `'str' object has no attribute 'get'` 错误。

### 备用方案：SiliconFlow VLM 直接调用

当 `vision_analyze` 失败时，使用 SiliconFlow CN 的 Qwen3-VL 模型直接分析图片。

### 方式一：一键脚本（推荐）

```bash
scripts/analyze_via_siliconflow.sh /path/to/image.jpg "请描述这张图片"
```

自动处理：密钥提取 → base64编码 → JSON写入临时文件 → curl发送 → 结果解析
保存在 `scripts/analyze_via_siliconflow.sh`，可独立执行。

---

### 阿里百炼 Qwen-VL（备选）

当 SiliconFlow 不可用时（超时/限流/模型切换），用阿里百炼 Qwen3-VL-Plus 替代。详见 `references/bailian-vision-alternative.md`。

```python
import yaml, os, requests
with open(os.path.expanduser('~/.hermes/config.yaml')) as f:
    cfg = yaml.safe_load(f)
ak = ''
for src in [cfg.get('custom_providers',{}), cfg.get('providers',{})]:
    for k,v in src.items():
        if 'bai' in k.lower(): ak = v.get('api_key',''); break
    if ak: break
payload = {'model':'qwen3-vl-plus','messages':[{'role':'user','content':[
    {'type':'text','text':'描述图片'},
    {'type':'image_url','image_url':{'url':f'data:image/jpeg;base64,{b64}'}}
]}]}
r = requests.post('https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
    headers={'Authorization':f'Bearer {ak}','Content-Type':'application/json'},
    json=payload, timeout=60)
```

### 批量照片扫描

用 Qwen-VL 从大量照片中识别特定主体：采样→批量分析（间隔0.3s）→汇总→入库。

### 方式二：Python + curl @file（最可靠）

```python
import base64, json, yaml, tempfile, os, subprocess

# 1. 从 config 获取 CN 站 key（直连无需代理）
with open(os.path.expanduser('~/.hermes/config.yaml')) as f:
    key = yaml.safe_load(f)['providers']['siliconflow-cn']['api_key']

# 2. 编码图片
with open('/path/to/image.jpg', 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()

# 3. 构建 JSON → tempfile（避开 shell 特殊字符问题）
payload = json.dumps({
    'model': 'Qwen/Qwen3-VL-8B-Instruct',
    'messages': [{'role': 'user', 'content': [
        {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{b64}'}},
        {'type': 'text', 'text': '描述这张图片'}
    ]}],
    'max_tokens': 1024
})
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    f.write(payload)
    tmpfile = f.name

# 4. curl @file 发送（urllib 偶发超时，curl @file 更可靠）
result = subprocess.run([
    'curl', '-s', '--max-time', '120',
    'https://api.siliconflow.cn/v1/chat/completions',
    '-H', f'Authorization: Bearer ***    '-H', 'Content-Type: application/json',
    '-d', f'@{tmpfile}'
], capture_output=True, text=True)
data = json.loads(result.stdout)
print(data['choices'][0]['message']['content'])
os.unlink(tmpfile)
```

### 关键要点

- **必须用 tempfile + curl @file**：base64 字符串含 `+`、`/`、`=` 等字符，嵌入 shell 双引号或行内 Python shell 会炸。先写 JSON 到文件，再 `-d @file` 是最可靠的方案。
- **国内站直连**：`api.siliconflow.cn` 无需代理，时延 ~500ms（国际站 `api.siliconflow.com` 需代理 ~2600ms）
- **模型选择**：`Qwen/Qwen3-VL-8B-Instruct` 最快（~1-2s 响应），`Qwen/Qwen3-VL-32B-Instruct` 精度更高
- **多图片分析**：content 数组可包含多条 image_url，模型会自动对比理解
- **API key 来源**：`config.yaml` 中 `providers.siliconflow-cn.api_key`（51 字符），非截断显示值
- **备用模型列表**：详见 siliconflow skill `references/vision.md`
- **批量 LI 图片分析**：百炼可用于 LI 调试图的批量分析（Wireshark 信令、系统界面、数据表格）。详见 `references/li-batch-vision-analysis.md`

### 方案三：SiliconFlow 国际站 + 代理（CN 超时备用）

当 `api.siliconflow.cn` 超时（`Read timed out`）时，降级到国际站 + Clash 代理。

```python
import base64, json, yaml, os, requests

with open(os.path.expanduser('~/.hermes/config.yaml')) as f:
    key = yaml.safe_load(f)['providers']['siliconflow']['api_key']  # 注意：用 intl key，不是 CN key

with open('/path/to/image.jpg', 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()

payload = {
    'model': 'Qwen/Qwen3-VL-8B-Instruct',
    'messages': [{'role': 'user', 'content': [
        {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{b64}'}},
        {'type': 'text', 'text': '描述这张图片'}
    ]}]
}

headers = {
    'Authorization': f'Bearer {key}',
    'Content-Type': 'application/json'
}

# ⚠️ 代理配置必须用 dict，不能用字符串
proxies = {'http': 'http://127.0.0.1:7897', 'https': 'http://127.0.0.1:7897'}

# 超时设长一些（CN 超时可能是因为限流，intl 也可能慢）
resp = requests.post(
    'https://api.siliconflow.com/v1/chat/completions',
    json=payload, headers=headers, proxies=proxies, timeout=60
)
data = resp.json()
print(data['choices'][0]['message']['content'])
```

**降级判断逻辑**：
1. 先试 CN 端点（直连，快速）
2. 如果 `requests.exceptions.ReadTimeout`（超时）或 `curl: (28) Connection timed out` → 切换到 intl + 代理
3. 切换时必须同时换 key：CN key → intl key（两个 key 不同）
4. 国际站端点：`https://api.siliconflow.com/v1/chat/completions`