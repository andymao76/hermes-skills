---
name: second-brain-inbox
description: 第二大脑统一收件箱 — 基于三分类体系（工作/知识/技能），所有输入先收集后分类，日报/周报/月报统一管理
trigger: 收集信息、保存笔记、写日报、记录灵感、存储网页摘录、会议纪要、故障排查记录、项目状态查看
---

# 第二大脑收件箱 (second-brain-inbox)

## 核心原则

1. **双层架构** — **知识库根层用 PARA**（00_INBOX→04_ARCHIVE），**Obsidian 用户层用三分类**（工作/知识/技能）
   - `~/knowledge/` 根目录：PARA 体系（00_INBOX/01_PROJECTS/02_AREAS/03_RESOURCES/04_ARCHIVE）
   - `~/knowledge/工作/`（+ 知识/技能）：三分类，与 Obsidian vault 通过 symlink 互通
   - 设计用意：PARA 管理知识本身，三分类适配 Obsidian 终端用户视角
2. **入口统一** — 所有新信息先进 `~/knowledge/00_INBOX/`，再由 auto-classify 或人工分类到 PARA/三分类目的地
3. **路径一致** — Obsidian vault 结构与知识库路径通过 symlink 互通，不复制文件
4. **Ubuntu 主存** — 所有文件在 Ubuntu 上，Windows/Samba 只读不存

## Obsidian vault 结构

```
Obsidian vault 顶层           说明
─────────────────────        ──────────────────────
工作/                         日报/周报/月报/项目笔记
  日报/YYYYMMDD.md            日工作日志
  周报/                       周五生成
  月报/                       月末生成
  项目/                       项目笔记/PoC记录
知识/                         symlink → ~/knowledge/ (852MB)
技能/                         skill文档/工作流指南
Brain/                        系统记忆层（O2B）
```

## 知识库映射

| Obsidian 路径 | 实际路径 | 用途 |
|-------------|---------|------|
| `工作/日报/` | `~/Documents/Obsidian Vault/工作/日报/` | Hermes 写入日报 |
| `知识/` | `~/knowledge/` (symlink) | kb-search 可索引 |
| `技能/` | `~/Documents/Obsidian Vault/技能/` | 工作流文档存放 |

## 日报管理

| 操作 | 命令 | 输出位置 |
|------|------|---------|
| 开始任务 | `开始任务：{工作内容}` | 暂存，日报时汇总 |
| 结束任务 | `结束任务，用了X小时` | 同上 |
| 快速记录 | `记一下：{内容}，X小时` | 同上 |
| 生成日报 | `生成今天的日报` | `工作/日报/YYYYMMDD.md` |
| 生成周报 | `生成本周周报` | `工作/周报/` |
| 生成月报 | `生成本月月报` | `工作/月报/` |

## 路径保障（每日 06:00 cron: `vault-structure-check`）

```bash
bash ~/.hermes/scripts/ensure-vault-structure.sh
```

自动确保：
- `工作/日报/周报/月报/项目/` 存在
- `知识/` symlink → `~/knowledge/`
- `技能/` 存在
- kb-search 可索引 symlink 路径

## Inbox 自动分类（新增工具）

`~/bin/inbox-classify.py` 自动扫描 `~/knowledge/00_INBOX/` 根目录下的新文件，按内容关键词分类到 8 个子目录：

| 分类 | 目标子目录 | 匹配关键词 |
|------|-----------|-----------|
| 反思卡片 | `反思卡片/` | 反思卡片, 经验总结, 学到了, 知识闭环 |
| 故障排查 | `故障排查记录/` | error, 故障, 报错, 排查, debug |
| 会议纪要 | `会议纪要/` | 会议, meeting, 讨论, 纪要 |
| 灵感 | `灵感/` | 灵感, idea, 创意, 建议 |
| 日报 | `日报/` | 日报, 今日完成, 明日计划 |
| 网页摘录 | `网页摘录/` | https://, article, 教程, 网页 |
| PDF摘要 | `PDF摘要/` | .pdf, 论文, arxiv, 摘要 |
| 飞书消息 | `飞书消息/` | 飞书, feishu, lark |
| Telegram指令 | `Telegram指令/` | telegram, tg, bot |

**用法：**
```bash
python3 ~/bin/inbox-classify.py            # 执行分类
python3 ~/bin/inbox-classify.py --dry-run  # 预览
python3 ~/bin/inbox-classify.py --watch    # 监控模式（30秒间隔）
python3 ~/bin/inbox-classify.py --rules    # 查看规则
python3 ~/bin/inbox-classify.py --log      # 查看分类历史
```

## 反思卡片 → 运维经验库

反思卡片 (`00_INBOX/反思卡片/`) 是经验闭环的入口。用户审核后，按以下规则分流：

| 卡片结论 | 去向 | 用途 |
|----------|------|------|
| ⭐ 升级为 Skill | `~/.hermes/skills/` + 备份到 `~/knowledge/技能/` | 有固定步骤+跨项目可复用的工作流 |
| 📝 存入运维经验库 | `~/knowledge/{telecom/hadoop/kafka/flink/hbase/greenplum/wireshark/hi2/troubleshooting}/` | 领域实战经验、踩坑记录、调优方案 |
| 📦 归档 | 留在 INBOX 不处理 | 一次性信息无需保留 |

### 操作流程

1. 用户说"审核反思卡片" → 列出 `00_INBOX/反思卡片/` 所有待处理卡片
2. 用户指定结果 → 执行 skill_manage 或 write_file 到对应目录
3. 已处理的卡片移出 INBOX（归档到对应领域目录，或删除）

## 参考

- `hermes-second-brain-v5` — 总览技能，含核心资产原则、知识闭环、运维经验库
- `obsidian-vault-maintenance` — vault 结构/Samba/GitHub 备份/密钥策略
- `references/second-brain-directory-conventions.md` — 完整目录约定、symlink 互通
- `references/secrets-backup-policy.md` — API Key 仅存本地，不推 GitHub
- `references/obsidian-remote-access.md` — Samba 共享 + Windows 连接
- `references/worklog-workflow.md` — 工作日志全流程
- `references/task-closure-cycle.md` — 任务闭环

## 用户偏好（避免踩坑）

- ✅ 知识库根层用 PARA（00_INBOX→04_ARCHIVE），Obsidian 显示层用三分类（工作/知识/技能）
- ❌ 不要在 PARA 和 三分类之间混用——它是两层，不是二选一
- ❌ Windows 不留副本
- ✅ Samba 只读远程访问
- ❌ 目录名不要用 `_` 或 `!` 前缀（locale 排序不生效）
- ✅ 用 `0` 数字前缀或纯中文分类名
