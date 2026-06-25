# JD MCP 服务器配置

路径: `/home/andymao/.hermes/jd_mcp/`

## 文件结构

- `server.py` — MCP 服务器入口（3个工具）
- `jd_scraper.py` — 京东刮削/API 逻辑

## 工具清单

| 工具名 | 说明 | 前置条件 |
|--------|------|---------|
| `jd_initialize_login` | QR 码登录（第一步必须） | 无 |
| `jd_search_products` | 搜索京东商品 | 已登录 |
| `jd_get_product_detail` | 获取商品详情 | 已登录 |

## 配置（config.yaml）

```yaml
mcp_servers:
  jd:
    command: /home/andymao/.hermes/hermes-agent/venv/bin/python3
    args:
      - /home/andymao/.hermes/jd_mcp/server.py
    connect_timeout: 30
    timeout: 120
```

## 验证命令

```bash
# CLI 测试连接
hermes mcp test jd
# 预期输出: ✓ Connected (响应时间)

# 直接 MCP 协议测试
printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test-client","version":"1.0"}}}\n' | timeout 5 /home/andymao/.hermes/hermes-agent/venv/bin/python3 /home/andymao/.hermes/jd_mcp/server.py 2>/dev/null
# 预期输出: jsonrpc result with serverInfo {name: "jd-mcp", version: "1.26.0"}
```

## 已知问题

- **Starts but never registers**: The server shows "starting MCP server 'jd'" in `mcp-stderr.log` but never completes initialization. No tools appear in `agent.log` registration messages. Check for silent crashes with:
  ```bash
  grep -A 20 "starting MCP server.*jd" ~/.hermes/logs/mcp-stderr.log | tail -20
  ```
  If this shows nothing after the "starting" line, the server likely crashed on import. Run it standalone:
  ```bash
  timeout 5 /home/andymao/.hermes/hermes-agent/venv/bin/python3 /home/andymao/.hermes/jd_mcp/server.py 2>&1
  ```
- 启动后不会自动注册到当前 Hermes 会话，需运行 `/reload-mcp`
- config.yaml 修改时间须早于 Gateway 启动时间，否则不生效
