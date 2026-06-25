# IMA OpenAPI Pitfalls & Reference

## 1. 知识库发现

| API | 返回范围 | 适用场景 |
|-----|---------|---------|
| `search_knowledge_base` with `query: ""` | **所有**知识库（个人+共享+订阅） | 枚举所有KB ✅ |
| `get_addable_knowledge_base_list` | 仅可添加内容的KB | 上传文件前选择目标 |
| `search_knowledge_base` with `query: "xxx"` | 按名称搜索KB | 知道名字时定位 |

**关键**：`get_addable_knowledge_base_list` 会漏掉共享和订阅的知识库。

## 2. PDF下载必须带Headers

IMA的PDF URL是签名URL，必须携带 `url_info.headers` 中所有header：

```bash
curl -s -o output.pdf \
  -H "X-IMA-Create-URL-Time: <value>" \
  -H "X-IMA-Platform: H5" \
  -H "X-IMA-Resource-Category: " \
  -H "X-IMA-Sign: <value>" \
  -H "X-IMA-Trace-ID: <value>" \
  -H "X-IMA-UID-SHA256: <value>" \
  "<url>"
```

不带headers → 返回空内容或403。

## 3. 无删除API

IMA OpenAPI **没有**删除知识库条目的接口。用户必须通过IMA网页/App手动删除。

## 4. ima_api.cjs 凭证自动加载

`~/.hermes/skills/ima/ima_api.cjs` 自动从以下位置读取凭证（优先级从高到低）：
1. 传入的 options JSON 中的 `clientId` / `apiKey`
2. 环境变量 `IMA_CLIENT_ID` / `IMA_OPENAPI_CLIENTID`
3. 文件 `~/.config/ima/client_id` / `~/.config/ima/api_key`

通常无需手动传凭证，直接调用即可：
```bash
node ~/.hermes/skills/ima/ima_api.cjs "openapi/wiki/v1/search_knowledge_base" '{"query":"","limit":20}'
```

## 5. 文件上传流程（5步）

```
preflight-check.cjs → check_repeated_names → create_media → cos-upload.cjs → add_knowledge
```

- `title` 必须等于 `file_name`（含扩展名），不可改名
- `cos-upload.cjs` 失败时必须停止，不可继续调用 `add_knowledge`
- 不支持的视频文件（B站/YouTube URL、file://）应提示用户使用IMA桌面端

## 6. media_type 对照表

| media_type | 类型 |
|-----------|------|
| 1 | PDF |
| 2 | 网页URL |
| 3 | Word文档 |
| 4 | PPT |
| 5 | Excel |
| 7 | Markdown |
| 9 | 图片 |
| 11 | 笔记 |
| 13 | 音频 |
| 14 | 视频 |
| 15 | 其他文件 |

## 7. API路径速查

| 接口 | 路径 |
|------|------|
| 搜索知识库 | `openapi/wiki/v1/search_knowledge_base` |
| 知识库内容列表 | `openapi/wiki/v1/get_knowledge_list` |
| 搜索知识条目 | `openapi/wiki/v1/search_knowledge` |
| 获取媒体信息 | `openapi/wiki/v1/get_media_info` |
| 创建媒体 | `openapi/wiki/v1/create_media` |
| 添加知识 | `openapi/wiki/v1/add_knowledge` |
| 检查重名 | `openapi/wiki/v1/check_repeated_names` |
| 导入URL | `openapi/wiki/v1/import_urls` |
| 可添加知识库 | `openapi/wiki/v1/get_addable_knowledge_base_list` |
| 笔记列表 | `openapi/note/v1/list_notebook` |
| 搜索笔记 | `openapi/note/v1/search_note` |
| 导入笔记 | `openapi/note/v1/import_doc` |
| 追加笔记 | `openapi/note/v1/append_doc` |
