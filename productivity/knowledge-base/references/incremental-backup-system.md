# 增量备份系统 — 14 步结构

> 参考实现: `/mnt/backup/hermes-backup/backup-hermes-incremental.py`

## 备份步骤（编号连续 1-14）

| 步 | 类别 | 说明 | 增量对比方式 |
|:--:|------|------|------------|
| 1 | 核心配置 | config.yaml, .env | SHA256 对比前次备份 |
| 2 | 数据库 | state.db, memory_store.db, kanban.db, response_store.db | SHA256 + integrity_check |
| 3 | 自定义脚本 | ~/.hermes/scripts/ | 递归对比整个目录树 |
| 4 | Systemd 服务 | hermes-*.service + .d/ | 逐个文件对比 |
| 5 | 知识库 | ~/knowledge/ 全部文件 | 递归对比，增量跳过未变 |
| 6 | Skills | ~/.hermes/skills/ | 递归对比 |
| 7 | 记忆 & Cron | memories/ + cron/ | 递归对比 |
| 8 | FTS5 索引 | knowledge_index.db (~73MB) | SHA256 + integrity_check |
| 9 | Obsidian vault | .obsidian/ + Brain/ + .open-second-brain/ | 跳过 symlink 文件，只配隔离 |
| 10 | 计算总大小 | backup_dir 所有文件汇总 | — |
| 11 | 生成 MANIFEST.json | 含 fts5_included / obsidian_vault_included | — |
| 12 | 更新 LATEST_BACKUP 指针 | — | — |
| 13 | 清理过期备份 | 保留 60 天 | — |
| 14 | 汇总输出 | — | — |

## 第 9 步（Obsidian vault）的备份隔离

只备份：
- `.obsidian/` 配置（community-plugins.json、graph.json、workspace.json、app.json、appearance.json）
- `Brain/` 目录（O2B 记忆层：active.md、log/*.md、metrics/index.jsonl）
- `.open-second-brain/brain.sqlite`（O2B 搜索索引）

明确不备份：
- `knowledge/` symlink 目录（知识库文件由第 5 步独立备份，不通过 vault 路径重复）
- vault 根目录下的 symlink .md 文件（仅备份非 symlink 的真实笔记）

## 脚本结构

```python
# /mnt/backup/hermes-backup/backup-hermes-incremental.py
# 329 行，7 个函数

def main():
    1. 检查挂载点 + 空间
    2. 创建备份目录
    3. 找前次备份（必须在 mkdir 之前）
    4-9. 逐步骤备份（copy_if_changed + backup_dir_structure）
    10. 计算总大小
    11. 写 MANIFEST.json
    12. 写 LATEST_BACKUP
    13. 清理 60 天前的备份
    14. 汇总日志

关键函数：
- copy_if_changed(src, dst, force, prev_dst) → (bool, reason)
- verify_db(path) → bool (PRAGMA integrity_check)
- backup_dir_structure(src, dst, force, prev_dir) → (copied, skipped)
```

## 关键坑

**prev_backup 查找时机**：`find_latest_backup()` 必须在 `backup_dir.mkdir()` 之前调用，否则 glob 结果包含刚创建的空目录，`prev_backup` 指向自己后被置为 None，导致所有文件被当作首次备份复制。
