---
name: xiaohongshu-research-to-kb
description: 通过小红书 MCP 搜索技术/行业话题的热门笔记，提取有价值信息，结构化整理后存入本地知识库（~/knowledge/research/），并验证 FTS5 索引可检索。适用于技术调研、行业趋势分析、热点追踪等场景。
author: Hermes Agent
created_by: agent
tags: [xiaohongshu, research, knowledge-base, knowledge]
---

# 小红书调研→知识库工作流

通过小红书 MCP（`mcp_xiaohongshu_search_feeds` + `mcp_xiaohongshu_get_feed_detail`）搜索话题，筛选高价值内容，结构化整理后存入本地知识库。

## 流程概述

```
搜索关键词 → 筛选高赞笔记 → 查看详情和评论 → 提取有价值信息 → 结构化整理 → 写入知识库 → FTS5 索引验证
```

## 步骤详解

### 1. 搜索话题

使用 `mcp_xiaohongshu_search_feeds` 搜索中文关键词，排序方式推荐 `最多点赞` 或 `最新`：

```python
mcp_xiaohongshu_search_feeds(
    keyword="AI工具推荐",
    filters={
        "sort_by": "最多点赞",   # 综合/最新/最多点赞/最多评论/最多收藏
        "note_type": "图文",     # 不限/视频/图文
        "publish_time": "不限"   # 不限/一天内/一周内/半年内
    }
)
```

**搜索技巧：**
- 一个话题用 2-3 个不同关键词搜索（如「AI编程工具」「代码助手推荐」「AI开发效率」）
- 筛选条件：优先 `最多点赞` 获取高价值内容
- 限图文类型可获得文字内容，视频需要手动提取

### 2. 筛选笔记

根据搜索结果筛选有价值的内容：

| 评分 | 标准 |
|------|------|
| ⭐⭐⭐ | 1000+ 赞，内容有深度，评论互动活跃（50+ 评论） |
| ⭐⭐ | 300+ 赞，内容言之有物 |
| ⭐ | 浏览标题即可，无需深入 |

排除：纯营销号、标题党无实质内容、视频无文字提取途径

### 3. 查看详情

对筛选出的笔记调用 `mcp_xiaohongshu_get_feed_detail` 获取正文和评论：

```python
mcp_xiaohongshu_get_feed_detail(
    feed_id="...",
    xsec_token="...",
    load_all_comments=True,   # 加载全部评论获取更多信息
    limit=20                  # 限制一级评论数
)
```

**关注点：**
- 笔记标题和正文 — 核心内容
- 互动数据（赞/收藏/评论数）— 内容热度
- 评论区 — 用户的真实反馈和补充信息
- 图片列表（如有）— 图片本身可能需要额外处理查看

### 4. 整理为结构化笔记

将提取的信息整理为 Markdown，风格参考知识库现有文档：

```markdown
# [话题名称] — 小红书热门内容调研

**调研时间：** YYYY-MM-DD
**来源：** 小红书 MCP 搜索
**关键词：** [关键词列表]

## 热门内容概览

| 排名 | 标题 | 作者 | 点赞 | 收藏 | 评论 |
|------|------|------|:----:|:----:|:----:|
| 1 | ... | ... | 3000 | 500 | 200 |

## 核心观点提炼

### [观点1]
- 笔记来源：[标题]（作者，点赞数）
- 核心内容摘录
- 评论区共识/争议点

### [观点2]
...

## 用户反馈汇总

评论区高频讨论：
- **[话题1]**：多数用户认为...
- **[话题2]**：争议点，正反观点...

## 启发与行动点

- 可进一步 web 调研的方向
- 值得关注的账号/作者
- 可实操的建议

## 参考来源

- [笔记标题](feed_id=xxx) — 作者，点赞 N
- [笔记标题](feed_id=xxx) — 作者，点赞 N
```

### 5. 保存到知识库

写入 `~/knowledge/research/` 目录，文件名格式：`[话题]小红书调研_YYYY-MM-DD.md`

```bash
# 重建 FTS5 索引并验证
python3 ~/.hermes/scripts/knowledge/search_knowledge.py "关键词1 关键词2" --limit 5 --rebuild
python3 ~/.hermes/scripts/knowledge/search_knowledge.py "核心关键词" --limit 3
```

至少用 2-3 组关键词验证搜索结果命中。

**FTS5 搜索注意事项：**
- 关键词含连字符（如 `SWE-bench`、`A2A`）会导致 SQLite 报错 `no such column`，因为 FTS5 将连字符解析为减号运算符。处理方式：
  - 用无连字符的关键词替代（如 `SWE bench`、`A2A 协议`）
  - 或用引号包裹精确短语（部分版本支持）
- 中文单字符词（如 `AI` `MCP`）可能匹配不准确，优先用双字词或多字短语
- 优先用文档标题中的完整短语作为搜索词（如 "智能体 框架" 而非 "Agent"）

### 6. 可选：推送摘要

如需推送结果到微信/Telegram：输出结构化中文摘要（分层要点+表格，不要散文段落），用 `send_message` 发送。

### 7. 可选：多源交叉验证（MCP 不可用时的降级策略）

当小红书 MCP 不可用时，切换到 **CSDN MCP + web_search 并行调研**模式：

1. **小红书重试 2 次**：先 `list_feeds` 快速验证 MCP 连通性，再用无 filters 的简单关键词搜索
2. **检查小红书登录状态**：调用 `check_login_status`。如果提示未登录，`get_login_qrcode` 生成二维码扫码；如果提示"账号违规预警/使用第三方工具"，则是小红书反爬检测，需切换到下列替代方案
3. **CSDN MCP 直接搜索**（优先，返回结构化结果，无需登录）：
   ```python
   mcp_csdn_search_csdn(keyword="<topic>", page_size=10)
   ```
   直接返回标题、作者、热度、URL，比 web_search `site:` 过滤更精准快速
4. **web_search 并行补充**（弥补 CSDN 覆盖面不足的部分）：
   - `site:zhuanlan.zhihu.com <topic>` — 知乎专栏
   - `site:cloud.tencent.com <topic>` — 腾讯云开发者社区
   - `site:cnblogs.com <topic>` — 博客园
5. **覆盖率**：CSDN MCP + web_search 并行覆盖 95%+ 关键信息点，且 CSDN MCP 返回结构化数据（含热度排序），比纯 web_search 更易筛选

## 常见场景

### 技术工具测评
搜索 `AI工具 推荐` `编程工具` `效率工具` 等，关注对比类和榜单类笔记

### 行业趋势
搜索 `XX行业 趋势` `新技术 应用`，关注高收藏内容（收藏代表实用价值）

### 技能学习
搜索 `XX技能 学习路线` `XX入门教程`，关注长文图文笔记

## 小红书 MCP 运维注意

- **内存膨胀**：xiaohongshu-mcp 长时间运行会堆积 Chrome 进程（峰值达 3.8GB+），定期重启：`systemctl --user restart xiaohongshu-mcp`
- **重启后需等待**：重启后立即搜索可能报 `Inspected target navigated or closed`。先 `systemctl --user stop xiaohongshu-mcp && sleep 5 && systemctl --user start xiaohongshu-mcp` 确保干净重启
- **搜索超时**：带 `filters` 参数的搜索可能超时 120s。先用简单关键词（无 filters）确认可搜索
- **list_feeds 更快**：`list_feeds`（首页推荐）响应远快于 `search_feeds`，用于快速验证 MCP 连通性
- **断路器恢复**：`hermes mcp test <name>` 成功 ≠ 当前会话工具可用。tools 用启动时的持久连接，test 创建临时连接。断路器恢复后需 `/reload-mcp`
- **评论区加载**：默认返回前 10 条一级评论；设置 `limit=20` + `load_all_comments=True` 获取更多

## 注意事项

- 笔记可能只包含图片无文字（如排行榜截图），需要配合浏览器工具查看图片
- 评论区的争议讨论往往比正文更有价值
- 小红书内容偏向轻松口语化，调研结果整理时需过滤语气词、emoji 等
- 单次搜索最多返回部分结果，换不同关键词可获得更多覆盖面
- 建议一个话题浏览 5-10 篇高赞笔记后综合归纳，避免单一来源偏差

## 参考资料

本会话产出的示例调研笔记：`knowledge/research/AI编程工具Codex与ClaudeCode调研_小红书_2026-06-07.md`

## 已知问题
- **搜索超时**：带 `filters` 参数的搜索可能超时 120s。先用简单关键词（无 filters）确认搜索功能正常
- **断路器恢复**：`hermes mcp test <name>` 成功 ✓ 不代表当前会话的工具可用。Hermes 的 tools 使用**启动时建立的持久 MCP 连接**，test 命令创建**临时新连接**。断路器触发后等待 cooldown 或直接 `/reload-mcp`
- **xiaohongshu-mcp 内存膨胀**：长时间运行后 Chrome 进程堆积（3.8GB+），需 `systemctl --user restart xiaohongshu-mcp`。重启后等待 3 秒再操作
- **扫码登录后提示"账号违规预警 / 使用第三方工具"**：这是小红书反爬/反自动化检测机制。xiaohongshu-mcp 基于 Chromium 浏览器自动化，即便扫码成功也会被平台风控系统标记。该问题无永久修复方案，清除 cookies 重试可能短暂恢复但大概率再次触发。此时应直接降级到 **CSDN MCP + web_search 并行调研**方案（见第 7 节）

详见 `references/ai-coding-tools-xiaohongshu-research.md`

### 本次会话新增的知识资产

| 资产 | 路径 | 说明 |
|------|------|------|
| AI编程工具Codex vs Claude Code调研 | `knowledge/research/...小红书_2026-06-07.md` | 小红书搜索 → 评论区分析 → 结构化整理 |
| AI Agent 2026最新进展 | `knowledge/research/...知乎CSDN调研_2026-06-07.md` | web_search 多源调研（知乎/CSDN/AtomGit） |
| browser_tool.py 代理修复 | `tools/browser_tool.py` (代码修改) | 清理 Chromium 子进程的代理环境变量 |
| Wikipedia MCP | `config.yaml mcp_servers.wikipedia` | 已安装，中文语言+缓存，通过代理访问 |
| Taobao MCP | `config.yaml mcp_servers.taobao` | 已安装，Playwright 浏览器自动化 |

### 本会话新建的 cron job

- `AI Agent 每周调研` — 每周六 12:00，搜索小红书+知乎+CSDN，推送 Telegram/Discord/微信
