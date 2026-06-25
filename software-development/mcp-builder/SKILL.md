---
name: mcp-builder
description: "Build Model Context Protocol (MCP) servers. Covers Python FastMCP and TypeScript MCP SDK. Use when creating MCP servers for external API integration, tool definitions, resource handlers, prompt templates. 25K+ installs. From Anthropic official skills."
version: 1.0.0
author: Anthropic
license: MIT
metadata:
  hermes:
    tags: [mcp, server, api, integration, python, typescript]
    related_skills: [native-mcp]
---

# MCP Server Builder

Guide for building Model Context Protocol servers. MCP lets AI agents connect to external APIs, databases, and services.

## Python (FastMCP)

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
def my_tool(param: str) -> str:
    """Tool description"""
    return f"Result: {param}"

@mcp.resource("config://app")
def get_config() -> str:
    """Read-only resource"""
    return "config data"

if __name__ == "__main__":
    mcp.run()
```

## TypeScript (MCP SDK)

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const server = new Server({ name: "my-server", version: "1.0.0" }, {
  capabilities: { tools: {} }
});

server.setToolHandler({ name: "my_tool", description: "...", inputSchema: {} }, async (request) => {
  return { content: [{ type: "text", text: "result" }] };
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

## Config in Hermes

```yaml
mcp_servers:
  my-server:
    command: python
    args: ["path/to/server.py"]
    env:
      API_KEY: "${API_KEY}"
```

## Best Practices

1. **Tools** for write/create actions, **Resources** for read-only data
2. Use `annotations` for authorization hints
3. Resources support URI templates with dynamic parameters
4. Always include `timeout` and `connect_timeout` for reliability
5. Test with `hermes mcp` commands

## Chinese Content Platform MCP Servers

For中文内容平台（知乎、CSDN、小红书等），参见配套参考：

| 文件 | 用途 |
|------|------|
| [references/content-platform-mcp-server.md](references/content-platform-mcp-server.md) | **两种构建模式对比** — API+抓取 vs Selenium 浏览器自动化 |
| [references/selenium-mcp-server-setup.md](references/selenium-mcp-server-setup.md) | **Selenium 模式详细指南** — snap chromium 坑点、path 问题、登录流程 |
| [references/csdn-mcp-server-reference.md](references/csdn-mcp-server-reference.md) | **CSDN API 模式参考模板** — 搜索接口、DOM 提取、工具签名 |
| [references/zhihu-mcp-server-setup.md](references/zhihu-mcp-server-setup.md) | **知乎 Selenium 模式安装指南** — snap chromium 路径、登录流程、python 路径坑 |

### Python 路径陷阱（必读）

Hermes 的 MCP server 默认使用 `/usr/bin/python3`（系统 python），
但依赖（mcp SDK, selenium, requests）通常装在 venv 下。

**config.yaml 中必须指定 venv python 路径：**

```yaml
command: /home/andymao/.hermes/hermes-agent/venv/bin/python3  # ✅
# command: /usr/bin/python3  # ❌ ModuleNotFoundError
```

### MCP test 通过但运行时失败

如果 `hermes mcp test <name>` 成功但重启后工具不出现：
1. `hermes mcp list` 查看运行状态
2. `grep '<name>' ~/.hermes/logs/agent.log` 查看连接错误
3. 如果是 transport 切换（stdio↔HTTP），需**完全重启 Hermes**（`/reload-mcp` 可能不足）
4. 更可靠的验证方式是 venv Python 直连测试（见 native-mcp skill）

### 项目结构规范

```
~/.hermes/mcp-servers/<platform>/
├── server.py                # FastMCP 定义 + 工具函数（单文件最简单）
├── login_manual.py          # 手动登录脚本（Selenium 模式）
├── data/                    # cookies 存储
└── run.py                   # 启动入口（避免模块路径问题）
```

## Real-World Example: xiaohongshu-mcp

The xiaohongshu-mcp setup from this session illustrates the full MCP lifecycle:

### Install
1. Download server + login binaries from GitHub Releases
2. Place in ~/.hermes/bin/
3. Start server: run binary in background (terminal(background=true))
4. Verify: `ss -tlnp | grep <port>` shows LISTEN

### Configure in config.yaml
```yaml
mcp_servers:
  xiaohongshu:
    command: /home/andymao/.hermes/bin/xiaohongshu-mcp
    args: []
    timeout: 120
    connect_timeout: 30
```

### Login
- Run login binary on a desktop machine with a display
- Scan QR code with the target app
- Cookies persist to data directory

### Verify
- `hermes mcp list` shows the server
- Tools become available after session reload
- The MCP protocol may use SSE (Server-Sent Events) rather than HTTP REST

### Headless server considerations
- If running on a headless server (no display), the binary may require Xvfb or may auto-detect and start it
- Environment variables like XHS_PROXY control proxy routing
