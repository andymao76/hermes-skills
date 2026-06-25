---
name: mcp-security-hardening
description: MCP 服务安全审计与生命周期管理 — 审计、清理、迁移 MCP 服务配置。覆盖明文凭据检测、死服务（HTTP 401）移除、多配置合并、环境变量切换、.bashrc 清理。
---

# MCP 安全审计与生命周期管理

## 触发条件

- 用户要求"列出 MCP 服务"、"检查 MCP 状态"
- 发现 config.yaml 中 `mcp_servers` 下某个服务含明文 Token/API Key
- 用户要求"清理明文 token"、"删除旧 MCP 服务"、"保留某个 MCP"
- MCP 服务返回 401/403 未认证
- 存在重复的 MCP 服务（如新旧两个 GitHub MCP）

## 完整审计工作流

### 步骤 1：列出配置的 MCP 服务

查看 `mcp_servers` 段：

```bash
sed -n '/^mcp_servers:/,/^platform_toolsets:/p' ~/.hermes/config.yaml
```

识别三个维度的问题：
- **明文凭据**: 服务配置内有 `env:` 段且值含显式 `sk-` / `ghp_` 等
- **死服务**: `url:` 类型的 HTTP 服务，未配认证时返回 401
- **重复服务**: 两个同名平台的不同 MCP（如 `github` + `github-gov1`）

### 步骤 2：检查正在运行的 MCP 进程

```bash
# 常驻 MCP 进程
ps aux | grep -iE 'mcp|stdio' | grep -v grep

# HTTP MCP 服务端口
ss -tlnp | grep -E '18060|3000'
```

### 步骤 3：诊断

| 发现 | 判定 | 处理 |
|------|------|------|
| `env:` 段含 `ghp_WS...` 明文 | 安全风险 | 删除或切环境变量 |
| HTTP URL + 401 | 未配 / 未用 | 配置 key 或直接删除 |
| 两套同平台 MCP | 功能重复 | 留环境变量版，删明文版 |
| `.bashrc` 有矛盾行（设又 unset） | 残留 | 清理冗余行 |

### 步骤 4：删除/修改

输出精确 sed 命令给用户执行（禁止直接改 config.yaml）：

```bash
# 删除一个 MCP 服务区块
# 格式: sed -i '/^  SERVICE-NAME:$/,/^  NEXT-SERVICE:/{/^  NEXT-SERVICE:/!d}' ~/.hermes/config.yaml

# 例：删除 composio
sed -i '/^  composio:$/,/^  github-gov1:/{/^  github-gov1:/!d}' ~/.hermes/config.yaml

# 例：删除旧的 github npm MCP
sed -i '/^  github:$/,/^  composio:/{/^  composio:/!d}' ~/.hermes/config.yaml

# 删除 .bashrc 中的冗余行
sed -i '172,173d' ~/.bashrc
```

### 步骤 5：验证

```bash
# 确认 MCP 段干净
sed -n '/^mcp_servers:/,/^platform_toolsets:/p' ~/.hermes/config.yaml

# 确认无明文凭据残留
grep -i 'ghp_\|sk-\|api_key:' ~/.hermes/config.yaml | grep -v '#'

# 确认 .bashrc 干净
grep GITHUB ~/.bashrc
```

### 步骤 6：重新加载

```bash
hermes config reload
```

## 常见场景

### 场景 A：GitHub MCP 双配置 → 合并

```
问题: github (npm + 明文 token) + github-gov1 (Go binary + 环境变量)
处理:
  1. 确认 github-gov1 wrapper 读取 $GITHUB_PERSONAL_ACCESS_TOKEN
  2. 确认环境变量来源（~/.bashrc / ~/.profile / ~/.hermes/.env）
  3. 删除 github 区块
  4. 清理 .bashrc 中矛盾的 export GITHUB_TOKEN + unset 行
  5. 验证仅剩 github-gov1
```

### 场景 B：HTTP 服务返回 401

```
问题: composio → connect.composio.dev/mcp → HTTP 401
判定: 未配置 API Key，从未生效过
处理: 直接删除整个区块
注意: 如果用户确实需要该平台，先配 key 再保留
```

### 场景 C：明文 token 在 config.yaml

```
问题: 某 MCP 的 env: 段写死了 sk-xxx / ghp_xxx
处理:
  1. 将 token 移至 ~/.bashrc: export SERVICE_TOKEN="xxx"
  2. 删除 config.yaml 中该服务的 env: 段
  3. 确保该服务的 command/binary 读取对应环境变量
  4. 或切到已有 wrapper 脚本的方案（如 github-gov1）
```

## 验证清单

```
□ mcp_servers 段无 HTTP 401 服务
□ 所有 token 从环境变量读取，config.yaml 无明文
□ 无重复的同平台 MCP 服务
□ .bashrc / .env 无矛盾的 export + unset
□ hermes config reload 已执行
□ 运行中 MCP 进程正常
```

---

## 关键 Pitfall：Hermes MCP 的 _build_safe_env() 环境变量过滤

### 问题现象

stdio 型 MCP 服务（wrapper 脚本→ Go/Python 二进制）启动后立即断开，`hermes mcp test` 报：
```
✗ Connection failed: Connection closed
```
但手动通过 pipe 测试二进制正常工作。

### 根本原因

Hermes 的 MCP 客户端在启动 stdio 子进程时调用 `_build_safe_env()`，它只传递**白名单**环境变量：

```python
_SAFE_ENV_KEYS = frozenset({
    "PATH", "HOME", "USER", "LANG", "LC_ALL", "TERM", "SHELL", "TMPDIR",
})
```

`GITHUB_PERSONAL_ACCESS_TOKEN`、`GITHUB_TOKEN` 以及任何其他非白名单 env var **均被过滤**，不会传递给 MCP 子进程。即使当前 shell 的 `.bashrc` 中有 export，子进程也收不到。

> 代码位置：`~/.hermes/hermes-agent/tools/mcp_tool.py` 中 `_build_safe_env()` 和 `_SAFE_ENV_KEYS`。

### 解决方案：文件传递 Token，绕过 env 过滤

#### 方案 A（推荐）：wrapper 脚本读取 token 文件

```bash
# 1. 将 token 写入仅自己可读的文件
echo "export SERVICE_TOKEN=\"ghp_xxx\"" > ~/.mcp-env/servicename
chmod 600 ~/.mcp-env/servicename

# 2. wrapper 脚本 source 该文件
cat > ~/bin/mycustom-wrapper.sh << 'WRAPPER'
#!/bin/bash
if [ -f ~/.mcp-env/servicename ]; then
  source ~/.mcp-env/servicename
fi
export TOKEN_VAR="${TOKEN_VAR:-$FALLBACK_VAR}"
exec /path/to/binary "$@"
WRAPPER
chmod +x ~/bin/mycustom-wrapper.sh
```

这样 token 值始终在文件系统中，不进 config.yaml，也不依赖 env 白名单传递。

#### 方案 B：config.yaml 的 env: 段（直接传递）

```yaml
  my-service:
    command: "/path/to/binary"
    args: ["stdio"]
    connect_timeout: 15
    timeout: 120
    env:
      SERVICE_TOKEN: "ghp_xxx"    # ⚠️ token 明文在 config.yaml 中
```

注意：`env:` 的值会直接覆盖到子进程环境，**不受** `_build_safe_env()` 过滤（因为 `user_env` 在过滤之后追加）。但 token 明文存于 config.yaml 有安全风险。

### 诊断流程

```bash
# 1. 确认二进制本身能工作（手动 pipe 测试）
printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n' | timeout 10 /path/to/binary stdio

# 2. 用 hermes mcp test 确认失败
hermes mcp test 服务名

# 3. 检查是否环境变量问题——创建一个调试 wrapper
cat > /tmp/debug-wrapper.sh << 'SCRIPT'
#!/bin/bash
env | sort > /tmp/mcp-env-dump.txt
exec /path/to/binary "$@"
SCRIPT
# 临时改 config.yaml 指向调试 wrapper，运行 hermes mcp test
# 然后检查 /tmp/mcp-env-dump.txt 中是否有需要的 token 变量

# 对比：手动 pipe 测试时 env 中有 token
GITHUB_PERSONAL_ACCESS_TOKEN=xxx printf '...' | /path/to/binary stdio
```
