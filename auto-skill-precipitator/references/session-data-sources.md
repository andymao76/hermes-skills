# Session Data Source Patterns

Skill-auto-precipitator 会话数据源已知格式（本机 rhino01 验证）：

## 1. session-transcript.jsonl

位置: `~/.hermes/open-second-brain/session-transcript.jsonl`
格式: JSONL, 每行一条用户消息
字段:
- `session_id`: 会话ID (如 20260608_214805_f4aa36)
- `user`: 用户输入文本
- `assistant`: Agent 回复文本（或者为 assistant 元数据字符串）

注意: 同一个 session_id 可能有多条消息，代表同一会话的多轮交互。

## 2. agent.log

位置: `~/.hermes/logs/agent.log`
格式: 纯文本日志
包含 INFO [TOOL_CALL], INFO [TOOL_RESULT] 等标记
可通过 grep "terminal\|read_file\|write_file\|skill_manage" 提取工具使用模式

## 3. 知识库 Worklog

位置: `~/knowledge/worklog/`
格式: Markdown 文件
按日期命名，内容为任务摘要

## 4. 计数口径差异（本机验证）

| 口径 | 命令 | 数量(2026-06-23) |
|------|------|:---------------:|
| 全量SKILL.md | `find -name "SKILL.md"` | 474 |
| 顶层活跃 | `find -maxdepth 2` | 65 |
| 分类目录数 | `ls -d skills/*/` | 97 |
| MCP Server | `config.yaml mcp_servers` | 8 |
| Public symlink | `find public -type l` | 31 |

## 5. 管道计时

- 扫描+分析 5 条会话: < 1s
- 草案写入: < 0.1s
- cron 调用: no-agent 模式, 0 token 消耗
