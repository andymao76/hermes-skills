# Hermes Maintenance Enterprise v2 — SOP 执行参考

> 配合 `cron-job-ops` 技能使用。描述了 Hermes 会话维护的完整工作流，涵盖上线前检查、分类清理、备份、执行和定时器启用。

## 执行流程

### 1. 上线前检查（Pre-flight）

每次执行前先确认环境健康：

```bash
# Hermes 状态
hermes sessions stats

# 基础环境
python3 --version
hermes --version

# 数据库
ls -lh ~/.hermes/state.db

# 配置目录
ls ~/.config/hermes-maintenance-v2/config.json

# 二进制存在性
ls ~/bin/hermes-maintenance-v2

# systemd 单元
systemctl --user list-unit-files 'hermes-maintenance*'
```

### 2. Doctor 检查

```bash
~/bin/hermes-maintenance-v2 --config ~/.config/hermes-maintenance-v2/config.json doctor
```

期望输出：`doctor_status=OK`，且 sqlite_sessions > 0、cli_sessions > 0。

### 3. Schema 检查

```bash
~/bin/hermes-maintenance-v2 --config ~/.config/hermes-maintenance-v2/config.json schema
```

验证所有必要表（sessions, messages, compression_locks, FTS 表等）结构完整。

### 4. 分类检查

```bash
~/bin/hermes-maintenance-v2 --config ~/.config/hermes-maintenance-v2/config.json classify
```

输出格式：`parsed=N candidates=N protected=N`

- `candidates` = 匹配测试/调试模式的会话（将被清理）
- `protected` = 匹配保护模式的工作会话（不会被触及）

### 5. Dry Run（必须先试）

在正式执行前用 dry-run 模式先跑一次，确认备份正常、无意外删除：

```bash
~/bin/hermes-maintenance-v2 --config ~/.config/hermes-maintenance-v2/config.json run --dry-run
```

检查输出：
- `backup=...` — 备份 JSONL 文件已创建
- `candidates=0` — 无测试会话可删除（系统干净）
- 或 `candidates=N` — 预期会被清理的会话数
- `deleted=0` — dry-run 模式下不会实际删除
- `failed=0` — 无处理失败
- `report=...` — 报告文件已生成

### 6. 检查报告

读取报告，重点检查：

- **Candidates 节** — 确认只含测试/调试会话，不含生产数据
- **Protected 节** — 确认工作会话（A1、Knowledge、Production 相关）全被正确保护

```bash
# 查看 Candidates
awk '/^## Candidates/{flag=1} /^## Protected/{flag=0} flag' <report_path>

# 查看 Protected
awk '/^## Protected/{flag=1} /^## Delete Logs/{flag=0} flag' <report_path>
```

### 7. 正式执行

```bash
~/bin/hermes-maintenance-v2 --config ~/.config/hermes-maintenance-v2/config.json run --execute
```

关键指标：
- `deleted` = 实际删除的会话数
- `failed` = 处理失败的会话数（必须为 0）

### 8. 启用定时任务

```bash
systemctl --user enable hermes-maintenance-v2.timer
systemctl --user start hermes-maintenance-v2.timer
```

验证：

```bash
systemctl --user status hermes-maintenance-v2.timer
systemctl --user list-timers 'hermes-maintenance*'
```

期望状态：`Active: active (waiting)`，下次触发时间正确。

### 9. 验收检查

```bash
# Doctor 确认
~/bin/hermes-maintenance-v2 --config ~/.config/hermes-maintenance-v2/config.json doctor

# Service 状态
systemctl --user status hermes-maintenance-v2.service

# Timer 状态
systemctl --user status hermes-maintenance-v2.timer

# 数据库完整性
sqlite3 ~/.hermes/state.db "SELECT COUNT(*) FROM sessions WHERE archived=0;"
```

## 设计原则

| 原则 | 说明 |
|------|------|
| **先备份，后操作** | 每次 `run --execute` 前自动创建 JSONL 备份到 `~/hermes_backup/` |
| **先分类，后删除** | `classify` 阶段区分 candidates（测试）和 protected（工作） |
| **先 dry-run，后 live** | `run --dry-run` 验证分类结果，确认无误后再 `--execute` |
| **先验证，后调度** | 手动执行确认通过后，再启用 timer 让系统自动运行 |
| **无法回滚时阻止** | 失败数为 0 才能确认进展正常 |

## 输出路径

| 路径 | 内容 |
|------|------|
| `~/hermes_backup/sessions_backup_<timestamp>.jsonl` | 会话备份（JSONL 格式） |
| `~/hermes_reports/hermes_enterprise_v2_maintenance_<timestamp>.md` | Markdown 报告 |
| `~/.config/hermes-maintenance-v2/config.json` | 配置文件 |
| `~/.config/systemd/user/hermes-maintenance-v2.timer` | systemd timer 单元 |
| `~/.config/systemd/user/hermes-maintenance-v2.service` | systemd service 单元 |
