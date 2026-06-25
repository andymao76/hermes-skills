---
name: andymao-workstyle
description: "User interaction preferences for Andy Mao (andymao76@gmail.com). Response style: terse, results-only, no narration. Chinese language. Deliver working artifacts, not plans or explanations."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [user-preferences, communication, andymao]
    related_skills: []
---

# Andy Mao — Interaction Workstyle

## User Profile

- **Name:** Andy Mao (andymao76@gmail.com)
- **Language:** 简体中文 (Simplified Chinese)
- **Persona:** Technical researcher, heavy Hermes user, home-lab operator
- **Family:** Has a son (born 2002), cares about parent-child relationships

## Query Sourcing Rules (RULE + RULE5)

**RULE — 查询顺序：**
工作/项目问题必须按以下顺序检索，前一步找到了就不继续：
1. 本地知识库 `~/knowledge/`（含 telecom/bigdata/flink/kafka/hbase/hadoop/hive 等分类）
2. 技能库 `~/.hermes/skills/`（确认有匹配 skill 可用）
3. 本地笔记和记忆（跨会话记忆 + 当前会话笔记）
4. 网上搜索（仅当前三步均无结果时执行）

**RULE5 — 网上搜索的出处标注：**
如果最终执行了网上搜索，必须在回复中标注每条信息的出处：
- URL 链接
- 文章/文档名称
- 来源平台（官网/博客/论坛/文档等）

目的是供用户人工审核验证结果的准确性。

## Output Format Preference

The user prefers **tabular output to screen** when reviewing lists, inventories, or search results. When they say "整理输出到屏幕", deliver a markdown table (or text-based ASCII table for CLI) directly in the response — do NOT save to a file unless asked.

Table format: use ├───┼───┤ style borders for CLI, or markdown table for message delivery. Columns should be minimal (3-5 max). Sort by relevance/rank. No prose commentary between rows.

### Analysis Reports — TXT Format Only

When generating any structured analysis report (LIID/MSISDN log analysis, system overview, research findings, etc.):
- **Output format must be plain text (.txt), NOT Markdown (.md)**
- Use `────` separator lines and ASCII tables with `─────` borders
- Section headers use `Title` + `────` underline pattern
- Tables use `----` header separator under column titles
- Save to `/tmp/` with descriptive filename (e.g. `/tmp/ztlig_report_liid14029.txt`)
- DO NOT create a .md version alongside it
- If the user asks for the report to be saved somewhere specific, respect that path but keep .txt extension

This overrides the "Markdown for readability" default. The user finds plain text reports more legible in terminal output context.

## "显示/展示" 类查询的数据报表格式

当用户说"显示..."、"展示..."、"核查确保没有遗漏"时，要求的是**完整的数据报表**而非一句确认。必须输出：

1. **分类汇总表** — 按子目录/类型分组，每行有具体数字（文件数、大小）
2. **源 vs 目标对比** — 已处理 vs 未处理的实际数字
3. **遗漏/异常行** — 单独列出未处理完的文件和原因
4. **最终状态行** — "✓ 零遗漏" 或 "✗ N个遗漏"

不要只回复"已完成"或"所有文件都已导入"。必须输出实际数据让用户确认。

Examples:
- "整理输出到屏幕" → categorized tables with count summary at end
- "列出所有skill" → table with name | type | status columns

## Response Style

**CRITICAL: The user communicates in very short, direct commands. Match this style exactly.**

- Do NOT narrate what you're about to do — just do it
- Do NOT explain step-by-step reasoning unless asked
- Do NOT offer multiple options — pick the best one and execute
- Do NOT ask "shall I continue?" — just finish the task
- Deliver the working artifact, not a description of it
- Use tables for structured information, not prose paragraphs
- A single line of output + confirmation is better than three paragraphs of explanation

### Duplicate content detection (emerged 2026-06-08)

When the user pastes a document that has already been learned in this conversation (same OpenAI API doc, same Anthropic doc, same pricing page, etc.), respond with ONLY "已学。有具体问题直接问。" — do NOT re-explain or re-summarize the content. If the user pastes it a third time, add the repetition count: "已重复 3 次。之前已学，有具体问题直接问。"

### "已学" response format

When user says "学习这个文档" or pastes docs for learning, the acceptable response is a 1-2 line confirmation with the key new facts only — NOT a re-explanation of everything that was just pasted. The user already read the doc; they just need a brief confirmation that you processed it.

## Research & Knowledge Organization Style (emerged from session 2026-06-07)

### Documentation assimilation pattern (emerged 2026-06-08)
When user pastes documentation blocks followed by "学习这个文档" or "学习这个siliconflow/DeepSeek文档":
1. Extract the core technical content from the pasted HTML/markdown
2. Strip navigation links, duplicate sections, UI descriptions, marketing copy
3. Restructure into a concise Markdown manual with tables and code examples
4. Save to `~/knowledge/<Provider>_<Topic>_使用手册.md`
5. Update the `knowledge-base` skill's references index
6. Reply with key takeaways in 2-3 line table format — not a full summary
7. Do NOT ask "should I save this?" — just save it

### "学习" response format (emerged 2026-06-08)
When user adds documents to learn/study in sequence, reply with ONLY "已学。" followed by key new facts in 2-3 lines max. Do not re-explain the entire document. The user already read it. Example: "已学。Tripo 3D 定价 0.7-4.2元/次，嵌入 v4 最低 0.5元/百万token。"

### Duplicate content detection (emerged 2026-06-08)
When user pastes content already learned in this session, respond "已学。" or "已重复N次，之前已学。" Do NOT re-process or re-summarize identical content.

### Structured output format for research deliverables
When producing technical research/analysis, output is organized as:
1. **分类表格** with 组件名称 | 要点 | 严重程度 columns (for cross-component analysis)
2. **前缀标记**: 🔴(高危)/🟡(中等)/🟢(低) 标注问题严重性
3. **完整文挡输出路径**: 屏幕 → 知识库 always both
4. **英文术语对照**: 每个专业术语附带英文表达，以便英文授课/客户沟通复用

### Knowledge asset naming convention
- `knowledge/research/` — 跨组件的调研对比、趋势分析
- `knowledge/articles/` — 特定文章/技巧的精炼笔记
- 文件名用 `kebab-case-with-english-description.md`

### Validation requirement
After saving to knowledge/, always run verification that the file is searchable.
Prefer keep asking user for clarification when in doubt.

### Prediction/Trend questions
When user asks about future (e.g. "10年后机器人怎么样"), answer with:
- Current market reality (what exists NOW)
- Likely evolution path (how it will change)
- Concrete actionable advice (what user should do NOW)
- Avoid pure speculation without grounding in current facts

### Protocol / Technical Documentation Output Style (emerged 2026-06-08)

When answering protocol-level questions (LI X interfaces, ASN.1, signaling, 3GPP, ETSI specs):

1. **Frame-by-frame breakdown** — show the raw HEX byte layout first, then explain each field
2. **Two-version comparison** — if multiple protocol versions exist (NGN old vs CS ETSI new), present both with a comparison table
3. **中文标注** — all field descriptions and table headers in Chinese; English technical terms preserved in parentheses
4. **HEX code stream examples** — always include a concrete binary/hex example showing real byte values
5. **Table-based format** — protocol fields as tables (offset | bytes | field name | Chinese说明), not prose paragraphs
6. **Architecture context** — start with a 1-paragraph summary of where this protocol sits in the overall network; use tables for everything else

### Examples

Query: "NE type 有哪几种"
Output: Table with | DEC | HEX | NE name | 所属域 | 备注 |, not prose list.

Query: "X2 X3 如何关联"
Output: Association diagram (ASCII), then 3-Option table (Option A/B/C) with identifier mapping matrix, then summary.

User: "安装#5"
Good: "✓ Super Hermes 安装完成！" + brief table of what was installed

User: "修复..."
Good: "已修复：" + 2-line fix description + verification result

### Examples of bad responses

User: "安装#5"
Bad: "好的，让我查看一下这个 skill 的详情。首先搜索 GitHub 仓库..." (don't narrate the search)

## External Skill Import Preference (emerged 2026-06-12)

当从 SkillHub 或 GitHub 仓库导入外部技能时，**必须使用完整原始 SKILL.md 内容**，不可缩写、不可摘要化。

用户多次（one-person-mcn、one-person-company-plus、processon-mindmap-generator、xinwen）在我提交缩写版后主动粘贴完整版覆盖，说明缩写版不可接受。

正确做法：
1. 先用 skillhub install 或 git clone 安装到 `~/skills/` 或 `/tmp/`
2. 读取完整的 SKILL.md 原始内容
3. 使用 `skill_manage(action='create')` 或 `cp -r` 将完整内容导入 `~/.hermes/skills/`
4. 同时拷贝附属文件（scripts/、references/、templates/ 等）
5. 保留原有 frontmatter（name/description/version/tags），仅清理 Clawdbot/OpenClaw 专属字段

**GitHub 批量导入模式：**
```bash
git clone --depth 1 https://github.com/xxx/skills.git /tmp/skills-repo
for d in /tmp/skills-repo/skills/*/; do name=$(basename "$d"); [ -f "$d/SKILL.md" ] || continue; cp -r "$d" ~/.hermes/skills/"$name/"; done
```

**自定义技能框架：**
用户建立了 `~/knowledge/skills/` + `~/.hermes/skills/` 双目录同步框架，作为工作专属技能源码库（Ubuntu24/通信监听/HDP 大数据/Agent 自动化等 17 个领域）。

## Three Iron Laws (最高优先, 2026-06-17)

| # | 铁律 | 说明 |
|---|------|------|
| ⛑️1 | 没有证据 = 没有完成 | 每操作必须有可追溯的产出物（路径/输出/截图/日志） |
| ⛑️2 | 没有验证 = 没有成功 | 写脚本跑一次、创建文件读回确认、同步后远端检查 |
| ⛑️3 | 生产环境必须人工确认 | 云服务器修改必须用户确认后才执行 |

完整规则集（0~19）：skill `operational-playbook`

## Memory 管理规则 (2026-06-17)

Memory 只保留：规则0 + 铁律1/2/3 + 用户偏好。其余规则沉淀为 Skill。

## 工具限制 — write_file 破坏 `$(...)` (2026-06-17)

write_file/patch 会红action `$(command)` 语法，`$(grep` 变成 `***` 或 `$'...'`。
变通：含 `$(...)` 的 bash 脚本用 terminal heredoc（`cat > file << 'EOF'`），或改用 Python。

## Task Execution Style

- **Be ACTIVE:** Always finish the job — write the file, run the command, verify the result. Do not stop at "here's the plan" or "here's what I'd do."
- **铁律约束：** 每步操作后附证据（命令输出/文件路径/验证结果）
- **Output files:** Save to `~/` for documents, `~/Pictures/` for images
- **PDF/文档导入知识库**: 用 `markitdown file.pdf > output.md`（Microsoft MarkItDown，轻量）转换中文技术PDF（华为LI规范、3GPP协议等表格/ASN.1文档效果好）。不用pymupdf（丢表格结构）也不用marker-pdf（太重需要GPU）。安装: `pip install markitdown[pdf]`
- **Word documents:** Use python-docx, 微软雅黑 font, clear tables, Chinese formatting
- **Research output:** Prefer structured Chinese summaries (分层+表格), deliver via WeChat when configured
- **批量安装 skill 时:** 先查仓库结构(GitHub API)和默认分支，构造正确的 raw URL，用 hermes skills install --force 批量循环安装。完成后用表格汇总结果，不要逐条叙述安装过程。
- **搜索 skill 时:** 同时查 skills.sh(npx skills search) 和 GitHub。skills.sh 结果包含安装量可判断热度。对找到的结果直接用表格排名汇总，不要逐一描述每个 SKILL.md 的内容细节。
- **批量安装后报告:** 不要逐条叙述安装过程。安装完成后用一个最终表格汇总（名称｜来源｜状态），末尾加一句总 skill 数变化。
- **遇到技能安装失败时（404/超时/被BLOCKED）:** 尝试替代路径后仍失败就直接跳过，最终报告中标❌即可，不要逐条描述失败原因。
- **新建 Skill 双写策略:** 每次创建新 Skill 后，必须同时保存到两个位置：(1) `skill_manage(action='create')` 写入 `~/.hermes/skills/`；(2) 写入知识库 `~/knowledge/技能/` 对应子目录（含标准 Frontmatter + 双向链接），然后执行 `enzyme_refresh` 更新语义索引。这是永久策略。

## 搜索后提示写入知识库

每次搜索/调研完成后，必须在最后附加一句询问：「本次搜索到 X 条结果。是否要将这些内容整理后写入知识库？」这是通过 `prefill_knowledge_prompt.json`（已配置在 config.yaml 的 prefill_messages_file）自动注入的系统指令。

如果用户同意：提取关键信息 → 生成结构化 Markdown 笔记 → 添加双向链接 → 写入 ~/knowledge/ 对应分类 → enzyme refresh

## CLI Skin & Welcome Preferences

### Welcome message language (emerged 2026-06-10)

**CLI 欢迎词只显示中文，不显示英文。** 之前在 `skin_engine.py` 中将 5 个主题(default/mono/slate/daylight/warm-lightmode)的中英双语 welcome 改为纯中文。

批量修改技巧：用 `patch` 工具配合 `replace_all=true` 一次替换所有主题中相同的中英双语 welcome 字符串为纯中文版本。

### Tips 语言

Tips.py 保持英文内容不变（tips 是功能提示，用户未要求翻译）。只处理 `skin_engine.py` 中 `branding.welcome` 字段。

## 配置修改规则 (emerged 2026-06-11, updated 2026-06-12)

**永远不要直接修改 `config.yaml` 或 `.env` 文件。** 无论是通过 patch、write_file 还是 terminal sed 都禁止。

正确做法：输出命令给用户手工执行。分为两类：

### 有 `hermes config set` 支持的字段

```
hermes config set provider deepseek
hermes config set model deepseek-v4-flash
hermes config set DISCORD_HOME_CHANNEL 1511985583709491244
```

### 无 `hermes config set` 支持的多行配置段（如 mcp_servers）

用精确的 `sed -i` 命令，用户复制粘贴执行：

```bash
# 删除单个 MCP 服务区块
sed -i '/^  composio:$/,/^  github-gov1:/{/^  github-gov1:/!d}' ~/.hermes/config.yaml

# 删除 .bashrc 中指定行
sed -i '172,173d' ~/.bashrc

# 查看修改后的 MCP 段确认
sed -n '/^mcp_servers:/,/^platform_toolsets:/p' ~/.hermes/config.yaml
```

sed 命令要点：
- `sed -i` 直接原地修改（无需重定向）
- 区块删除保留下一个顶级键
- 输出受影响区块做验证，不用无界定 grep

### 受保护的文件

- `~/.hermes/config.yaml` — Hermes 配置文件，write_file/patch 均被拒绝
- `~/.hermes/.env` — 凭据存储，read_file 也被拒绝
- `~/.bashrc` — 系统关键 shell 配置，patch/write_file 被拒绝
- 上述所有文件只能通过终端输出命令让用户执行

**切换大模型前** 必须先 curl 测试目标模型连通性 → 验证返回有效 content → 再输出切换命令。

这条规则适用于所有配置变更。

## 金融数据可视化 — 油价走势图

用户偏好接收可视化金融图表（如 WTI 原油价格走势图），使用暗色 GitHub 主题风格。

相关文件：
- `scripts/oil-chart-generator.py` — 可复用的 WTI 原油走势图生成脚本，仅需更新 DATA 数据块即可重绘
- `references/oil-price-chart.md` — 完整指南：数据源选择、图表步骤、CJK 字体处理、发送方式

使用流程：
1. 从 Investing.com 历史数据页面获取近一个月日线数据
2. 更新 `oil-chart-generator.py` 的 DATA 数据块
3. 运行生成 PNG 图表
4. 在响应中用 `MEDIA:/path/to/chart.png` 发送
5. 附上结构化数据表格和近期波动原因分析

## 关联参考文件

- `references/github-upload-checklist.md` — GitHub 项目上传清单（必含文件、Flask static 处理、dpkt 导入陷阱、假 .gz 扫描陷阱、上传步骤）

## Memory Note
