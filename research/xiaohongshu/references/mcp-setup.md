# Xiaohongshu (小红书) MCP Setup — Hermes 集成

## 关键要点

**推荐的连接方式：stdio bridge 模式**（Python 桥接脚本中转），而非直接 HTTP。

原因：xiaohongshu-mcp 使用 Go MCP SDK，其 Streamable HTTP 实现与 Hermes 的 Python MCP SDK 存在传输层兼容性问题（`unhandled errors in a TaskGroup`）。stdio bridge 脚本调用 Python SDK 连接 HTTP 后端，协议栈完全兼容。

## 快速安装

```bash
# 1. 下载二进制
# 从 https://github.com/xpzouying/xiaohongshu-mcp/releases
# 放到 ~/.hermes/bin/

# 2. systemd 服务
systemctl --user daemon-reload
systemctl --user enable --now xiaohongshu-mcp.service

# 3. 验证服务启动
ss -tlnp | grep 18060
systemctl --user status xiaohongshu-mcp
```

## stdio bridge 配置（推荐）

```yaml
# ~/.hermes/config.yaml
mcp_servers:
  xiaohongshu:
    command: /home/andymao/.hermes/venv/bin/python3
    args:
      - /home/andymao/.hermes/scripts/xiaohongshu_bridge.py
    timeout: 120
    connect_timeout: 30
```

桥接脚本在 `~/.hermes/scripts/xiaohongshu_bridge.py`，通过 `streamable_http_client` 连接 `localhost:18060/mcp`。

## 验证

```bash
hermes mcp test xiaohongshu
# 预期：✓ Connected + 13 tools

/reload-mcp          # 当前会话热加载
mcp_xiaohongshu_check_login_status  # 检查登录
```

## 登录流程

1. 调用 `mcp_xiaohongshu_get_login_qrcode` 获取二维码 Base64
2. 将 Base64 解码为 PNG：用 Python 的 `base64.b64decode()` 写入文件
   ⚠️ 不要用 shell 的 `base64 -d`，可能因换行/截断导致 "bad adaptive filter value"
3. 用手机小红书 App 扫码
4. 调用 `mcp_xiaohongshu_check_login_status` 确认

## 备选：直接 HTTP（可能不稳定）

```yaml
mcp_servers:
  xiaohongshu:
    url: http://localhost:18060/mcp
    transport: streamable-http
    timeout: 120
    connect_timeout: 30
```

注意：
- `transport: sse` 不通（Go SDK 的 /mcp 端点只接受 POST，GET 返回 405）
- `hermes mcp test` 可能报 `400 Bad Request` 但运行时可能是 OK 的
- 如果直连接不上，切回 stdio bridge 是已知稳定方案
