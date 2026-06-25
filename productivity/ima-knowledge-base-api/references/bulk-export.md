# ima 知识库批量导出备份参考

## 下载脚本位置

```
~/.hermes/ima-skill/download_kb.py
```

脚本由 `ima_api.cjs`（官方 skill 包，位置 `~/.hermes/ima-skill/ima_api.cjs`）驱动，通过 `node` 调用 ima OpenAPI。

## 核心逻辑

1. 调用 `get_knowledge_list` 逐页列出根目录内容和所有子文件夹
2. 递归进入每个子文件夹（media_type=99=folder）
3. 对每个文件条目（media_type≠99）调用 `get_media_info` 获取访问 URL
4. 根据 media_type 决定下载方式：
   - media_type=1/3/4/5/7/9/13/15（文件）：curl 下载，需携带 headers
   - media_type=2/6（网页/微信文章）：保存 URL 到 `.url.md`
   - media_type=11（笔记）：调用 notes API `get_doc_content` 获取文本
5. 已下载的文件跳过不重复下载（文件存在且 size>0）

## 已知缺陷

- 文件名中的扩展名需手动去除（标题自带 .pdf/.md 后缀导致双后缀如 `.md.md`），脚本已自动处理
- `get_media_info` 有每日硬性限额（220021），运行至配额满即停，次日续跑
- 部分条目 `get_media_info` 后无 `url_info` 也无 `notebook_ext_info`，只能保存 `media_id` 信息

## 调优参数

在脚本顶部：
- `API_CALL_DELAY = 1.0`：每次 API 调用间隔（秒）
- `DAILY_QUOTA_HIT`：自动标记，遇 220021 后停止所有下载
