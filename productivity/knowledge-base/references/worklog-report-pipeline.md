# 工作日志与报告生成体系

## 技能包

Hermes skills 中已安装 4 个报告相关技能：

| 技能 | SKILL.md 位置 | 职责 |
|------|---------------|------|
| `worklog` | `~/.hermes/skills/worklog/SKILL.md` | 工作流水账自动解析 |
| `daily_report` | `~/.hermes/skills/daily_report/SKILL.md` | 日报生成（单项目/多项目双格式） |
| `weekly_report` | `~/.hermes/skills/weekly_report/SKILL.md` | 周报生成（按项目聚合工时） |
| `monthly_report` | `~/.hermes/skills/monthly_report/SKILL.md` | 月报生成（含状态变化/关键产出） |

## 使用节奏

| 时间 | 命令 | 输出位置 |
|------|------|---------|
| 每天下班前 | `生成今天的日报` | `0sinovatio/日报/YYYYMMDD.md` |
| 每周五下班前 | `生成本周周报` | `0sinovatio/周报/YYYYMMDD_周报.md` |
| 每月最后一天 | `生成本月月报` | `0sinovatio/月报/YYYYMMDD_月报.md` |

## 输出路径

日报/周报/月报统一写入 Obsidian vault 首层 `0sinovatio/` 目录。
symlink 确保 kb-search 也可索引：
`~/knowledge/0sinovatio/ → ~/Documents/Obsidian Vault/0sinovatio/`

## 项目映射

worklog 的默认项目为 **A1 PC项目（苏丹NISS）**。
用户不写项目名时自动归到默认项目。
映射表存于 `worklog/SKILL.md` 的「项目名称映射」章节。

## 日常记录话术

- `开始任务：{工作内容}` — 开始一个任务
- `结束任务，用了{X小时}` — 结束当前任务
- `记一下：{内容}，{工时}` — 快速记录
- `补记 {时间} {内容} {工时}` — 补记历史

## 开发者自建技能包

本地 Git 仓库：`~/hermes-skills-package/`（2 commits）
含 worklog/daily_report/weekly_report/monthly_report 的 SKILL.md + skill.yaml 双格式。
可推送到 GitHub: `git remote add origin https://github.com/andymao76/hermes-worklog-skills.git`
