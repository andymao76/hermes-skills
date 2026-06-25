---
name: ima-kb-api
description: 腾讯 ima 知识库 HTTP API 集成 — 文件上传/网页导入/笔记管理/查询浏览
tags: [ima, knowledge-base, api, upload, search, tencent]
---

# IMA 知识库 API 集成

API base path: `openapi/wiki/v1`

完整 API 参考见 `references/api.md`。

## 接口决策表

| 用户意图 | 调用接口 |
| --------- | -------- |
| 上传文件到知识库 | `check_repeated_names` → `create_media` → COS Upload → `add_knowledge` |
| 上传文件到知识库的某个文件夹 | 先定位文件夹 → 同上（`folder_id` 传入目标文件夹 ID） |
| 添加网页/微信文章到知识库 | `import_urls` |
| 添加笔记到知识库 | `add_knowledge`（`media_type=11`） |
| 添加 URL（文件型）到知识库 | `check_repeated_names` → 下载 → 走上传文件流程 |
| 检查文件名是否重复 | `check_repeated_names` |
| 获取知识库信息 | `get_knowledge_base` |
| 浏览知识库内容列表 | `get_knowledge_list` |
| 在知识库中搜索 | `search_knowledge` |
| 按关键词查找知识库 | `search_knowledge_base` |
| 查看所有知识库 | `search_knowledge_base`（`query: ""`） |
| 添加内容但未指定目标知识库 | `get_addable_knowledge_base_list` |
| 查看/导出原文 | `get_media_info` |

## 文件上传安全门

GATE 1: preflight-check.cjs → pass=false 直接拒绝
GATE 2: add_knowledge title = 原始文件名（不改名、不翻译、不缩短）
GATE 3: check_repeated_names → is_repeated=true 问用户保留两者(加时间戳)或取消
GATE 4: cos-upload.cjs 非零退出 → 停止，不调用 add_knowledge

## 分页

所有列表/搜索接口使用游标分页：首次 `cursor: ""`，检查 `is_end`，用 `next_cursor` 翻页。

## 用户体验

- 隐藏内部 ID（knowledge_base_id、media_id、folder_id），使用名称展示
- 精简进度（不暴露 COS/API 内部操作细节）
- 批量操作汇总结果
- 格式化展示（📚知识库列表 / 📂📄内容列表 / 🔍搜索结果）

## 关联参考

- `references/api.md` — API 完整参考
- `references/tech-doc-cross-validate.md` — 技术文档多源交叉验证
