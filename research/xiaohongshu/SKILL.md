---
name: xiaohongshu
description: |
  小红书（RedNote）内容工具。使用场景：
  - 搜索小红书笔记并获取详情
  - 获取首页推荐列表
  - 获取帖子详情（正文、图片、互动数据、评论）
  - 发表评论 / 回复评论
  - 获取用户主页和笔记列表
  - 点赞、收藏帖子
  - 发布图文或视频笔记
  - 热点话题跟踪与分析报告
  - 帖子导出为长图
  触发词示例：
  - "搜一下小红书上的XX"
  - "跟踪一下小红书上的XX热点"
  - "分析小红书上关于XX的讨论"
  - "小红书XX话题报告"
  - "生成XX的小红书舆情报告"
---

# 小红书 MCP Skill

基于 [xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp) 的 MCP 工具集，通过 Hermes 原生 MCP 客户端调用。

## Hermes 集成（关键）

**xiaohongshu-mcp 是 HTTP 服务器（Go SDK），但 Hermes 用 stdio bridge 模式连接更可靠。** 
直接 HTTP (streamable-http/sse) 连接可能因 Go SDK 与 Python MCP SDK 传输层不兼容而失败。

### 架构（推荐 — stdio bridge）

```
小红书 App (扫码登录)
        │
        ▼
xiaohongshu-mcp (Go, HTTP :18060)  ← 独立 systemd 服务
        │
        ▼
xiaohongshu_bridge.py (Python stdio) ← Hermes config.yaml command
        │
        ▼
Agent 调用 mcp_xiaohongshu_* 工具
```

bridge 脚本（`~/.hermes/scripts/xiaohongshu_bridge.py`）充当翻译层：接受 Hermes 的 stdio MCP 协议，内部通过 `streamable_http_client` 连接 xiaohongshu-mcp HTTP 服务。

### 步骤 1：安装二进制

从 [Releases](https://github.com/xpzouying/xiaohongshu-mcp/releases) 下载 `xiaohongshu-mcp-linux-amd64`，放到 `~/.hermes/bin/`：

```bash
chmod +x ~/.hermes/bin/xiaohongshu-mcp
```

首次运行会自动下载 headless 浏览器（~150MB）。

### 步骤 2：创建 systemd 服务

```ini
# ~/.config/systemd/user/xiaohongshu-mcp.service
[Unit]
Description=Xiaohongshu MCP HTTP Server
After=network-online.target

[Service]
Type=simple
ExecStartPre=/bin/sh -c '/usr/bin/Xvfb :99 -screen 0 1280x1024x24 -ac & sleep 1'
ExecStart=/home/andymao/.hermes/bin/xiaohongshu-mcp -headless=true -port ":18060"
Restart=on-failure
RestartSec=5
Environment=DISPLAY=:99

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now xiaohongshu-mcp.service
```

### 步骤 3：创建 stdio bridge 脚本

```python
# ~/.hermes/scripts/xiaohongshu_bridge.py
# 把 HTTP MCP 服务转成 stdio 供 Hermes 连接
import asyncio, sys
from mcp.client.streamable_http import streamable_http_client
from mcp.server.stdio import stdio_server
from mcp import ClientSession
from mcp.types import Tool, TextContent

XHS_URL = "http://localhost:18060/mcp"

class Bridge:
    def __init__(self):
        self.client = None
        self.tools = []

    async def connect(self):
        self._ctx = streamable_http_client(XHS_URL)
        read, write, _ = await self._ctx.__aenter__()
        self._session_ctx = ClientSession(read, write)
        self.client = await self._session_ctx.__aenter__()
        await self.client.initialize()
        result = await self.client.list_tools()
        self.tools = result.tools

    async def disconnect(self):
        if self.client: await self._session_ctx.__aexit__(None, None, None)
        if hasattr(self, '_ctx'): await self._ctx.__aexit__(None, None, None)

async def main():
    bridge = Bridge()
    await bridge.connect()
    mcp_tools = [Tool(name=t.name, description=t.description or "", inputSchema=t.inputSchema) for t in bridge.tools]

    async def list_tools(): return mcp_tools

    async def call_tool(name, arguments):
        result = await bridge.client.call_tool(name, arguments)
        items = []
        if hasattr(result, 'content') and result.content:
            for c in result.content:
                items.append(TextContent(type="text", text=getattr(c, 'text', str(getattr(c, 'data', str(result))))))
        return items or [TextContent(type="text", text=str(result))]

    try:
        from mcp.server.lowlevel import Server
        app = Server("xiaohongshu-bridge")
        app.list_tools()(list_tools)
        app.call_tool()(call_tool)
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
    finally:
        await bridge.disconnect()

asyncio.run(main())
```

### 步骤 4：配置 Hermes MCP（stdio bridge — 推荐）

```yaml
# ~/.hermes/config.yaml — MCP servers section
mcp_servers:
  xiaohongshu:
    command: /home/andymao/.hermes/venv/bin/python3
    args:
      - /home/andymao/.hermes/scripts/xiaohongshu_bridge.py
    timeout: 120
    connect_timeout: 30
```

**⚠️ 必须用 Hermes venv 的 python3（有 mcp 包），不是系统 python3。**

配置修改后需 `/reload-mcp` 才会生效。

### 备选：直接 HTTP transport（不推荐）

如果 stdio bridge 方式不可用，可尝试直连：

```yaml
mcp_servers:
  xiaohongshu:
    url: http://localhost:18060/mcp
    transport: streamable-http    # Go SDK 使用 Streamable HTTP 协议
    timeout: 120
    connect_timeout: 30
```

**已知问题：** 
- `transport: sse` 会导致运行时 `unhandled errors in a TaskGroup`（Go SDK 不支持 SSE GET 端点）
- `hermes mcp test` 可能返回 `400 Bad Request`（测试路径与运行时路径不一致），但实际运行时可能成功
- 如果直连失败，切回 stdio bridge 是稳定方案

### 步骤 4：登录

Gateway 重启后，Agent 自动获得 `mcp_xiaohongshu_*` 工具。首次使用需扫码：

```
用户: 帮我登录小红书
Agent: 调用 mcp_xiaohongshu_get_login_qrcode → 返回二维码 Base64
       用户用小红书 App 扫码
       调用 mcp_xiaohongshu_check_login_status → 确认已登录
```

**二维码保存（重要）：** 用 Python 解码 Base64 写入 PNG 文件：

```python
import base64
with open("/path/to/qrcode.png", "wb") as f:
    f.write(base64.b64decode(base64_string))
```

⚠️ **不要用 shell 的 `base64 -d`**：管道中换行/截断问题会导致 "bad adaptive filter value" 错误，图片无法打开。

Cookies 有效期约 30 天，过期需重新扫码。

## 核心数据流

**重要：** 大多数操作需要 `feed_id` + `xsec_token` 配对。这两个值从搜索/推荐/用户主页结果中获取，**不可自行构造**。

```
search_feeds / list_feeds / user_profile
        │
        ▼
  返回 feeds 数组，每个 feed 包含:
  ├── id          → 用作 feed_id
  ├── xsecToken   → 用作 xsec_token
  └── noteCard    → 标题、作者、封面、互动数据
        │
        ▼
  get_feed_detail(feed_id, xsec_token)
        │
        ▼
  返回完整笔记: 正文、图片列表、评论列表
  评论中包含 comment_id、user_id（用于回复评论）
```

## 工具调用方式

在 Hermes 中，MCP 工具会被自动发现并注册为 `mcp_xiaohongshu_<tool_name>`。无需通过 shell 脚本调用，直接让 Agent 使用即可。

部分工具（如热点跟踪）没有对应的 MCP 工具时，Agent 会通过组合调用 `search_feeds` + `get_feed_detail` 来实现相同效果。

## MCP 工具详细参数

### search_feeds — 搜索笔记

```json
{"keyword": "咖啡", "filters": {"sort_by": "最新", "note_type": "图文", "publish_time": "一周内"}}
```

filters 可选字段：
- `sort_by`: 综合 | 最新 | 最多点赞 | 最多评论 | 最多收藏
- `note_type`: 不限 | 视频 | 图文
- `publish_time`: 不限 | 一天内 | 一周内 | 半年内
- `search_scope`: 不限 | 已看过 | 未看过 | 已关注
- `location`: 不限 | 同城 | 附近

### get_feed_detail — 帖子详情

```json
{"feed_id": "...", "xsec_token": "...", "load_all_comments": true, "limit": 20}
```

- `load_all_comments`: false(默认) 返回前10条，true 滚动加载更多
- `limit`: 加载评论上限（仅 load_all_comments=true 时生效），默认 20
- `click_more_replies`: 是否展开二级回复，默认 false
- `reply_limit`: 跳过回复数超过此值的评论，默认 10
- `scroll_speed`: slow | normal | fast

### post_comment_to_feed — 发表评论

```json
{"feed_id": "...", "xsec_token": "...", "content": "写得真好！"}
```

### reply_comment_in_feed — 回复评论

```json
{"feed_id": "...", "xsec_token": "...", "content": "谢谢！", "comment_id": "...", "user_id": "..."}
```

`comment_id` 和 `user_id` 从 get_feed_detail 返回的评论列表中获取。

### user_profile — 用户主页

```json
{"user_id": "...", "xsec_token": "..."}
```

`user_id` 从 feed 的 `noteCard.user.userId` 获取，`xsec_token` 使用该 feed 的 `xsecToken`。

### like_feed — 点赞/取消

```json
{"feed_id": "...", "xsec_token": "..."}
{"feed_id": "...", "xsec_token": "...", "unlike": true}
```

### favorite_feed — 收藏/取消

```json
{"feed_id": "...", "xsec_token": "..."}
{"feed_id": "...", "xsec_token": "...", "unfavorite": true}
```

### publish_content — 发布图文

```json
{"title": "标题(≤20字)", "content": "正文(≤1000字)", "images": ["/path/to/img.jpg"], "tags": ["美食","旅行"]}
```

- `images`: 至少1张，支持本地路径或 HTTP URL
- `tags`: 可选，话题标签
- `schedule_at`: 可选，定时发布（ISO8601，1小时~14天内）

### publish_with_video — 发布视频

```json
{"title": "标题", "content": "正文", "video": "/path/to/video.mp4"}
```

### 其他工具

| 工具 | 参数 | 说明 |
|------|------|------|
| `check_login_status` | 无 | 检查登录状态 |
| `list_feeds` | 无 | 获取首页推荐 |
| `get_login_qrcode` | 无 | 获取登录二维码（Base64 PNG） |
| `delete_cookies` | 无 | 删除 cookies，重置登录 |

## 热点跟踪

自动搜索 → 拉取详情 → 生成 Markdown 报告。

```bash
./track-topic.sh "DeepSeek" --limit 5
./track-topic.sh "春节旅游" --limit 10 --output report.md
./track-topic.sh "iPhone 16" --limit 5 --feishu    # 导出飞书
```

报告包含：概览统计、热帖详情（正文+热评）、评论关键词、趋势分析。

## 长图导出

将帖子导出为白底黑字的 JPG 长图。

```bash
./export-long-image.sh --posts-file posts.json -o output.jpg
```

posts.json 格式：
```json
[{
  "title": "标题", "author": "作者", "stats": "1.3万赞",
  "desc": "正文摘要", "images": ["https://..."],
  "per_image_text": {"1": "第2张图的说明"}
}]
```

依赖：Python 3.10+、Pillow。

## 注意事项

- Cookies 有效期约 30 天，过期需重新扫码
- 首次启动会下载 headless 浏览器（~150MB）
- 同一账号避免多客户端同时操作
- 发布限制：标题≤20字符，正文≤1000字符，日发布≤50条
- Linux 服务器需 xvfb（`apt-get install xvfb`）
- **Go MCP SDK 兼容性**：xiaohongshu-mcp 使用 Go 官方 MCP SDK，与 Hermes 的 Python MCP SDK 可能存在传输层兼容问题。当前环境已配置 `transport: sse`。若连接报 `unhandled errors in a TaskGroup`，切换 `transport: streamable-http` 试之
- **HTTP 服务必须先行启动**：Hermes 的 native MCP 客户端在启动时连接 MCP 服务器。若 xiaohongshu-mcp 服务未运行，工具列表中将不出现 `mcp_xiaohongshu_*` 工具
- **热加载**：修改 config.yaml 后执行 `/reload-mcp`（in-session）或重启 gateway。`hermes mcp test xiaohongshu` 可测试连接

## 已知限制：小红书反爬检测

### 症状

扫码登录后小红书提示 **"账号违规预警，账号疑似使用第三方工具或脚本"**。真实触发场景完整流程：

```
Agent 调用 get_login_qrcode() → 生成二维码（有效期 ~5分钟）
用户用小红书 App 扫码
App 提示："账号违规预警，您当前的操作环境存在风险"
原因：xiaohongshu-mcp 基于 Chromium 浏览器自动化，
即便手动扫码，X-Forwarded-For、User-Agent、WebDriver 特征
都会被小红书风控系统检测到。
```

### 影响程度

- ❌ **新扫码登录** → 大概率直接触发警告（严重）
- ⚠️ 已登录 session → 某些操作可能正常工作，但随时可能被封
- 该问题**无永久修复方案**。清除 cookies 重试（`mcp_xiaohongshu_delete_cookies`）可能短暂恢复，但再次登录大概率同样触发

### 降级方案：多源交叉搜索

当小红书 MCP 不可用时（触发反爬），不要反复重试登录——直接切换到以下替代方案，**三者并行可达 95%+ 覆盖率**：

```
xiaohongshu MCP 不可用
        │
        ├── CSDN MCP: mcp_csdn_search_csdn(keyword)  ← 最优降级
        │   - 返回结构化结果（标题+热度+URL），无需登录
        │   - 中文技术/行业内容覆盖广
        │   - 调用后直接聚合返回，无需额外提取
        │
        ├── Zhihu MCP: 已配置的 zhihu MCP 服务
        │   - 知乎社区深度讨论
        │   - 无需登录
        │   ⚠️ 但注意：知乎 MCP 当前仅有发布工具，
        │     搜索需通过 web_search(site:zhihu.com) 间接完成
        │
        ├── web_search: site:zhuanlan.zhihu.com <topic>
        │   - 定向搜索知乎专栏
        │
        ├── web_search: 纯关键词搜索
        │   - Google/Bing 通用搜索
        │   - 覆盖面最广，但可能有部分低质量内容
        │
        └── web_search_plus(provider='auto', mode='research')
            - 多提供商聚合搜索 + 内容提取
            - 耗时较长但信息密度最高
```

**推荐做法：** 同时调用 CSDN MCP + web_search（通用 + site:zhihu.com），并行取结果后去重聚合。无需等一个结果再调用下一个。

### cookies 清除后残留问题

```bash
mcp_xiaohongshu_delete_cookies
# 结果：cookies.json 已删除
# 但：下次扫码仍然触发反爬（无法消除特征）
```

清除 cookies 只是重置登录状态，不影响浏览器的 WebDriver 特征。

## 故障排查

| 症状 | 原因 | 解决 |
|------|------|------|
| `StdioServerParameters validation error` | 用了 `command` 而非 `url` | 改为 `url: http://localhost:18060/mcp` |
| `unhandled errors in a TaskGroup` | Go/Python SDK 传输层不兼容 | 切换 `transport: sse` 或 `streamable-http` |
| MCP 工具列表无 xiaohongshu | 服务未启动或 gateway 未重载 | `systemctl --user start xiaohongshu-mcp` + `/reload-mcp` |
| `get_login_qrcode` 无响应 | 未登录或 Xvfb 未运行 | 检查 `pgrep Xvfb` 和 `systemctl --user status` |
