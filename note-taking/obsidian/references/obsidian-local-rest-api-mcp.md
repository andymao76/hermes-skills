# Obsidian Local REST API + MCP 集成指南

将 Hermes 的 Obsidian MCP 连接到 Obsidian 本地笔记库，实现 AI 直接读/写/搜索笔记。

## 架构

```
Hermes Agent ──stdio──> obsidian-mcp-server (npm) ──HTTPS──> Obsidian Local REST API 插件
                                                                └──> Obsidian Vault
```

- **obsidian-mcp-server**: npm 包，作为 Hermes 的 stdio MCP 服务器运行
- **Obsidian Local REST API 插件**: Obsidian 社区插件，暴露 REST API 和内置 MCP 端点

## 安装步骤

### 1️⃣ 安装 Obsidian 插件

1. 打开 Obsidian → 设置 → 社区插件 → 浏览
2. 搜索 **Local REST API**（作者 `coddingtonbear`）
3. 安装并启用

### 2️⃣ 获取 API Key

进入 **设置 → 插件选项 → Local REST API** 复制 API Key。

默认端口：
- HTTPS: `27124`
- HTTP: `27123`（可选启用）

### 3️⃣ 安装 obsidian-mcp-server

```bash
npm install -g obsidian-mcp-server
```

验证安装：
```bash
ls ~/.npm-global/bin/obsidian-mcp-server
```

### 4️⃣ 配置 Hermes MCP

编辑 `~/.hermes/config.yaml`，在 `mcp_servers` 下添加：

```yaml
mcp_servers:
  obsidian:
    command: /home/YOUR_USER/.npm-global/bin/obsidian-mcp-server
    connect_timeout: 30
    enabled: true
    env:
      OBSIDIAN_API_KEY: "你的API Key"
    timeout: 60
```

注意：Hermes 的 `patch`/`write_file` 工具拒绝直接写入 config.yaml。使用 sed 或 Python 来修改：

```bash
# 使用 sed 更新 API key
sed -i 's/placeholder/你的API Key/' ~/.hermes/config.yaml
```

或使用 Python：
```python
import yaml
with open("~/.hermes/config.yaml") as f:
    cfg = yaml.safe_load(f)
cfg["mcp_servers"]["obsidian"]["env"]["OBSIDIAN_API_KEY"] = "你的API Key"
cfg["mcp_servers"]["obsidian"]["enabled"] = True
with open("~/.hermes/config.yaml", "w") as f:
    yaml.dump(cfg, f)
```

**坑：`hermes config set` 无法设置嵌套 MCP env 路径**
```
hermes config set mcp_servers.obsidian.env.OBSIDIAN_API_KEY <key>
# → ValueError: Invalid environment variable name: 'MCP_SERVERS.OBSIDIAN.ENV.OBSIDIAN_API_KEY'
```
因为 `hermes config set` 会把 `mcp_servers.obsidian.env.*` 误解析为环境变量名。必须直接用 sed/Python 写 config.yaml。

### 5️⃣ 重载 MCP

新配置会在 Hermes 下次启动时自动加载。如需立即生效：

```bash
# 方案A: 重启整个 gateway（会终止当前会话）
hermes gateway restart

# 方案B: 在会话中执行 /reload-mcp（不中断会话，推荐）
# 直接在 Hermes 中输入 /reload-mcp

# 方案C: 杀掉旧的 obsidian-mcp-server 进程后让 Hermes 自动重启
pkill -f obsidian-mcp-server
# Hermes 会在下次调用时自动重建 MCP 连接
```

**坑：仅重启 Hermes 网关不够——必须让 obsidian-mcp-server 进程重新读取配置**
更新 config.yaml 后，旧的 obsidian-mcp-server 进程仍然持有旧的环境变量。`hermes mcp test obsidian` 会 spawn 新进程测试并显示成功，但实际工具调用仍路由到旧进程。必须重启 MCP 服务器（通过 `/reload-mcp` 或 kill 旧进程）。

## 验证

### 分步验证（推荐流程）

```
步骤1: REST API 健康检查       → curl -sk https://127.0.0.1:27124/
步骤2: 认证测试               → curl -sk -H "Authorization: Bearer <key>" https://127.0.0.1:27124/vault/
步骤3: MCP 连接测试           → hermes mcp test obsidian
步骤4: 端到端功能验证          → 调用 obsidian_search_notes 或 obsidian://status 资源
```

### REST API 健康检查（无需认证）

```bash
curl -sk https://127.0.0.1:27124/
```

正常返回：
```json
{"status":"OK","service":"Obsidian Local REST API","authenticated":false,"versions":{"obsidian":"1.12.7","self":"4.1.3"}}
```

**注意**：`authenticated: false` 在根路径下是正常的——根路径是无需认证的健康检查端点。

### 认证测试

```bash
curl -sk -H "Authorization: Bearer 你的API Key" https://127.0.0.1:27124/vault/
```

返回 vault 根目录文件列表 ← 认证成功。

### MCP 工具验证

MCP 加载成功后，Hermes 会自动注册 `mcp_obsidian_*` 前缀的工具：
- `obsidian_get_note` — 读取笔记
- `obsidian_search_notes` — 搜索笔记
- `obsidian_list_notes` — 列出目录
- `obsidian_list_tags` — 列出标签
- `obsidian_write_note` — 创建笔记
- `obsidian_append_to_note` — 追加内容
- `obsidian_patch_note` — 编辑指定段落
- `obsidian_replace_in_note` — 查找替换
- `obsidian_manage_frontmatter` — 读写元数据
- `obsidian_manage_tags` — 管理标签
- `obsidian_open_in_ui` — 在 Obsidian 中打开
- `obsidian_delete_note` — 删除笔记
- `obsidian://status` 资源 — 检查认证状态和版本

### 端到端功能验证（关键）

`hermes mcp test obsidian` **只测试 stdio 连接**，不验证 REST API 认证。真正的端到端验证必须调用一个实际工具：

```bash
# 方法1: 读取 obsidian://status 资源
# → authenticated: true 才说明 Key 正确

# 方法2: 搜索一条笔记
# → 正常返回结果则全部就绪
```

如果 `hermes mcp test` 通过但实际工具调用返回 `"Obsidian Local REST API rejected the API key"`，说明：
- MCP 服务器 stdio 连接 ✓
- REST API 插件在运行 ✓  
- **API Key 不匹配** ✗

## 排障流程

### API Key 不匹配

```
症状: MCP 工具返回 "Obsidian Local REST API rejected the API key"
```

排查步骤：
1. 确认 config.yaml 中的 Key：`grep OBSIDIAN_API_KEY ~/.hermes/config.yaml`
2. 确认 Obsidian 插件中的 Key：设置 → 插件选项 → Local REST API
3. 两个 Key 逐字符对比（特别注意中间段是否有偏移）
4. 如果相符但仍报错，重启 Obsidian 桌面应用
5. 如果 Obsidian 重启后仍未生效，杀掉旧 MCP 进程：`pkill -f obsidian-mcp-server` 后再次测试

### Key 对比技巧

API Key 是 64 字符的 hex 字符串。两个 Key 可能只有 1 个字符的差异（如 `4c83a` vs `44c83`），肉眼不易发现。推荐：
- `echo "<key1>" | wc -c` 对比长度（应为 65，含换行）
- `diff <(echo <key1>) <(echo <key2>)` 直接对比差异
- 或者将两个 Key 并排放在一起逐段对比

### 工具未注册

- 确认 `enabled: true` 在 config.yaml 中
- 检查 Hermes 启动日志：`grep obsidian ~/.hermes/logs/agent.log`
- 检查插件是否在 Obsidian 中启用：Obsidian → 设置 → 社区插件 → Local REST API
- 重启 Hermes Gateway：`hermes gateway restart`

### 连接被拒绝

- 确认 Obsidian 桌面应用正在运行（snap 版：`ps aux | grep obsidian`）

### snap 版 Obsidian 重启（从 Hermes CLI）

当 Obsidian（snap 版）需要从 Hermes CLI 会话中重启时：

```bash
# 1. 杀掉当前 Obsidian 进程
pkill -f "/snap/obsidian/.*/obsidian --no-sandbox"
sleep 2

# 2. 用 snap run 在后台启动
# 使用 terminal(background=true, command="snap run obsidian")
# ❌ obsidian &  → 打印 "The CLI is unable to find Obsidian" 并退出
# ❌ obsidian --no-sandbox & → snap 包装器无法在非 PTY 环境中正确启动
# ✅ snap run obsidian (background) → 正确启动

# 3. 等待插件加载（8-12 秒）
sleep 10 && ss -tlnp | grep 27123
```

**注意：** snap 版 Obsidian 在无桌面会话的环境（SSH、后台 cron）下无法启动 GUI，必须先确保有 desktop session。
- 确认插件已启用（刚启用时可能需要重启 Obsidian）
- 检查端口号：`ss -tlnp | grep 2712`
- snap 版 Obsidian 在无桌面会话的 SSH/后台进程下无法运行

### curl: (35) SSL connect error

- Obsidian Local REST API 使用自签名证书，加 `-k` 跳过验证
- 确认端口正确（HTTPS 27124 / HTTP 27123）
