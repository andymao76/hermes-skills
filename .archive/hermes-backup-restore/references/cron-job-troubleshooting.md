# Hermes Cron 定时任务故障排查

排查 Hermes Agent 内部定时任务失败问题的工作流。

## 日志定位

cron 任务不在 gateway.log 里，需查看以下来源：

| 日志源 | 路径 / 命令 | 用途 |
|--------|------------|------|
| 调度器日志 | `~/.hermes/logs/agent.log` | 任务生命周期、API 调用、错误详情 |
| 会话日志 | `~/.hermes/logs/agent.log` 中按 session_id 搜索 | 单个任务执行过程 |
| 错误汇总 | `~/.hermes/logs/errors.log` | 全局错误事件汇总 |

## 排查步骤

### 1. 确认任务状态

```bash
# 查看所有 cron 任务状态
hermes cron list
```

关注 `last_status` 和 `last_delivery_error` 字段。

### 2. 在 agent.log 中查找任务执行记录

每个 cron 任务运行时有唯一的 session ID（格式：`cron_<job_id>_<timestamp>`）：

```bash
grep "<job_id>" ~/.hermes/logs/agent.log | head -5
```

### 3. 提取完整错误上下文

```bash
# 按 session 标记查找
grep "cron_<job_id>_" ~/.hermes/logs/agent.log | grep -E "ERROR|WARNING|error|failed"
```

### 4. 手动重跑验证

```bash
# 通过 cronjob 工具手动触发
# cronjob(action='run', job_id='<job_id>')
# 等 60 秒后重新查看 last_status
```

## 常见错误模式

### DeepSeek "Content Exists Risk" (HTTP 400)

```
Error code: 400 - {'error': {'message': 'Content Exists Risk', ...}}
```

**原因**：DeepSeek 的内容安全过滤拦截了任务输出。当新闻日报、调研报告等包含 DeepSeek 认为敏感的关键词时，会返回 HTTP 400 而非正常响应。DeepSeek 的内容过滤越来越严，这是服务端行为，无法通过修改 prompt 绕过。

**解决方案**：
1. 切换模型：将 cron 任务的 provider 改为不受内容审查限制的模型（如 SiliconFlow）
2. 在调度器配置中无法动态改 provider 的，修改 `config.yaml` 切换默认模型再重跑

### 超时 (timeout)

```
RuntimeError: Tool call timed out after 180s
```

**原因**：web_search 或 web_extract 等网络工具耗时过长。在受限网络环境（GFW）下尤为常见。

**解决方法**：缩短搜索范围、减少并行搜索数、或延长任务的 `timeout`。

### 交付失败

```
last_delivery_error: "Platform 'weixin' is not connected"
```

**原因**：
- 目标平台网关离线
- WeChat 会话过期（`errcode=-14`）
- 目标平台配置变更

**解决方法**：检查 `hermes gateway status`，确认目标平台在线。

### API Key 耗尽

```
payment / credit error
Auxiliary: marking <provider> unhealthy for 60s (payment / credit error)
```

**原因**：辅助任务的 provider API 配额耗尽。

**解决方法**：`hermes auth list <provider>` 检查剩余配额，补充 API key。

## DeepSeek 内容过滤的特殊说明

DeepSeek 的内容安全过滤与中国国内的大模型合规要求一致。以下类型的 cron 任务容易触发：

- **新闻聚合**（每日头条新闻、热点追踪）—— 概率最高
- **技术调研涉及敏感领域**（安全研究、内容审核技术）
- **跨平台内容搬运**（从墙外源抓取内容推送）

**规避策略**：
- 新闻类任务永远不要用 DeepSeek，改走 SiliconFlow 的 Qwen 或其他海外模型
- 如果必须用 DeepSeek，在 prompt 中明确要求输出"中立的、事实性的技术内容"，避免输出任何可能触发安全过滤的表述
