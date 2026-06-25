# 从本地文件学习→知识笔记（DOCX / PDF / TXT 等）

当用户说「学习这个文件」「把这个整理到知识库」，且内容来自本地文件而非 URL/粘贴文本时，走以下工作流。

## 完整流程

```
1. 提取文件内容（根据文件类型选择工具）
       ↓
2. 读取知识库中已有的相关笔记
       ↓
3. 判断是新增还是补充（避免重复）
       ↓
4. 写入结构化笔记（YAML frontmatter + cross-links）
       ↓
5. 双向交叉引用（patch 已有笔记补充反向链接）
       ↓
6. enzyme refresh
       ↓
7. 验证文件已写入
```

## 第1步：提取文件内容

### DOCX 文件（python-docx，推荐）

```bash
python3 -c "
from docx import Document
doc = Document('/path/to/file.docx')
for i, para in enumerate(doc.paragraphs):
    if para.text.strip():
        print(f'[{para.style.name}] {para.text}')
"
```

**优点**：保留段落样式（Heading 1 / First Paragraph / Source Code 等），能清晰看出文档结构。
**依赖**：`pip install python-docx`（通常已安装）

### PDF 文件

参见 `ocr-and-documents` skill：文本型 PDF 用 pymupdf，扫描件用 marker-pdf。

### TXT / Markdown

直接 `read_file` 读取即可。

## 第2步：检查已有笔记

在写入前，先扫描知识库中相关主题的已有内容：

```bash
# 方法一：搜索文件
search_files(pattern="*关键词*", path="~/knowledge/", target="files")

# 方法二：搜索内容
search_files(pattern="关键词", path="~/knowledge/research/", target="content")
```

**原则**：优先补充已有笔记（patch），不新建孤立笔记。只有当内容覆盖了已有笔记未触及的新主题时才新建。

## 第3步：判断新增还是补充

| 情况 | 操作 |
|------|------|
| 内容与某篇已有笔记高度重合 | 用 `==` 追加新章节到该笔记末尾 |
| 内容是新方向，无已有笔记覆盖 | 新建笔记 |
| 内容与已有笔记部分重叠 | 新建笔记 + 在相关段落写 `[[已有笔记]]` 引用 |

**避免笔记重复**：同一概念不要分到 2+ 个独立笔记里。

## 第4步：写入笔记

### YAML frontmatter 标准格式（不要重复字段）

```yaml
---
title: <中文标题>
tags: [<标签1>, <标签2>]
created: <YYYY-MM-DD>
source: <原始文件路径>
---
```

⚠️ **常见错误**：不要写两个 `tags:` 字段（YAML 只保留最后一个）。一次性写对。

### wikilinks 交叉关联

在笔记开头或结尾写：

```markdown
## 关联笔记

- [[feishu-lark-connection-solutions]] — 上一级连接方案总览
- [[已有笔记2]] — 补充说明
```

## 第5步：双向交叉引用

**写完新笔记后，必须 patch 已有笔记添加反向链接**，否则 Obsidian 图谱无法形成双向网络：

```python
# 使用 patch 工具为已有笔记添加反向链接
patch(
  path="/home/andymao/knowledge/research/已有关联笔记.md",
  old_string="## 关联笔记",
  new_string="## 关联笔记\n\n- [[新笔记]]\n"
)
```

**为什么必须做**：只有正向链接，Obsidian 图谱显示的是单向箭头，用户无法通过反向链接面板发现这篇新笔记。

## 第6步：索引更新

```bash
cd /home/andymao/knowledge && enzyme refresh
```

## 第7步：验证

```bash
wc -l /home/andymao/knowledge/<目录>/<文件名>.md
ls -lh /home/andymao/knowledge/<目录>/<文件名>.md
```

确认行数和文件大小合理。

## 与 URL/Web 工作流的区别

| 步骤 | URL/粘贴内容 | 本地文件 |
|------|-------------|---------|
| 提取方式 | web_extract / 浏览器 | python-docx / pymupdf |
| 结构识别 | HTTP 响应直接可用 | 需遍历 paragraphs |
| 已有关联检查 | 可选 | **必须**做（用户说「补充到相关知识库」） |
| 反向链接 | 可选 | **必须**做（因为文件常是对已有知识的补充） |
