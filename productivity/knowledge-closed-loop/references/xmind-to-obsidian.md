# .Xmind → Obsidian Markdown 批量转换

## 背景

.xmind 文件本质是 ZIP 压缩包，内含 `content.json`（XMind 2020+ 格式）或 `content.xml`（XMind 8 格式）。需要提取思维导图层级结构并转为 Markdown 笔记存入知识库。

## 解析脚本

```python
import json, os, zipfile

XPATH = '/path/to/your.xmind'

def parse_content_json(data, lines, depth=0):
    if isinstance(data, list):
        for sheet in data:
            lines.append(f'## 画布: {sheet.get("title", "未命名")}\n')
            walk_json(sheet.get('rootTopic', {}), lines, 0)
    elif isinstance(data, dict):
        walk_json(data.get('rootTopic', data), lines, 0)

def walk_json(node, lines, depth):
    if not isinstance(node, dict):
        return
    title = node.get('title', '')
    if depth == 0 and not title:
        return
    if title:
        lines.append('  ' * depth + '- ' + title)
    note = node.get('note', '')
    if note:
        import re
        note_text = re.sub(r'<[^>]+>', '', note.get('plain', note.get('html', str(note))))
        if note_text.strip():
            lines.append('  ' * (depth + 1) + '  > ' + note_text.strip()[:300])
    labels = node.get('labels', [])
    if labels:
        lines.append('  ' * (depth + 1) + f'  标签: {", ".join(labels)}')
    for child_type in ['attached', 'detached', 'summaries']:
        for child in node.get('children', {}).get(child_type, []):
            walk_json(child, lines, depth + 1)
```

## 完整工作流

1. 遍历目录下所有 `.xmind` 文件
2. 用 `zipfile.ZipFile` 读取 `content.json`（优先）或 `content.xml`（回退）
3. 递归遍历 JSON 树，生成 Markdown 缩进列表
4. 添加 YAML frontmatter（title, tags, source, creator）
5. 写入知识库对应目录（如 `工作/项目/OWLS/{原文件名}.md`）
6. 执行 `enzyme_refresh()` 更新语义索引

## 注意事项

- 优先解析 `content.json`（XMind 2020+），`content.xml` 为 XMind 8 旧格式
- 节点折叠状态（branch: folded）保留在 JSON 中但不影响 Markdown 输出
- 图片/超链接等富媒体以文本引用方式保留
- 文件命名：保留原文件名，仅换扩展名
- 大文件批量处理时先验证 1-2 个样本
