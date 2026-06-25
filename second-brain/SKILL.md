---
name: second-brain
description: 第二大脑 — 收件箱自动化、知识分类、inbox→skills/projects/worklog 归档管道、进化机制集成、复盘流程
version: 2.0.0
author: andymao
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [second-brain, inbox, knowledge, automation, feishu, evolution]
    related_skills: [hermes-agent-evolution-mechanism, feishu-agent, knowledge-base]
---

# Second Brain

第二大脑 — 收件箱管理与自动化归档系统。

核心原则：**所有输入先进 inbox → 按规则自动分类归档 → 可检索可复用。**

## 收件箱目录结构

```
~/knowledge/inbox/
├── feishu/         # 飞书消息
├── whatsapp/       # WhatsApp 消息
├── quick_notes/    # 随手记
└── README.md       # 使用说明
```

## 自动化管道

### 入口：feishu_to_inbox.py

保存一条消息到收件箱（支持预先分类前缀）：

```bash
# 直接参数
python3 ~/.hermes/scripts/feishu_to_inbox.py 记录：今天Kafka ISR异常

# 管道输入
echo "项目：A1 客户问题跟进" | python3 ~/.hermes/scripts/feishu_to_inbox.py
```

自动检测前缀：
| 前缀 | 文件名前缀 |
|------|-----------|
| `项目：` | `proj_` |
| `记录：` | `note_` |
| `故障：` | `trouble_` |
| `经验：` | `exp_` |
| `知识：` | `k_` |
| 其他 | `msg_` |

### 分类：inbox_sorter.py

将 inbox 中的文件按关键词自动移至对应目录：

```bash
python3 ~/.hermes/scripts/inbox_sorter.py
```

分类规则（按优先级）：
| 关键词（首行） | 目标目录 |
|---------------|---------|
| `项目：` 或 包含 Project_A 代号 | `projects/project_a/` |
| 包含 签证/visa | `projects/us_visa/` |
| 包含 Apple Notes/iCloud | `projects/apple_notes_sync/` |
| `故障：` 或 `经验：` | `skills/troubleshooting/` |
| 包含 报错/error/failed/异常 | `skills/troubleshooting/` |
| 包含 Kafka/Flink/HDFS 等大数据关键词 | `skills/bigdata/` |
| 包含 3GPP/ETSI/HI2 等通信关键词 | `skills/telecom/` |
| `巡检：` 或 `维护：` | `worklog/daily/` |
| `记录：` | `worklog/daily/` |
| 默认（无法分类） | `worklog/daily/` |

### 定时任务

| cron | 动作 | 说明 |
|------|------|------|
| 每日 22:30 | `inbox_sorter.py` | 自动分类归档 |
| 消息到达时（手动） | `feishu_to_inbox.py` | 保存消息到 inbox |

## 行为规则

当用户在飞书/微信/Telegram 发送以以下关键词开头的消息时，自动调用 feishu_to_inbox.py 保存到 inbox：

- `记录：xxx` → 工作日志 → worklog/daily/
- `项目：xxx` → 项目进展 → projects/
- `故障：xxx` → 故障经验 → skills/troubleshooting/
- `经验：xxx` → 技能沉淀 → skills/
- `知识：xxx` → 留在 inbox

## 与进化机制集成

进化机制（hermes-agent-evolution-mechanism）定义了知识沉淀闭环：

```
问题输入 → 分析与执行 → 解决方案 → 经验总结 → 写入 Knowledge → 提炼 Skill → 未来自动复用
```

第二大脑的 inbox 管道是实现该闭环的**基础设施层**。每次完成重要任务后：
1. 将经验写入 knowledge 对应目录
2. 更新 project_status.yaml 中的项目状态
3. 必要时创建/更新 Hermes Skill

## 命令速查

```bash
# 手动收件箱归档
python3 ~/.hermes/scripts/inbox_sorter.py

# 手动保存消息
python3 ~/.hermes/scripts/feishu_to_inbox.py 记录：内容

# 查看收件箱状态
find ~/knowledge/inbox/ -name "*.md" -not -name "README.md" | wc -l

# 查看今日归档
find ~/knowledge/worklog/daily/ -name "$(date +%Y-%m-%d)*.md"

# 查看项目状态
cat ~/knowledge/_system/project_status.yaml

# 查看决策日志
cat ~/knowledge/_system/decision_log.md
```

## 知识库结构

```
~/knowledge/
├── _system/          # 项目状态、决策日志、进化日志
├── worklog/          # 日报/周报/月报
│   └── daily/        # inbox 归档目的地
├── skills/           # 技能沉淀
│   ├── bigdata/      # Hadoop/Kafka/Flink 等
│   ├── telecom/      # HI2/3GPP/Wireshark 等
│   ├── troubleshooting/  # 故障排查经验
│   └── hermes/       # Hermes 自身
├── projects/         # 项目经验
├── bigdata/          # 大数据运维笔记
├── telecom/          # 通信协议笔记
├── inbox/            # 收件箱（feishu/whatsapp/quick_notes）
└── 丢丢/             # 丢丢相关（健康档案、照片）
```

## 项目状态中心

`~/knowledge/_system/project_status.yaml` 是项目调度中心。
每次涉及项目类任务时优先读取，任务完成后更新 next_action。

```yaml
projects:
  项目名:
    priority: high|highest|medium|low
    status: active|planning|waiting|completed
    next_action: "下一步做什么"
    notes: "备注"
```

## Pitfalls

- **inbox_sorter 只扫描子目录中的 .md 文件**，不会误移 README.md
- **feishu_to_inbox.py 不支持图片**，只保存文字
- **归档后不会删除原文件**，用 shutil.move 而非 copy（节省空间）
- **文件名含时间戳**避免重名冲突，格式 `YYYYMMDD_HHMMSS_前缀_摘要.md`
- **收件箱应每日清理**，积压超过50篇应考虑优化分类规则

## 关联技能

- **knowledge-privacy-policy** — 知识分层隔离策略。涉及项目信息/客户数据时，必须先脱敏再写入知识库和技能。任何包含项目代号、客户名的关键词必须按 RULE6 规则处理。
