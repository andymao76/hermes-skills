# 数据备份策略：GitHub + /mnt/backup/ 双层保护

## 原则

| 数据类型 | 大小 | 备份方式 | 原因 |
|---------|:----:|---------|------|
| Skill 文件（SKILL.md） | 小 | GitHub 私有仓库 | 可版本管理，换机快速恢复 |
| 配置（config.yaml 脱敏版） | 小 | GitHub 私有仓库 | 同上 |
| 脚本（.sh/.py） | 小 | GitHub 私有仓库 | 同上 |
| Memory（MEMORY.md/USER.md） | 小 | GitHub 私有仓库 | 用户画像不可丢 |
| 项目状态（project_status.yaml） | 小 | GitHub 私有仓库 | 优先级调度核心 |
| Cron 清单 | 小 | GitHub 私有仓库 | 定时任务快照 |
| 知识库（~/knowledge/） | 852MB | /mnt/backup/ 每日增量+每周完整 | Git 装不下 |
| 备份数据自身 | — | /mnt/backup/ 保留 60 天 | 备份的备份 |

## GitHub 仓库清单

| 仓库 | 用途 |
|------|------|
| `andymao76/hermes-worklog-skills` | 工作日志技能包（worklog/daily/weekly/monthly） |
| `andymao76/hermes-config` | 配置 + 脚本 + memory + 技能备份 + cron 清单 |
| `andymao76/hermes-community-skills` | 社区技能收藏索引 |

## 恢复流程（换机/重装）

```bash
# 1. 拉配置和数据
git clone https://github.com/andymao76/hermes-config.git
git clone https://github.com/andymao76/hermes-worklog-skills.git

# 2. 恢复技能
cp hermes-worklog-skills/skills/* ~/.hermes/skills/
cp hermes-config/skills/*.md ~/.hermes/skills/
cp hermes-config/scripts/* ~/.hermes/scripts/
cp hermes-config/memories/* ~/.hermes/memories/
cp hermes-config/project_status.yaml ~/knowledge/_system/

# 3. 恢复知识库（从 /mnt/backup/）
bash /mnt/backup/restore-hermes.py

# 4. 重建搜索索引
python3 ~/.hermes/scripts/kb-search.py init
python3 ~/.hermes/scripts/kb-search.py embed  # 可后台跑

# 5. 确保 vault 结构
bash ~/.hermes/scripts/ensure-vault-structure.sh
```

## 不备份到 GitHub 的内容

- API Key（只在.env 和 config.yaml 中，脱敏后才提交）
- 知识库文件（852MB → /mnt/backup/）
- 超过 20MB 的单文件（→ /mnt/backup/）
