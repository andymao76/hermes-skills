---
name: learning-content-to-knowledge-base
title: 学习内容入库工作流
description: 用户分享学习材料（技术文档、规范、教程、报文等）时，解析、结构化摘要、逐段增量校对、最终写入知识库的标准化工作流。涵盖首次解析、入库创建、增量 patch 更新三个阶段。
category: knowledge
tags:
  - learning
  - knowledge-base
  - documentation
  - vendor-docs
  - bilingual
---

# 学习内容入库工作流

用户分享学习材料时，将其解析、结构化并写入知识库的标准化工作流。支持逐段增量校对模式（shared-edit-correction pattern）。

## 变体 A：用户分享内容入库（默认）

用户发送「学习 [topic]」+ 原始内容 → 结构化摘要 → 写入知识库（见下方三阶段工作流）。

## 变体 B：从已知文件路径提取知识点

当用户提供一个已知文件路径（如 `/tmp/some-book.txt`），要求从特定章节提取知识时，使用以下模式：

### 步骤

1. **定位结构标记**：使用 `search_files(context=1, output_mode=content)` 搜索章节标题模式（如 `Chapter 1[2]`、`\fChapter` 等）
2. **确定章节边界**：搜索目标章节的起始位置，同时搜索相邻下一章节的起始位置，确定完整范围
3. **分块读取**：按章节边界使用 `read_file(offset=X, limit=Y)` 分块读取。大文件单次读取会被截断（>100K 字符），需逐步翻页
4. **持续翻页**：当输出显示 `"truncated": true` 且有 `"Use offset=Z to continue reading"` 提示时，继续读取后续内容
5. **合成输出**：将各章节内容整合为结构化 Markdown，含实用速查表、对比表、编码公式等

### 注意

- 大型文本文件（如 1MB+ 的教材）每次 read_file 最多返回 ~1000 行。需多次读取才能覆盖完整章节
- 文件内可能含 `\f`（分页符），搜索时注意转义或使用宽松模式
- 教材的章节标题格式可能不统一，搜索时可用多个模式备选

## 触发条件

用户消息以「学习 [topic]」开头，并附带了文档/规范/报文/对比表等原始内容。

## 工作流程

### 第 1 阶段：接收与解析

1. 用户发送「学习 [topic]」+ 原始内容
2. 首次回复：立即确认已收到，并提供结构化摘要（表格/列表/逐字节解析）
3. 摘要完成后，主动询问是否写入知识库

### 第 2 阶段：入库（用户确认后）

1. 搜索已有知识库内容，建立双向链接关联
2. 创建 Markdown 文件，包含 YAML frontmatter、结构化内容、双语并存、交叉链接
3. 写入适当目录：`~/knowledge/hi2/厂商对接/`、`~/knowledge/telecom/lawful_interception/` 等
4. 尝试 enzyme refresh

### 第 3 阶段：增量校对

用户可能逐段分享 Description → Syntax → Arguments → Status → Output → Examples，需逐段更新：

1. patch 前先 read_file 确认上下文，避免多处匹配
2. 保留原文措辞，不简化为替代描述
3. 用户逐字键入时耐心等待完整内容

## 输出格式

- 参数表：`| 参数 | M/O | 说明 |`（英文原文 + 中文）
- 元数据：来源、入库时间、分类、数据级别

## 注意事项

- patch 冲突时，用节标题 + 相邻行唯一上下文定位
- 标准接口文档标记 LEVEL 3

## Patch 操作进阶技巧

### 1. 唯一上下文匹配策略

当同一知识库笔记包含多个相同结构（如多个命令的状态码表都有 `| 0 | 成功 |`），`patch` 会报 `Found N matches` 错误。解决方法：

- 使用该状态码表所在章节的完整头作为上下文前缀，例如：
  ```
  #### 状态码\n\n| 码 | 含义 |
  ```
  而不是只匹配表内行。

### 2. Patch 意外吞噬章节标题的恢复

当 patch 的 `old_string` 过于宽泛时，可能意外替换掉相邻章节的标题行（例如 `#### lealist — 显示 LEA` 被吞掉变成裸文本）。恢复步骤：

1. 立即用 `read_file` 查看受影响区域
2. 找到丢失的标题出现的精确位置和周围文本
3. 用一个新的 patch（old_string 为被吞标题下方的文本，new_string 为重新插入的标题 + 该文本）修复
4. 只修复丢失的局部，不要尝试整体重构

典型场景：在一个 `### 7.9` 段落之后插入内容，patch 的 old_string 无意中匹配到 `### 7.8` 或 `### 8.0` 的标题行。

### 3. 长会话中 read_file 警告的处理

经过多次 patch 后，文件写入时可能提示：
```
was last read with offset/limit pagination (partial view). Re-read the whole file before overwriting it.
```

这只是一个警告，patch 仍然生效。在后续 patch 前用 `read_file path=... offset=1 limit=1000` 刷新文件缓存即可消除警告。

### 4. 结构修复后的后续操作

如果因为前面的 patch 不慎导致部分内容错位（如参数表或状态码表被截断），不要尝试用单个大 patch 一次修复。应：

1. 用 `read_file` 确认受影响的具体范围
2. 用多个小 patch 逐个修复，每次只修复一个小块
3. 修复完成后用 `read_file` 整体验证结构正确
