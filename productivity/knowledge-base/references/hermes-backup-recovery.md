# Hermes Agent 备份恢复体系

> 参考实现：`/mnt/backup/hermes-backup/`

## 目录结构

```
/mnt/backup/hermes-backup/
├── README.md                      ← 操作手册
├── backup-hermes-incremental.py   ← 备份脚本（完整/增量）
├── inspect-hermes.py              ← 巡检脚本
├── restore-hermes.py              ← 恢复脚本（--dry-run / --force）
├── logs/                          ← YYYYMMDD_HHMMSS-backup.log
├── backups/                       ← YYYYMMDD_HHMMSS-{full,incremental}
└── LATEST_BACKUP                  ← 最新备份名
```

## 备份内容

| 编号 | 类别 | 路径 | 说明 |
|:----:|------|------|------|
| 1 | 核心配置 | `config.yaml`, `.env` | Provider/模型/平台集成 |
| 2 | 数据库 | `state.db`, `memory_store.db`, `response_store.db` | 会话/Holographic记忆/响应缓存 |
| 3 | 自定义脚本 | `scripts/` | 自定义脚本 |
| 4 | Systemd 服务 | systemd `hermes-*.service` | Gateway + Bridge |
| 5 | 知识库 | `knowledge/` | 本地知识库全文（~425 文件） |
| 6 | Skills | `skills/` | 全部 skill 定义（~185 个） |
| 7 | 记忆 & Cron | `memories/`, `cron/` | 持久化记忆条目 + 定时任务 |
| 8 | FTS5 索引 | `knowledge_index.db` | FTS5 全文搜索数据库（~73MB） |
| 9 | Obsidian vault 配置 | `obsidian-vault/.obsidian/`, `Brain/`, `.open-second-brain/` | Obsidian 插件注册/图谱/O2B 记忆**

**注（第 9 项）**：只备份 `.obsidian/` 配置、`Brain/`（O2B 记忆层）和 `.open-second-brain/brain.sqlite`（O2B 索引）。知识库文件本身由第 5 项独立备份，不通过 vault symlink 路径重复备份。

## 增量备份关键坑

**Bug**: `find_latest_backup()` 在 `backup_dir.mkdir()` **之后**调用，导致 glob 结果包含刚创建的空目录，`prev_backup` 指向自己后被置为 `None`，所有文件被当作"首次备份"全部复制。

**Fix**: 将 `find_latest_backup()` 移到 `backup_dir.mkdir()` **之前**：

```python
# 正确顺序
prev_backup = find_latest_backup()   # ← 先查
backup_dir.mkdir()                    # ← 后建
```

## Cron 调度

| 任务 | 频率 | 脚本 |
|------|------|------|
| 每日增量备份 | 03:00 | `daily-backup.sh` |
| 每周完整备份 | 周日 04:00 | `weekly-full-backup.sh` |
| 每周健康检查 | 周五 23:00 | `health-check.sh force` |

## 日志老化

- 保留期：60 天（2 个月）
- 备份脚本和健康检查脚本每次运行时自动清理
- 清理动作记录到日志和 systemd journal
- 格式：`🗑 删除过期备份: <name> (<size> MB, <age> 天前)`

## 崩溃恢复

```bash
sudo mount /dev/sda2 /mnt/backup
python3 /mnt/backup/hermes-backup/restore-hermes.py --force
# 自动恢复全部配置/数据库/脚本/知识库/skills + 重启 gateway+bridge
```
