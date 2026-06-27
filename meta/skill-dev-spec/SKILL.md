---
name: skill-dev-spec
description: Use when creating a new skill from scratch, editing an existing skill, or reviewing skill quality against the official Agent Skills specification. Reference for format, YAML frontmatter, directory structure, progressive disclosure, and validation.
user-invocable: true
metadata:
  version: "1.1.0"
  sources:
    - "https://agentskills.io — Official Agent Skills spec"
    - "/home/andymao/tempfile/skill.md — Anthropic Skill 开发规范"
    - "https://github.com/agentskills/agentskills — GitHub repo"
---

# Skill 开发规范

参考官方 [Agent Skills Specification](https://agentskills.io)（CC-BY-4.0 / Apache 2.0 许可）。

Three iron laws: **简洁为王**、**渐进披露**、**测试驱动**。

---

## 什么是 Skill

一个 Skill 就是一个目录，包含 `SKILL.md` 文件（必需）和可选的支持文件：

```
skill-name/
├── SKILL.md            # 必需：YAML frontmatter + 指令正文
├── scripts/            # 可选：可执行代码
├── references/         # 可选：按需加载的参考文档
├── assets/             # 可选：模板、图片、数据文件
└── ...                 # 其他文件或目录
```

### Skill 是什么 / 不是什么

| Skill 是 | Skill 不是 |
|:---------|:-----------|
| 可复用的技术、模式、工具参考 | 一次性问题解决记录 |
| Agent 的能力扩展包 | 项目特定约定（放 CLAUDE.md） |
| 结构化的流程文档 | 机械约束（用正则/验证器更好） |
| 跨平台可移植的知识 | 某个库的完整 API 文档搬运 |

---

## 三种 Skill 类型

| 类型 | 说明 | 示例 |
|:----|:-----|:-----|
| **Technique** | 有具体步骤的方法论 | systematic-debugging |
| **Pattern** | 思维模型/思考方式 | clean-code |
| **Reference** | API 文档、语法指南 | pptxgenjs.md |

---

## SKILL.md 格式

### YAML Frontmatter（官方 Agent Skills 规范）

```yaml
---
name: skill-name              # 必需：≤64字符，小写+数字+连字符
description: Use when ...      # 必需：≤1024字符，描述做什么和何时用
license: Apache-2.0            # 可选：许可协议
compatibility: Requires git    # 可选：环境要求（≤500字符）
metadata:                      # 可选：任意键值对
  author: example-org
  version: "1.0"
allowed-tools: "Read, Write"   # 可选（实验性）：预批准工具
---
```

**name 规则：**
- 仅小写字母(a-z)、数字(0-9)、连字符(-)
- 不以连字符开头或结尾，无连续连字符
- **必须与父目录名一致**
- 不含保留词 `anthropic`/`claude`

**description 铁律：**
- 以 `Use when...` 开头
- 描述**触发条件**，不是工作流总结
- 包含具体关键词（症状、工具名、场景）
- 第三人称，尽量500字符以内

```
# ✅ 正确
description: Extracts text and tables from PDF files, fills PDF forms.
Use when working with PDF documents or when the user mentions PDFs.

# ❌ 错误：总结了工作流（Agent 可能跳过正文）
description: Use for TDD — write test first, watch it fail, write minimal code

# ❌ 错误：太抽象
description: For PDFs.
```

---

## 目录结构规范

### 文件组织原则

- **扁平命名空间** — 所有 Skill 处于同一可搜索命名空间
- **引用链保持一层深度**（SKILL.md → 引用文件，不嵌套）
- **引用文件超100行**，顶部加目录
- **所有路径使用正斜杠**（`reference/guide.md`）

### 何时拆分文件

- 重型参考文档（100+行）→ `references/`
- 可复用工具代码 → `scripts/`
- 模板文件 → `assets/`

### 何时保持内联

- 原则和概念
- 短代码片段（<50行）
- 其他所有内容

---

## 渐进式披露（三级加载）

| 层级 | 内容 | Token | 加载时机 |
|:----|:-----|:------|:---------|
| 元数据层 | name + description | ~100/skill | 启动时预加载 |
| 指令层 | SKILL.md 正文 | <5000 tokens, <500行 | Skill 触发时 |
| 资源层 | scripts/references/assets | 0 | 按需加载 |

### Token 预算

| Skill 类型 | 目标字数 | SKILL.md 行数 |
|:-----------|:--------|:-------------|
| 入门/频繁加载 | <150 词 | <50 行 |
| 常用 Skill | <200 词 | <100 行 |
| 其他 Skill | <500 词 | <500 行 |

### 压缩技巧

1. **Move details to --help** — 参数列表引用工具帮助
2. **Use cross-references** — 一句话引用已有 skill
3. **Compress examples** — 精简到核心模式

---

## 正文结构推荐

```
## Overview
核心原则，1-2句话

## When to Use
何时使用 / 何时不用

## Core Pattern / Workflow
核心模式，Before/After 对比

## Quick Reference
表格或要点，便于快速扫描

## Implementation
简单代码内联；重型参考链接到文件

## Common Mistakes / Anti-Patterns
常见错误 + 修复方法
```

### 指导自由度

| 自由度 | 适用场景 | 示例 |
|:------|:---------|:-----|
| 高（文本指令） | 多种方法有效 | 代码审查、设计评审 |
| 中（伪代码/参数化脚本） | 有首选模式 | 报告生成、数据处理 |
| 低（具体脚本） | 操作脆弱，一致性关键 | 数据库迁移、签名流程 |

---

## 测试驱动开发（TDD for Skills）

**铁律：没有失败的测试，就没有 Skill。**

### RED — 建立基线
1. 不用 Skill 完成任务，记录反复提供的信息
2. 设计 3+ 压力场景（时间压力、沉没成本、权威压力）
3. 不用 Skill 运行场景，记录 Agent 行为
4. 识别失败模式和合理化借口

### GREEN — 写最小 Skill
1. 针对 RED 发现的失败点写 Skill
2. 不为假设情况添加额外内容
3. 有 Skill 验证场景，确认 Agent 遵守

### REFACTOR — 堵漏洞
1. 识别新合理化借口
2. 添加显式反驳
3. 构建合理化借口表格
4. 创建红旗列表
5. 反复测试直到无懈可击

### 各类 Skill 测试方法

| Skill 类型 | 测试方法 | 成功标准 |
|:-----------|:---------|:---------|
| 纪律型（规则/要求） | 学术问题 + 压力场景 | 最大压力下遵守规则 |
| 技巧型（操作指南） | 应用场景 + 变体 | 成功应用到新场景 |
| 模式型（思维模型） | 识别场景 + 反例 | 正确判断何时用/不用 |
| 参考型（文档/API） | 检索 + 应用 + 覆盖率 | 找到并正确使用参考信息 |

---

## 引用方式

```
# ✅ 正确
REQUIRED SUB-SKILL: Use superpowers:test-driven-development
REQUIRED BACKGROUND: You MUST understand superpowers:systematic-debugging

# ❌ 错误：模糊引用
See skills/testing/test-driven-development

# ❌ 错误：@强制加载（消耗200k+ context）
@skills/testing/test-driven-development/SKILL.md
```

---

## 代码与脚本规范

1. **Solve, don't punt** — 显式处理错误，不推给 Agent
2. **禁止魔法数字** — 所有常量加注释
3. **显式声明依赖** — 不假设已安装
4. **MCP 工具全限定名** — `ServerName:tool_name`

---

## 反模式清单

| 反模式 | 为什么糟糕 | 正确做法 |
|:-------|:-----------|:---------|
| 叙事式示例 | 太具体，不可复用 | 提炼为通用模式 |
| 多语言示例 | 质量平庸，维护负担 | 一个优秀示例即可 |
| 通用标签（step1, helper2） | 无语义含义 | 描述性名称 |
| Windows 风格路径 | 跨平台不兼容 | 始终用正斜杠 |
| 提供过多选项 | 让人困惑 | 给默认方案 + 逃生出口 |
| 时间敏感信息 | 会过时变错 | "Current method" + "Old patterns" |
| 深层嵌套引用 | 信息不完整 | 保持一层深度 |
| 脚本推卸错误处理 | Agent 接收不友好 | 显式处理错误 |
| 魔法数字 | 无法理解原因 | 所有常量加注释 |
| 假设工具已安装 | 运行时失败 | 显式声明依赖 |

---

## 验证工具

官方提供 `skills-ref` 验证工具：

```bash
# 安装 (Python 3.14+)
pip install -e /path/to/agentskills/skills-ref

# 验证 Skill
skills-ref validate path/to/skill

# 读取 Skill 属性 (JSON)
skills-ref read-properties path/to/skill

# 生成 <available_skills> XML
skills-ref to-prompt path/to/skill-a path/to/skill-b
```

### 验证检查项
- YAML frontmatter 格式正确
- name 与父目录名一致
- name 命名规则合规（小写+数字+连字符）
- description 非空

---

## 运维 Skill 开发模式

运维 Skill（监控/大数据/LI平台/网关）有独特的结构要求：命令必须可复制执行、必须标注预期输出、危险操作必须加警告、每步必须有验证。

详见 `references/ops-skill-patterns.md`：
- Grafana+Prometheus 监控栈 — Docker部署、自定义exporter、端口规范、scrape配置模板
- OWLS LI 平台 — 数据流检查、API模板、设控排查四步法
- 大数据 HDP — 组件巡检结构、排障表模板
- ZTLIG 网关 — 进程架构、日志grep模板、VNEID映射
- 通用质量规则 — 命令规范、涉密隔离、反模式

## 参考链接

- **官网**: https://agentskills.io
- **规范源码**: https://github.com/agentskills/agentskills
- **示例 Skill**: https://github.com/anthropics/skills
- **Discord**: https://discord.gg/MKPE9g8aUy
- **运维 Skill 编写规范**: `references/ops-skill-rules.md` — Grafana+Prometheus/OWLS/大数据HDP/ZTLIG 四类系统的 Skill 结构模板和质量要求
