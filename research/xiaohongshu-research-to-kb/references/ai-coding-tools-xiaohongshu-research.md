# AI 编程工具调研 — 小红书 MCP 调研示例

**会话时间：** 2026-06-07
**数据源：** 小红书 MCP（xiaohongshu-mcp）
**话题：** AI 编程工具（Codex vs Claude Code）

## 调研流程回放

### 第1步：搜索
```python
mcp_xiaohongshu_search_feeds(keyword="AI工具", ...)
# → 22 条结果，含大量高赞笔记
```

### 第2步：筛选高价值笔记
| 筛选标准 | 本例命中 |
|----------|----------|
| 1000+ 赞 | 8 篇 |
| 1万+ 赞 | 2 篇（Ali Abdaal 11万赞，小离Niko 1.7万赞）|
| 评论区活跃 (50+) | 6 篇 |

### 第3步：查看详情并分析评论区
3 篇深入查看：
- Ali Abdaal "如何利用一个周末掌握Claude Code" — 评论区 857 条，核心讨论：国内能否使用、Claude vs Gemini/GPT 对比
- Cyrus宇 "Codex和Claude Code小白选哪个" — 评论区 271 条，作者亲自回复各类场景选型建议
- 老A "写Claude Code中文教程的人真是个天才" — 3551 条评论（未加载完，超时）

### 第4步：整理入库
产出文件：`knowledge/research/AI编程工具Codex与ClaudeCode调研_小红书_2026-06-07.md`

### 第5步：FTS5 验证
- "Codex Claude Code" → 命中（高亮）
- "Vibe Coding 编程工具" → 命中（正文提及）
- 验证通过

## 关键发现

### 小红书调研的天然优势
1. **评论区价值 > 正文价值** — 用户的真实反馈、争议讨论、替代方案往往比笔记正文更有信息量
2. **交互数据是质量指标** — 收藏数/点赞数反映了内容的实用价值
3. **时效性强** — 评论区的用户提到"Claude 更新太快，视频里的界面两三周前就过时了"

### Claude Code vs Codex 社区共识
- Codex 写代码更稳，Claude Code 更快但容易出 bug
- Claude 的文本能力、审美、创意输出更强
- 国内用户通过 Deepseek V4 + ccswitch 搭配 Claude Code 使用
- Pro 版 $20/月，Codex Plus 也是 $20/月

### 运维注意
- `search_feeds` 带筛选参数时延迟大（可能超时 120s），先用 `list_feeds` 或裸关键词搜索确认连接
- 单次遍历 20+ 笔记详情时，MCP 桥接进程可能超时断开
