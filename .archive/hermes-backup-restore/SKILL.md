---
name: hermes-backup-restore
description: 完整的 Hermes Agent 备份/恢复/巡检体系，支持增量备份、自动 cron、系统 journal 日志、灾难恢复
tags: [backup, restore, disaster-recovery, cron, exfat, systemd-journal]
---

# Hermes Agent 备份恢复

为 Hermes Agent 建立完整的灾备体系：全量备份 + SHA256 增量备份 + 自动 cron + 巡检 + 一键恢复。

## 触发条件

- 用户要求备份 Hermes 配置或数据
- 用户提到「崩溃恢复」「重装恢复」「灾备」
- 用户询问如何保护 Hermes Agent 配置不丢失

## 备份体系架构

```
/mnt/backup/hermes-backup/
├── README.md                      ← 操作手册（备份/巡检/恢复/故障处理）
├── LATEST_BACKUP                  ← 最新备份名（供脚本读取）
├── backup-hermes.py               ← 完整备份脚本
├── backup-hermes-incremental.py   ← 增量备份脚本（SHA256 对比）
├── inspect-hermes.py              ← 巡检脚本
├── restore-hermes.py              ← 恢复脚本
├── logs/                          ← 日志目录
│   └── YYYYMMDD_HHMMSS-backup.log
└── backups/                       ← 备份存储
    ├── YYYYMMDD_HHMMSS-full/      ← 完整备份
    └── YYYYMMDD_HHMMSS-incremental/ ← 增量备份
```

## 备份内容清单（14 步）

| 步骤 | 类别 | 路径 | 说明 |
|:----:|------|------|------|
| 1 | 核心配置 | `~/.hermes/config.yaml`, `~/.hermes/.env` | provider、model、平台集成 |
| 2 | 数据库 | `~/.hermes/*.db` | state.db, memory_store.db, knowledge_index.db 等 |
| 3 | 自定义脚本 | `~/.hermes/scripts/` | 知识库搜索、图片生成、bridge 脚本等 |
| 4 | Systemd 服务 | `~/.config/systemd/user/hermes-*` | gateway + bridge service 文件 |
| 5 | 知识库 | `~/knowledge/` | 完整本地知识库（425+ .md 文件） |
| 6 | Skills | `~/.hermes/skills/` | 所有 skill 定义 |
| 7 | 记忆 & Cron | `~/.hermes/memories/` + `~/.hermes/cron/` | 持久化记忆、定时任务 |
| **8** | **FTS5 索引** | `~/.hermes/knowledge_index.db` | **知识库 SQLite FTS5 全文索引（~73MB）** |
| **9** | **Obsidian vault** | `~/Documents/Obsidian Vault/` | **.obsidian/ 配置 + Brain/ + O2B brain.sqlite（不重复备份 symlink 知识库文件）** |
| 10 | 计算总大小 | — | 汇总备份包体积 |
| 11 | 生成 MANIFEST | `backup_dir/MANIFEST.json` | 含 fts5_included、obsidian_vault_included 标志 |
| 12 | 更新最新指针 | `LATEST_BACKUP` 纯文本文件 | 供脚本读取最新备份 |
| 13 | 清理过期 | 自动删除 >60 天的备份和日志 | 双通道日志记录 |
| 14 | 汇总 | — | 输出到文件日志 + systemd journal |

### 9. Obsidian vault 的备份策略（方案一 symlink）

```python
# 只备份三样东西，不备份 symlink 目标文件：
# 1. .obsidian/ 配置目录（社区插件注册、workspace 布局、图谱设置）
obsidian_cfg = vault_path / ".obsidian"
# 2. vault 根目录的非 symlink .md 文件（用户自建笔记）
for item in vault_path.glob("*.md"):
    if item.is_file() and not item.is_symlink():
# 3. Open Second Brain 数据：Brain/ 目录 + .open-second-brain/brain.sqlite
brain_dir = vault_path / "Brain"
osb_db = vault_path / ".open-second-brain" / "brain.sqlite"
```

knowledge/ 目录下的 425 个文件由第 5 步独立备份（原始路径），不通过 vault symlink 重复备份。

## 核心脚本

### 增量备份 (backup-hermes-incremental.py)

```bash
# 增量（默认，仅复制变更文件）
python3 /mnt/backup/hermes-backup/backup-hermes-incremental.py

# 完整备份
python3 /mnt/backup/hermes-backup/backup-hermes-incremental.py --full
```

日志双输出：文件（`logs/YYYYMMDD_HHMMSS-backup.log`）+ systemd journal（`journalctl --user -t hermes-backup`）。

### 关键实现：增量对比

增量模式通过 SHA256 哈希对比前次备份，仅复制变更文件。典型效果：完整备份 82 MB，日常增量仅 1-5 MB。

### 巡检 (inspect-hermes.py)

```bash
python3 /mnt/backup/hermes-backup/inspect-hermes.py
```

检查项：备份盘挂载、可用空间、备份时效、数据库完整性、服务运行状态。

### 恢复 (restore-hermes.py)

```bash
# 预览（安全检查）
python3 /mnt/backup/hermes-backup/restore-hermes.py --dry-run

# 一键恢复
python3 /mnt/backup/hermes-backup/restore-hermes.py --force

# 恢复到指定时间点
python3 /mnt/backup/hermes-backup/restore-hermes.py 20260607_034115
```

## Cron 自动备份

每天 03:00 增量 + 每周日 04:00 完整备份。

```bash
# 每日增量包装脚本 → ~/.hermes/scripts/daily-backup.sh
#!/usr/bin/env bash
exec python3 /mnt/backup/hermes-backup/backup-hermes-incremental.py

# 每周完整包装脚本 → ~/.hermes/scripts/weekly-full-backup.sh
#!/usr/bin/env bash
exec python3 /mnt/backup/hermes-backup/backup-hermes-incremental.py --full
```

> ⚠ **Cron 约束**：cronjob 的 `script` 参数必须是 `~/.hermes/scripts/` 下的文件名（相对路径），不能用绝对路径。这是 Hermes cron 调度器的限制。

### DeepSeek 内容过滤对 cron 任务的影响

新闻聚合类 cron 任务（如"每日头条新闻"）如果用 DeepSeek 模型运行，容易触发 `Content Exists Risk` 错误（HTTP 400）。DeepSeek 的内容安全过滤会拦截包含敏感关键词的输出。

**规避方案**：新闻类 cron 任务应改用 SiliconFlow Qwen 或其他不受内容审查限制的模型。详见 `references/cron-job-troubleshooting.md`。

### 日志老化策略（60 天 / 2 个月）

备份脚本每次运行时自动清理超过 60 天的备份目录和日志：

```python
# 清理过期备份目录
for b in BACKUP_ROOT.glob("backups/*"):
    age_days = (now - b.stat().st_mtime) / 86400
    if age_days > 60:
        shutil.rmtree(b)
        logger.info(f"🗑 删除过期备份: {b.name} ({size_mb:.1f} MB, {age_days:.0f} 天前)")

# 清理过期日志
for logfile in LOGS_DIR.glob("*-backup.log"):
    age_days = (now - logfile.stat().st_mtime) / 86400
    if age_days > 60:
        logfile.unlink()
        logger.info(f"🗑 删除过期日志: {logfile.name} ({age_days:.0f} 天前)")
```

清理动作同时写入文件日志和 systemd journal，无过期项目时输出「✅ 无过期项目（保留 60 天以内）」。

### 健康检查集成

备份盘上另有独立健康检查（`~/.hermes/scripts/health-check.sh`），每周五 23:00 运行，结合 systemd 开机补检。健康检查日志同样 60 天老化。详见 `hardware-diagnostics` skill。

## 坑与教训

### 1. find_latest_backup 必须在 mkdir 之前调用

增量对比需要找到前次备份目录。如果在 `backup_dir.mkdir()` 之后调用 `find_latest_backup()`，glob 会返回刚建的空目录，导致 `prev_backup` 被设为 None（与自身对比后跳过），所有文件被视为「变更」。

**正确顺序**：
```python
backup_dir = BACKUP_ROOT / "backups" / f"{TS}-{btype}"
prev_backup = find_latest_backup()          # ← 必须在 mkdir 之前
backup_dir.mkdir(parents=True, exist_ok=True)
```

### 2. exFAT 文件系统限制

`/dev/sda2` 是 exFAT 格式（卷标 BACKUP，894 GB）：
- **不支持符号链接**：不能用 `os.symlink()`，改用 `LATEST_BACKUP` 纯文本文件记录最新备份名
- **不支持 Unix 权限**：`chmod` 无实际效果（权限位被忽略）
- **`du` 报告不准确**：exFAT 的簇分配可能导致 `du` 显示大小远超实际文件内容
- **`shutil.copy2` 可用**：文件复制正常，但元数据（权限/时间戳）可能丢失

### 3. systemd journal 集成

```python
try:
    from systemd import journal
    jh = journal.JournalHandler(SYSLOG_IDENTIFIER="hermes-backup")
    logger.addHandler(jh)
except ImportError:
    pass  # 非 systemd 环境静默回退
```

查看：`journalctl --user -t hermes-backup --since "1 day ago"`

### 4. 数据库备份最佳实践

- **大文件（> 5 MB）**：备份前可选 `VACUUM` 压缩（仅在完整模式），增量模式用 hash 对比跳过
- **完整性验证**：每次备份后自动执行 `PRAGMA integrity_check`
- **锁竞争**：备份期间 Hermes Agent 可继续运行（SQLite 读锁不影响 WAL 模式写入）

## 参考文件

- `references/backup-script-template.md` — 完整备份脚本核心逻辑模板
- `references/exfat-quirks.md` — exFAT 文件系统在备份场景的已知限制
- `references/cron-job-troubleshooting.md` — Hermes cron 任务故障排查（日志定位、常见错误模式、DeepSeek Content Exists Risk 处理）
