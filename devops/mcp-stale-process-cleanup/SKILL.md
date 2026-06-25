---
name: mcp-stale-process-cleanup
description: "Hermes MCP 进程生命周期管理 — 全量重启（kill+test 恢复）与清理陈旧进程（保留最新）。释放内存，防止端口冲突和凭据过期。"
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [MCP, Cleanup, DevOps, Processes]
---

# MCP 进程生命周期管理

## 何时使用

当 MCP 服务器出现以下情况时执行：

**需要全量重启：**
- MCP 凭据过期 / Token 失效
- 长时间运行后 MCP 工具报错或不稳定
- 传输层切换（stdio ↔ HTTP）后残留旧进程
- 当前会话 MCP 工具全部报 `ClosedResourceError`

**需要清理陈旧进程：**
- 每个 MCP 服务器有 2+ 个进程实例（陈旧进程积压）
- 怀疑端口冲突或凭据过期（旧进程持有旧 token）
- Hermes 重启后遗留的旧进程未自动终止
- 日志显示 "Connection refused" 但 `hermes mcp test` 失败

## 快速执行

直接运行以下命令清理所有陈旧 MCP 实例（保留最新一个）：

```bash
for proc in 'csdn/server.py' 'db_query_server.py' 'taobao_mcp/server.py' 'wikipedia-mcp' 'zh_mcp_server/run.py' 'github-mcp-server' 'jd_mcp/server.py' 'xiaohongshu-mcp'; do
    pids=$(ps aux | grep "$proc" | grep -v grep | awk '{print $2}' | sort -n)
    count=$(echo "$pids" | wc -l)
    if [ "$count" -gt 1 ]; then
        echo "$pids" | head -n -1 | xargs -r kill 2>/dev/null
        echo "清理 $proc: 杀掉 $((count-1)) 个陈旧进程"
    fi
done
```

## 验证

清理后验证每个服务器是否只剩 1 个进程：

```bash
for name in csdn db-query github-gov1 jd taobao wikipedia xiaohongshu zhihu; do
    case "$name" in
        csdn)       pn="csdn/server.py" ;;
        db-query)   pn="db_query_server.py" ;;
        github-gov1) pn="github-mcp-server" ;;
        jd)         pn="jd_mcp/server.py" ;;
        taobao)     pn="taobao_mcp/server.py" ;;
        wikipedia)  pn="wikipedia-mcp" ;;
        xiaohongshu) pn="xiaohongshu-mcp" ;;
        zhihu)      pn="zh_mcp_server" ;;
    esac
    c=$(ps aux | grep -v grep | grep -c "$pn")
    echo "${c:+✓} $name: ${c}个进程"
done
echo "---"
echo "总进程数: $(ps aux | grep -E 'server\.py|mcp-server|wikipedia-mcp|zh_mcp|db_query|xiaohongshu' | grep -v grep | wc -l)"
```

## 全量重启 MCP 服务（vs 清理陈旧进程）

当需要**故意重启所有 MCP 服务**（如凭据过期、长时间运行后不稳定、传输层切换后残留）时，与清理陈旧进程不同，需要完整的 kill + 恢复流程。

### 何时用"清理" vs "全量重启"

| 场景 | 方法 | 说明 |
|------|------|------|
| Hermes 多次重启后遗留旧进程 | 清理陈旧进程 | 保留最新实例，kill 旧的 |
| MCP 凭据过期 / 长时间未重启 / 传输层切换 | **全量重启** | 杀死所有，重新连接 |
| 当前会话 MCP 工具全部报 ClosedResourceError | 全量重启 | 旧连接已断，需重建 |

### 全量重启工作流

```bash
# 1. 终止所有 MCP 服务器进程（排除 xiaohongshu 独立进程和 open-second-brain）
for p in $(ps aux | grep -E "(mcp-server|mcp-servers|github-mcp-server|wikipedia-mcp|zh_mcp_server|obsidian-mcp-server)" | grep -v grep | awk '{print $2}'); do
  kill $p 2>/dev/null && echo "Killed PID $p"
done

# 2. 逐个触发重连（hermes mcp test 会启动新的子进程）
for s in csdn db-query github-gov1 jd taobao wikipedia zhihu filesystem obsidian time chart; do
  hermes mcp test "$s" 2>&1 | head -3
done
```

验证：

```bash
hermes mcp list
hermes mcp test <任意服务名>  # 确认 Connected
```

### 当前会话注意事项

- 杀死所有 MCP 进程后，**当前会话**已有的 MCP 通道立即失效（报 `ClosedResourceError`）
- `hermes mcp test` 会启动新进程并在 CLI 层面验证连通性，但**当前会话的 MCP 通道需要下一次工具调用时自动重建**
- 如果下轮工具调用仍报 `ClosedResourceError`，结束当前会话重新开始即可
- TUI 模式下 dashboard 不会自动重启 MCP 子进程，必须通过 `hermes mcp test` 或实际工具调用触发

## 清理陈旧进程（保留最新实例）

与全量重启不同，此模式只杀重复的旧实例，保留每个服务器最新的进程。

```bash
for proc in 'csdn/server.py' 'db_query_server.py' 'taobao_mcp/server.py' 'wikipedia-mcp' 'zh_mcp_server/run.py' 'github-mcp-server' 'jd_mcp/server.py' 'xiaohongshu-mcp'; do
    pids=$(ps aux | grep "$proc" | grep -v grep | awk '{print $2}' | sort -n)
    count=$(echo "$pids" | wc -l)
    if [ "$count" -gt 1 ]; then
        echo "$pids" | head -n -1 | xargs -r kill 2>/dev/null
        echo "清理 $proc: 杀掉 $((count-1)) 个陈旧进程"
    fi
done
```

## 注意事项

- Hermes Gateway 在启动、/reload-mcp、重启时会自动拉起新的 MCP 进程，旧进程不自动终止
- 清理后建议运行 `hermes mcp list` 确认所有服务状态正常
- 如果清理后某个服务变为 0 进程，可能是 grep 模式不匹配，检查实际进程名后调整 pattern
- 🚫 **清理陈旧进程时** — 只 kill 旧实例（保留最新一个），否则 MCP 工具在当前会话中会立即失效
- ✅ **全量重启时** — kill 所有进程是预期行为，必须配合 `hermes mcp test` 恢复连接
- kill 后 MCP 工具在当前会话中不会自动恢复连接，需要下一轮工具调用或新会话触发重建
