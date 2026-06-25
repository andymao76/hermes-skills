---
name: hermes-troubleshooting
description: Hermes Agent 排障 — Gateway 诊断、Provider 通信、TUI 命令、cron 恢复
category: devops
---

# Hermes Troubleshooting

Hermes Agent 全栈排障 — 涵盖 MCP 服务器诊断、Gateway 状态检查、Provider 通信、定时任务恢复、文件写入故障排查。

## 触发条件

- MCP 工具不可用 / `hermes mcp list` 崩溃
- `mcp_` 前缀的工具调用报错或返回空
- 平台消息推送失败（Telegram/Discord/微信）
- Provider 调用返回认证错误、4xx/5xx
- Cron 任务执行失败或未触发
- 文件写入被 File-mutation verifier 拦截
- **跨实例审计与同步** — 需要审计远程服务器上的 Hermes 配置、对比技能差异、同步知识库或配置
- **多实例运维** — 多台机器上的 Hermes 实例需要统一管理或排查差异
- **MCP 生态差异** — 两边 MCP 服务器列表不同（平台类 vs 基础工具类），需要分析是否统一

### MCP 诊断（最常用）

当 MCP 工具异常、或 `hermes mcp list` 崩溃时，运行 9 步诊断流程：

1. **配置检查** → `grep -B1 -A5 'mcp_servers' ~/.hermes/config.yaml`
2. **类型检查** → 确认所有 server 为 `dict`（非 `str`）
3. **注册检查** → `grep 'MCP: registered.*from' ~/.hermes/logs/agent.log`
4. **stderr 检查** → `grep 'starting MCP server' ~/.hermes/logs/mcp-stderr.log`
5. **工具数检查** → 确认每个 server 的正确工具数量
6. **二进制检查** → 确认 server 脚本/wrapper 存在
7. **CLI 检查** → `hermes mcp list`
8. **错误日志** → `~/.hermes/logs/errors.log`
9. **综合诊断脚本** — 见上方

> **MCP 服务器卡在 "connecting" 状态？** → 优先检查步骤 **6.5（npm/npx 二进制检查）**，常见原因是 npm 全局包缺失（.npm-global 符号链接断裂导致备份盘未挂载时路径不可达）。详见 `references/mcp-diagnostics.md#65-npmnpx-二进制检查--mcp-服务器卡在-connecting-状态`。

**跨实例审计与同步：** 多台机器 Hermes 间的完整审计（知识库/技能/配置/MCP/Provider/Open WebUI）及同步流程见 `references/cross-instance-skill-sync.md`，涵盖 SSH tar 管道 / rsync 两种技能同步方式、知识库 rsync、配置 diff 对比（含13模块分析模板）、MCP 生态统一（含依赖安装/路径确认/config编辑/生效流程）、审计速查表。

```bash
echo "=== Config types ==="
python3 -c "
import yaml, pathlib
cfg = yaml.safe_load(pathlib.Path.home().joinpath('.hermes/config.yaml').read_text())
for key in ['mcp_servers', 'mcp', 'servers']:
    v = cfg.get(key, {})
    if isinstance(v, dict):
        for n, c in v.items():
            print(f'  {n}: {type(c).__name__}')
"
echo "=== Registered ==="
grep 'MCP: registered' ~/.hermes/logs/agent.log 2>/dev/null | tail -1
echo "=== stderr ==="
tail -3 ~/.hermes/logs/mcp-stderr.log 2>/dev/null
echo "=== Errors ==="
grep -i 'mcp' ~/.hermes/logs/errors.log 2>/dev/null | tail -3
```

完整 9 步检查清单及每个步骤的预期输出：`references/mcp-diagnostics.md`

### MCP 配置字符串污染（JSON 字符串）

`hermes mcp list` 崩溃报 `TypeError: string indices` → 某个 MCP server 配置被写成了 JSON 字符串而非 YAML 对象。

```bash
python3 << 'PYEOF'
import yaml, pathlib
p = pathlib.Path.home() / ".hermes/config.yaml"
cfg = yaml.safe_load(p.read_text())
for key in ["mcp_servers", "mcp", "servers"]:
    v = cfg.get(key)
    if isinstance(v, dict):
        for name, conf in v.items():
            if isinstance(conf, str):
                print(f"BAD: {name} is {type(conf).__name__}")
PYEOF
```

修复脚本示例：
```bash
python3 << 'PYEOF'
import yaml, pathlib
p = pathlib.Path.home() / ".hermes/config.yaml"
cfg = yaml.safe_load(p.read_text())
# 按需替换 server_name 和配置
cfg["mcp_servers"]["github-gov1"] = {
    "command": "/home/andymao/bin/github-mcp-wrapper.sh",
    "args": ["stdio"],
    "connect_timeout": 15,
    "timeout": 120,
}
p.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False))
print("fixed")
PYEOF
```

验证：再次运行 `hermes mcp list` 确认正常。

## `hermes update` 故障诊断

`hermes update` 通过 `git fetch origin <branch>` 从远程拉取更新。常见失败模式及诊断步骤：

### 1. TLS 握手失败 (`gnutls_handshake() failed: The TLS connection was non-properly terminated`)

这种错误通常是**暂时的网络抖动**，重试即可恢复。

诊断步骤：

```bash
# 1. 找到 Hermes 安装目录
which hermes                   # symlink 指向 ~/.hermes/hermes-agent/venv/bin/hermes
ls -la ~/.hermes/hermes-agent/.git   # git 仓库在此

# 2. 检查代理配置
env | grep -i proxy
# 期望: HTTP_PROXY=http://127.0.0.1:7897, HTTPS_PROXY=http://127.0.0.1:7897
# ALL_PROXY=socks5://127.0.0.1:7897

# 3. 从 git 层面测试连通性
cd ~/.hermes/hermes-agent
git remote -v                  # 检查远程源: origin(GitHub), mirror(国内镜像)
git fetch origin main          # 重试 fetch
git rev-list HEAD..origin/main --count   # 0 = 已最新

# 4. 从 curl 层面测试网络
curl -s -o /dev/null -w "%{http_code}" https://github.com --max-time 10
```

注意点：
- Hermes 可能有多个 remote——`origin` (GitHub) 和 `mirror` (cnb.cool 国内镜像)
- `hermes update` 命令实现在 `~/.hermes/hermes-agent/hermes_cli/main.py` 的 `_cmd_update_impl()` 中
- 它固定使用 `origin` remote，不会自动 fallback 到 mirror
- 如果 `fetch` 失败但网站能访问，可能是代理时延导致 git 底层 gnutls 超时
- **最佳处理：等待几秒重试**，这种 TLS 间歇性断开通常不是永久性故障

### 2. 其他 Git 失败

| 错误 | 原因 | 处理 |
|------|------|------|
| `fatal: 不是 git 仓库` | 在当前目录以外运行了 update | 进 `~/.hermes/hermes-agent/` 重试 |
| `Could not resolve host` | DNS 或网络断开 | 检查代理/外网连通性 |
| `Authentication failed` | GitHub token/SSH 失效 | 检查 git credentials |
| `fatal: 无法访问... 连接超时` | 网络不通 (30s+ 无响应) | 检查代理/翻墙状态 |

### 3. 确认已是最新

```bash
cd ~/.hermes/hermes-agent
git log --oneline -1           # 当前 HEAD
git fetch origin main          # 拉取最新
git rev-list HEAD..origin/main --count   # 0 = 已最新
```

## Gateway 诊断

```bash
# 检查 Gateway 进程
ps aux | grep -E 'hermes.*gateway|gateway run' | grep -v grep

# 检查 Gateway 运行时长
ps -p <PID> -o pid,start,etime,args --no-headers

# 查看 Gateway 日志
tail -50 ~/.hermes/logs/gateway.log

# 检查平台连接
grep -E 'Connected|Reconnect|ERROR.*platform' ~/.hermes/logs/gateway.log | tail -10
```

## Provider / 模型通信诊断

参见 `hermes-provider-debugging` 技能。

## Cron 任务恢复

参见 `cron-job-ops` 技能。

## 文件写入拦截恢复

参见 `file-mutation-verifier-protocol` 技能。

## 记忆架构诊断

当 `memory` 工具返回 `"No entry matched"` 但你认为条目确实存在时——该条目可能不在 `memory_store.db` 的事实表中，而在 `~/.hermes/memories/` 的 flat markdown 文件中。这两个存储系统不互通。

1. 查数据库：`sqlite3 ~/.hermes/memory_store.db "SELECT fact_id, content FROM facts WHERE content LIKE '%关键词%';"`
2. 查 flat 文件：`grep -n "关键词" ~/.hermes/memories/MEMORY.md ~/.hermes/memories/USER.md`
3. 如果在 flat 文件中，用 `sed -i` 或 `patch` 直接编辑文件

详见 `references/memory-architecture.md`。

## 快速状态摘要

```bash
echo "=== Session ===" && hermes model 2>/dev/null
echo "=== Gateway ===" && ps aux | grep 'gateway run' | grep -v grep | awk '{print "PID "$2" running "$(NF-2)" "$(NF-1)" "$NF}'
echo "=== Cron ===" && hermes cron list 2>/dev/null | grep -E 'Next run|Last run'
echo "=== Disk ===" && df -h / | tail -1 | awk '{print $5 " used of " $2}'
echo "=== Memory ===" && free -h | grep Mem | awk '{print $3 "/" $2}'
echo "=== Load ===" && uptime | grep -o 'load average:.*'
```
