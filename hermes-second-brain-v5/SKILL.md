---
name: hermes-second-brain-v5
category: productivity
description: Hermes 第二大脑 V5 体系 — 收件箱/项目状态/决策日志/知识闭环/运维经验库/每日复盘/网络诊断/模型切换/Copilot委托/PMO助理。当用户提到优化第二大脑、整理架构、建立知识库、知识闭环、反思卡片、运维经验库、V5规划、项目状态、复盘、网络自愈、模型切换、Copilot结合、PMO自动化、经验池、领域知识库时加载此技能。
---

# Hermes Second Brain V5 Skill

## Purpose

Use this skill when the user wants Hermes Agent to operate as a long-term second brain, project assistant, operations assistant, knowledge manager, coding coordinator, and personal PMO assistant.

This skill is for: Ubuntu 24.04 workstation, Hermes Agent as main AI framework, Obsidian/Markdown knowledge base as primary storage, Telegram/Feishu/WeChat/CLI as input channels, Copilot CLI as coding delegate, China + overseas network environments.

## Core Principle

Build a closed-loop second brain: **Capture -> Understand -> Remember -> Relate -> Act -> Review**

Hermes should become: Second Brain + Project Secretary + Operations Assistant + Knowledge Manager + Coding Coordinator + Personal PMO.

### 核心资产原则（重要）

> **用户最有价值的资产不是AI模型，而是20年通信经验 + 大数据平台经验 + LI合法监听经验。**

模型随时可以换，但用户的实战经验——跨域排障直觉、多厂商对接经验、架构决策能力——是唯一的不可替代资产。

Hermes 的全部工作应当服务于：**捕获、结构化、复用**用户的领域经验。知识闭环和运维经验库的存在意义正在于此。

## Storage Rule

- Obsidian/Markdown is the primary brain.
- Apple Notes is only a mobile display layer.
- Never make Apple Notes the only source of truth.

## Directory Layout

### PARA 体系（知识库根层）

```
~/knowledge/_system/         项目状态、决策、规则
~/knowledge/00_INBOX/        所有原始输入（含反思卡片/）
~/knowledge/01_PROJECTS/     活跃项目
~/knowledge/02_AREAS/        长期责任领域
~/knowledge/03_RESOURCES/    技术参考
~/knowledge/04_ARCHIVE/      已完成内容
~/knowledge/review/          周/月复盘
~/knowledge/daily/           每日日志
```

### 运维经验库（领域层）

用户20年经验的沉淀目录，按领域扁平组织：

```
~/knowledge/telecom/         通信/电信 — 信令、3GPP、2G/3G/4G/5G、项目经验
~/knowledge/hadoop/          Hadoop生态 — HDFS/YARN/Hive/Ambari
~/knowledge/kafka/           Kafka消息队列
~/knowledge/flink/           Flink流计算
~/knowledge/hbase/           HBase列式数据库
~/knowledge/greenplum/       Greenplum MPP数据仓库
~/knowledge/wireshark/       Wireshark/tcpdump抓包分析
~/knowledge/hi2/             合法监听LI — 华为/ZTE/爱立信/NSN/Mavenir
~/knowledge/troubleshooting/ 通用排障方法论、War Story、SOP
```

**原则**：每个领域目录扁平扩展，踩坑记录、调优方案、项目经验直接写入对应子目录。新领域出现时直接新建一级目录。

## Project Status Center

File: `~/knowledge/_system/project_status.yaml`

Maintain YAML with project status, priority, next_action. When user asks "我现在最重要的事情是什么？", read this file first.

Format:
```yaml
projects:
  project_name:
    status: active|waiting|blocked|done
    priority: high|medium|low
    next_action: description
    owner: andy

### Routines Sync（Cron 与 YAML 同步）

创建/修改 CRON 任务时，同步更新 `routines` 段：

```yaml
routines:
  daily:
    - "17:40 日报生成提醒（工作日）"
    - "07:00 IMA知识库备份"
  weekly:
    - "Fri 18:00 周报生成"
    - "Sun 21:00 周报复盘"
  monthly:
    - "月末最后一天 月报生成"
```

**规则：** 每次操作 CRON 任务，同步 routines 条目。routines 用自然语言描述，与 cron 表达式互为对照。
```

## Decision Log

File: `~/knowledge/_system/decision_log.md`

Record major decisions with: Decision, Context, Options Considered, Reason, Risk, Review Date.

Key decisions to record: Why Hermes, why Obsidian, why Apple Notes is display-only, why DeepSeek/Qwen in China, why Gemini/OpenAI overseas, why Copilot CLI as delegate.

## Daily Inbox Workflow

All new info enters `~/knowledge/00_INBOX/`. Daily processing:
1. Read new files from INBOX
2. Classify into PROJECTS/AREAS/RESOURCES/ARCHIVE
3. Extract action items
4. Update project_status.yaml if needed
5. Save daily summary to `~/knowledge/daily/YYYY-MM-DD.md`

## Network Doctor

Create script to check: proxy, DNS, DeepSeek, SiliconFlow, Bailian, Gemini, Nous, GitHub, Telegram, Cloudflare connectivity.

## Provider Switch

Modes: china, china-proxy, overseas, low-bandwidth, no-proxy.
- China: DeepSeek -> SiliconFlow Qwen -> Bailian
- Overseas: Gemini -> OpenAI -> Nous

## Copilot Delegate

Hermes handles: requirement analysis, task decomposition, architecture design, knowledge capture, documentation.
Copilot handles: code reading, generation, modification, tests, GitHub PRs.

## PMO Assistant

Monthly schedule:
- Day 1: Remind maintenance reports
- Day 5: Check missing reports
- Day 8: Self-check reminder
- Day 10: Generate PMO email template

## Knowledge Closed-Loop（知识闭环）

每次问题解决后，按以下流水线沉淀经验：

```
问题 → 解决 → 反思卡片 → 审核分类 → Skill（umbrella级别）或 运维经验库（领域目录）→ 未来复用
```

### 闭环流程（B阶段 — 手动画卡+人工审核）

1. **生成反思卡片** — 放入 `~/knowledge/00_INBOX/反思卡片/`
   - 格式：发生了什么 / 学到了什么 / 可复用判断 / 结论
   - 触发时机：排错成功、学到新知识、完成调研、配置成功、用户说"记下来"
2. **分流决策** — 三类目标：
   - ⭐ **Skill** — 有固定操作步骤 + 跨项目可复用 → 用 `skill-creator` 流程创建 umbrella Skill
   - 📝 **Knowledge（领域经验）** → 存入 `~/knowledge/{对应领域目录}/`
   - 📦 **归档** — 一次性、无需保留
3. **升格执行**
   - Skill：`skill_manage(action='create')` + 备份到知识库
   - 经验：写入对应领域目录（telecom/hadoop/kafka/flink/hbase/greenplum/wireshark/hi2/troubleshooting）
4. **闭环确认** — 告知用户结果

### 三层记忆体系

| 层 | 位置 | 用途 |
|----|------|------|
| 🧠 Memory | Hermes 内部 | 用户偏好、环境事实（跨会话） |
| 💡 Skill | `~/.hermes/skills/` | 可执行的工作流（过程记忆 — 怎么做） |
| 📚 Knowledge | `~/knowledge/` 领域目录 | 实战经验、踩坑记录、调优方案（陈述记忆 — 知道什么） |

### 反思卡片模板

```markdown
# 反思卡片: [主题]
日期: YYYY-MM-DD
来源: [问题描述]

## 发生了什么
[简要描述问题和解决过程]

## 学到了什么
[核心收获]

## 可复用判断
- 同类问题发生频率: [首次/偶尔/频繁]
- 解决步骤是否固定: [是/否]
- 是否需要工具命令: [是/否]

## 结论
→ [ ] 升级为 Skill
→ [ ] 存入 运维经验库/{领域}/
→ [ ] 归档
```

## Do Not Do

- Do not add MCPs without workflow
- Do not store knowledge only in chat history
- Do not make Apple Notes the only source of truth
- Do not modify Hermes core files
- Do not rely on single provider or proxy
- Do not create automation without logs

## 多实例同步（本地 ↔ 腾讯云）

V5.1 架构支持 MEMORY 和 RULE 两层数据从本地同步到腾讯云实例，使两地知识体系和Agent能力一致。

### 同步范围

| 层 | V5.1 要素 | 同步方式 | 排除 |
|----|----------|---------|------|
| 🧠 MEMORY | MEMORY.md + USER.md | scp 直接复制 | — |
| 💡 RULE-Skills | `~/.hermes/skills/` | rsync 补齐缺失 | `huawei-hi2`, `zte-li`, `playwright-cli-openclaw` |
| 📚 RULE-Knowledge | `~/knowledge/` | rsync 全量刷新（--delete） | `li/`, `hi2/`, `secrets/`, `OWLS_*`, `articles_baidu/`, `ima-sync/` |
| ⚙️ Config | `~/.hermes/config.yaml` | 各自独立维护 | 不做自动 merge |

### 触发时机

- 首次部署新远程实例时
- 本地 Knowledge 有重大更新后
- 用户主动要求同步

### 详细命令

参见 `hermes-evolution-mechanism` skill 下的 `references/multi-instance-sync.md`。

### 安全原则

- LI 数据（hi2/、li/）绝对禁止同步到云端
- 密钥/凭证目录（secrets/）不同步
- Config 不做自动 merge（两地平台/通道差异大）
