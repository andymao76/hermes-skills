# LI 批量图片分析 → 知识库入库工作流

## 场景

用户提供 `/home/andymao/tempfile/` 目录下的多张 LI（合法监听）调试参考图，要求用视觉模型分析并入库。

## 执行步骤

### 1. 获取视觉 API Key

百炼（DashScope）key 存在 `.env` 中 `DASHSCOPE_API_KEY=`。Python 直接读取：

```python
with open(os.path.expanduser('~/.hermes/.env')) as f:
    for line in f:
        if 'DASHSCOPE_API_KEY' in line:
            api_key = line.strip().split('=', 1)[1].strip("'\" ")
            break
```

**陷阱**：`.env` 在终端中输出会被红化为 `***`，但 `open().read()` 可拿到真实值。config.yaml 中的 `custom_providers.bailian.api_key` 也以 `$DASHSCOPE_API_KEY` 形式引用，解析时需回退到 .env。

### 2. 扫描图片文件

注意扩展名大小写：`.png`, `.PNG`, `.jpg`, `.jpeg`, `.gif`, `.bmp` 都要匹配。

```python
import glob
img_dir = '/home/andymao/tempfile'
images = []
for ext in ('*.png', '*.PNG', '*.jpg', '*.jpeg', '*.gif', '*.bmp'):
    images.extend(glob.glob(os.path.join(img_dir, ext)))
```

### 3. 构造请求

使用百炼 `qwen3-vl-plus` 模型，端点 `https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions`。

**提示词设计**（LI 场景专用）：
```
"这是一张合法监听(LI)系统的调试参考图。请详细描述这张图片的内容：
图中有什么信息、结构、参数、数据流、状态、错误码等。
如果是信令流程、数据结构、协议分析、配置截图等，请详细说明每个关键元素。
使用中文回答。"
```

**参数**：`max_tokens=1500`, `temperature=0.1`（稳定输出）。

### 4. 批量发送

- 逐张图片发送（百炼无并发限频）
- 每张请求间隔无需 sleep（实测 12 张 ~4.7 分钟完成）
- 结果暂存 `/tmp/li-images-analysis.json`

### 5. 汇总入库

- 根据内容自动分类（Wireshark 信令 / LI 系统界面 / 数据表格 / 语音工具）
- 写入 `~/knowledge/telecom/lawful_interception/li-debug-reference-images.md`
- 包含每张图的结构化描述 + 调试场景索引

### 模型选择

| 模型 | 适用场景 | 时延 |
|------|---------|------|
| `qwen3-vl-plus` | LI 调试图（Wireshark/信令/日志），精度优先 | ~15-25s/张 |
| `qwen3-vl-flash` | 简单的截图/图标识别，速度优先 | ~5-10s/张 |
| `qwen-vl-ocr` | 含大量文字的截图（日志/配置） | ~10-20s/张 |

### 备用方案

当百炼不可用时（欠费/超时/限流），降级到 SiliconFlow VLM：
- CN 端点（直连）：`https://api.siliconflow.cn/v1/chat/completions`
- 模型 `Qwen/Qwen3-VL-8B-Instruct`（最快）或 `Qwen/Qwen3-VL-32B-Instruct`（精度高）
- 注意：SiliconFlow 有图片过期机制（1小时），需及时分析
