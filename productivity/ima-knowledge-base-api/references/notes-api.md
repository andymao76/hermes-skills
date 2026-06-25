# IMA Notes API 参考

## 接口总览

| 接口 | 触发场景 | Endpoint |
|------|---------|----------|
| SearchNote | 搜索笔记 | `/openapi/note/v1/search_note` |
| ListNote | 列出笔记 | `/openapi/note/v1/list_note` |
| GetNoteContent | 获取笔记内容 | `/openapi/note/v1/get_doc_content` |
| ImportNote | 新建笔记 | `/openapi/note/v1/import_doc` |
| AppendNote | 追加内容到笔记 | `/openapi/note/v1/append_doc` |
| ListNoteFolder | 笔记本列表 | `/openapi/note/v1/list_notebook` |

## 数据结构

### NoteBookInfo
| 字段 | 类型 | 说明 |
|------|------|------|
| note_id | string | 笔记唯一 ID |
| title | string | 标题 |
| summary | string | 简介 |
| create_time | int64 | 创建时间(ms) |
| modify_time | int64 | 修改时间(ms) |
| note_ext_info | NoteExtinfo | 扩展字段 |

### NoteExtinfo
| 字段 | 类型 | 说明 |
|------|------|------|
| folder_id | string | 所属笔记本 ID |
| folder_name | string | 所属笔记本名称 |

### NoteFolderInfo
| 字段 | 类型 | 说明 |
|------|------|------|
| folder_id | string | 笔记本 ID |
| name | string | 笔记本名称 |
| create_time | int64 | 创建时间(ms) |
| modify_time | int64 | 修改时间(ms) |
| note_number | int64 | 笔记数量 |
| parent_folder_id | string | 父笔记本 ID |
| folder_type | FolderType | 0=用户自建, 1=全部笔记, 2=未分类 |

### QueryInfo（搜索条件）
| 字段 | 类型 | 说明 |
|------|------|------|
| title | string | 标题关键词 |
| content | string | 正文关键词 |

## 请求/响应

### SearchNote
**Request:** `{"search_type":0, "sort_type":0, "query_info":{...}, "start":0, "end":20}`
- search_type: 0=标题, 1=正文
- start/end: 相差不超过20
**Response:** `{"search_note_infos":[...], "is_end":bool, "total_hit_num":int64}`

### ListNote
**Request:** `{"folder_id":"", "cursor":"", "limit":20}`
- cursor 首次传空字符串
- limit: 0<limit≤20
**Response:** `{"note_book_list":[...], "is_end":bool}`

### GetNoteContent
**Request:** `{"note_id":"xxx", "target_content_format":0}`
- target_content_format: 0=纯文本, 1=Markdown(不支持), 2=JSON
**Response:** `{"content":"..."}`

### ImportNote
**Request:** `{"content_format":1, "content":"# Markdown...", "folder_id":"", "folder_name":""}`
- content_format 固定为 1(Markdown)
- content 不可为空，必须合法 UTF-8
**Response:** `{"note_id":"..."}`

### AppendNote
**Request:** `{"note_id":"xxx", "content_format":1, "content":"追加内容"}`
- 需要是笔记作者
**Response:** `{"note_id":"..."}`

### ListNoteFolder
**Request:** `{"cursor":"0", "limit":20}`
- cursor 首次传 "0"，后续传 next_cursor
- limit: 0<limit≤20
**Response:** `{"note_folder_infos":[...], "next_cursor":"...", "is_end":bool}`

## 错误码

| code | 说明 |
|------|------|
| 210001 | 参数错误 |
| 210002 | 无效 UID |
| 210003 | 服务器错误 |
| 210005 | 不是笔记作者 |
| 210006 | 笔记已被删除 |
| 210009 | 超过大小限制 |
| 210011 | 共享库笔记无权限 |
| 20002 | apiKey 超过限频 |
| 20004 | apiKey 鉴权失败 |
