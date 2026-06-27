---
name: knowledge-base
description: 完整的本地知识库方案 — kb-search (FTS5+语义嵌入/100%嵌入) + 工作日志/日报/周报/月报体系 + 自动采集 cron job + 会话挖掘入库 + 多源MCP调研 + 百度网盘索引 + 社区技能生态
author: Hermes Agent
created_by: agent
tags: [knowledge, rag, memory, research, holographic, baidupan]
---

# 本地知识库 (Local Knowledge Base)

一套完整的本地知识库方案，包含三层架构：

1. **Holographic Memory** — 会话级 RAG，存储结构化事实，支持实体检索
2. **FTS5 文件检索** — 搜索 ~/knowledge/ 目录下的所有 .md/.txt 文件
3. **自动采集** — cron job 定时抓取内容存入知识库

## 目录结构

当前结构（2026-06-11 起三分类）：

```
~/knowledge/
├── 工作/                    symlink → Obsidian vault 工作/
├── 知识/                    主知识库（本目录自身）
├── 技能/                    symlink → Obsidian vault 技能/
├── 00_INBOX/                统一收件入口
├── _system/                 系统文件（project_status.yaml / decision_log.md）
├── research/                技术研究笔记
├── articles/                采集文章
├── articles_baidu/          百度网盘导入文档
├── notes/                   笔记
├── daily/                   每日日志（遗留，逐步迁移）
├── Hermes/                  Hermes 运维知识
├── hermes-docs-en/          Hermes 官方文档
└── ...

~/.hermes/scripts/knowledge/
├── save_article.py         # 保存文章到知识库
├── search_knowledge.py     # FTS5 全文搜索知识库
└── knowledge_collector.py  # 采集器（搜索+提取+保存）
```

## 从百度网盘导入知识文档（新版工作流）

**推荐方案：xpan API 全盘扫描 → 索引 → 分类 → 写入知识库**。无需下载文件到本地，直接在网盘上建立文档索引即可使用。如需下载文件（如 PDF 内容分析），也通过同一个 access_token 获取 dlink 下载（见 `baidunetdisk` skill 的 `references/baidu-file-download.md`）。

### 方案一：xpan API 全盘索引 + 自动分类（首选，2026-06-08）

**无需额外安装工具**，直接用 bypy 已有的 access_token 即可访问整个网盘。

**前置条件**：bypy 已授权（`~/.bypy/bypy.json` 存在且 scope 含 `netdisk`）

**完整工作流**（详见 `baidunetdisk` skill 的 `references/xpan-api-full-scan.md`）：

1. **全盘扫描** → BFS 遍历所有非空目录，生成原始 Markdown 索引
2. **文档分类** → 按目录路径 + 文件名双层关键词映射，分类到 19 个知识领域
3. **重复检测与去重** → 同名+同大小判定重复；SAGE 多语言 HTML 自动清除；真实重复用 `↳` 引用替代
4. **写入知识库** → `~/knowledge/baidu-netdisk/_index.md` + 各分类 `.md` 文件

**关键注意点**：
- ⚠️ **调用 xpan API 前必须清除 HTTP_PROXY 环境变量**，否则会卡死无响应
- API 端点：`https://pan.baidu.com/rest/2.0/xpan/file?method=list&dir=/&access_token=<TOKEN>`
- User-Agent 必须设为 `pan.baidu.com`
- 限速：每次调用后 sleep 0.15~0.2 秒，避免 429
- 全盘递归扫描（约 600~1800 个 API 调用，取决于目录深度）需 3~8 分钟
- 文档过滤：仅收集 .ppt/.pptx/.pdf/.doc/.docx/.xls/.xlsx/.txt/.md/.mobi/.epub/.azw3，排除 <1KB 文件和 Python 2.7 相关
- 已知数据量示例：根目录 294 个（149 非空），全盘 1810 个目录，3912 个文档，4.8GB，334 组重复

### 方案二（传统）：下载到本地 + 格式转换（旧版，仅需下载时使用）

如需实际下载文档到本地（索引不足以满足需求时），使用 BaiduPCS-Go：

```bash
BaiduPCS-Go login -bduss="<BDUSS>" -stoken="<STOKEN>"
BaiduPCS-Go config set -savedir ~/baidupan_docs/ -max_parallel=5
BaiduPCS-Go download /目标目录/
```

下载后用 `baidupan_convert.py` 转换格式为 Markdown，详见 `references/baidupan-import-guide.md`。

**注意**：BaiduPCS-Go 需要 BDUSS+STOKEN（从 Chrome 开发者工具 Cookie 获取），不能用 bypy 的 access_token 登录。

### 批量转换脚本 `baidupan_convert.py`

**位置**：`~/.hermes/scripts/baidupan_convert.py`

自动处理 6 种文档格式到 Markdown：

| 源格式 | 转换方式 | 说明 |
|--------|----------|------|
| `.md` | 直接复制 | 最快，零转换 |
| `.docx` | pandoc → md | 首选，失败自动走备选 |
| `.doc` | LibreOffice → docx → pandoc → md | 旧版 Word 格式 |
| `.pdf` | pdftotext → markdown 包装 | pandoc 不支持 pdf 输入格式，必须用 pdftotext |
| `.chm` | 7z 解压 → pandoc → md | Windows 帮助文档 |
| `.html/.htm` | pandoc → md | 网页存档 |

**文件名智能分类**（依据关键词自动分拣）：

| 文件名含有的关键词 | 导入知识库目录 |
|--------------------|----------------|
| 3GPP, TS_, TR_, spec, release | `research/` |
| IMS, SIP, VoLTE, VoWiFi, NR, LTE | `research/` |
| ZTE, Huawei, Nokia, Ericsson | `research/` |
| 5G, 6G, MIMO, beamforming | `research/` |
| 架构, 流程, flow, call | `research/` |
| config, deploy, 配置, 安装 | `notes/` |
| 培训, training, tutorial, 教程 | `notes/` |
| manual, guide, 手册, 指南 | `research/` |
| 其他（不含关键词） | `articles_baidu/` |

**参数**：
| 参数 | 用途 |
|------|------|
| `--dry-run` | 预览操作，不实际转换 |
| `--limit N` | 最多处理 N 个文件 |
| `--input DIR` | 自定义输入目录 |
| `--verify-only` | 仅重建索引+验证检索 |

转换完成后自动重建 FTS5 索引并用 `3GPP/5G/IMS` 等关键词验证可检索性。

日志保存在 `~/baidupan_import.log`。

### 转换进度监控

当 `baidupan_convert.py` 在后台运行时（另一个 Hermes 进程或 nohup），可用以下命令查看进度：

```bash
# 查看转换进程是否运行
ps aux | grep baidupan_convert | grep -v grep

# 查看已转换文件数和总文件数
echo "已转换: $(ls ~/knowledge/articles_baidu/ | grep -v '\.tmp$' | wc -l)"
echo "总源文件: $(find ~/baidupan_docs/ -type f 2>/dev/null | wc -l)"

# 查看当前 LibreOffice 正在转换的文件
ps aux | grep soffice | grep -v grep | awk '{for(i=10;i<=NF;i++) printf "%s ", $i; print ""}'

# 查看最新转换完成的文件
ls -lt ~/knowledge/articles_baidu/ 2>/dev/null | grep -v '\.tmp$' | head -10

# 查看最早的转换文件（确认开始时间）
ls -ltr ~/knowledge/articles_baidu/ 2>/dev/null | head -5

# 查看源目录文件类型分布（估算剩余耗时）
FILES=$(find ~/baidupan_docs/364769201_andymao76/ -type f 2>/dev/null)
echo "doc文件: $(echo \"$FILES\" | grep -ic '\.doc$')"
echo "docx文件: $(echo \"$FILES\" | grep -ic '\.docx$')"
echo "pdf文件: $(echo \"$FILES\" | grep -ic '\.pdf$')"
echo "其他文件: $(echo \"$FILES\" | grep -vic '\.\(doc\|docx\|pdf\)$')"
```

**速率估算：**
- `.md` / `.txt` / `.html` 文件：秒级完成
- `.docx` / `.pdf` 文件：几秒到几十秒
- `.doc` 文件（LibreOffice 转 docx）：30秒到2分钟/个（大文件可能更久）
- 平均速率约 5-10 个/分钟（大量 .doc 时降至 1-2 个/分钟）

根据已转换数量/时间可推算剩余时间。

### 导入后核查

导入完成后执行标准化三步核查（遗漏检查 → 索引完整性 → 搜索验证），详见 `references/baidupan-import-verification.md`。

### ZIP 文档导入（中文编码注意事项）

从 Windows 来源的 ZIP 文件（尤其是厂商中文文档包）使用 GBK/GB18030 编码的中文文件名，直接 `unzip` 会显示乱码：

```bash
# ❌ 错误 — 中文文件名变成乱码
unzip 华为LI标准协议翻译.zip
# → ╗к╬кLI▒ъ╫╝╨н╥щ╖н╥ы/  # 乱码目录名

# ✅ 正确 — 指定 GBK 编码
unzip -O gbk 华为LI标准协议翻译.zip -d 华为LI标准协议翻译
```

**导入工作流（ZIP → 知识库）：**

1. `unzip -O gbk file.zip -d output_dir`
2. 检查实际文件名：`ls -la output_dir/`
3. 重点文件处理：
   - `.docx` → `pandoc -t markdown --wrap=none` 提取为 .md
   - `.asn` → 直接复制（ASN.1 纯文本，UTF-8 编码一般无问题）
   - `.html`(差异对比) → `pandoc -t plain` 提取可读内容
4. 创建索引入口 `.md`（含 YAML frontmatter + wikilinks 链接到相关知识库文档）

frontmatter 标准格式：
```yaml
---
title: <文档标题>
tags:
  - <领域标签1>
  - <领域标签2>
links:
  - "[[关联知识库文档1]]"
  - "[[关联知识库文档2]]"
created: <YYYY-MM-DD>
source: <原始文件路径>
---
```

4. 创建索引入口 `.md`（含 YAML frontmatter + wikilinks 链接到相关知识库文档）
5. 文件放入 `~/knowledge/research/<主题>/` 目录
6. `python3 ~/.hermes/scripts/kb-search.py refresh` 重建搜索索引
7. 在屏幕上总结内容要点

### 多文件 ZIP 处理模式

当 ZIP 包含多种文件类型时（如 .docx + .asn + .html 差异对比），一次性并行处理：

```
步骤1: unzip -O gbk → 确认目录结构
步骤2: 分类处理每个文件类型
  ├── .docx → pandoc -t markdown --wrap=none 提取到同目录
  ├── .asn  → 直接复制到知识库（纯文本）
  └── .html → pandoc -t plain 提取为文本（差异对比摘要）
步骤3: 创建索引入口 .md + ASN.1 Tag 映射表（如有）
步骤4: 所有文件统一放入 ~/knowledge/research/<主题>/
`python3 ~/.hermes/scripts/kb-search.py refresh`
步骤6: 屏幕总结每个文件的关键内容
```

注意 `.docx` 提取完成后输出行数和字符数确认完整性。

### `.tag.log` / `.tag` 文件导入（ASN.1 Tag 映射表）

格式为 `type_name: <name> schema_type: <type> tags <hex>` 的文件通常是 ASN.1 Tag 索引：

**处理工作流：**

1. 完整读取文件
2. 按功能分类分组（基础标识、用户标识、位置信息、SMS、EPS 参数、5GS 参数、地理形状、速度、定位、会话管理等）
3. 每类一个 Markdown 表格（变量名 | Schema 类型 | BER Tag）
4. 创建独立的参考文件 `~/knowledge/research/<主题>/<描述>_Tag映射表.md`
5. 更新索引入口文档增加链接
6. `python3 ~/.hermes/scripts/kb-search.py refresh` 重建索引

**注意**：`0x80-0xBF` 区间为 ASN.1 context-specific tag 的常见范围，`0xA0+` 通常是 constructed (SEQUENCE/SET/CHOICE) 类型。

注意：`.docx` 内嵌的图片（media/ 目录资源）在 pandoc 转换后以 `![](media/image1.png)` 形式引用，在纯文本语境中不可见但保留引用标记。

#### 已知限制与排障

- bypy 免费版下载速度较慢（80~200KB/s），大文件建议分批下载

**kb-search.py embed 的 SQLite 游标陷阱**

`kb-search.py embed` 遍历 chunks 表时，如果使用 `for row in cursor.execute(...)` 并在循环内 `conn.commit()`，SQLite 游标会在 commit 后失效，循环只执行一次就退出。

**症状**：每次跑 embed 只处理 50 段就显示「✅ 嵌入完成: 50/72115」

**修复**：先将所有行读到内存再遍历，而非在游标迭代中 commit：

```python
# ❌ 错误 — commit 使游标失效
for row in cursor.execute("SELECT ... WHERE embedding IS NULL"):
    batch.append(...)
    if len(batch) >= 50:
        conn.commit()  # 游标失效，循环退出

# ✅ 正确
all_rows = list(cursor.execute("SELECT ... WHERE embedding IS NULL"))
for row in all_rows:
    batch.append(...)
    if len(batch) >= 50:
        conn.commit()  # 安全，遍历的是内存列表
```

验证：`python3 ~/.hermes/scripts/kb-search.py status` 看嵌入数持续增长
- bypy 只能操作网盘的 `/apps/bypy/` 目录，需手动把文件移入该目录
- CHM 文件解压依赖 `p7zip`：`apt install p7zip-full`
- LibreOffice 转换 `.doc` 时需 `libreoffice-writer` 包
- 大量 PDF 并发转换耗时较长（每个 30s~2min），建议 `--limit 20` 分批
- **kb-search.py 批量嵌入**：SQLite 游标在循环内 `commit()` 会失效，详见 `references/kb-search-sqlite-cursor-pitfall.md`

**大 .doc 文件 LibreOffice 超时处理：**
- 10MB+ 的旧版 .doc 文件（如 25331-4k0-RRC Protocol.doc 17MB）经常导致 LibreOffice 在默认 120 秒超时内无法完成转换
- 症状：日志显示 `doc→md 失败: Command '['libreoffice', ...]' timed out after 120 seconds`
- 排障步骤：先 `ps aux | grep -i libre | grep -v grep` 确认无僵尸进程残留；杀掉残留进程 `pkill -9 libreoffice; pkill -9 soffice.bin`；清理遗留的 `.docx` 中间文件
- 两种应对方式：
  1. 临时排除大文件：`mv <file>.doc ~/baidupan_docs/excluded/`，先跑完其他文件
  2. 修改脚本中的 `timeout=120` 为 `timeout=300`（适合网络稳定的大文件环境）
- 已被排除的 2 个大文件存放在 `~/baidupan_docs/excluded/`

**FTS5 验证检索超时：**\n- 知识库超过 300 个文件（~75MB 索引）后，FTS5 搜索可能超时（未 optimize）\n- `baidupan_convert.py` 索引重建后已自动执行 `optimize`\n- 手动修复：`python3 -c "import sqlite3; conn=sqlite3.connect('/home/andymao/.hermes/knowledge_index.db'); conn.execute('INSERT INTO knowledge_fts(knowledge_fts) VALUES(\"optimize\")'); conn.commit()"`\n- 优化后搜索毫秒级

## Holographic Memory 使用

Holographic 插件已在 config.yaml 中配置（当前可能被 open-second-brain 替代，取决于 `memory.provider` 设置）：
- 数据库位置: `~/.hermes/memory_store.db`
- 当前事实数: ~101 条（含知识库概览/通信技术/API文档/运维笔记/Agent趋势 5 大类）
- 使用 `fact_store` 工具（action=add/search/probe/reason）
- 使用 `fact_feedback` 工具训练信任评分（action=helpful/unhelpful）

> 当前 memory provider 为 open-second-brain。切换回 holographic 或查看 provider 状态见 `hermes-obsidian-sync` skill 的 `references/open-second-brain-install-records.md`。

### 常用操作

```
# 存事实
fact_store(action='add', content='用户偏好简洁回复', category='user_pref')

# 搜索
fact_store(action='search', query='部署配置')

# 探针（查询某个实体的所有事实）
fact_store(action='probe', entity='Andymao76Bot')

# 跨实体推理
fact_store(action='reason', entities=['代理', 'Telegram'])

# 反馈训练
fact_feedback(action='helpful', fact_id=5)
```

## 知识库文件搜索

使用 `kb-search.py`（推荐，FTS5+语义混合，阿里云百炼/SiliconFlow）或旧版 `search_knowledge.py` 在 ~/knowledge/ 目录中搜索：

```bash
python3 ~/.hermes/scripts/kb-search.py init          # 初始化FTS5全文索引（快速，无API）
python3 ~/.hermes/scripts/kb-search.py embed         # 生成语义嵌入向量（可选，需API）
python3 ~/.hermes/scripts/kb-search.py search "关键词" # 搜索（关键词FTS5 + 语义混合）
python3 ~/.hermes/scripts/kb-search.py status        # 查看索引状态
python3 ~/.hermes/scripts/kb-search.py refresh       # 增量更新

# 旧版（仅FTS5）：
python3 ~/.hermes/scripts/knowledge/search_knowledge.py "关键词" --limit 10
```

脚本会自动重建索引（增量更新），无需手动操作。

### FTS5 自动去重机制（2026-06-08 修复）

知识库中可能存在同名文件被多次复制到不同子目录的情况（如同一个文件同时存在于 `articles_baidu/` 和 `移动通信相关/`）。索引脚本使用 `os.path.realpath()` 识别硬链接/同名文件真实路径，确保每个物理文件只被索引一次：

```python
real = os.path.realpath(f)
if real in seen_paths:
    continue
seen_paths.add(real)
```

**验证去重效果**：
```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('/home/andymao/.hermes/knowledge_index.db')
cur = conn.execute('SELECT COUNT(*) FROM knowledge_fts')
total = cur.fetchone()[0]
cur = conn.execute('SELECT COUNT(DISTINCT filepath) FROM knowledge_fts')
unique = cur.fetchone()[0]
print(f'总行数: {total}, 唯一路径: {unique}')
"
# 预期输出: 总行数和唯一路径数一致（如 423=423）
```

### FTS5 搜索注意事项

- SQLite FTS5 默认分词器**不支持 CJK 分词**，中文搜索用英文关键词或单字
- 「OpenAI 别名陷阱」搜不到 → 搜「OpenAI」；「Q.850」报 parsing error → 搜「Q850」；含连字符的 `SWE-bench` → 搜 `SWEbench`
- `--rebuild` 可以**独立运行，不需要提供 query 参数**：
```bash
python3 ~/.hermes/scripts/knowledge/search_knowledge.py --rebuild
# → {"action": "rebuild", "count": 425, "message": "索引重建完成，共 425 条"}
```
可在 cron job 的末尾调用（已配置在"AI Agent 每周调研" cron 中）。

## 调研工作流

### 调研→入库闭环 (Research-to-Knowledge Pipeline)

当进行技术调研时，遵循「搜索→提取→过滤→结构化→写入→索引→验证」闭环：

1. **多维度 web_search** — 同时搜索英文和中文关键词，覆盖标准、厂商、社区
2. **web_extract 提取** — 选 4-6 个最权威的来源
3. **来源筛选（关键）** — 保留 3GPP/ETSI/IETF 标准、厂商官方文档、专家经验；排除营销页面、无法验证的博客、过时草案
4. **归纳为结构化章节** — 架构图 → ASCII 时序图 → 表格速查 → 排障场景 → 工具命令
5. **加入「常见误解纠正」章节** — 如 401≠错误、Diameter Result-Code 需结合 Experimental
6. **写入 `~/knowledge/research/`** — 命名含技术关键词
7. **重建 FTS5 索引并验证** — 用 3+ 组关键词确认可检索

**已完成的技术调研产物**：
| 文件 | 大小 | 涵盖 |
|------|------|------|
| `research/IMS_SIP信令流程与排障指南.md` | 22KB | IMS 注册/呼叫 SIP 流程、Diameter Rx、QCI |
| `research/2G_3G呼叫流程与排障指南.md` | 31KB | GSM/UMTS MO/MT、CSFB、Q.850 原因码 |

### 创建目录索引笔记

当知识库的某个子目录文件增多后（如 `articles_baidu/` 有 378 个文件），可以创建索引笔记来集中管理：

1. **扫描目录文件列表**：`search_files(pattern="*.md", path="~/knowledge/<dir>/", target="files")`
2. **按文件名关键词分类**：基于文件名中的技术关键词（5G/IMS/LTE/核心网/华为/爱立信等）分组
3. **写入索引笔记**：创建 `~/knowledge/<目录>_索引.md`（含 YAML frontmatter: created/description/tags）
4. **格式**：每类一个二级标题→文件清单→末尾标注数量→汇总表
5. **验证**：FTS5 搜索确认索引笔记可检索

不要读取文件内容，只根据文件名关键词分类。典型产物大小约 20KB/552 行/19 个分类。

### 多源 MCP 调研

当小红书/知乎/CSDN/Wikipedia/Taobao MCP 已配置时，可扩展为**多源交叉验证**：

**推荐组合工作流：**
```
小红书搜索（用户反馈 + 热点发现）
    ↓
知乎搜索（深度分析 + 行业趋势）
    ↓
CSDN/AtomGit搜索（代码实战 + 框架教程）
    ↓
Wikipedia 搜索（概念定义 + 背景知识）
    ↓
web_search（官方文档 + 英文资源）
    ↓
结构化整理 → 写入knowledge/research/ → FTS5索引验证 → （可选）多平台推送
```

### 各平台特点

| 平台 | 擅长 | 不擅长 |
|------|------|--------|
| 小红书 | 真实用户反馈、产品体验、评论区价值高 | 深度技术分析较少 |
| 知乎 | 深度技术分析、框架对比、行业趋势 | 信息更新速度不如小红书 |
| CSDN/AtomGit | 技术教程、代码实战、框架文档 | 用户反馈较少 |
| Wikipedia | 概念定义、背景知识、标准化术语 | 无时效性内容、不覆盖产品评测 |
| web_search | 综合补全、官方文档、英文资源 | 无差异化内容 |

### MCP 子进程代理问题

MCP 服务器作为 stdio 子进程启动时，**不会自动继承**父 Hermes 进程的 `HTTPS_PROXY`/`HTTP_PROXY` 环境变量。如需代理访问被墙网站，必须在 `config.yaml` 的 `mcp_servers.<name>.env` 中显式设置。

详见 `references/mcp-proxy-env-quirks.md`

## 周期性自动化调研（Cron Job + 多平台推送）

调研类任务可以设置为 cron job，按周期间自动执行并推送到微信/Telegram/Discord：

**典型配置：**
```bash
hermes cron create "0 12 * * 6" \
  --name "AI Agent 每周调研" \
  --skills "xiaohongshu-research-to-kb" \
  --deliver "telegram,discord,weixin" \
  --prompt "<完整的调研指令>"
```

cron job 的 prompt 应包含：搜索→筛选→提取→整理→推送→存档的完整链路。
推送使用 `send_message` 工具发送结构化中文摘要（分层要点+表格）。
完整笔记同时用 write_file 保存到 `~/knowledge/research/`。

现有周期性调研 cron job：
- AI Agent 每周调研 — 每周六 12:00 → 微信/Telegram/Discord（详见 cronjob list）
- GitHub 生态项目每日调研 — 每天 10:00，搜索 hermes-agent 相关项目并对比知识库

GitHub 生态监控的工作流细节、`gh` 字段名陷阱（`stargazersCount` vs `stargazerCount`）、多关键词搜索策略等详见 `references/github-ecosystem-monitoring.md`。

## HTML 可视化图表创建

当需要将调研结果以可视化 HTML 图表形式呈现时（健康指南、对比表、教育内容等非技术类主题），参考 `references/infographic-html-creation.md` 中的设计系统和工作流。包含：暗色主题 CSS、分级标签、统计卡片、纵向时间线、检查清单等组件模板。

工作流：research → create HTML → xdg-open 用 Chrome 打开 → 同时保存 Markdown 到知识库。

与 architecture-diagram 的区别：architecture-diagram 适合 SVG 技术架构图，本参考适合卡片/表格/时间线类的信息型 HTML 图表。

## 知识库维护：检查并迁移散落的笔记

**核心规则：知识库笔记不能放在 Hermes config.yaml 或 ~/.hermes/ 目录下。** config.yaml 只放配置项（provider、model、tools 等），`prefill_knowledge_prompt.json` 是 agent 系统指令（非知识笔记），保留在 `.hermes/`。其余知识类的 .md 文件发现一个迁移一个。

### 审计流程

当接到指令检查 config 目录下的知识笔记时：

1. **搜索 config.yaml** — 确认无知识内容嵌入（配置项的 value 不应是知识笔记正文）
2. **扫描 `.hermes/` 根目录** — `search_files(pattern="*.md", path="~/.hermes/", target="files")` 排除 skills/ plugins/ logs/ 等子系统目录，只看根目录
3. **文件分类判定**：每份文件归属
   - `SOUL.md` / `EXIT_REASON.md` — 系统/运行时文件，不是知识笔记，保留
   - 非 SKILL.md 的指南/教程类 `.md` — 知识笔记，需迁移
   - `prefill_*.json` — 系统指令配置，不是知识笔记，保留
4. **迁移目标目录**：`~/knowledge/Hermes/`（Hermes 相关笔记）、`~/knowledge/notes/`（通用笔记）、或按内容分类到 `research/` / `编程规范/` / `数据库相关/` / `AI_Agent相关/` 等对应子目录
删除源文件：确认目标内容一致后 `rm` 移除 `.hermes/` 下的副本

**关键判定：** `prefill_knowledge_prompt.json` 是 agent prefills 指令（定义行为模板），不是知识笔记，不应迁移。只迁移实际的知识内容文件。

## 从 ~/Documents/ 和 ~/ 导入已有知识文档

如果 ~/knowledge/ 目录为空或稀疏，而用户已有文档散落在 ~/Documents/ 和 ~/ 根目录：

1. **扫描源头**: `find ~/Documents ~/ -maxdepth 1 -name "*.md" -o -name "*.txt" 2>/dev/null`
2. **分类映射**:
   - 电信/协议/标准文档 (3GPP, ETSI, TS 系列) → `~/knowledge/research/`
   - 部署方案/架构设计/笔记 → `~/knowledge/notes/`
   - 热点/日报 → `~/knowledge/daily/`
   - 纯文本原文 vs Markdown 渲染 → 都放 research/ 并不冲突
3. **复制而非移动**: 用 `cp` 保留原位置文件，只在 knowledge 中建立副本
4. **去重检测**: `diff` 比较目标文件与源文件，内容相同则跳过复制
5. **导入后验证**: `find ~/knowledge -type f | wc -l` 统计总数；`du -sh ~/knowledge/` 统计总大小
6. **FTS5 搜索确认**: 用搜索脚本检查新文件是否可检索

注意：~/Documents/ 中的大文件 (5MB+ 如 3GPP 协议全文) 导入后 knowledge 大小会从几 KB 跃升到数 MB，这是正常的。

## 会话挖掘入库 (Session Mining)

**最重要的知识来源之一：从你与 Hermes Agent 的历史对话中提炼实战经验。** 每次排错、配置、架构讨论都可能产出值得保存的知识。

### 挖掘流程

1. **用 session_search 发现候选会话** — 多维度搜索定位有价值的会话
2. **用 session_search 滚动浏览** — 定位到关键消息范围，精确读取
3. **提炼为结构化笔记** — 提取的内容分九大类：systemd 服务陷阱、消息平台集成、Provider/模型配置、Open WebUI + Bridge 整合、Dify 部署、截图/文件工作流、硬件/文件系统、工具链、故障排查速查表
4. **写入 knowledge/notes/** — Markdown 格式，命名含关键词 + 日期
5. **重建 FTS5 索引并验证** — 写完后验证可检索

详见 `references/session-mining-example.md`、`references/hermes-backup-recovery.md`、`references/incremental-backup-system.md`、`references/ops-english-glossary-pattern.md`

## 本地文件目录→Obsidian 知识图谱工作流

当需要将本地已有的文件目录（如百度网盘下载的技术资料）组织成 Obsidian 知识图谱时，遵循以下流程：

### 触发场景
- 用户说「把这些资料整理到知识库，通过 Obsidian 整理并生成知识图谱」
- 发现 `/mnt/backup/` 或 `~/Downloads/` 下有大量未整理的行业文档
- PDF/PPT/DOC 等原始文件保持在原位置不动，只创建 Markdown 索引笔记

### 步骤

**1. 摸底扫描**
```bash
# 查看目录结构
find /目标目录 -maxdepth 2 -type d | head -80

# 查看各子目录大小，识别重点
du -sh /目标目录/*/ | sort -rh | head -20

# 深入展开每个子目录
ls -la /目标目录/<子目录>/
```

**2. 按技术领域分类**
根据目录名和文件名中的关键词归类。例如 LI 领域的关键词映射：
| 目录/关键词 | 领域分类 | 关联标签 |
|------------|---------|---------|
| 5GC, SUCI, PDU会话 | 5GC 核心网 | 5GC, 5G核心网 |
| EPC, MME, SGW, PGW, LTE-TDD | EPC 核心网 | EPC, 4G核心网 |
| 2G, 3G, GSM, UMTS, WCDMA, HLR, HSS, MSC, MGW | 2G/3G 核心网 | 2G, 3G, GSM, UMTS, IMS |
| 7750 SR, MG, Mobile Gateway | 诺基亚 7750 SR | 7750SR, 诺基亚 |
| 5620 SAM | SAM 运维管理 | 5620SAM, 网管 |
| ASN.1, 3GPP, 正则 | 3GPP 规范 | ASN.1, 3GPP |
| EVE-NG, Lab | 实验环境 | EVE-NG, 模拟器 |
| HW, 华为, USN9810, UMG, M2000, MSOFTX3000 | 华为 LI 体系 | HW, 华为, CS, PS, LI |
| ZTE, 中兴, ZXWN, ZTELIG | ZTE LI 体系 | ZTE, 中兴, LI |
| Ericsson, 爱立信, MSC, EIP, ENM | 爱立信 LI 体系 | Ericsson, 爱立信, LI |
| NSN, 诺西, Nokia, FlexiNG, HLRI | NSN LI 体系 | NSN, 诺西, LI |
| UTIMACO, Utimaco | UTIMACO LI 体系 | UTIMACO, LI |
| ETSI, HI1, HI2, HI3, X1, X2, X3, CORBA | LI 标准规范 | ETSI, 3GPP, LI标准 |
| OWLS, SICMS, TMC, Linsener | LI 管理平台 | OWLS, SICMS, TMC |

**3. 创建总索引笔记**
`~/knowledge/research/<领域>-index.md`，格式：
```yaml
---
title: <领域> 技术资料库总索引
tags: [标签1, 标签2, ...]
created: YYYY-MM-DD
---
# <领域> 技术资料库总索引

## 目录分类

### [[子笔记1]]
说明

### [[子笔记2]]
说明

## 关联标签
#标签1 #标签2

---
**物理路径**：`/源目录/`
```

**4. 为每个子类创建独立笔记**
- 笔记写入 `~/knowledge/research/` 目录
- 必须包含 YAML frontmatter（title/tags/created/aliases）
- 使用 `[[wikilinks]]` 双向关联相关笔记
- 内容以**表格**为主整理文件清单（文件名 | 说明 | 大小）
- 结尾加「关联笔记」分区，把本领域相关的其他笔记用 wikilink 列出

**5. 知识图谱可视化**
创建 SVG 知识图谱展示笔记间关联关系：
- 4-6 层结构：总索引 → 核心领域 → 子专题 → 厂商/体系 → 标准 → 管理平台
- 每层用不同颜色区分（总索引 amber，5GC cyan，EPC emerald, 等等）
- **等距布局计算**：每层 N 个框体，框宽 w，需等距分布。公式：总宽度 = N×w + (N+1)×gap，gap = (canvas_w - N×w) / (N+1)。验证：left_margin + N×w + N×gap + right_margin = canvas_w。每次增删框体必须重新计算全部 x 坐标，不能手动微调
- 实线=强关联（直接引用），虚线=弱关联（间接引用）
- 底部加图例
- 输出 `.html`（可编辑源）+ `.svg`（独立矢量图）双格式
- SVG 导出确保 XML 有效（用 `ET.parse` 验证），注意 `&` 需转义为 `&amp;`

**6. 关联已有笔记**
链接知识库中已存在的相关笔记。如 LI 领域可关联：
- `[[3GPP 标准研究笔记]]` — 已有知识库内容
- 其他 `research/` 目录下的技术笔记

**7. 更新索引**
```bash
cd ~/knowledge && python3 ~/.hermes/scripts/kb-search.py refresh
```

### 关键原则
- **原始文件不动**：PDF/PPT/DOC/ZIP 保留在原路径，Markdown 索引笔记只记录路径引用
- **表格优先**：文件清单用表格（文件名 | 说明 | 大小），避免散文段落
- **wikilinks 双向关联**：每个子笔记的末尾必须列出所有相关的兄弟/父笔记
- **knowledge graph SVG**：用 architecture-diagram skill 的样式生成，确保 XML 有效
- **每层一个颜色**：不同知识领域用不同色系区分，一目了然
- **版本号追踪**：每次生成知识图谱后，在副标题标注版本号。大架构改动（增删厂商层级/网络代际）→ 大版本+1；小修改（标题修正/连线调整/标签更正/名称修正如 NISS→SICMS）→ 小版本+1。更新前先读文件确认当前版本。版本格式 `vN.N` 标注在 SVG/HTML 副标题和文件注释中，同时记录到 memory
- **迭代审查循环**：图谱生成后用户会审查并指出缺失或不准确之处，这是正常流程。常见的反馈：遗漏厂商、遗漏网络代际、名称不准确、框体重叠。每次修复后递增小版本号

### 领域关键词分类映射（示例：LI 技术资料）
当整理特定领域（如合法监听/LI）的资料时，按以下关键词映射分类：

| 目录/关键词 | 领域分类 | 关联标签 |
|------------|---------|---------|
| 5GC, SUCI, PDU会话 | 5GC 核心网 | 5GC, 5G核心网 |
| EPC, MME, SGW, PGW, LTE-TDD | EPC 核心网 | EPC, 4G核心网 |
| 2G, 3G, GSM, UMTS, WCDMA, HLR, HSS, MSC, MGW | 2G/3G 核心网 | 2G, 3G, GSM, UMTS, IMS |
| 7750 SR, MG, Mobile Gateway | 诺基亚 7750 SR | 7750SR, 诺基亚 |
| 5620 SAM | SAM 运维管理 | 5620SAM, 网管 |
| ASN.1, 3GPP, 正则 | 3GPP 规范 | ASN.1, 3GPP |
| EVE-NG, Lab | 实验环境 | EVE-NG, 模拟器 |
| HW, 华为, USN9810, UMG, M2000, MSOFTX3000 | 华为 LI 体系 | HW, 华为, CS, PS, LI |
| ZTE, 中兴, ZXWN, ZTELIG | ZTE LI 体系 | ZTE, 中兴, LI |
| Ericsson, 爱立信, MSC, EIP, ENM | 爱立信 LI 体系 | Ericsson, 爱立信, LI |
| NSN, 诺西, Nokia, FlexiNG, HLRI | NSN LI 体系 | NSN, 诺西, LI |
| UTIMACO, Utimaco | UTIMACO LI 体系 | UTIMACO, LI |
| ETSI, HI1, HI2, HI3, X1, X2, X3, CORBA | LI 标准规范 | ETSI, 3GPP, LI标准 |
| OWLS, SICMS, TMC, Linsener | LI 管理平台 | OWLS, SICMS, TMC |

**多厂商 LI 技术资料知识库（15 篇笔记）：**

**网络设备与标准层：** `research/5gc-core-network.md`、`research/5gc-suci-identifier.md`、`research/epc-core-network.md`、`research/2g-3g-core-network.md`、`research/nokia-7750-sr-technical-manual.md`、`research/5620-sam-management.md`、`research/asn1-3gpp-spec-analysis.md`、`research/eve-ng-lab-environment.md`

**多厂商 LI 体系层：** `research/huawei-li-system.md`、`research/zte-li-system.md`、`research/ericsson-li-system.md`、`research/nsn-li-system.md`、`research/utimaco-li-system.md`

**标准与平台层：** `research/li-standards-specifications.md`、`research/owls-niss-tmc-platform.md`（标题已更新为 OWLS/SICMS/TMC）

- SVG 图谱：`research/li-knowledge-graph.svg`
- HTML 图谱：`research/li-knowledge-graph.html`

## 已安装的 MCP 服务器速查

当前环境安装了 6 个 MCP 服务器，共 61+ 个工具：

| MCP | 工具数 | 说明 |
|-----|:------:|------|
| db-query | — | 本地 SQLite 数据库查询 |
| xiaohongshu | 13 | 小红书内容搜索/发布/互动 |
| zhihu | — | 知乎内容搜索 |
| csdn | — | CSDN 内容搜索 |
| wikipedia | 22 | 中文 Wikipedia（需代理） |
| taobao | 2 | 淘宝/天猫商品查询（需初始化登录） |

最后，`chinese-platform-mcp-adapters` 技能下还有一个 `references/hongkong-bank-account-guide.md`（香港渣打银行卡国内办理指南），涉及跨境金融的实操信息。

## 特殊格式文件导入（XMind/drawio/Visio）

XMind 脑图、drawio 流程图、Visio 图表等非 Markdown 格式文件的解析和导入方法详见 `references/specialized-file-import.md`。

## SiliconFlow 官方文档库

从 https://docs.siliconflow.com/llms-full.txt 摄取的 10 份使用手册已存入 `~/knowledge/SiliconFlow_*.md`，涵盖文本生成、视觉、视频、图片、TTS、推理、Function Calling、代码补全等全部功能模块。详见 `references/siliconflow-knowledge-bank.md`。

## DeepSeek API 官方文档库

从 https://api-docs.deepseek.com/zh-cn/ 摄取，存入 `~/knowledge/DeepSeek_*.md`，涵盖首次调用、模型价格、Token 计算、限速、思考模式、Tool Calls、JSON Output、对话前缀续写、FIM、上下文缓存、Anthropic API 兼容等。详见 `references/deepseek-knowledge-bank.md`。

## 阿里云百炼 (Bailian) 文档库

从 https://help.aliyun.com/zh/model-studio/ 摄取，存入 `~/knowledge/阿里云百炼_*.md`。已配置为 Hermes provider (bailian, qwen-plus, 华北2北京)。涵盖平台概览、API Key 获取、地域选择、限流规则、免费额度、完整价格表等。详见 `references/bailian-knowledge-bank.md`。

## 文档即学模式（用户分享 → 存知识库）

用户常直接粘贴文档或 URL 说「学习这个」「放到知识库里」。完整标准工作流见 `references/document-learning-workflow.md`，从本地文件（DOCX/PDF 等）提取入库见 `references/document-learning-from-local-files.md`。核心要点：

### 跨技能知识注入（文档→技能更新闭环）

当用户提供完整的技能/知识文档时（如技能图谱、运维指南），除了保存到知识库，还需同步评估并更新相关 Hermes 技能：

**工作流：**
1. **读取全文** — 大文件分段读取确认内容范围
2. **技能覆盖分析** — skill_view() 读取相关领域的所有技能，逐技能评估：
   - 空占位符 → 需全面充实
   - 内容不足 → 需补充新章节
   - 已有完善 → 无需操作
3. **展示分析表给用户确认** — 表格格式（技能 | 现状 | 建议操作）
4. **并行更新** — 使用 delegate_task 同时更新多个技能（经验证安全高效）
5. **保存原文到知识库** — 按内容领域分类（知识/大数据/等）
6. **刷新索引** — enzyme refresh 或 kb-search.py refresh

**陷阱：**
- 技能注册名可能与文件系统目录名不一致（如注册为 `hdfs-ops` 但目录为 `hdfs-expert`），使用 `skill_view()` 准确获取实际名称
- delegate_task 最多 3 个并行，超出的分批次
- 更新前保留 YAML frontmatter 不变

核心要点：

1. **读取全文** — 大文件分段读取，确认读到末尾。优先尝试 web_extract，被阻断时改用 curl + 代理下载 HTML 后本地解析
2. **浓缩归纳** — 保留关键规则编号和核心要求，比例约 10:1~15:1，用表格替代段落
3. **YAML frontmatter** — 必须含 title/tags/created/source（填来源 URL）
4. **目录选择** — 编程规范→`编程规范/`，协议→`research/`，数据库→`数据库相关/`，AI→`AI_Agent相关/`
5. **`python3 ~/.hermes/scripts/kb-search.py refresh`** — 写完必须重建搜索索引
6. **添加 wikilinks** — 链接 2-3 个相关笔记

**关键原则：** 不逐段回应，一次总结完。文件名用中文。大文件确认 `truncated: false`。

**页面类型检测技巧：**
- JS 渲染 SPA 的特征：HTML 内容极少（几 KB），`<div id="root">` 为空，大量 `<script>` 标签
- **飞书/Lark 文档特殊技巧**：官方文档链接后加 `.md` 可直接获取 AI 友好的纯 Markdown 版本。如 `https://open.feishu.cn/document/client-docs/h5/.md`
- **静态页面**：直接 curl 或 web_extract 即可
- **回退策略**：web_extract 失败 → curl + 代理下载 HTML → 本地解析。浏览器是最后手段

**电信/LI 协议笔记特有规范**：见 `references/telecom-li-note-template.md` — 含 LI 实战视角、表格优先、双语格式、华为/中兴/爱立信差异对比等模板。

## 小红书 + 知乎 + CSDN 多源MCP调研

详见 `xiaohongshu-research-to-kb` skill 获取完整的搜索→提取→整理→入库流程。

## 备份恢复

知识库和 Hermes 配置的完整备份系统位于 `/mnt/backup/hermes-backup/`，14 步结构化备份：

| 脚本 | 功能 |
|------|------|
| `backup-hermes-incremental.py` | 增量/完整备份（14 步：config → 数据库 → scripts → systemd → knowledge → skills → memories/cron → FTS5 索引 → Obsidian vault → 计算 → 清单 → 指针 → 清理 → 汇总） |
| `inspect-hermes.py` | 健康巡检（备份盘状态、数据库完整性、服务状态） |
| `restore-hermes.py` | 灾难恢复（--dry-run 预览 / --force 自动恢复 + 重启服务） |

第 8 步（FTS5 索引）备份 `knowledge_index.db`（~73MB）并做 integrity_check。
第 9 步（Obsidian vault）备份 `.obsidian/` 配置、`Brain/`（O2B 记忆层）、`.open-second-brain/brain.sqlite`（O2B 索引）。知识库文件由第 5 步独立备份，不通过 vault symlink 路径重复。

备份包含 knowledge/ 目录的全部 .md 文件和 FTS5 索引数据库 `knowledge_index.db`，恢复后知识库完全可用。

每日凌晨 3 点自动增量备份 + 每周日 4 点完整备份（cron job），保留 60 天（2 个月），日志和备份双通道记录。增量模式和调度策略详见 `references/incremental-backup-system.md`。

## 知识库搜索（使用 kb-search.py）

**2026-06-11 已从 Enzyme 完全切换到 `kb-search.py`。**
Enzyme 需要云端信用额度（3 credits），用完需付费。kb-search.py 用本地 FTS5 + SiliconFlow 嵌入，零成本。

```bash
python3 ~/.hermes/scripts/kb-search.py status        # 查看索引状态
python3 ~/.hermes/scripts/kb-search.py search "关键词" # 搜索（优先语义，回退 FTS5）
python3 ~/.hermes/scripts/kb-search.py refresh        # 增量更新
python3 ~/.hermes/scripts/kb-search.py embed          # 生成语义嵌入（首次或增量后）
```

## 语义搜索（kb-index — 替代 enzyme refresh）

**2026-06-26 新增：`kb-index`** — 基于 TF-IDF + LSA 的全本地语义索引，完全替代 enzyme refresh。零网络调用，依赖 scikit-learn（已装到 Hermes venv）。

```bash
# 激活 Hermes venv 后使用
source ~/.hermes/venv/bin/activate

kb-index index --full    # 全量重建索引
kb-index                 # 增量刷新（只索引变更文件）
kb-index search "关键词"  # 语义搜索
kb-index status          # 索引状态
```

示例：`kb-index search "LIS12 HI2 IRI CC SBG 拦截"` 可从不同厂商文档中跨源检索。

**安装/更新**：
所在路径：`~/.local/bin/kb-index`（脚本，直接编辑即可更新）
依赖：Hermes venv 中的 `scikit-learn`、`numpy`、`scipy`（无需 torch）

**国内 pip 安装技巧**（如需补充依赖）：
```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple <包名>
# torch 先用 --no-deps 绕过 NVIDIA CUDA 包，再让下游依赖拉剩余部分
pip install --no-deps -i https://pypi.tuna.tsinghua.edu.cn/simple torch
```

详见 `references/free-semantic-indexing-alternatives.md`。

### 维护参考

- `references/kb-search-maintenance.md` — SQLite 游标批处理陷阱（`commit()` 使游标失效）、嵌入耗时估算

> **旧方案参考（已废弃）：** Enzyme 需要云端信用额度（3 credits），余额不足时返回 `Insufficient credits`。2026-06-11 已完全切换至 kb-search.py。2026-06-26 enzyme 二进制、插件、配置、缓存已全部清理。
>
> 如需 enzyme 以外的免费语义索引方案（txtai / ChromaDB / FAISS / kb-index 等），见 `references/free-semantic-indexing-alternatives.md`。

### 知识库 ↔ Obsidian Vault 双向打通

知识库 `~/knowledge/` 已通过 symlink 挂入 Obsidian vault，Hermes 负责知识生产（调研/排错/采集），Obsidian 负责可视化发现（图谱/反向链接/孤岛检测）。

详见 skill `hermes-obsidian-sync`。

**双向 symlink：**
```bash
cd ~/Documents/Obsidian\\ Vault/
ln -sf ~/knowledge knowledge                # vault -> knowledge

cd ~/knowledge
ln -sf ~/Documents/Obsidian\\\\ Vault/工作 工作  # knowledge -> vault 工作目录
```

**项目状态中心（`_system/project_status.yaml`）：**
所有项目的优先级、下一步操作、进度集中管理。Hermes 查当前最重要的事时读此文件按 priority 排序回答。

**决策日志（`_system/decision_log.md`）：**
关键决策的原因记录，避免 Herems 重复询问用户已定过的事。

当前状态：双向 symlink 已创建，600+ 文件，OBSIDIAN_VAULT_PATH 已设。

### 知识流与图谱质量

```
Hermes 调研/排错
       ↓
  写入 ~/knowledge/research/ 或 notes/
       ↓
  Obsidian 图谱自动出现新节点（因 symlink）
       ↓
  用户在 Obsidian 中手动添加 wikilinks 优化关联
       ↓
  反向链接面板暴露知识间的隐藏联系
```

 云同步方案对比

| 方法 | 优点 | 缺点 |
|------|------|------|
| symlink（当前） | 零成本，实时更新 | Obsidian 不跟踪 symlink 目标的变化时间戳 |
| rsync cron job | 可控制同步方向和时间 | 有延迟，可能产生冲突 |
| Obsidian Git 插件 | 版本历史，可回滚 | 大仓库（400+文件）同步慢 |
| Syncthing | 跨设备，局域网快 | 需要额外配置 |

## 工作日志系统

详见 `references/worklog-manual.md`（日常命令速查、项目映射、输出路径）。

用户当前只有一个活跃项目（A1 PC项目/苏丹NISS）时，记录工作日志不写项目名自动归到默认项目。每天下班前说"生成今天的日报"即可。路径统一到 Obsidian vault 的 `工作/日报/YYYYMMDD.md`（三级分类，工作/知识/技能）。生成日报后同时存入 `~/knowledge/工作/日报/YYYYMMDD.md`（symlink，kb-search 可索引）。

技能文件：
- `~/.hermes/skills/worklog/SKILL.md` — 工作流水账记录
- `~/.hermes/skills/daily_report/SKILL.md` — 日报生成
- `~/.hermes/skills/weekly_report/SKILL.md` — 周报生成
- `~/.hermes/skills/monthly_report/SKILL.md` — 月报生成

## Windows 远程访问（Samba）

详见 `references/obsidian-samba-network-share.md`。

Samba 共享 Ubuntu 上的 Obsidian vault，Windows 通过网络路径打开，不留副本在 Windows。只读模式。

## 社区技能生态

详见 `references/hermes-community-top-skills.md`。

| 技能 | 用途 | 安装 |
|------|------|------|
| Obra Superpowers | TDD/调试/验证门禁 | `git clone https://github.com/obra/superpowers.git ~/.hermes/skills/superpowers` |
| Composio | 1000+ SaaS 集成 | MCP 方式或 CLI 安装 |

发现更多：agentskills.io（官方注册中心）、GitHub wondelai/skills（380+ 社区技能）

## config.yaml 配置

社区技能安装参考：`references/hermes-community-top-skills.md` — Obra Superpowers、Composio 等安装方式。
Copilot CLI ACP 集成：`references/hermes-acp-copilot-cli.md` — 认证、ACP 协议测试、Hermes 调用方式。

```yaml
memory:
  provider: open-second-brain  # 2026-06-08 从 holographic 切换，可用 O2B 替代

# 如果换回 holographic，用以下配置：
# memory:
#   provider: holographic
#
# plugins:
#   hermes-memory-store:
#     db_path: ~/.hermes/memory_store.db
#     auto_extract: false
#     default_trust: 0.5
#     hrr_dim: 1024
```
