# IMA Knowledge Base API 参考

## 接口总览

Base Path: `/openapi/wiki/v1`

| 接口 | 触发场景 | Endpoint |
|------|---------|----------|
| get_knowledge_base | 获取知识库信息 | `/openapi/wiki/v1/get_knowledge_base` |
| get_knowledge_list | 浏览知识库内容 | `/openapi/wiki/v1/get_knowledge_list` |
| search_knowledge | 搜索知识库内容 | `/openapi/wiki/v1/search_knowledge` |
| search_knowledge_base | 搜索知识库列表 | `/openapi/wiki/v1/search_knowledge_base` |
| get_addable_knowledge_base_list | 可添加的知识库列表 | `/openapi/wiki/v1/get_addable_knowledge_base_list` |
| create_media | 创建媒体(上传第一步) | `/openapi/wiki/v1/create_media` |
| add_knowledge | 添加知识(上传第三步) | `/openapi/wiki/v1/add_knowledge` |
| import_urls | 批量导入 URL | `/openapi/wiki/v1/import_urls` |
| check_repeated_names | 检查文件名重复 | `/openapi/wiki/v1/check_repeated_names` |
| get_media_info | 获取媒体信息 | `/openapi/wiki/v1/get_media_info` |

## 数据结构

### KnowledgeBaseInfo
| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 知识库 ID |
| name | string | 知识库名称 |
| cover_url | string | 封面 URL |
| description | string | 描述 |
| recommended_questions | string[] | 推荐问题列表 |

### KnowledgeInfo（知识条目）
| 字段 | 类型 | 说明 |
|------|------|------|
| media_id | string | 媒体 ID |
| title | string | 标题 |
| parent_folder_id | string | 所属文件夹 ID |

### FolderInfo（文件夹）
| 字段 | 类型 | 说明 |
|------|------|------|
| folder_id | string | 文件夹 ID |
| name | string | 文件夹名称 |
| file_number | int64 | 文件数 |
| folder_number | int64 | 子文件夹数 |
| parent_folder_id | string | 父文件夹 ID |
| is_top | bool | 是否置顶 |

### Credential（COS 临时凭证）
| 字段 | 类型 | 说明 |
|------|------|------|
| token | string | 临时 TOKEN |
| secret_id | string | 临时 Secret ID |
| secret_key | string | 临时 Secret Key |
| expired_time | int64 | 过期时间(s) |
| bucket_name | string | COS 桶名称 |
| region | string | COS 区域 |
| cos_key | string | COS 对象 Key |

## 接口详情

### 创建媒体 (create_media)
上传文件的第一步，获取 COS 上传凭证。

**Request:** `{"file_name":"xxx.pdf", "file_size":12345, "content_type":"application/pdf", "knowledge_base_id":"kb_id", "file_ext":"pdf"}`

**Response:** `{"media_id":"...", "cos_credential":{...}}`

### 添加知识 (add_knowledge)
上传文件的最后一步，或直接添加网页/笔记。

**Request (文件):** `{"media_type":1, "media_id":"...", "title":"xxx.pdf", "knowledge_base_id":"kb_id", "folder_id":"", "file_info":{"cos_key":"...", "file_size":12345, "file_name":"xxx.pdf"}}`

**Request (网页):** `{"media_type":2, "title":"网页标题", "knowledge_base_id":"kb_id", "web_info":{"content_id":"https://..."}}`

**Request (公众号文章,media_type=6):** 同上 web_info，URL 需为 mp.weixin.qq.com/s 格式

**Request (笔记,media_type=11):** `{"media_type":11, "title":"笔记标题", "knowledge_base_id":"kb_id", "note_info":{"content_id":"note_id"}}`

### 获取知识库信息
**Request:** `{"ids":["kb_id1","kb_id2"]}` (1-20个)
**Response:** `{"infos":{"kb_id1":{...}, ...}}`

### 浏览知识库内容
**Request:** `{"cursor":"", "limit":20, "knowledge_base_id":"kb_id", "folder_id":""}`
- cursor 首次传空字符串
- folder_id 省略则列出根目录，根目录 folder_id = knowledge_base_id
- limit: 1-50

**Response:** `{"knowledge_list":[...], "is_end":bool, "next_cursor":"...", "current_path":[...]}`

### 搜索知识库
**Request:** `{"query":"关键词", "cursor":"", "knowledge_base_id":"kb_id"}`
- 结果含 highlight_content 高亮片段

### 搜索知识库列表
**Request:** `{"query":"关键词", "cursor":"", "limit":20}`

### 可添加列表
**Request:** `{"cursor":"", "limit":50}`
**Response:** `{"addable_knowledge_base_list":[{"id":"...","name":"..."}], "next_cursor":"...", "is_end":bool}`

### 检查文件名重复
**Request:** `{"params":[{"name":"file.pdf","media_type":1}], "knowledge_base_id":"kb_id"}`
**Response:** `{"results":[{"name":"file.pdf","is_repeated":false}]}`

### 批量导入 URL
**Request:** `{"knowledge_base_id":"kb_id", "folder_id":"kb_id(根目录)", "urls":["https://..."]}`
- urls 1-10 个
- folder_id 必填，根目录传 knowledge_base_id 值

### 获取媒体信息
**Request:** `{"media_id":"..."}`
**Response 分支:**
- URL 可访问 → `data.url_info.url` + headers
- media_type=11(笔记) → `data.notebook_ext_info.notebook_id` 作 note_id 调 notes API
- 不可访问 → 提示用户使用 ima 客户端查看

## 文件上传完整流程

1. `check_repeated_names` → 检查是否已存在
2. `create_media` → 获取 COS 临时凭证 + media_id
3. 将文件二进制上传到 COS（使用临时凭证的 token/secret_id/secret_key）
4. `add_knowledge` → 通知服务端完成

COS 上传使用腾讯云 COS SDK 或直接 HTTP PUT 到 COS 域名。
