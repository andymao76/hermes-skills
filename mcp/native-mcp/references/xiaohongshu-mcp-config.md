# 小红书 MCP（xiaohongshu-mcp）配置

## 概述

xiaohongshu-mcp 是一个 Go SDK 实现的 MCP 服务器，提供小红书内容搜索、互动和发布功能。

## 服务端部署

xiaohongshu-mcp 以 systemd user service 运行，绑定在端口 `:18060`：

```
~/.config/systemd/user/xiaohongshu-mcp.service
```

需要 Xvfb（虚拟显示器，`:99`）用于 headless 浏览器操作。

## Hermes MCP 客户端配置

### 稳定方案：stdio bridge（推荐）

在 `~/.hermes/config.yaml` 的 `mcp_servers` 段配置：

```yaml
mcp_servers:
  xiaohongshu:
    command: "/home/andymao/.hermes/venv/bin/python3"
    args:
      - /home/andymao/.hermes/scripts/xiaohongshu_bridge.py
    connect_timeout: 30
    timeout: 120
```

该方式通过一个 Python bridge 脚本将 HTTP SSE 转换为 stdio MCP 协议。已在生产环境中验证稳定，13 个工具全部注册通过。

**bridge 脚本位置**：`~/.hermes/scripts/xiaohongshu_bridge.py`

工作原理：
1. bridge 连接本地 HTTP 服务 `:18060` 的 Streamable HTTP 端点
2. 将工具列表和调用桥接到 Hermes 的 stdio MCP 通道
3. 对 Hermes 透明——看起来就是一个 stdio MCP 服务器

### 备选方案：直接 HTTP（streamable-http）

```yaml
mcp_servers:
  xiaohongshu:
    url: "http://localhost:18060/mcp"
    transport: streamable-http
    connect_timeout: 30
    timeout: 120
```

**⚠️ 此方式在部分环境中运行时连接失败**（Hermes 的 TaskGroup 异常）。通过 venv Python 直连 `streamable_http_client` 测试可以连上，但 Hermes 运行时的 MCP 框架在 `_preflight_content_type` 预检步骤中失败（400 Bad Request），导致初始化失败。详见下方排错说明。

### 不支持的方案：SSE

**不要设置 `transport: sse`**。xiaohongshu-mcp 的 Go SDK 使用 Streamable HTTP 协议，不支持 SSE 端点。`GET /mcp` 返回 `405 Method Not Allowed`。

## 重要：工具命名差异

通过 Hermes bridge 调用时，工具名称带 `xiaohongshu_` 前缀：
- `mcp_xiaohongshu_get_login_qrcode`
- `mcp_xiaohongshu_search_feeds`

通过**直接 HTTP 调用 Go 服务端**时，工具名称**不带前缀**：
- `get_login_qrcode`
- `search_feeds`

这是 bridge 脚本在转发时自动添加的命名空间前缀。

## 直接 HTTP 调用（绕过 bridge 调试用）

当 stdio bridge 不可用或 Hermes MCP 连接断开时，可直接通过 HTTP 调用 Go 服务端进行调试：

```python
import requests, json

base = "http://127.0.0.1:18060/mcp"

# 1. 初始化会话，获取 Mcp-Session-Id
r = requests.post(base, json={
    "jsonrpc":"2.0", "id":1, "method":"initialize",
    "params":{"protocolVersion":"2024-11-05","capabilities":{}}
})
sid = r.headers['Mcp-Session-Id']
h = {"Content-Type":"application/json","Mcp-Session-Id":sid}

# 2. 完成初始化
requests.post(base, json={"jsonrpc":"2.0","method":"notifications/initialized"}, headers=h)

# 3. 调用工具（用不带前缀的原始名称）
r = requests.post(base, json={
    "jsonrpc":"2.0", "id":2, "method":"tools/call",
    "params":{"name":"get_login_qrcode","arguments":{}}
}, headers=h, timeout=30)

data = r.json()
content = data['result']['content']
# content[0] = text (描述)
# content[1] = image (PNG base64数据)
img_b64 = content[1]['data']
```

**适用场景**：
- bridge 进程挂掉但 Go 服务端仍在运行
- Hermes MCP 连接处于 ClosedResourceError 状态
- 需要绕过 bridge 的工具名前缀直接调用

**注意事项**：
- 每次 HTTP 请求都需要先初始化获取新的 Session-Id
- 服务端使用 Streamable HTTP MCP 协议，**不**支持 SSE 方式
- 响应中 content 数组包含多个类型：`text`（描述文字）和 `image`（图片数据）
- 图片数据在 content[1] 的 `data` 字段中（base64），不在 text 字段里

## 二维码问题排查

### 症状：PNG 打开报 "bad adaptive filter value"

表现为：
- `pngcheck -v xhs_qrcode.png` 报 `zlib: inflate error = -3 (data error)`
- `private (invalid?) row-filter type (255)` 警告
- ImageMagick 报 `bad adaptive filter value`
- 终端日志：二维码请求返回正常，但图片数据流损坏

### 根因：xiaohongshu-mcp 服务端的 headless Chrome 内存泄漏

服务长期运行（数小时）后 headless Chrome 进程内存膨胀至 700MB-1.1GB，导致二维码渲染异常。**不是 base64 传输问题**——每次调用都返回同样的损坏数据（约 3067 字节，比正常 3103 字节少）。

### 快速修复

```bash
# 重启服务
systemctl --user restart xiaohongshu-mcp
sleep 3

# 验证服务恢复（内存应降至 ~25MB）
systemctl --user status xiaohongshu-mcp 2>/dev/null | head -10

# 验证健康状态
curl -s http://127.0.0.1:18060/health
# 预期: {"success":true,"data":{"status":"healthy"},"message":"服务正常"}
```

### 诊断工具

```bash
# 安装 pngcheck
sudo apt install -y pngcheck

# 验证 PNG 文件完整性
pngcheck -v xiaohongshu_qrcode.png
# 正常: "No errors detected in ... (N chunks, X.X% compression)"
# 损坏: "zlib: inflate error = -3 (data error)" + "ERRORS DETECTED"

# 快速文件类型验证
file xiaohongshu_qrcode.png
# 正常: "PNG image data, 128 x 128, 32-bit RGB+alpha"

# ImageMagick 6（当前环境）用 convert，不用 magick
convert -version  # 显示 ImageMagick 6.x
convert xhs_qr.png out.png  # 读写验证
```

### 预防措施

- 定期检查 xiaohongshu-mcp 服务内存：`systemctl --user status xiaohongshu-mcp | grep Memory`
- 正常范围：~25-50MB（刚启动）→ 如果超 500MB 应考虑重启
- 可设置 cron 定时重启（如每日凌晨低峰期）

### `get_login_qrcode` 重复调用生成新二维码

每次调用都会使之前的二维码失效。扫码有时间限制（约 40 秒），超时需要重新获取。

## 排错

### `hermes mcp test` 返回 400 / 运行时 TaskGroup 异常

这是一个**已知问题**。`hermes mcp test` 使用简单的测试 HTTP 客户端，而运行时 `streamable_http_client` 的预检步骤（`_preflight_content_type` 发 HEAD/GET 请求）可能因 xiaohongshu-mcp Go 服务的响应格式触发 400。

**验证方法**（比 `hermes mcp test` 更可靠）：

```bash
cd ~/.hermes
source hermes-agent/venv/bin/activate
python3 -c "
import asyncio
from mcp.client.streamable_http import streamable_http_client
from mcp import ClientSession

async def test():
    async with streamable_http_client('http://localhost:18060/mcp') as (read, write, sid):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            print(f'Connected! Tools: {len(result.tools)}')
            for t in result.tools:
                print(f'  - {t.name}')

asyncio.run(test())
"
```

如果 venv 直连成功但 Hermes 运行时失败，请改用 stdio bridge 方案。

### transport 切换后的服务失效

当从 stdio 切换到 streamable-http（或反向）时，**仅靠 `/reload-mcp` 可能不足以让新配置生效**。原因是 MCP 连接状态在 agent 进程中缓存，transport 变更后缓存中的旧状态可能干扰新配置的连接。

**完整切换步骤**：
1. 修改 `~/.hermes/config.yaml` 中 `mcp_servers.xiaohongshu` 的配置
2. `hermes mcp test xiaohongshu` 确认 CLI 层连接成功
3. 如果 CLI 测试通过但运行时失败 → **必须退出当前会话，启动全新 `hermes` 进程**（不要用 `/reload-mcp`）
4. 重新进入后检查工具是否注册：`grep "registered" ~/.hermes/logs/agent.log` | grep xiaohongshu
5. 实际调用一个工具验证

**快速验证运行时连接的工具数量**（查看 agent.log）：
```bash
grep -i "registered.*tool.*xiaohongshu" ~/.hermes/logs/agent.log
```
预期输出：注册了 13 个工具。如果只有 9 个工具（只有 db-query），说明 xiaohongshu 未连接成功。

### 服务端未运行

```bash
systemctl --user status xiaohongshu-mcp
```

确认服务 active，Xvfb 在 `:99` 运行中。

## 可用工具（13 个）

| 工具 | 用途 |
|------|------|
| `check_login_status` | 检查登录状态 |
| `get_login_qrcode` | 获取扫码二维码 |
| `delete_cookies` | 重置登录 |
| `search_feeds` | 搜索笔记（关键词+筛选） |
| `list_feeds` | 首页推荐列表 |
| `get_feed_detail` | 笔记详情（含评论） |
| `user_profile` | 用户主页信息 |
| `like_feed` | 点赞/取消点赞 |
| `favorite_feed` | 收藏/取消收藏 |
| `post_comment_to_feed` | 发表评论 |
| `reply_comment_in_feed` | 回复评论 |
| `publish_content` | 发布图文笔记 |
| `publish_with_video` | 发布视频笔记 |

## 典型流程

1. 检查登录：`mcp_xiaohongshu_check_login_status`
2. 如未登录：`mcp_xiaohongshu_get_login_qrcode` → 手机扫码
3. 搜索内容：`mcp_xiaohongshu_search_feeds(keyword="...")`
4. 查看详情：`mcp_xiaohongshu_get_feed_detail(feed_id, xsec_token)`
5. 互动：点赞/收藏/评论（需要 feed_id + xsec_token 从搜索结果获取）

## 历史

- 原配置为 stdio bridge（稳定工作）
- 曾尝试改为 streamable-http 直接连接：venv 直连测试通过但 Hermes 运行时失败（TaskGroup 400）
- 最终回退到 stdio bridge，验证通过
