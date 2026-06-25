# xiaohongshu-research-to-kb 的 cron job prompt 模板

以下是用于创建周期性调研 cron job 的 prompt 模板。复制此内容到 `hermes cron create` 的 `--prompt` 参数中。

## 模板

```
你的任务是完成一份「<TOPIC>」领域的每周调研简报，并推送到微信/Telegram/Discord。

**每周六中午12点执行以下步骤：**

## 步骤1：搜索最新内容

### 小红书搜索（3个关键词）
使用 mcp_xiaohongshu_search_feeds 搜索以下关键词（按最多点赞排序，图文类型）：
- "<keyword1>"
- "<keyword2>"
- "<keyword3>"

### 知乎搜索（web_search）
- site:zhuanlan.zhihu.com <topic> 2026
- site:zhihu.com <topic>

### CSDN/其他搜索（web_search）
- site:blog.csdn.net <topic> 2026
- site:gitcode.csdn.net <topic>

### 小红书备选策略（如 MCP 不可用）
如果小红书 MCP 搜索超时或报错，记录备注 "小红书 MCP 不可用（原因：XXX）" 并跳过。不影响其他渠道调研。调研完成后重启服务：`systemctl --user restart xiaohongshu-mcp`

## 步骤2：筛选高价值内容

从搜索结果中筛选出：
- ⭐⭐⭐ 高价值：1000+点赞/阅读，有实质技术内容，评论活跃
- ⭐⭐ 中等价值：内容言之有物
- ⭐ 低价值：跳过

对于 ⭐⭐ 及以上内容，用 web_extract 提取正文。

**web_extract 失效处理**：知乎专栏、CSDN博客正文可能被反爬。改用浏览器工具（browser_navigate + browser_snapshot）访问，或者从搜索结果摘要中的 description 字段提取足够信息。AtomGit（gitcode.csdn.net）文章通常可通过 web_extract 正常提取。

## 步骤3：提取关键信息

关注以下内容方向：
1. 新工具/框架/平台发布
2. 协议/标准更新（MCP/A2A等）
3. 企业落地案例
4. 社区热议/用户反馈
5. 开发者实战经验

## 步骤4：生成结构化中文简报

简报格式：
```
🤖 <TOPIC> 每周调研简报（2026-XX-XX）
━━━━━━━━━━━━━━━━━━━━━━

## 🔥 本周热点
- [热点1]
- [热点2]

## 📖 精选文章
1. [标题]（来源，赞数）
   核心观点：...

## 🛠️ 新工具/新框架
- [名称] — [一句话描述]

## 💬 社区热议
- [评论区有价值讨论]

## 📊 与 Hermes Agent 的关联
- [可借鉴/接入的点]
```

## 步骤5：发送到微信/Telegram/Discord

使用 send_message 将简报分别发送到：
- target="telegram"
- target="discord:#综合"
- target="weixin"

注意保持简报简洁清晰，每条 message 不超过2000字。

## 步骤6：存档到知识库

将完整调研笔记保存到 ~/knowledge/research/ 目录下，文件名格式：<topic>_每周调研_YYYY-MM-DD.md
然后重建 FTS5 索引验证。

**FTS5 验证注意事项**：
- 查询关键词含连字符（`SWE-bench`）会报错 `no such column`。用无连字符的关键词替代（`SWE bench`）。
- 至少用 2-3 组不同关键词验证新文档可被检索到。
- 优先用标题中的完整短语作为搜索词。
```

## 使用示例

```bash
hermes cron create "0 12 * * 6" \
  --name "AI Agent 每周调研" \
  --skills "xiaohongshu-research-to-kb" \
  --deliver "telegram,discord,weixin" \
  --prompt "$(cat references/weekly-research-cron-prompt.md | sed 's/<TOPIC>/AI Agent/g; s/<keyword1>/AI Agent 2026/g; s/<keyword2>/智能体 开发/g; s/<keyword3>/多Agent 框架/g')"
```
