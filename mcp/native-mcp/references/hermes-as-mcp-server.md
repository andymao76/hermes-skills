# Hermes 作为 MCP 服务端

Hermes 也可以运行为一个 MCP 服务端（使用 FastMCP），对外暴露 Hermes 的对话能力。外部 MCP 客户端可以连接并调用 Hermes 的各种工具（web_search、terminal、read_file 等）。

## 启动 MCP 服务端

```bash
hermes mcp serve
```

这会启动一个本地 MCP 服务器，默认暴露以下工具：
- fact_store / fact_feedback (Holographic memory)
- web_search / web_extract
- terminal
- read_file / write_file / search_files / patch
- 以及其他已启用的工具

## 暴露的工具

服务端模式下 Hermes 暴露以下工具给 MCP 客户端：

- `browse_conversations` — 浏览和分页 Hermes 会话列表
- `read_messages` — 读取指定会话的完整消息历史
- `search_sessions` — 全文搜索所有历史对话
- `manage_attachments` — 访问会话中的文件/附件

这些工具让外部 AI 工具（VS Code Copilot、Claude Desktop 等）能直接查询 Hermes 的知识库和历史对话。

## 用途

- **IDE 集成**：让代码编辑器通过 MCP 协议调用 Hermes 的工具
- **多 Agent 编排**：其他 MCP 客户端可以通过 Hermes 的 MCP 服务端间接使用其工具
- **远程能力暴露**：通过 HTTP 传输方式将 Hermes 工具暴露给远程客户端

## 连接到 VS Code

### GitHub Copilot Chat

VS Code 内置 `code --add-mcp` 命令，一键注册：

```bash
code --add-mcp '{"name":"hermes","command":"hermes","args":["mcp","serve"]}'
```

配置文件自动写入 `~/.config/Code/User/mcp.json`：

```json
{
  "servers": {
    "hermes": {
      "command": "hermes",
      "args": ["mcp", "serve"]
    }
  },
  "inputs": []
}
```

VS Code 会在 Copilot Chat 中使用 Hermes 工具时自动启动 `hermes mcp serve` 子进程，无需手动运行。

### Continue.dev

编辑 `~/.continue/config.json`：

```json
{
  "mcpServers": {
    "hermes": {
      "command": "hermes",
      "args": ["mcp", "serve"]
    }
  }
}
```

### Cline / Roo Code

在扩展设置 → MCP Servers 中添加 stdio 类型服务器：
- 名称：`hermes`
- 命令：`hermes mcp serve`

### 验证连接

检查 VS Code MCP 日志确认服务端已注册：

```bash
# 查看 MCP 网关日志
tail -20 ~/.config/Code/logs/*/mcpGateway.log

# 查看 hermes 服务端日志
tail -20 ~/.config/Code/logs/*/mcpServer.mcp.config.usrlocal.hermes.log
```

## 连接到 Claude Desktop

编辑 `~/.config/Claude/claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "hermes": {
      "command": "hermes",
      "args": ["mcp", "serve"]
    }
  }
}
```

## 注意事项

- 默认绑定 localhost，不对外暴露，确保安全
- 工具调用需要经过 Hermes 的安全审批流程（approvals）
- 与作为 MCP 客户端的 `mcp_servers` 配置可同时运行
- `hermes mcp serve` 是 stdio 传输，VS Code/Claude Desktop 会自动管理子进程生命周期
- 服务端工具数量取决于 Hermes 已启用的 toolsets，精简 toolsets 可减少上下文开销
