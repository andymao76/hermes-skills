---
name: ima-knowledge-base-api
description: 腾讯 ima 知识库 HTTP API 集成 — 笔记管理（搜索/创建/追加/读取）+ 知识库管理（上传/搜索/浏览/添加网页）。无需 QClaw，直接调用 ima.qq.com OpenAPI。提供 MCP 配置模板和调用示例。
category: productivity
tags:
  - ima
  - knowledge-base
  - notes
  - tencent
  - api
  - openapi
triggers:
  - ima知识库
  - ima 笔记
  - 腾讯ima
  - 知识库下载
  - ima API
---

# ima Knowledge Base API Integration

Tencent ima 知识库 HTTP API 集成。无需 QClaw（小龙虾），直接通过 `ima_api.cjs` 或 curl 调用 `https://ima.qq.com`。

## 凭证获取

1. 打开 https://ima.qq.com/agent-interface
2. 点击"获取 API Key"，跳转到本地 ima 客户端弹出
3. 复制 **Client ID** 和 **API Key**
4. **API Key 只展示一次**，丢失需删除后重新获取

## 配置方式（三选一）

### A — 环境变量
```bash
export IMA_CLIENT_ID="你的ClientID"
export IMA_API_KEY="你的API Key"
```

### B — 配置文件
```bash
mkdir -p ~/.config/ima
echo "你的ClientID" > ~/.config/ima/client_id
echo "你的API Key" > ~/.config/ima/api_key
```

### C — 直接传参给 ima_api.cjs
```bash
node ima_api.cjs openapi/list_docs '{"limit":10}' '{"clientId":"xxx","apiKey":"xxx"}'
```

## API 架构

| 模块 | Base Path | 功能 |
|------|-----------|------|
| Notes | `/openapi/note/v1` | 搜索/列表/创建/追加/读取笔记 |
| Knowledge Base | `/openapi/wiki/v1` | 上传文件/搜索/浏览/添加网页 |

所有请求：**HTTP POST + JSON Body**，认证头：
- `ima-openapi-clientid`
- `ima-openapi-apikey`
- `Content-Type: application/json`

## Notes API

| 操作 | Endpoint | 说明 |
|------|----------|------|
| 搜索笔记 | `POST /openapi/note/v1/search_note` | 支持标题/正文搜索，分页 start/end 相差不超20 |
| 列出笔记 | `POST /openapi/note/v1/list_note` | 按笔记本 folder_id 筛选，游标翻页 |
| 获取内容 | `POST /openapi/note/v1/get_doc_content` | 返回纯文本/Markdown/JSON |
| 创建笔记 | `POST /openapi/note/v1/import_doc` | content_format=1(Markdown)，需 UTF-8 校验 |
| 追加内容 | `POST /openapi/note/v1/append_doc` | 往已有笔记末尾追加 |
| 笔记本列表 | `POST /openapi/note/v1/list_notebook` | 列出笔记本/文件夹，游标翻页 |

## Knowledge Base API

| 操作 | Endpoint | 说明 |
|------|----------|------|
| 获取知识库信息 | `POST /openapi/wiki/v1/get_knowledge_base` | 传 ids 列表，1-20个 |
| 浏览内容 | `POST /openapi/wiki/v1/get_knowledge_list` | 游标翻页，支持 folder_id 进子文件夹 |
| 搜索知识库 | `POST /openapi/wiki/v1/search_knowledge` | 全文搜索知识库内容 |
| 搜索知识库列表 | `POST /openapi/wiki/v1/search_knowledge_base` | 搜索可用的知识库 |
| 可添加列表 | `POST /openapi/wiki/v1/get_addable_knowledge_base_list` | 当前用户有权限添加的知识库 |
| 上传文件 | `create_media` → COS Upload → `add_knowledge` | 三步流程 |
| 添加网页 | `POST /openapi/wiki/v1/import_urls` | 批量导入 URL（1-10个） |
| 检查文件名 | `POST /openapi/wiki/v1/check_repeated_names` | 上传前检查是否重复 |
| 获取媒体信息 | `POST /openapi/wiki/v1/get_media_info` | 获取文件访问 URL 或笔记 ID |

## 调用方式

### 方式 1 — 直接 curl

```bash
curl -s -X POST "https://ima.qq.com/openapi/note/v1/list_notebook" \
  -H "ima-openapi-clientid: $IMA_CLIENT_ID" \
  -H "ima-openapi-apikey: $IMA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"cursor":"0","limit":20}'
```

### 方式 2 — ima_api.cjs（推荐）

从官方 skill 包获取脚本：
```
https://app-dl.ima.qq.com/skills/ima-skills-1.1.7.zip
```

```bash
# 列出笔记本
SKILL_DIR="/path/to/ima-skill"
OPTS=$(printf '{"clientId":"%s","apiKey":"%s"}' "$IMA_CLIENT_ID" "$IMA_API_KEY")
node "$SKILL_DIR/ima_api.cjs" "openapi/note/v1/list_notebook" '{"cursor":"0","limit":20}' "$OPTS"

# 搜索笔记
node "$SKILL_DIR/ima_api.cjs" "openapi/note/v1/search_note" \
  '{"query_info":{"content":"关键词"},"start":0,"end":20}' "$OPTS"

# 创建笔记
node "$SKILL_DIR/ima_api.cjs" "openapi/note/v1/import_doc" \
  '{"content_format":1,"content":"# 标题\n\n正文内容","folder_name":"我的笔记本"}' "$OPTS"

# 浏览知识库
node "$SKILL_DIR/ima_api.cjs" "openapi/wiki/v1/get_knowledge_list" \
  '{"cursor":"","limit":20,"knowledge_base_id":"KB_ID"}' "$OPTS"
```

### 方式 3 — MCP 配置

```yaml
# ~/.hermes/config.yaml
mcp_servers:
  ima-kb:
    type: stdio
    command: node
    args:
      - /path/to/ima-skill/ima_api.cjs
    env:
      IMA_CLIENT_ID: "你的ClientID"
      IMA_API_KEY: "你的API Key"
```

## 接口响应格式

成功:
```json
{"code": 0, "msg": "success", "data": {...}}
```

业务错误（在 stdout 中，进程正常退出）:
```json
{"code": 210001, "msg": "参数错误", "data": {}}
```

脚本错误（在 stderr 中，进程非0退出）:
```json
{"code": -100, "msg": "缺少凭证"}
```

## 媒体类型枚举（MediaType）

| 值 | 类型 | content_type |
|----|------|-------------|
| 1 | PDF | application/pdf |
| 2 | 网页 | N/A (url) |
| 3 | Word | application/msword / .docx |
| 4 | PPT | application/vnd.ms-powerpoint |
| 5 | Excel | application/vnd.ms-excel / csv |
| 6 | 微信公众号文章 | mp.weixin.qq.com/s 格式 URL |
| 7 | Markdown | text/markdown |
| 9 | 图片 | image/png / jpeg / webp |
| 11 | 笔记 | N/A (使用 note_id) |
| 13 | TXT | text/plain |
| 15 | 录音 | audio/mpeg / m4a / wav |

## 注意事项与 Pitfalls

### 配额限制
- **`get_media_info`** 每日有硬性配额上限（220021: 资料获取次数已达上限，请明天再尝试）—— 这是每日配额，不是频率限制，需等次日重置
- **频率限制**（200001: 请求频率超限，请稍后重试）—— API 调用过快时触发，建议每次调用间隔 ≥ 1 秒
- **apiKey 频率限制**（20002）—— notes API 有独立限频
- **方案**：批量下载时使用 `download_kb.py` 脚本（已内置 1 秒间隔限速 + 每日配额检测 + 可重入跳过已下载文件）

### UTF-8 编码
- 笔记写入（import_doc/append_doc）的 content 必须是合法 UTF-8
- 非法编码会导致内容乱码且不可逆

### 上传文件流程
1. `check_repeated_names` 检查重名
2. `create_media` 获取 COS 临时上传凭证
3. 上传文件到腾讯云 COS（使用临时凭证）
4. `add_knowledge` 通知服务端完成

### 文件夹定位
- 根目录的 `folder_id` 等于 `knowledge_base_id`
- 搜索文件夹用 `search_knowledge` 按名称搜索
- 浏览用 `get_knowledge_list` 逐级导航

## 批量下载整库

超大知识库（数千条目）的完整备份工作流。使用 `download_kb.py` 脚本（`~/.hermes/ima-skill/download_kb.py`）。

### 下载脚本能力

| 特性 | 说明 |
|------|------|
| 递归遍历 | 自动进入所有子文件夹，保持目录结构 |
| 多类型支持 | PDF/Word/PPT/Markdown/TXT/网页链接/笔记 |
| 可重入 | 已下载的文件自动跳过，适合分日续跑 |
| 配额感知 | 检测到 220021 每日配额时自动停止，不浪费调用 |
| 限速 | 内置 1 秒 API 调用间隔，避免触发 200001 频率限制 |

### 使用方法

```bash
# 编辑脚本，修改 KB_ID 和目标目录
python3 ~/.hermes/ima-skill/download_kb.py

# 配额用完后第二天重新运行
python3 ~/.hermes/ima-skill/download_kb.py
```
### 已知限制

- **每日配额**：`get_media_info` 每日调用次数有限，大知识库需多日分批完成
- **无效条目**：部分已删除或不可达的条目会报错，脚本会记录到 `.url.txt` 调试文件
- **根目录 folder_id**：`get_knowledge_list` 返回的 `current_path[0].folder_id` 才是真正的根目录 folder_id，不等于 `knowledge_base_id`

## 批量下载自动续跑（Cron 编排）

对大知识库（如 51学通信知识星球 3091 条目），推荐使用 **recurring cron + 进度追踪包装脚本** 而非 one-shot 单次任务。包装脚本自动累积已下载数，报告剩余估算。

### 方案 A: 一键式 one-shot cron（简单版）

每天同一时间自动续跑，配额用完后自动停止，次日 cron 不会自然续跑（需手动重建）。适合一次性备份。

```bash
hermes cron create \
  --name "ima-知识库备份" \
  --prompt "运行 python3 ~/.hermes/ima-skill/download_kb.py 继续下载 [知识库名称] 的剩余内容。
报告下载结果：新增下载了多少文件、总文件数、有无错误。
如果有配额限制（code 220021）就报告剩余数量，明天同一时间再跑。" \
  --schedule "2026-06-11T09:00:00" \
  --enabled-toolsets terminal
```

### 方案 B: recurring cron + 进度追踪包装脚本（推荐）

创建一个包装脚本 `~/.hermes/scripts/ima-backup.sh`，包含：
1. 运行 `download_kb.py`
2. 统计实际已下载文件数
3. 读写状态文件 `~/.hermes/ima-skill/backup_progress.json`
4. 输出进度报告（新文件数、总完成度、剩余天数估算）

然后设置 cron 为 daily recurring + `no_agent=true`，脚本 stdout 自动投递到各平台：

```bash
cronjob(action='create',
    name='ima-51kb-backup',
    schedule='0 7 * * *',
    script='ima-backup.sh',
    no_agent=true,
    deliver='telegram,discord:#综合,weixin:user@im.wechat')
```

**优势：**
- 每天自动跑，配额用完自动停，第二天自动续跑
- 进度累计，每次推送显示已下载/总数/剩余天数
- 全部完成后推送会显示 🎉 完成信息
- 无需手动管理 cron 生命周期

**注意：** 脚本必须放在 `~/.hermes/scripts/` 目录下，cron 的 `script` 字段只填文件名（相对路径）。

### 运维要点

| 场景 | 做法 |
|------|------|
| 每日自动续跑 | 下载完成后检查配额，如果触发 220021 就输出"明天再跑"，不额外操作 |
| 全部下载完成 | 脚本会输出下载完毕（无剩余条目），此时手动删除 one-shot cron 或用 `cronjob action=remove` |
| 重入安全 | `download_kb.py` 已跳过已下载文件，重复运行不会产生重复 |
| 交付方式 | 不设 deliver（默认 origin），结果自动回到当前会话终端 |
| 监控 | 每次运行后检查配额是否耗尽 + 今日新增文件数，决定是否继续 |
