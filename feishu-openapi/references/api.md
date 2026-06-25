# 飞书开放平台 API 参考

## 基础信息

| 项目 | 说明 |
|------|------|
| 基础 URL | https://open.feishu.cn/open-apis |
| 认证方式 | tenant_access_token（通过 app_id + app_secret 获取） |
| SDK | lark-oapi (Python) / @larksuiteoapi/node-sdk (Node.js) |
| 权限模式 | 自建应用 → 权限管理 → 添加权限 → 发布 |

## 核心 API 端点

### 即时通讯 (IM)

| 功能 | API 路径 | 方法 |
|------|----------|------|
| 搜索群聊 | `/im/v1/chats/search` | GET |
| 获取群成员 | `/im/v1/chats/{chat_id}/members` | GET |
| 发送消息 | `/im/v1/messages` | POST |
| 上传图片 | `/im/v1/images` | POST |
| 上传文件 | `/im/v1/files` | POST |

### 文档 (Docx)

| 功能 | API 路径 | 方法 |
|------|----------|------|
| 创建文档 | `/docx/v1/documents` | POST |
| 获取文档内容 | `/docx/v1/documents/{id}/raw_content` | GET |
| 更新文档块 | `/docx/v1/documents/{id}/blocks/{block_id}` | PATCH |
| 追加文档块 | `/docx/v1/documents/{id}/blocks/{block_id}/children` | POST |

### 消息类型 (msg_type)

| 类型 | content 格式 |
|------|-------------|
| text | `{"text":"hello"}` |
| image | `{"image_key":"xxx"}` |
| file | `{"file_key":"xxx"}` |
| post (富文本) | 富文本 JSON 结构 |
| interactive (卡片) | 卡片 JSON 结构 |

## SDK 参考

**Python (lark-oapi):**
```bash
pip install lark-oapi
```
官方仓库: https://github.com/larksuite/oapi-sdk-python

**Node.js:**
```bash
npm install @larksuiteoapi/node-sdk
```
官方仓库: https://github.com/larksuite/oapi-sdk-nodejs

## 官方文档

- 飞书开放平台: https://open.feishu.cn
- API Explorer: https://open.feishu.cn/api-explorer
- 常见问题: https://open.feishu.cn/document/faq
- 权限列表: https://open.feishu.cn/document/server-docs/authentication/permission
