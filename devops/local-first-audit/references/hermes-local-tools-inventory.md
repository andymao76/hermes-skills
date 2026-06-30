# Hermes 本地工具清单参考

> 本文件保存 Hermes 环境下可用本地工具的静态清单。用于审计时快速对照。
> 更新时机：安装/移除了本地 CLI 工具后。

## 搜索类

| 工具 | 位置 | 功能 | 零 LLM |
|------|------|------|--------|
| `rg` (ripgrep) | `/usr/bin/rg` | 文件内容正则搜索 | 是 |
| `fdfind` (fd) | `/usr/bin/fdfind` | 文件名 glob 搜索 | 是 |
| `fzf` | `/usr/bin/fzf` | 终端模糊匹配 | 是 |
| `kb-index` | `~/.local/bin/kb-index` | TF-IDF+LSA 本地语义搜索 | 是（完全离线） |
| `enzyme` | `~/.local/bin/enzyme` | **已移除（2026-06-30）**，由 kb-index 替代 | 是 |

## 数据/格式处理

| 工具 | 功能 |
|------|------|
| `jq` | JSON 处理 |
| `python3` + 标准库 | CSV/YAML/TOML 处理 |
| `html2text` | HTML → Markdown |
| `markitdown` | 多种格式→Markdown |
| `mammoth` | DOCX→Markdown |
| `pdfplumber` | PDF 提取 |
| `pytesseract` | OCR（英文） |

## 脚本集合 (`~/.hermes/scripts/`)

| 脚本 | 用途 | 模式 |
|------|------|------|
| `inbox_sorter.py` | 收件箱自动分类（关键词规则） | 纯本地 |
| `feishu_to_inbox.py` | 保存消息到收件箱 | 纯本地 |
| `skill-precipitator.py` | 技能沉淀扫描 | 纯本地 |
| `kb-search.py` | 知识库搜索前端 | 纯本地 |
| `proxy-autoheal.sh` | 代理自愈 | 纯本地 |
| `audit-full-chain.sh` | 安全审计全链路 | 纯本地 |
| `daily-startup-healthcheck.sh` | 每日健康检查 | 纯本地 |
| `github-trending.py` | GitHub 趋势 | 纯脚本 |
| `gas-price-monitor.sh` | 油价监控 | 纯脚本 |
| `remote-healthcheck.sh` | 远程服务器巡检 | 纯脚本 |
| `ops_agent.py` | 运维 Agent 巡检 | 纯本地 |

## 纯本地 cron 任务（已有 no_agent=true）

这些 cron 完全不消耗 LLM token：

- 代理健康检查（每小时）
- L1-L4 多层备份（每日/每周/每月）
- 安全审计推送（每日）
- 汽油价格监控（每日）
- GitHub Trending 日报（每日）
- IMA 知识库备份（每日）
- 技能沉淀扫描（每日）
- 远程服务器巡检（每日）
- Sinovatio 路径检查（每日）
- 每周系统健康检查

## Hermes 内置工具（底层也是本地工具）

| 工具别名 | 底层实现 | 说明 |
|----------|----------|------|
| `search_files(target='content')` | `rg` | 内容搜索，零 LLM 消耗 |
| `search_files(target='files')` | `fd` | 文件名搜索，零 LLM 消耗 |
| `terminal` | bash | 任意 shell 命令 |
| `session_search` | SQLite FTS5 | 对话历史搜索 |
| `read_file` | 直接读文件 | 文件内容读取 |
| `patch` | 本地文本替换 | 文件修改 |

## 本地索引状态（kb-index）

- 文件数: ~1760
- 片段数: ~950K
- 特征数: 50000
- LSA 维度: 256
- 方差保留: ~44%
- 增量更新: `kb-index`（自动检测变更文件）
- 全量重建: `kb-index --full`
- 搜索: `kb-index search <query>`
