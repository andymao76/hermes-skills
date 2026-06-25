# MCP 服务器代理环境变量问题

## 问题描述

MCP 服务器作为 stdio 子进程运行（通过 `command` + `args` 启动），**不会**自动继承父 shell 的代理环境变量。即使 Hermes Agent 进程本身通过 `HTTPS_PROXY`/`HTTP_PROXY` 成功连接了 OpenAI API 等服务，独立启动的 MCP 子进程看到的 `os.environ` 也不包含这些变量。

## 影响范围

| MCP 服务器 | 是否需要代理 | 受影响操作 |
|------------|:----------:|-----------|
| wikipedia-mcp (Python) | 是（zh.wikipedia.org 被 GFW 封锁） | search, get_article, get_summary |
| taoke-mcp (Node.js) | 是（远程配置服务器） | 初始化、搜索 |
| xiaohongshu-mcp | 否（通过 systemd 自身管理代理） | — |

## 解决方案

在 `~/.hermes/config.yaml` 中 **显式设置** `env` 字段：

```yaml
mcp_servers:
  wikipedia:
    command: /path/to/wikipedia-mcp
    args: ["--language", "zh", "--enable-cache"]
    env:
      HTTPS_PROXY: "http://127.0.0.1:7897"
      HTTP_PROXY: "http://127.0.0.1:7897"
```

## 验证方法

1. 配置后运行 `hermes mcp test <name>` 确认连接
2. 调用实际工具（如搜索）确认 API 调用成功
3. 观察 MCP 服务器日志中是否有 `ConnectTimeoutError` 或 `Connection to ... timed out`

## 常见错误

```
Error fetching from Wikipedia: [TypeError: fetch failed]
  cause: ConnectTimeoutError: Connect Timeout Error (attempted address: en.wikipedia.org:443, timeout: 10000ms)
```

这是代理未生效的典型表现。即使 `hermes mcp test` 连接成功（stdio 层面），实际的 HTTP API 调用仍可能超时。

## 技术原理

MCP stdio 子进程的启动方式：
1. Hermes MCP 框架读取 `config.yaml` 中 `mcp_servers.<name>` 的配置
2. 用 `subprocess.Popen(..., env=browser_env)` 启动子进程
3. `browser_env` 从 `os.environ` 复制而来，**但 Hermes 本身不设置代理 env**
4. 因此子进程默认没有代理环境变量
5. 解决方案：在配置的 `env:` 块中明确指定
