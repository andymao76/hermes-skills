---
name: hermes-evolution-mechanism
version: 1.0.0
description: Hermes Agent 进化机制 — 将 Hermes 从聊天工具进化为会工作、会记录、会总结、会复用、会自我优化的个人 AI 操作系统
tags: [hermes, knowledge, skill, evolution, workflow]
triggers:
  - 进化
  - knowledge
  - 知识沉淀
  - skill 沉淀
  - 经验总结
---

# Hermes Agent 进化机制

## 核心理念

> 每解决一次问题，都要让 Hermes 变得更聪明一点。

## 进化闭环

```
问题输入 → 分析与执行 → 解决方案 → 经验总结 → 写入 Knowledge → 提炼 Skill → 未来自动复用
```

## 知识库结构

```text
~/knowledge/
├── _system/              # 系统级配置
│   ├── project_status.yaml
│   ├── agent_rules.md
│   └── evolution_log.md
├── worklog/daily/        # 每日工作日志
├── skills/               # 技能经验沉淀
│   ├── hermes/
│   ├── linux/
│   ├── bigdata/
│   ├── telecom/
│   ├── li-hi2/
│   └── troubleshooting/
├── projects/             # 项目经验
├── bigdata/              # 大数据组件知识
├── telecom/              # 电信领域知识
└── inbox/                # 移动端快速输入
    ├── feishu/
    ├── whatsapp/
    └── quick_notes/
```

## 沉淀规则

### 1. 故障排查类
- **触发**：Linux/Hermes/MCP/Bridge/Hadoop/Kafka/Flink/Hive/HBase/GP/Wireshark 故障
- **路径**：`~/knowledge/skills/troubleshooting/`
- **命名**：`YYYYMMDD_问题关键词_fix.md`

### 2. 运维流程类
- **触发**：巡检脚本、启停服务、日志分析、数据导出、健康检查
- **路径**：`~/knowledge/skills/bigdata/` `linux/` `hermes/`

### 3. 项目经验类
- **触发**：项目跟进、客户问题、状态更新、会议纪要、风险总结
- **路径**：`~/knowledge/projects/项目名/`
- **同步更新**：`~/knowledge/_system/project_status.yaml`

## Skill 标准模板

```markdown
# Skill: 问题或能力名称

## 适用场景
说明这个 Skill 适合解决什么问题。

## 典型症状
- 报错信息 1
- 报错信息 2

## 根因分析
总结常见原因。

## 处理步骤
### 1. 检查状态
### 2. 定位问题
### 3. 修复操作

## 验证方法
验证命令

## 注意事项
- 风险 1
- 风险 2

## 可复用经验
一句话总结以后如何快速判断。

## 标签
#hermes #linux #bigdata #troubleshooting
```

## 移动端输入分类

| 类型 | 示例 | 保存路径 |
|------|------|----------|
| 临时想法 | `记录：今天发现 Kafka ISR 异常` | `inbox/quick_notes/YYYY-MM-DD.md` |
| 故障经验 | `经验：Flink 8081 refused 先查 Yarn` | `skills/bigdata/flink/` |
| 项目进展 | `项目：Project_A 今天完成客户问题跟进` | `projects/project_a/worklog.md` |

## UI 分工

| UI | 定位 | 用途 |
|----|------|------|
| Open WebUI | 日常入口 | 手机/Mac 访问、日常问答、知识库查询 |
| Hermes TUI | 实时驾驶舱 | 运维排障、MCP 调试、Skill 开发 |
| Dashboard | 系统指挥中心 | 总体状态、Gateway、Session/Memory/Skill |
| CLI | 底层发动机 | 脚本调用、后台任务、SSH 环境 |

## 周期性优化

### 每日
- 整理 `inbox/` 归档到 `worklog/` `skills/` `projects/`
- 输出：`~/knowledge/worklog/daily/YYYY-MM-DD.md`

### 每周
- 执行 `hermes curator`
- 合并重复 Skill、删除过期内容、修正分类、提炼高频经验
- 输出：`~/knowledge/_system/evolution_log.md`

### 每月
- 生成能力报告：`~/knowledge/_system/monthly_evolution_report_YYYY-MM.md`
- 内容：新增 Skill 数量、高价值经验、常用领域、待补强能力

## 项目状态中心

每次涉及项目任务时，优先读取 `~/knowledge/_system/project_status.yaml`：

```yaml
projects:
  hermes_second_brain:
    priority: highest
    status: active
    next_action: "完善 Knowledge 和 Skill 自动沉淀机制"
  project_a:
    priority: highest
    status: active
    next_action: "项目日常跟进"
    customer: "Customer_A"
```

## 进化优先级

### P0 立即执行
- 建立 Knowledge 标准目录 ✅
- 所有排错过程转为 Skill
- 完善 project_status.yaml
- 建立 daily worklog

### P1 短期优化
- Open WebUI 统一入口
- TUI 运维驾驶舱
- Dashboard 状态中心
- GitHub MCP 管理 Skill

### P2 中期优化
- Feishu 自动归档
- WhatsApp 快速记录
- Apple Notes 同步
- Curator 周期整理

### P3 长期进化
- Agent Team（运维/知识/文档/项目/代码）
- 自动巡检/报告/学习/清理 Agent

## 成功标准

- [ ] 新问题能自动参考历史经验
- [ ] 相同故障不再重复分析
- [ ] 每次排错后自动生成 Skill
- [ ] 项目状态可以自动延续
- [ ] 手机输入可以自动进入 Knowledge
- [ ] Dashboard 可查看整体健康状态
- [ ] TUI 可调试执行细节
- [ ] Open WebUI 可作为统一入口

## 参考知识库（references/）

本 Skill 附带以下参考资料，按需查阅：

| 文件 | 内容 | 触发场景 |
|------|------|----------|
| `references/mining-malware-cleanup.md` | 挖矿木马排查与清理手册 | 服务器CPU异常、安全审计 |
| `references/tencent-cloud-mcp.md` | 腾讯云 MCP Server 家族 | 用户需要AI管理腾讯云资源 |
| `references/ida-pro-mcp.md` | IDA Pro MCP Server | 逆向工程、二进制分析 |
| `references/multi-instance-sync.md` | 多 Hermes 实例同步（本地↔腾讯云）— 含 LI/OWLS 内容排除规则 | 需要对比/同步两台机器上的技能、知识库、配置 |
| `references/multi-instance-mcp-unification.md` | 多实例 MCP 服务器统一方法 | 两边运行不同 MCP 工具集，需要合并 |
| `references/cross-platform-migration.md` | Hermes 跨平台迁移（Linux↔Windows↔macOS） | 需要迁移 Hermes 到另一台机器或另一个 OS |
| `references/skill-lifecycle.md` | Skill 全生命周期管理：创建→测试→验证→维护→归档，含三阶验证模型 | 需要创建/修改/评估 skill 时加载 |

## 关联技能

- **knowledge-privacy-policy** — 知识分层隔离策略。沉淀 Skill 和写入知识库时，项目名、客户名必须脱敏处理。详见 RULE6。

---

> **最终目标**：Hermes 不只是回答问题，而是持续积累用户的经验体系，并逐步形成个人专属 AI 运维专家。