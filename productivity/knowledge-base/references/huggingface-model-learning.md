# HuggingFace 模型学习 → 知识库笔记 工作流

当用户说「去学习某个 HuggingFace 模型页面」时，执行以下闭环：

## 触发词

- "去 https://huggingface.co/... 学习"
- "学习这个模型"
- "了解一下这个模型"

## 工作流（4 步）

### 1. 提取页面内容

```python
web_extract(urls=["https://huggingface.co/<org>/<model-name>"])
```

首次提取若被截断（页面 >5000 字符），再次提取一次以获取剩余内容。HF 页面通常很长，可能需要 2 次提取。

### 2. 结构化呈现（屏幕输出）

用表格+分类标题而非段落呈现。标准分类：

- **模型定位**：全称、开发者、参数量、架构、基座、训练数据
- **核心差异**：与该模型家族其他成员的对比表
- **安装方式**：pip 命令
- **API 用法**：从简到繁分层展示（Pipeline → 带参数 → 底层 API）
- **关键参数速查表**：参数名 | 含义 | 典型值
- **常见场景组合**：场景 | 参数
- **资源消耗**：精度 | 显存 | 适用 GPU
- **全系列对比**（如适用）：各变体对比表
- **总结**：一句话核心结论

### 3. 询问是否保存到知识库

结构呈现完后问"是否要将这些内容整理后写入知识库？"，不要默认写入。

### 4. 写入知识库笔记

用户同意后，写入 `~/knowledge/LLM_API相关/<model-name>_<描述>.md`：

**必须包含的 YAML frontmatter：**
```yaml
---
title: <模型中文描述>
aliases:
  - <英文名>
  - <缩写>
tags:
  - AI模型
  - <领域标签>
created: <YYYY-MM-DD>
source: <HuggingFace URL>
---
```

**内容规范：**
- Markdown 标题层级清晰（最多三级 ###）
- 数据优先用表格
- 代码块标注语言类型
- 双向链接（wikilinks）链接到 vault 中已有笔记
- 底部放「相关链接」节，包含 HF 页面、GitHub 仓库等原始链接

**写完后的收尾：**
```python
enzyme_refresh()
```

## 目录选择

| 模型类型 | 保存目录 | 示例 |
|---------|---------|------|
| LLM/推理/语音/视觉模型 | `~/knowledge/LLM_API相关/` | whisper-large-v3-turbo_语音转文字模型.md |
| Agent 框架 | `~/knowledge/AI_Agent相关/` | — |
| 通信协议/标准 | `~/knowledge/research/` | — |

## 笔记格式示例

参见已生成的良好笔记：
- `~/knowledge/LLM_API相关/whisper-large-v3-turbo_语音转文字模型.md`

## 易错点

- ❌ 不要只口头总结不写文件
- ❌ 不要等用户催促才问「是否要保存」
- ❌ 文件名不要用空格，用下划线
- ❌ 不要在 frontmatter 中漏掉 `source` 字段
- ❌ HF 页面一次 web_extract 可能被截断，注意检查内容完整性
