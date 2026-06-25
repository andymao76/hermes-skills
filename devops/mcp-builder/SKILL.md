---
name: mcp-builder
description: MCP Server 构建 — 构建、测试、调试和部署 MCP 服务。覆盖 Python FastMCP 模式、Playwright 浏览器自动化、扫码登录+Session持久化、抗反爬策略。
tags: [mcp, server, testing, debugging, playwright, scraper]
---

# MCP Server Builder

构建、测试、调试和部署 MCP（Model Context Protocol）服务。

## 适用场景

- 构建基于 Python FastMCP 的 stdio MCP 服务
- 用 Playwright 浏览器自动化创建内容平台 MCP（淘宝、京东、小红书等）
- 需要扫码登录 + Session 持久化的场景
- 批量测试 MCP 服务的可用性

## 快速参考

### 1. MCP Server 基础模板 (FastMCP)

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

mcp_server = Server("my-server")

@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(name="tool_name", description="...",
             inputSchema={"type":"object","properties":{}})
    ]

@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    ...

async def main():
    async with stdio_server() as (r, w):
        await mcp_server.run(r, w, mcp_server.create_initialization_options())

if __name__ == "__main__":
    import asyncio; asyncio.run(main())
```

### 2. 测试 MCP 服务

测试 stdio MCP 服务是否正常工作：

```bash
cd ~/.hermes/path/to/server/
printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}\n' \
  | timeout 10 /venv/bin/python3 server.py 2>/dev/null \
  | tail -1 | python3 -m json.tool
```

期望响应包含:
- `result.serverInfo` — 服务名 + 版本
- `result.tools[]` — 注册的工具列表
- 无 `error` 字段

批量自动测试多个 MCP 服务：

```python
# See references/mcp-test-script.py for full script
# Pattern: subprocess -> send initialize -> read response -> send tools/list -> read -> terminate
```

### 3. 中文内容平台 MCP 抗反爬策略

| 平台 | 搜索 | 详情 | 是否需要登录 |
|------|------|------|------------|
| 淘宝/天猫 | ✅ 免登录 | ✅ 免登录 | Playwright headless 可用 |
| 京东 | ❌ 需登录 | ⚠️ 可能需登录 | 重定向到 passport 登录页 |
| 小红书 | ✅ 免登录 | ✅ 免登录 | 有独立 MCP 二进制 |
| 知乎 | ✅ 免登录 | ✅ 免登录 | 公开内容可访问 |
| CSDN | ✅ 免登录 | ✅ 免登录 | API 模式可用 |

京东反爬极强：Playwright Stealth、真实 Chrome CDP、xvfb 非无头模式均被识别。唯一可行方案是**扫码登录 + Session 持久化**。

### 4. 扫码登录 + Session 持久化 (JD.com 模式)

```python
from pathlib import Path
import json

SESSION_FILE = Path.home() / ".hermes" / "jd_mcp" / "session.json"

async def _save_session(self, context):
    state = await context.storage_state()
    with open(SESSION_FILE, "w") as f:
        json.dump(state, f, ensure_ascii=False)

async def _load_session(self, context):
    with open(SESSION_FILE) as f:
        state = json.load(f)
    await context.add_cookies(state.get("cookies", []))
```

工具流程：`jd_initialize_login` (首次扫码) → `jd_search_products` / `jd_get_product_detail` (复用 Session)

### 5. Config.yaml 配置

```yaml
mcp_servers:
  jd:
    command: /home/andymao/.hermes/hermes-agent/venv/bin/python3
    args: [/home/andymao/.hermes/jd_mcp/server.py]
    connect_timeout: 30
    timeout: 120
```

注意：`command` 必须使用 venv 下的 python3，系统 python 会报 `ModuleNotFoundError`。

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 无响应(initialize) | Python 模块找不到 | config.yaml 使用 venv python 路径 |
| 连接重置 | 脚本启动时崩溃 | 直接运行看 traceback |
| 超时 | 缺少环境变量 | 在 config.yaml 添加 env |
| tools/list 为空 | 错误的装饰器 | 检查 `@mcp_server.list_tools()` 模式 |

## 参考文件

- `references/mcp-test-script.py` — 批量测试所有 MCP 服务的 Python 脚本
