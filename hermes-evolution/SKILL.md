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

### 需要时：系统架构图输出

当需要输出/更新系统架构图时，从以下 8 个数据源采集运行时信息：

| # | 数据源 | 获取方式 | 用途 |
|---|--------|----------|------|
| 1 | Hermes 主配置 | `~/.hermes/config.yaml` | Provider/MCP/Plugin/Security 配置 |
| 2 | systemd 服务 | `systemctl --user list-units` | 运行时系统服务（Gateway/Bridge/CDP） |
| 3 | 端口监听 | `ss -tlnp` | 运行时端口状态 |
| 4 | 定时任务 | `~/.hermes/cron/jobs.json` | cron 任务清单 |
| 5 | 知识库结构 | `find ~/knowledge/ -maxdepth 2 -type d` | Obsidian Vault 目录层次 |
| 6 | MCP 服务详情 | `config.yaml` 中 `mcp_servers:` 段 | 每个 server 的命令/参数/env |
| 7 | 现有架构版本 | 扫描已有 `.svg`/`.html` 文件 | 版本号递增 |
| 8 | 技能列表 | `skills_list()` | 技能总数和分类 |

**采集顺序：** 系统信息 → config.yaml → systemd → 端口 → cron → 知识库 → skills → 版本检查

**布局参考（8 层架构，viewBox 1340×1120）：**
- 用户交互层: y=50~200（5-6 个平台）
- 核心引擎层: y=225~390（Gateway→Session→Router）
- LLM Provider 层: y=400~510（4-5 个模型）
- MCP 服务层: y=530~700（2 行）
- 技能层: y=720~890（按分类展示）
- 知识存储层: y=910~1030
- 图例: y=1060~1100

**数据流图（viewBox 1340×620）：**
- 入口 → Gateway → 模型路由器（菱形 4 分支）
- 分支: Codex CLI / Ollama(本地) / DeepSeek Pro / DeepSeek Flash
- 汇聚 → 知识库 → 结果整合

**安全标记规则：** LI 相关（Ollama/私有知识库）用玫瑰色边框 + 标注「数据不出本地」

**工具：** 使用 `architecture-diagram` skill（SVG HTML）生成，输出 `.html` + `.svg` 双文件。

## 技能库批量重构（Cross-Skill Rename/Refactor）

当底层组件、API、工具名称变更（如 Enzyme → Qdrant、旧 CLI 名 → 新名），需要跨所有 Skill 文件做系统化改名清理时，遵循以下流程。

### 触发条件

- 组件/API/binary 被重命名或废弃
- 配置项、环境变量、命令名变更
- 需要更新散布在多个 Skill 中的引用

### 执行步骤

1. **全量搜索定位**：用 `search_files()` 搜索目标名称（如 `enzyme`），`limit=50` 或更高，`file_glob=*.md`
2. **归类分析**：将每个命中文件分为三类：
   - **活跃引用**（需要改的代码路径、命令、配置说明、命令示例）
   - **历史说明**（如 "迁移过程日志" 或含 `已迁移`、`历史` 的段落）→ 通常无需修改
   - **知识库偏业务**（如 knowledge/ 下的学习笔记）→ 改为新名称引用
3. **按文件依次修改**：用 `patch` 替换每个活跃引用。改完一个标一个。
4. **验证零残留**：再次全量搜索旧名称，确认结果为 0。排除已确认的合理的残留（如历史说明、CHANGELOG 引用）
5. **检查 cron job**：如果被改组件有定时任务引用（如 `kb-index`），更新其脚本路径/描述

### 常见陷阱

- **代理环境干扰**：SOCKS/HTTP 代理可能导致新组件客户端连接失败。备选方案：用 curl REST API 替代 Python 客户端
- **cron output 残留**：cron 历史 output 日志可能含旧名称，但属历史记录无需清理
- **知识库文件**：`~/knowledge/` 下的笔记（非 skill）若有旧名称引用，确认是否需要更新。skill 必须更新，知识库笔记按业务需要决定
- **技能多词引用**：同一行可能有 `enzymes` / `memory` 这种多词引用，只替换旧词
- **全量搜索截断**：若搜索匹配过多（>50），用 `offset` 翻页或用更精确的 `file_glob` 缩小范围

### 参考案例

详细工作记录见 [references/enzyme-to-qdrant-migration.md](references/enzyme-to-qdrant-migration.md) — 含完整的搜索命令、修改清单、验证方法和跳过决策。未来同类任务可直接参考步骤流程。

## 进化成功标准

- [ ] 新问题能自动参考历史经验
- [ ] 相同故障不再重复分析
- [ ] 每次排错后自动生成 Skill
- [ ] 项目状态可以自动延续
- [ ] 手机输入可以自动进入 Knowledge