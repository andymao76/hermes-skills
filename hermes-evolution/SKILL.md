---
name: hermes-evolution
description: Hermes Agent 进化机制 — 知识库结构、Skill 沉淀规则、自动归档流程
tags: [hermes, knowledge, skill, evolution]
---

# Hermes Agent 进化机制

## 核心闭环

```
问题输入 → 分析执行 → 解决方案 → 经验总结 → 写入 Knowledge → 提炼 Skill → 未来复用
```

## 目录边界

| 目录 | 用途 | 内容类型 |
|:---|:---|:---|
| `~/.hermes/skills/` | Hermes 内置 Skill | 可被 skill_view 调用的操作手册 |
| `~/knowledge/` | 个人知识库 | 文档、笔记、项目资料、工作日志 |

**原则：** Skill 是"怎么做"，Knowledge 是"做了什么"。

## Knowledge 目录结构

```
~/knowledge/
├── _system/              # 系统配置
│   ├── project_status.yaml
│   ├── agent_rules.md
│   └── evolution_log.md
├── worklog/              # 工作日志
│   └── daily/YYYY-MM-DD.md
├── skills/               # 领域技能文档
│   ├── hermes/
│   ├── linux/
│   ├── bigdata/
│   ├── telecom/
│   ├── li-hi2/
│   └── troubleshooting/
├── projects/             # 项目资料
│   ├── a1_pc_project/
│   ├── hermes_second_brain/
│   ├── li_decoder_project/
│   └── us_visa_project/
├── bigdata/              # 大数据组件
│   ├── hdfs/yarn/hive/hbase/kafka/flink/greenplum/ambari/
├── telecom/              # 电信领域
│   ├── core_network/sip_rtp/lawful_interception/wireshark/
└── inbox/                # 收件箱
    ├── feishu/whatsapp/quick_notes/
```

## 沉淀规则

### 1. 故障排查 → Skill

触发：Linux/Hermes/MCP/大数据/电信故障

输出：`~/.hermes/skills/` 下创建 Skill 文件

命名：`YYYYMMDD_问题关键词_fix.md`

### 2. 运维流程 → Skill

触发：巡检/启停/日志分析/数据导出

输出：`~/.hermes/skills/` 对应领域目录

### 3. 项目经验 → Knowledge

触发：项目跟进/客户问题/会议纪要

输出：`~/knowledge/projects/项目名/`

同步更新：`~/knowledge/_system/project_status.yaml`

### 4. 手机输入自动分类

| 前缀/关键词 | 归档位置 |
|:---|:---|
| "记录：" / 临时想法 | `~/knowledge/inbox/quick_notes/YYYY-MM-DD.md` |
| "经验：" / 故障经验 | `~/knowledge/skills/对应领域/` |
| "项目：" / 项目进展 | `~/knowledge/projects/项目名/worklog.md` |

**注意：** 用户可能不加前缀，Hermes 需自动判断意图。

## Skill 标准模板

```markdown
# Skill: 问题名称

## 适用场景
## 典型症状
## 根因分析
## 处理步骤
## 验证方法
## 注意事项
## 可复用经验
## 标签
```

## 周期性任务

### 每日（cron job）
- 扫描当天 session
- 提取关键经验
- 写入 `~/knowledge/worklog/daily/YYYY-MM-DD.md`

### 每周
- 运行 `hermes curator`
- 合并重复 Skill
- 更新项目状态

### 每月
- 生成能力报告
- 统计新增 Skill 数量
- 分析最常用知识领域

## 进化成功标准

- [ ] 新问题能自动参考历史经验
- [ ] 相同故障不再重复分析
- [ ] 每次排错后自动生成 Skill
- [ ] 项目状态可以自动延续
- [ ] 手机输入可以自动进入 Knowledge