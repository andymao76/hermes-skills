---
name: gmail
description: Gmail API 集成 — 通过 Maton.ai 代理读取、发送和管理邮件、标签、草稿。
  依赖 MATON_API_KEY 环境变量和 Maton CLI。
  Skillhub 导入版。
category: productivity
---

# Gmail

通过 Maton.ai 代理接口访问 Gmail API。支持读、发、管理邮件、线程、标签、草稿。

## 前置条件

```bash
# 安装 Maton CLI
npm install -g @maton-ai/cli
# 或
brew install maton-ai/cli/maton

# 登录
maton login
export MATON_API_KEY="YOUR_API_KEY"
```

## 基础用法

### 列出邮件
```bash
maton google-mail message list -L 10
maton google-mail message list --query 'is:unread' -L 10
```

### 发送邮件
```bash
maton google-mail message send --to alice@example.com --subject 'Hello' --body 'Hi there!'
```

### 回复/转发
```bash
maton google-mail message reply {messageId} --body 'Thanks!'
maton google-mail message forward {messageId} --to dave@example.com --body 'FYI'
```

### 标签管理
```bash
maton google-mail label list
maton google-mail message modify {messageId} --add-label STARRED --remove-label UNREAD
```

### 线程
```bash
maton google-mail thread list -L 10
maton google-mail thread view {threadId}
```

### 草稿
```bash
maton google-mail draft create --to alice@example.com --subject 'Hello' --body 'Draft'
maton google-mail draft send {draftId}
```

## 查询语法

| 参数 | 说明 |
|------|------|
| `is:unread` | 未读 |
| `is:starred` | 星标 |
| `from:email@example.com` | 发件人 |
| `to:email@example.com` | 收件人 |
| `subject:keyword` | 主题 |
| `after:2024/01/01` | 日期之后 |
| `has:attachment` | 有附件 |

## 错误码

| 状态 | 含义 |
|------|------|
| 400 | 缺少 Gmail 连接 |
| 401 | API Key 无效 |
| 429 | 限流（10 req/sec） |

## 安全提示

- 写操作（发、删、改标签）需要用户确认
- 多个 Gmail 连接时需指定 `--connection {id}`
