# Enterprise Handbook Series — 知识库多卷手册写作规范

## 适用场景

当需要将一套体系化的多卷技术手册写入知识库时（如 Hermes Agent Enterprise Handbook Vol.01~12）。

## 目录结构与文件命名

新版采用**独立子目录**组织方式（v3.0+），取代旧版散列文件：

```
knowledge/<领域>/<手册名>-v<版本号>/
├── README.md                        # 卷索引（总入口 + 阅读建议）
├── Volume-01-<英文主题>.md           # 已交付卷 — 单文件直接存放
├── Volume-02-<英文主题>.md           # 已交付卷 — 单文件直接存放
├── Volume-03-<英文主题>/             # 待交付卷 — 子目录 + index.md 占位
│   └── index.md
├── Volume-04-<英文主题>/
│   └── index.md
└── ...
```

### 命名约定

| 类型 | 格式 | 示例 |
|------|------|------|
| 系列根目录 | `<手册名>-v<主版本号>` | `Hermes-Agent-Enterprise-Handbook-v3` |
| 已交付卷 | `Volume-NN-<英文主题>.md` | `Volume-01-Architecture.md` |
| 待交付卷（子目录） | `Volume-NN-<英文主题>/index.md` | `Volume-03-Conversation-Compression/index.md` |
| 系列索引 | `README.md` | 卷总目录 + 阅读建议（按角色推荐阅读顺序） |

**命名原则**：
- 根目录名不含 `Volume` 前缀（它是整个系列容器，不是某卷）
- Volume 编号两位填充（01, 02, ..., 12）
- 主题用英文连字符，首字母大写
  
### 与旧命名方案的对应

旧版（单文件散列于知识库根目录）：

```
knowledge/hermes/Hermes_Agent_<Topic>_V3.0.md
knowledge/hermes/Hermes_Agent_<Topic>_V3.0_Volume_02.md
```

新版（独立子目录 + 统一 Volume-NN 命名）：

```
knowledge/hermes/Hermes-Agent-Enterprise-Handbook-v3/Volume-01-Architecture.md
knowledge/hermes/Hermes-Agent-Enterprise-Handbook-v3/Volume-02-Memory-System.md
```

Volume 01 不再特殊处理为无后缀文件，统一按 `Volume-NN-<主题>.md` 命名。

## YAML Frontmatter 规范

### 已交付卷（完整内容）

```yaml
---
title: Hermes Agent Enterprise Handbook Volume 02 — Enterprise Memory System
version: v3.0
author: Andy Mao AI Engineering Notes
tags:
  - hermes                    # 领域
  - architecture              # 范围
  - enterprise                # 级别
  - memory-engine             # 卷特有主题标签
created: 2026-07-01           # 写入日期
aliases:
  - Hermes Memory Engine V3
  - Enterprise Memory System V3
relations:
  - Hermes_Agent_Enterprise_Architecture_V3.0    # 链接到 Volume 01
---
```

### 待交付卷（占位 index.md）

```yaml
---
tags:
  - hermes/handbook/v03          # 层级标签：领域/系列/卷号
  - conversation/compression     # 主题标签
status: placeholder              # 关键标记
---

# Volume 03: Conversation Compression Engine

> 简短描述

## 待交付内容

- [ ] 待实现项 1
- [ ] 待实现项 2
- [ ] 待实现项 3
```

**待交付卷 frontmatter 要点**：
- `status: placeholder` 是必需字段，标记卷未完成
- `tags` 使用分层格式 `领域/系列/卷号` + `主题/子主题`
- 正文使用无序待办列表（`- [ ]`）列出预期内容
- 标题行使用 `# Volume NN: 主题` 格式

### 标签体系

| 层级 | 示例 | 说明 |
|------|------|------|
| 领域 | hermes, telecom, devops | 一级分类 |
| 范围 | architecture, enterprise, production | 文档级别 |
| 卷主题 | memory-engine, compression, memory | 本卷核心内容 |
| 分层标签（新版） | hermes/handbook/v03 | 领域/系列/卷号 |

### relations 字段

用于链接系列内的其他卷。每个条目是文件名（不含 `.md` 扩展名）。Volume 01 的 relations 列出所有后续卷，后续卷的 relations 至少指向 Volume 01。

## 正文中的交叉引用

使用 Obsidian wikilink 语法：

```markdown
详见 [[Hermes_Agent_Enterprise_Architecture_V3.0]] — Volume 01: 架构总览
参见 [[Hermes_Agent_Model_Routing_Rules_V1.0]] — 模型路由规则
```

## 文档结构规范

每卷应包含：

1. **目录** — Markdown 序号列表 + 锚点跳转
2. **16 章标准结构** — 从 Overview 到 Checklist
3. **Checklist 章节** — 末尾用 `- [x]` / `- [ ]` 标记完成状态
4. **下一卷预告** — 预告后续内容，保持系列连贯性
5. **相关链接** — 尾部列出所有关联文档的 wikilink

## 内容组织原则

- **表格优先**：结构化数据用表格，不用散文段落
- **ASCII 流程图**：架构图用 etc. ASCII 图，不依赖外部渲染
- **代码块**：YAML 示例、代码、配置用 fenced code block
- **SOP 嵌入**：每个功能模块后直接嵌入 SOP（操作步骤/参数表）
- **双语术语**：关键技术术语保留英文（括号中文注释），如 Memory Engine（记忆引擎）

## 实际示例

参见知识库中的实际文件：

| 卷 | 路径 |
|----|------|
| Vol 01 | `~/knowledge/hermes/Hermes-Agent-Enterprise-Handbook-v3/Volume-01-Architecture.md` |
| Vol 02 | `~/knowledge/hermes/Hermes-Agent-Enterprise-Handbook-v3/Volume-02-Memory-System.md` |
| Vol 03 占位 | `~/knowledge/hermes/Hermes-Agent-Enterprise-Handbook-v3/Volume-03-Conversation-Compression/index.md` |
| 系列索引 | `~/knowledge/hermes/Hermes-Agent-Enterprise-Handbook-v3/README.md` |

## README 索引文件规范

README.md 作为整个手册系列的卷索引，应包含：

1. **YAML frontmatter** — `tags: [hermes/handbook, enterprise/architecture, index]` + `status: in_progress`
2. **卷目录表格** — 编号 | 卷名 | 状态（✅已交付/📝待交付）| 说明
3. **目录结构** — 代码块展示物理目录树
4. **阅读建议** — 按角色推荐阅读路径（运维/架构师、开发者、管理者）
5. **贡献说明** — 简短的维护策略

## 卷索引占位index.md文件创建工作流

创建手册系列目录结构时遵循以下步骤：

1. **创建根目录** — `knowledge/<领域>/<手册名>-v<版本号>/`
2. **写入 README.md** — 总索引（含卷目录表格 + 阅读建议）
3. **移入已交付卷** — 将已有单文件更名为 `Volume-NN-<主题>.md` 移入
4. **为未交付卷创建子目录 + index.md** — 每个子目录一个占位文件：
   - frontmatter: `tags` + `status: placeholder`
   - 正文: `# Volume NN: 主题` + 一句话描述 + `- [ ]` 待办列表
5. **验证目录结构** — `ls -la` 确认 README + Volume 文件 + Volume 子目录均存在
6. **更新 memory** — 记录手册系列根目录位置和已交付/待交付卷数
