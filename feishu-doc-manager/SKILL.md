---
name: feishu-doc-manager
description: 飞书文档管理器 — 将 Markdown 内容发布到飞书文档，自动渲染格式。
  Markdown 表格转换、权限管理、批量写入。
  Skillhub 导入版，依赖 Maton CLI 和 MATON_API_KEY。
category: productivity
---

# 飞书文档管理器 | Feishu Doc Manager

Seamlessly publish Markdown content to Feishu Docs with automatic formatting.
解决核心痛点：Markdown 表格转换、权限管理、批量写入。

## 解决的痛点

| 问题 | 解决方案 |
|------|----------|
| Markdown 表格无法渲染 | 自动转换为格式化列表 |
| 权限管理复杂 | 一键协作者管理 |
| 长内容 400 错误 | 自动分段写入 |
| 格式不一致 | write/append 自动渲染 |

## 核心功能

### 智能 Markdown 发布
- **Auto-render**: `write`/`append` actions automatically render Markdown
- **Table handling**: Tables auto-converted to formatted lists
- **Syntax support**: Headers, lists, bold, italic, code, quotes

### 权限管理
- Add/remove collaborators
- Update permission levels (view/edit/full_access)
- List current permissions

### 文档操作
- Create new documents
- Write full content with Markdown
- Append to existing documents
- Update/delete specific blocks

## 所需权限

- `docx:document`
- `docx:document:write_only`
- `docs:permission.member`

## 依赖

需要 `maton` CLI 和 `MATON_API_KEY` 环境变量。

```bash
maton login                          # 登录 Maton
export MATON_API_KEY="YOUR_API_KEY"  # 设置 API Key
```

来自 skillhub，作者：Shuai-DaiDai
