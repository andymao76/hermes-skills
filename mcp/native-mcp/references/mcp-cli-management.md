# MCP 热重载与配置管理

除了 config.yaml 的静态配置，Hermes 还支持在会话中管理 MCP 服务器：

## CLI 命令

```bash
# 添加一个 MCP 服务器（交互式或非交互式）
hermes mcp add my-server --url https://example.com/mcp
hermes mcp add my-server --command npx --args "-y @modelcontextprotocol/server-filesystem /tmp"

# 添加带认证的服务器
hermes mcp add my-server --url https://example.com/mcp --auth bearer
hermes mcp add my-server --url https://example.com/mcp --auth oauth

# 从预设添加（内置已知 MCP 服务器模板）
hermes mcp add my-server --preset filesystem

# 查看所有已配置的 MCP 服务器
hermes mcp list

# 测试连接
hermes mcp test my-server

# 配置单个服务器的工具启用/禁用状态
hermes mcp configure my-server

# 移除服务器
hermes mcp remove my-server
# 或
hermes mcp rm my-server
```

## 钩子（Hooks）支持

MCP 服务端模式支持钩子系统。可以通过 `--accept-hooks` 启用：

```bash
hermes mcp serve --accept-hooks
```

## 热重载

当配置变化后，在会话中使用 `/reload-mcp` 命令可以重新加载 MCP 服务器配置，无需重启整个 Hermes。

## CLI vs config.yaml 优先级

- `hermes mcp add` 命令将配置写入 config.yaml 的 `mcp_servers` 段
- 手动编辑 config.yaml 后需要 `/reset` 或重启会话（除非使用 `/reload-mcp`）
- 两种方式结果相同
