# MCP Server 配置审计与清理

完整的 MCP Server 审计工作流：列出 → 检查冗余/明文Token → 清理 → 验证。

## 1. 列出所有已配置的 MCP 服务

### 从 config.yaml 读取配置

```bash
# 提取 mcp_servers 段
grep -A5 '^mcp_servers:' ~/.hermes/config.yaml | head -80

# 或用 python 解析完整结构
python3 -c "
import yaml
c = yaml.safe_load(open('/home/andymao/.hermes/config.yaml'))
servers = c.get('mcp_servers', {})
for name, cfg in servers.items():
    cmd = cfg.get('command', cfg.get('url', '(url)'))
    to = cfg.get('timeout', '?')
    en = cfg.get('env', {})
    has_token = any('token' in k.lower() or 'key' in k.lower() for k,v in en.items() if v and len(v) > 20)
    print(f'{name:20s} | {str(cmd)[:50]:50s} | timeout={to}s | {\"⚠️HAS_TOKEN\" if has_token else \"✅\"}')
"
```

### 检查独立运行的 MCP 进程

```bash
# 正在运行的 MCP 相关进程
ps aux | grep -iE 'mcp|stdio.*server' | grep -v grep

# MCP 端口监听
ss -tlnp 2>/dev/null | grep -E '(18060|300[0-9])'
```

常见 MCP 端口：
- `18060` — 小红书 MCP 二进制独立服务
- `3000` — open-second-brain (Obsidian MCP 插件)

## 2. 检查冗余/重复的 MCP 服务

常见的重复模式：

| 问题 | 症状 | 处理 |
|------|------|------|
| 两个 GitHub MCP | 同时有 `github` (npm) + `github-gov1` (Go binary) | 仅保留一个，优先选 env-var 版本 |
| 同一个服务的 stdio + 独立二进制 | 如 xiaohongshu 同时有 bridge 脚本 + 独立二进制 | 通常这是正常的设计（bridge 是代理层） |

## 3. 检查明文 Token 风险

在 config.yaml 的 `mcp_servers.<name>.env` 段中，如果有 `TOKEN`、`KEY` 等敏感字段且值是明文（不是 `${VAR}` 引用环境变量），需要改造：

```bash
# 快速扫描所有 mcp_servers env 中的明文 token
python3 -c "
import yaml
c = yaml.safe_load(open('/home/andymao/.hermes/config.yaml'))
servers = c.get('mcp_servers', {})
for name, cfg in servers.items():
    for k, v in cfg.get('env', {}).items():
        if isinstance(v, str) and len(v) > 20 and not v.startswith('$') and \
           any(t in k.lower() for t in ['token','key','secret','pass','auth']):
            print(f'⚠️  {name}/{k} = {v[:12]}... (明文token)')
        elif isinstance(v, str) and len(v) > 20:
            print(f'  {name}/{k} = {v[:12]}... (长字符串，请人工检查)')
"
```

## 4. 改造方案：从明文 Token 改为环境变量

### 方案 A：wrapper 脚本（推荐，通用性强）

创建 wrapper 脚本从环境变量读取 token：

```bash
cat > ~/bin/my-mcp-wrapper.sh << 'EOF'
#!/bin/bash
export MCP_TOKEN="${MY_MCP_TOKEN:-}"   # 从环境变量读取
exec /path/to/mcp-server "$@"
EOF
chmod +x ~/bin/my-mcp-wrapper.sh
```

在 `.bashrc`（或 `.env`）中设置 token：

```bash
export MY_MCP_TOKEN="你的实际token"
```

在 config.yaml 中引用 wrapper：

```yaml
mcp_servers:
  my-service:
    command: /home/andymao/bin/my-mcp-wrapper.sh
    args: [stdio]
    connect_timeout: 15
    timeout: 120
```

### 方案 B：直接引用 env 变量名（适用于支持 ${VAR} 的 MCP 实现）

某些 MCP 实现支持从环境变量读值。直接在 config.yaml 中设 `api_key_env`：

```yaml
mcp_servers:
  my-service:
    command: /path/to/server
    args: []
    api_key_env: MY_SERVICE_TOKEN
    timeout: 120
```

## 5. 验证清理结果

```bash
# 验证旧服务已移除
grep -A2 '^  github:' ~/.hermes/config.yaml   # 应该无输出

# 验证新服务配置正确
grep -A5 '^  github-gov1:' ~/.hermes/config.yaml

# 验证环境变量可用
echo ${GITHUB_PERSONAL_ACCESS_TOKEN:0:10}...

# 验证 wrapper 可执行
ls -la ~/bin/github-mcp-wrapper.sh
```

## 6. MCP 完整检查清单

| # | 检查项 | 命令 |
|---|--------|------|
| 1 | 配置中所有 MCP 服务 | `grep -B1 'command:\|url:' ~/.hermes/config.yaml` |
| 2 | 正在运行的 MCP 进程 | `ps aux \| grep -i mcp \| grep -v grep` |
| 3 | 监听端口 | `ss -tlnp \| grep -E '(18060\|300[0-9]\|9377)'` |
| 4 | 明文 token 扫描 | 见第3节 Python 脚本 |
| 5 | 重复服务 | 人工对比服务名和命令路径 |
| 6 | proxy 配置合理 | 国内 MCP 直连，国外 MCP 走代理 |
| 7 | .bashrc 冗余 env | `grep GITHUB ~/.bashrc`（清理冲突行） |
