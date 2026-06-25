# Obsidian MCP Server 配置

Obsidian MCP Server (`obsidian-mcp-server`) 是一个 npm 包，通过 Obsidian 的 Local REST API 插件与笔记库交互。

## 依赖

- **Obsidian 桌面端**（必须运行中）
- **Local REST API 插件**（在 Obsidian 社区插件中搜索安装）
- **npm 包**：`obsidian-mcp-server`

## 安装步骤

### 1. 安装 npm 包

```bash
npm install -g obsidian-mcp-server
```

验证安装：
```bash
ls ~/.npm-global/bin/obsidian-mcp-server
```

### 2. 安装 Obsidian 插件

打开 Obsidian → 设置 → 社区插件 → 浏览 → 搜索 **Local REST API**（作者 `coddingtonbear`）→ 安装并启用

### 3. 获取 API Key

设置 → 插件选项 → Local REST API → 复制 **API Key**（一串 hex 字符串）

### 4. Hermes 配置

在 `~/.hermes/config.yaml` 的 `mcp_servers` 下添加：

```yaml
mcp_servers:
  obsidian:
    command: /home/andymao/.npm-global/bin/obsidian-mcp-server
    connect_timeout: 30
    enabled: true
    env:
      OBSIDIAN_API_KEY: "your-api-key-here"
    timeout: 60
```

> **注意**：`patch` 和 `write_file` 工具拒绝写入 config.yaml。需要用以下方式之一：
> - `sed` 直接替换（推荐）：`sed -i 's/旧Key/新Key/' ~/.hermes/config.yaml`
> - Python 脚本直接修改 YAML
> - 手动编辑文件

### 5. 生效

- 重启 Hermes Gateway：`hermes gateway restart`
- 或在会话中输入 `/reload-mcp`

## 验证

检查 Obsidian REST API 是否正常：
```bash
# 健康检查（无需认证）
curl -sk https://127.0.0.1:27124/
# 返回: {"status":"OK","authenticated":false,...}

# 认证访问（替换 API Key）
curl -sk -H "Authorization: Bearer YOUR_KEY" https://127.0.0.1:27124/vault/
# 返回 vault 根目录内容
```

MCP 加载成功后，Hermes 工具列表中会出现 `mcp_obsidian_*` 前缀的工具（如 `mcp_obsidian_list_tags`、`mcp_obsidian_search_notes` 等）。

## 注意事项

- **Obsidian 必须运行中**：REST API 插件是 Obsidian 桌面端插件，Obsidian 未运行时无法使用
- **默认禁用**：建议首次配置时 `enabled: false`，配好 API key 后再启用
- **端口**：插件默认 HTTPS 端口 27124，HTTP 端口 27123（可选）
- **自签名证书**：本地访问使用 `-k` 跳过证书验证即可
- **API Key 变更**：重新生成 API Key 后需要更新 config.yaml 并重启 Hermes
- **文件中读取 key**：不要直接把 key 硬编码到 SKILL.md，通过 config.yaml 的 env 配置传递

## 故障排查

| 问题 | 原因 | 解决 |
|------|------|------|
| `connect ECONNREFUSED 127.0.0.1:27124` | Obsidian 未运行或插件未启用 | 打开 Obsidian，确认插件状态 |
| `401 Unauthorized` | API Key 错误或过期 | 从 Obsidian 插件设置重新复制 |
| `authenticated: false` | API Key 不匹配 | 检查 config.yaml 的 OBSIDIAN_API_KEY 与插件设置是否一致 |
| `hermes mcp test` 通过但实际调用失败 | MCP server 连接 OK，但 Obsidian REST API 拒认 Key | 确认 Key 一致后需 `/reload-mcp` 生效 |
| MCP 工具未注册 | Gateway 未 reload | `/reload-mcp` 或重启 Hermes |

## 常见坑点

### API Key 不匹配

Obsidian 插件里的 Key 和 config.yaml 的必须完全一致（64 位 hex 字符串）。即便差一个字符，`obsidian://status` 返回 `authenticated: false`。

**对比 Key 的方法：**
```bash
# 查看 config.yaml 中的 Key
grep OBSIDIAN_API_KEY ~/.hermes/config.yaml

# 去 Obsidian 插件设置页面复制 Key 对比
```

### `hermes config set` 不支持嵌套 MCP env 路径

```bash
# ❌ 会报错：ValueError: Invalid environment variable name
hermes config set mcp_servers.obsidian.env.OBSIDIAN_API_KEY xxx
```

**正确修改方法 —— sed 直接替换：**
```bash
sed -i 's/旧Key/新Key/' ~/.hermes/config.yaml
```

### 修改 Key 后必须 reload 才能生效

即便 config.yaml 已改对，MCP server 进程用的是旧启动时的缓存 Key：

```bash
# 需要 reload 让 MCP server 重新读取 config
# 在 Hermes 会话中输入：
/reload-mcp

# 或彻底重启：
# 先杀掉旧 Obsidian 再启动
pkill -f "/snap/obsidian" 2>/dev/null; sleep 2
snap run obsidian &   # 或用终端 background 模式启动
```

### Snap 版 Obsidian 启动问题

Snap 版 Obsidian 从终端启动需要特殊处理：

```bash
# 正确的后台启动方式（不能用 &）
terminal(background=true, command="snap run obsidian")
# 等待 8-10 秒让插件加载完成
```

普通 `obsidian` 命令或 `obsidian --no-sandbox` 可能报错 "The CLI is unable to find Obsidian"。

### 验证连接三步走

```bash
# 1. 确认 Obsidian 进程和端口
ps aux | grep "obsidian" | grep -v grep
ss -tlnp | grep 27123  # HTTP 端口（默认）
# 或
ss -tlnp | grep 27124  # HTTPS 端口

# 2. 确认 MCP server 连通性
hermes mcp test obsidian
# 期望: ✓ Connected + ✓ Tools discovered: 12

# 3. 实际调用测试
# 在会话中搜索一条笔记验证
mcp_obsidian_obsidian_search_notes(mode="text", query="test")
```
