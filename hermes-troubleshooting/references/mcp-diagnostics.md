# MCP 服务器诊断检查清单

## 1. 配置检查 — 确认 MCP server 定义

```bash
grep -B1 -A5 'mcp_servers' ~/.hermes/config.yaml | head -80
```

预期：每个 server 显示为 YAML 对象（command/args/connect_timeout 等字段）

## 2. 类型检查 — 检测 JSON 字符串污染

```bash
python3 << 'PYEOF'
import yaml, pathlib
p = pathlib.Path.home() / ".hermes/config.yaml"
cfg = yaml.safe_load(p.read_text())
for key in ["mcp_servers", "mcp", "servers"]:
    v = cfg.get(key)
    if isinstance(v, dict):
        print(f"\n{key}:")
        for name, conf in v.items():
            print(f"  {name}: {type(conf).__name__}")
PYEOF
```

预期：所有 server 显示 `dict`。显示 `str` = JSON 字符串污染（见 hermes-mcp-string-config-fix 技能）

## 3. 启动注册检查 — 确认 MCP 工具已注册

```bash
grep -n 'MCP.*registered.*from\|MCP: registered.*from' ~/.hermes/logs/agent.log | tail -5
```

预期输出示例：
```
2026-06-12 14:38:01,175 INFO tools.mcp_tool: MCP: registered 87 tool(s) from 7 server(s)
```

如果无注册记录：Gateway 可能尚未完成 MCP 初始化，或 MCP 配置加载失败。

## 4. 启动错误检查 — 检查 stderr 日志

```bash
# 查看所有 MCP 启动尝试
grep 'starting MCP server' ~/.hermes/logs/mcp-stderr.log

# 查看 JD 服务器等特定 server 的启动详情
grep -A10 'starting MCP server.*jd' ~/.hermes/logs/mcp-stderr.log

# 查找 mcp-stderr 中的错误/异常
grep -i 'error\|traceback\|exception\|fail' ~/.hermes/logs/mcp-stderr.log | tail -10
```

常见问题：
- 某个 server 启动两次但未注册 → 可能初始化时静默崩溃
- 无任何启动记录 → Gateway 未正确加载 mcp_servers 配置

## 5. 工具注册详情 — 查看单个 server 的工具数

```bash
grep 'MCP server' ~/.hermes/logs/agent.log | grep -o "MCP server '[^']*' (stdio): registered [0-9]* tool(s)" | sort | uniq
```

预期输出：
```
MCP server 'csdn' (stdio): registered 6 tool(s)
MCP server 'db-query' (stdio): registered 9 tool(s)
MCP server 'github' (stdio): registered 26 tool(s)
MCP server 'taobao' (stdio): registered 2 tool(s)
MCP server 'wikipedia' (stdio): registered 26 tool(s)
MCP server 'xiaohongshu' (stdio): registered 13 tool(s)
MCP server 'zhihu' (stdio): registered 5 tool(s)
```

## 6. Server 二进制检查 — 确认可执行文件存在

```bash
for s in ~/.hermes/skills/*/mcp_servers/*/*.py ~/.hermes/*mcp/server.py; do
  [ -f "$s" ] && echo "OK $s" || echo "MISSING $s"
done 2>/dev/null

# 检查 wrapper 脚本
ls -la ~/bin/github-mcp-wrapper.sh 2>/dev/null && echo "github wrapper OK" || echo "github wrapper MISSING"
```

## 6.5 npm/npx 二进制检查 — MCP 服务器卡在 "connecting" 状态

当 `hermes mcp list` 显示某个服务器 **Status 正常（✓ enabled）但实际连接不上**，或者一直卡在 "connecting" 状态时，该服务器可能依赖 npm 全局包（如 filesystem / obsidian MCP 使用 `mcp-server-filesystem` / `obsidian-mcp-server`）。

检查二进制是否存在：

```bash
# 查看 config.yaml 中该服务器的 command 路径
grep -A3 'filesystem:\|obsidian:' ~/.hermes/config.yaml

# 直接检查命令是否存在
ls -la /home/andymao/.npm-global/bin/mcp-server-filesystem 2>/dev/null
ls -la /home/andymao/.npm-global/bin/obsidian-mcp-server 2>/dev/null

# 或用 which 搜索 PATH
which mcp-server-filesystem 2>/dev/null
which obsidian-mcp-server 2>/dev/null
```

**二进制不存在 → 诊断符号链接链：**

```bash
# 检查 npm prefix 和 .npm-global 目录状态
npm config get prefix 2>/dev/null
file "$(npm config get prefix)" 2>/dev/null
ls "$(npm config get prefix)/bin/" 2>/dev/null

# 如果报 "not a directory" 或 "broken symbolic link"：
readlink -f "$(npm config get prefix)" 2>/dev/null || echo "BROKEN SYMLINK"

# 同样检查 .npm 缓存目录
file ~/.npm 2>/dev/null
```

**常见根因链：**
1. `.npm-global` 或 `.npm` 是符号链接 → 指向 `/mnt/backup/` 等备份盘路径
2. 备份盘未挂载 → 符号链接断裂 → npm 无法读写
3. npm 全局包从未安装或安装到断裂路径 → 二进制文件不存在
4. MCP 服务器无法启动 → 一直卡在 "connecting"

**修复（备份盘未挂载时的临时方案）：**

```bash
# 1. 删除断裂符号链接，创建本地目录
rm /home/andymao/.npm-global 2>/dev/null
rm /home/andymao/.npm 2>/dev/null
mkdir -p /home/andymao/.npm-global /home/andymao/.npm

# 2. 配置 npm prefix
npm config set prefix /home/andymao/.npm-global

# 3. 重新安装缺失的 MCP 包
npm install -g @modelcontextprotocol/server-filesystem obsidian-mcp-server

# 4. 验证
hermes mcp list
```

如果备份盘之后重新挂载，可以恢复到符号链接方式。但本地目录方式更稳定，不依赖备份盘状态。

## 7. CLI 工具检查

```bash
hermes mcp list
```

如果此命令崩溃（TypeError: string indices），参见 `hermes-mcp-string-config-fix` 技能。
注意：即使 CLI 报错，agent 运行时可能仍能正常使用 MCP 工具。

## 8. 最近错误日志

```bash
grep -i 'mcp' ~/.hermes/logs/errors.log | tail -10
```

## 9. 综合诊断脚本

```bash
echo "=== MCP Servers in config ==="
python3 -c "
import yaml, pathlib
cfg = yaml.safe_load(pathlib.Path.home().joinpath('.hermes/config.yaml').read_text())
for key in ['mcp_servers', 'mcp', 'servers']:
    v = cfg.get(key, {})
    if isinstance(v, dict):
        for n, c in v.items():
            t = type(c).__name__
            print(f'  {n}: {t}')
"
echo ""
echo "=== Registration status ==="
grep 'MCP: registered' ~/.hermes/logs/agent.log 2>/dev/null | tail -1
echo ""
echo "=== mcp-stderr recent ==="
tail -5 ~/.hermes/logs/mcp-stderr.log 2>/dev/null
echo ""
echo "=== Errors ==="
grep -i 'mcp' ~/.hermes/logs/errors.log 2>/dev/null | tail -5
```
