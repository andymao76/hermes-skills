# 小红书 MCP（xiaohongshu-mcp）传输模式配置

## 概述

xiaohongshu-mcp 是一个 Go 语言编写的 HTTP MCP 服务（非 stdio），通过 systemd 管理在 `:18060` 端口运行。底层使用 Go SDK 的 `streamable-http` 协议。

## 服务管理

### systemd 服务

```bash
# 状态
systemctl --user status xiaohongshu-mcp

# 重启
systemctl --user restart xiaohongshu-mcp

# 日志
journalctl --user -u xiaohongshu-mcp --no-pager -n 50
```

服务启动时自动拉起 Xvfb `:99` 虚拟显示（Go SDK 需要）。

### 服务进程

```bash
/home/andymao/.hermes/bin/xiaohongshu-mcp -headless=true -port :18060
```

## 传输模式选择

这个服务支持两种 MCP 传输方式，但有兼容性问题：

### ❌ 方式一：streamable-http（直接连接）

```yaml
mcp_servers:
  xiaohongshu:
    url: "http://localhost:18060/mcp"
    transport: streamable-http
    connect_timeout: 30
    timeout: 120
```

**问题：** `hermes mcp test` 报 400。运行时 agent 连接失败，日志显示 `"unhandled errors in a TaskGroup (1 sub-exception)"`，最终 `"Client error '400 Bad Request'"`。原因是 xiaohongshu-mcp 的 Go SDK 版本与 Hermes 的 Python MCP SDK 版本之间有协议兼容性差异。

### ❌ 方式二：SSE（transport: sse）

```yaml
mcp_servers:
  xiaohongshu:
    url: "http://localhost:18060/mcp"
    transport: sse
```

**问题：** 该服务不暴露 SSE 端点，HEAD 请求返回 `405 Method Not Allowed`，GET 请求返回 `400 Bad Request`。

### ✅ 方式三：stdio bridge（推荐 - 稳定工作）

通过一个 Python 桥接脚本将 HTTP 服务转为 stdio 传输：

```yaml
mcp_servers:
  xiaohongshu:
    command: "/home/andymao/.hermes/venv/bin/python3"
    args: ["/home/andymao/.hermes/scripts/xiaohongshu_bridge.py"]
    connect_timeout: 30
    timeout: 120
```

桥接脚本位置：`/home/andymao/.hermes/scripts/xiaohongshu_bridge.py`

工作原理：
1. 桥接脚本内部使用 `mcp.client.streamable_http` 连接到 `http://localhost:18060/mcp`
2. 将 HTTP 端的工具列表暴露为 stdio 接口
3. Hermes 通过 stdio 协议与本脚本通信

**验证：**
```bash
hermes mcp test xiaohongshu
```
预期：`✓ Connected` + `✓ Tools discovered: 13`

## 可用工具（13个）

| 工具 | 功能 |
|------|------|
| check_login_status | 检查登录状态 |
| get_login_qrcode | 获取登录二维码（Base64） |
| delete_cookies | 重置登录状态 |
| search_feeds | 搜索笔记（关键词 + 筛选排序） |
| list_feeds | 首页推荐列表 |
| get_feed_detail | 笔记详情（内容、图片、评论） |
| user_profile | 用户主页 |
| like_feed | 点赞/取消点赞 |
| favorite_feed | 收藏/取消收藏 |
| post_comment_to_feed | 发表评论 |
| reply_comment_in_feed | 回复评论 |
| publish_content | 发布图文笔记 |
| publish_with_video | 发布视频笔记 |

## 扫码登录流程

```bash
# 1. 检查状态 → 未登录
# 2. 获取二维码（返回 Base64 PNG）
# 3. 保存到文件并打开扫码
# 4. 验证登录成功
```

## 配置切换

config.yaml 修改后需要：
1. CLI 模式：`/reload-mcp` 或退出重开
2. Gateway 模式：`/restart`

注意：`hermes mcp test` 通过 stdio bridge 可正常工作；`streamable-http` 和 `sse` 传输模式均不可用，不要尝试切换。
