---
name: reddit-readonly
description: 只读方式浏览和搜索 Reddit（使用公开 JSON 端点）。
  包括：浏览子版块、搜索帖子、查看评论线程、生成帖子链接短名单。
  Skillhub 导入版，依赖 Node.js 脚本。
category: research
---

# Reddit Readonly

Read-only Reddit browsing. 浏览 Reddit 但不会发帖、回复、投票或管理。

## 适用范围

- 查找子版块帖子（hot/new/top/controversial/rising）
- 按关键词搜索帖子（子版块内或全站）
- 拉取评论线程
- 生成短名单供用户手动操作

## 硬性规则

- **只读。** 绝不发帖、回复、投票或管理。
- 对 Reddit API 保持礼貌：先用小数量（5-10），按需扩展。
- 返回结果时附带 **permalink** 链接。

## 命令

脚本路径：`{skill_dir}/scripts/reddit-readonly.mjs`

### 1) 列出子版块帖子

```bash
node {skill_dir}/scripts/reddit-readonly.mjs posts <subreddit> \
  --sort hot|new|top|controversial|rising \
  --time day|week|month|year|all \
  --limit 10
```

### 2) 搜索帖子

```bash
# 子版块内搜索
node {skill_dir}/scripts/reddit-readonly.mjs search <subreddit> "<query>" --limit 10

# 全站搜索
node {skill_dir}/scripts/reddit-readonly.mjs search all "<query>" --limit 10
```

### 3) 获取帖子评论

```bash
node {skill_dir}/scripts/reddit-readonly.mjs comments <post_id|url> --limit 50 --depth 6
```

### 4) 获取子版块最近评论

```bash
node {skill_dir}/scripts/reddit-readonly.mjs recent-comments <subreddit> --limit 25
```

### 5) 线程打包（帖子 + 评论）

```bash
node {skill_dir}/scripts/reddit-readonly.mjs thread <post_id|url> --commentLimit 50 --depth 6
```

### 6) 多子版块查找

```bash
node {skill_dir}/scripts/reddit-readonly.mjs find \
  --subreddits "python,learnpython" \
  --query "fastapi deployment" \
  --include "docker,uvicorn,nginx" \
  --exclude "homework,beginner" \
  --minScore 2 \
  --maxAgeHours 48 \
  --perSubredditLimit 25 \
  --maxResults 10 \
  --rank new
```

## 环境变量（调优）

```bash
export REDDIT_RO_MIN_DELAY_MS=800
export REDDIT_RO_MAX_DELAY_MS=1800
export REDDIT_RO_TIMEOUT_MS=25000
export REDDIT_RO_USER_AGENT='script:clawdbot-reddit-readonly:v1.0.0 (personal)'
```

## 建议工作流

1. 明确范围：子版块 + 关键词 + 时间范围
2. 先用 `find` 或 `posts` 小批量查询
3. 对 1-3 个结果用 `thread` 获取详细上下文
4. 展示短名单：标题、子版块、分数、时间、链接
5. 如需要，提供回复草稿，但提醒用户手动发帖
