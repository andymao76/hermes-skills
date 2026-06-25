---
name: batch-download
description: "批量下载图片和视频。通过 curl/wget/requests 下载单张或多张图片，通过 yt-dlp 下载视频，通过 aiohttp 并发批量下载。自动提取网页中的图片链接。支持代理（国内不可达站点需走 127.0.0.1:7897）。当用户说'下载这个图片'、'批量下载图片'、'下载视频'、'从页面提取图片'时触发。"
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [download, image, video, batch, scraper, yt-dlp]
    related_skills: [web-scraping, agent-browser, firecrawl-scrape]
---

# 批量下载工具（图片 + 视频）

一键下载图片和视频的脚本和指南。

## 核心脚本

```bash
~/.hermes/scripts/batch-download.py
```

## 网络注意事项

本机网络环境：
- **直连国内**：百度、B站等国内站点可直接访问
- **代理 127.0.0.1:7897 当前未运行**：抓取国外站点（YouTube、Google、GitHub raw 等）需要先启动 clash 代理
- **测试方法**：`curl -s --connect-timeout 3 https://www.baidu.com/` 测国内；`curl -s --connect-timeout 3 -x http://127.0.0.1:7897 https://www.google.com` 测代理

### 启动代理后再下载国外资源
```bash
export HTTPS_PROXY=http://127.0.0.1:7897
export HTTP_PROXY=http://127.0.0.1:7897
python3 ~/.hermes/scripts/batch-download.py --type video --url "YouTube_URL"
```

### 用法

```bash
# 下载单张图片
python3 ~/.hermes/scripts/batch-download.py --urls <URL1> <URL2>

# 从网页提取所有图片
python3 ~/.hermes/scripts/batch-download.py --type images-from-page --url "https://example.com/gallery"

# 下载视频（yt-dlp）
python3 ~/.hermes/scripts/batch-download.py --type video --url "https://www.youtube.com/watch?v=xxx"

# 指定输出目录
python3 ~/.hermes/scripts/batch-download.py --urls <URL> --output ~/Pictures/myfolder

# 从文件读取 URL 列表
python3 ~/.hermes/scripts/batch-download.py --file urls.txt
```

### 输出目录

默认：`~/Pictures/downloads/`

## 工具依赖

| 工具 | 用途 | 状态 |
|---|---|---|
| `requests` | 同步 HTTP 下载 | ✅ 已装 |
| `aiohttp` | 异步并发下载 | ✅ 已装 |
| `httpx` | HTTP/2 客户端 | ✅ 已装 |
| `Pillow` | 图片处理 | ✅ 已装 |
| `ffmpeg` | 视频处理/转码/截帧 | ✅ 已装 (v6.1) |
| `yt-dlp` | 视频下载（YouTube/B站等） | ✅ 已装 |
| `BeautifulSoup4` | 网页解析/图片链接提取 | ✅ 已装 |
| snap chromium | 浏览器自动化截图 | ✅ 可用 |

### 快速下载（一行命令）

```bash
# 单张图片
curl -sL "https://example.com/image.jpg" -o ~/Pictures/downloads/photo.jpg

# 带处理的批量下载
python3 -c "
import requests; from PIL import Image; from io import BytesIO
r = requests.get('https://example.com/photo.jpg')
img = Image.open(BytesIO(r.content))
img.thumbnail((800, 800))
img.save('/home/andymao/Pictures/downloads/thumb.jpg')
"

# 视频下载
yt-dlp -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]" -o "~/Pictures/downloads/%(title)s.%(ext)s" "https://www.youtube.com/watch?v=xxx"
```

## 网络说明

- **国内站点**（百度、B站等）：直接访问，无需代理
- **国外站点**（YouTube、Google、GitHub raw 等）：需要代理 `127.0.0.1:7897`
- 脚本默认不带代理参数。如需代理：

```bash
# 方式一：环境变量
export HTTPS_PROXY=http://127.0.0.1:7897
python3 ~/.hermes/scripts/batch-download.py ...

# 方式二：直接在 Python 中指定
python3 -c "
import requests
proxies = {'https': 'http://127.0.0.1:7897'}
r = requests.get('https://youtube.com/...', proxies=proxies)
"
```

## 常见场景

### 场景 1：从页面批量抓取图片

```python
from hermes_tools import terminal
terminal("python3 ~/.hermes/scripts/batch-download.py --type images-from-page --url 'https://example.com/gallery'")
```

### 场景 2：并发批量下载图片

脚本内部使用 aiohttp 实现 5 并发下载（可调整），适合几十张图片的批量任务。

### 场景 3：爬虫 + 下载组合

先用 `firecrawl-scrape` 或 `agent-browser` 抓取页面内容，提取图片 URL 列表，再传给 batch-download.py：

```python
# firecrawl 提取页面 → 正则提取图片 URL → 批量下载
web_extract(urls=["https://example.com/page"])
# 提取出的图片 URL 传递给 batch-download.py
```

## Common Pitfalls

1. **代理 7897 可能未运行** — 默认直连国内，国外需要启动 clash 代理。先 `curl -s --connect-timeout 3 https://www.google.com` 看是否可达
2. **yt-dlp 下载 B 站可能被拦截** — B 站有反爬，可尝试加 `--user-agent` 或使用 `--extractor-args "bilibili:header=..."` 
3. **大批量下载注意硬盘空间** — 当前剩余 165GB，大文件视频需留意

## Verification Checklist

- [ ] `python3 ~/.hermes/scripts/batch-download.py --help` 显示用法
- [ ] 单张图片下载正常
- [ ] 从页面提取图片正常
- [ ] yt-dlp 可解析视频 URL
- [ ] ffmpeg 可用
