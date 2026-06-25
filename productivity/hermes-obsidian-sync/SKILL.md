---
name: hermes-obsidian-sync
description: Hermes Agent 与 Obsidian 双向知识同步方案 — 将 ~/knowledge/ 与 Obsidian vault 打通，使 Hermes 的知识生产能力和 Obsidian 的图谱可视化/双向链接形成互补；含社区 8 个开源项目的调研对比
author: Hermes Agent
tags: [obsidian, knowledge-base, sync, vault, second-brain, graph, open-second-brain, enzyme, troubleshooting]
---

# Hermes ↔ Obsidian 双向知识同步

## 触发条件

当用户提及以下内容时务必加载本 skill：
- "整理 Obsidian" / "管理 Obsidian" / "同步 Obsidian"
- "Obsidian 知识库" / "第二大脑" / "知识图谱"
- "Hermes + Obsidian" / "Obsidian vault"
- "笔记管理" / "整理笔记" / "备份笔记到 Obsidian"
- 跨多个平台搜索如何整合 Hermes 与 Obsidian 时

同时加载本 skill 和 `note-taking/obsidian` skill（官方内置），二者互补：
- `note-taking/obsidian` 用于执行具体的 vault 操作（读/写/搜索笔记）
- 本 skill 用于架构设计、同步方案、社区最佳实践调研

**memory provider 切换说明**：在当前系统中，`hermes memory status` 可能显示 `open-second-brain` 或 `holographic` 作为活跃 provider。本 skill 不依赖具体 provider——symlink 文件同步和知识库搜索始终通过文件系统 + FTS5 工作，与 memory provider 无关。O2B 索引不跟踪 symlink 文件需额外注意。

**Telegram 冲突修复模式**：当 Gateway 日志出现 `Telegram polling conflict — previous session still held open` 或 `Conflict: terminated by other getUpdates request` 时，表示有残留的旧 Gateway 进程阻塞了 Telegram 连接。修复步骤：先用 curl 释放 Telegram 侧残留连接（`getUpdates?timeout=0`），然后 stop → kill 残留 → start gateway。`hermes gateway restart --replace` 不一定够，systemctl stop + kill 残留 + start 最彻底。

## 架构总览

```
┌──────────────────────┐      ┌──────────────────────┐
│  Hermes Agent        │      │  Obsidian Desktop    │
│  知识生产层           │      │  可视化/发现层        │
│                      │      │                      │
│  ┌────────────────┐  │      │  ┌────────────────┐  │
│  │ ~/knowledge/   │  │◄────►│  │ Obsidian Vault │  │
│  │ 422 .md 文件   │  │同步  │  │ (symlink)      │  │
│  │ FTS5 索引      │  │      │  │ 图谱·反向链接   │  │
│  │ Holographic    │  │      │  │ CLI 查询        │  │
│  │ Memory         │  │      │  └────────────────┘  │
│  │ cron 采集     │  │      │                      │
│  └────────────────┘  │      └──────────────────────┘
│                      │
│  调研·排错·会话挖掘   │
└──────────────────────┘
```

## 核心原则

| 职责 | 归属 | 原因 |
|------|------|------|
| **知识生产** | Hermes Agent | 自动调研、排错记录、会话挖掘、cron 采集 |
| **知识发现** | Obsidian | 图谱可视化、反向链接暴露知识关联和孤岛 |
| **知识存储** | 共用的 .md 文件 | 双方都可读写同一份文件 |
| **快速搜索** | Hermes FTS5 | 毫秒级全文搜索，Hermes 会话内检索 |
| **结构化记忆** | Holographic Memory / Open Second Brain | 实体推理、跨会话知识关联 |

---

## 安装

### 方案一：symlink 挂载（推荐，零配置零成本）

将 `~/knowledge/` 目录以符号链接形式挂载到 Obsidian vault 中，Hermes 写文件即 Obsidian 可见，Obsidian 编辑即 Hermes 可搜。

```bash
cd ~/Documents/Obsidian\ Vault/
ln -sf ~/knowledge knowledge
```

**前提检查**：
- vault 路径存在：`~/Documents/Obsidian Vault/`
- knowledge 路径存在：`~/knowledge/`
- 二者在**同一文件系统**（用 `df ~/knowledge/` 和 `df ~/Documents/Obsidian\ Vault/` 对比设备名）

**效果**：
- Obsidian 图谱自动出现 422+ 节点
- 反向链接面板显示关联关系
- 全文搜索（Ctrl+Shift+F）覆盖所有文件
- 标签聚合、属性查询全部可用

> **安全提示**：`~/knowledge/` 是用多平台推送的公开内容目录。如果 vault 中包含私有信息，建议不要将整个 vault 同步到 Hermes。单向 symlink（vault→knowledge）不会将 vault 中其他内容暴露给 Hermes。

#### symlink 兼容性说明

| 场景 | 是否支持 | 说明 |
|------|---------|------|
| Linux/Ubuntu 同文件系统 | 完全支持 | knowledge 和 vault 在同一硬盘分区时完美运行 |
| Linux/Ubuntu 跨文件系统 | 谨慎 | Obsidian 无法跨设备拖拽文件（移动文件变成删除+重建） |
| macOS | 有问题 | Obsidian 0.11.1+ 在 macOS 上已知有 symlink 问题 |
| Windows | 支持 | NTFS junction 或符号链接均可 |
| 生产环境非桌面 CLI | 不支持 | 使用方案二 rsync 代替 |

#### FTS5 与 Obsidian 的关系

FTS5 和 Obsidian **互不冲突**，是独立的两层：

| 方面 | FTS5（search_knowledge.py） | Obsidian 图谱 |
|------|----------------------------|--------------|
| 索引方式 | SQLite FTS5 虚拟表 | Obsidian 内部 metadataCache（内存） |
| 触发时机 | 主动调用脚本时 | Obsidian 启动时自动扫描 |
| 文件锁定 | 只读 .md 文件，写自己的 .db | 只读 .md 文件，不写锁 |
| 数据来源 | 读取 `~/knowledge/` 下 .md 文件 | 读取 vault 目录下 .md 文件 |
| 同一文件 | `os.path.realpath()` 解析到同一实体 | symlink 写穿透到原文件 |

**重复风险**：FTS5 索引脚本已通过 `os.path.realpath()` 去重。即使同一文件在多个子目录中出现硬链接/软链接副本，FTS5 只索引一次。Obsidian 通过 symlink 访问的目录理论上也不会产生重复索引——但若同时将 `~/knowledge/` 和 vault symlink 路径都加入搜索范围（不会发生，因为 FTS5 只扫描 `~/knowledge/` 一个根目录），会出现重复。

**备份隔离**：`/mnt/backup/hermes-backup/backup-hermes-incremental.py` 的第 5 步（知识库）和第 9 步（Obsidian vault）明确隔离——knowledge 文件只通过第 5 步备份原始路径，第 9 步跳过 `knowledge/` symlink 目录和 vault 根目录下的 symlink .md 文件，不会产生重复副本。

Obsidian **v0.11.1+ 已内置 symlink 目录支持**（你的 1.12.7 完全支持），无需额外插件。旧插件 [pjeby/obsidian-symlinks](https://github.com/pjeby/obsidian-symlinks) 已标记为 ARCHIVED。

#### 方案一B：Local REST API + obsidian-mcp-server（AI Agent 原生访问）

For MCP-enabled agents (Hermes, Claude Desktop, Cursor, etc.), the [Obsidian Local REST API plugin](https://github.com/coddingtonbear/obsidian-local-rest-api) provides authenticated HTTP + MCP access to the vault — CRUD, search, tags, commands, periodic notes, surgical patching.

**Install & configure:**

1. In Obsidian: Settings → Community plugins → Browse → Search "Local REST API" (coddingtonbear) → Install & Enable
2. Go to Settings → Local REST API → Copy the API key
3. Enable the obsidian-mcp-server in Hermes config:
```yaml
# ~/.hermes/config.yaml
  obsidian:
    command: /home/andymao/.npm-global/bin/obsidian-mcp-server
    connect_timeout: 30
    enabled: true
    env:
      OBSIDIAN_API_KEY: "<your-key>"
    timeout: 60
```
4. Reload MCP: `hermes mcp reload` (or restart gateway)
5. Verify: `curl -sk https://127.0.0.1:27124/` → `{"status":"OK"}`

**Rest API endpoints** (plugin v4.1.3):
- `GET /vault/` — List files
- `GET /vault/{path}` — Read note
- `PUT /vault/{path}` — Write note
- `PATCH /vault/{path}` — Surgical edit (heading/block/frontmatter)
- `POST /search/simple/` — Full-text search
- `GET /tags/` — All tags with counts
- `GET /commands/` — List available commands
- `POST /commands/{id}/` — Execute command
- `GET/POST /mcp/` — MCP endpoint (Streamable HTTP)

**Pitfalls:**
- The API key is a Bearer token — store it in config.yaml's `env.OBSIDIAN_API_KEY`, not in .env
- The plugin listens on `https://127.0.0.1:27124` (self-signed cert; use `-k` with curl)
- HTTP fallback at `http://127.0.0.1:27123/` if enabled in plugin settings
- MCP endpoint at `https://127.0.0.1:27124/mcp/` — also accessible via the npm `obsidian-mcp-server` package

### 方案二：rsync 双向同步（跨文件系统 / macOS / 服务器环境）

当 symlink 不可用或不可靠时：

```bash
# knowledge → vault（Hermes 生产 → Obsidian 消费）
rsync -a --delete ~/knowledge/ ~/Documents/Obsidian\ Vault/知识库/

# vault → knowledge（Obsidian 笔记 → Hermes 可检索）
find ~/Documents/Obsidian\ Vault/ -name "*.md" -newer ~/knowledge/.last_sync 2>/dev/null \
  -exec cp --parents {} ~/knowledge/notes/from_obsidian/ \;
touch ~/knowledge/.last_sync
```

### 方案三：cron 自动同步（全自动）

```bash
cat > ~/.hermes/scripts/obsidian-sync.sh << 'SCRIPT'
#!/bin/bash
VAULT="$HOME/Documents/Obsidian Vault"
KNOWLEDGE="$HOME/knowledge"
LOG="$HOME/.hermes/logs/obsidian-sync.log"
mkdir -p "$VAULT/knowledge" "$(dirname "$LOG")"

direction="${1:-both}"
if [[ "$direction" == "to-obsidian" || "$direction" == "both" ]]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] knowledge → vault" >> "$LOG"
    rsync -a --delete "$KNOWLEDGE/" "$VAULT/knowledge/" 2>&1 | head -5 >> "$LOG"
fi
if [[ "$direction" == "from-obsidian" || "$direction" == "both" ]]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] vault → knowledge" >> "$LOG"
    find "$VAULT" -name "*.md" -not -path "*/knowledge/*" -newer "$KNOWLEDGE/.last_sync" 2>/dev/null \
        -exec cp --parents {} "$KNOWLEDGE/notes/from_obsidian/" \; 2>&1 | head -5 >> "$LOG"
    touch "$KNOWLEDGE/.last_sync"
fi
python3 "$HOME/.hermes/scripts/knowledge/search_knowledge.py" --rebuild 2>/dev/null
echo "--- done ---" >> "$LOG"
SCRIPT
chmod +x ~/.hermes/scripts/obsidian-sync.sh

hermes cron create "0 * * * *" \
  --name "obsidian-knowledge-sync" \
  --script "$HOME/.hermes/scripts/obsidian-sync.sh" \
  --no-agent
```

## Hermes 安装方式（已验证 2026-06-08）

```bash
# 克隆插件
git clone --depth 1 https://github.com/jshph/enzyme-skill ~/.hermes/plugins/enzyme-skill

# 安装 CLI 二进制（自动下载 Linux x86_64 33MB 二进制）
bash ~/.hermes/plugins/enzyme-skill/install.sh
# → 会打开浏览器完成 enzyme.garden 账号注册
# → 登录 andymao76@gmail.com，自动写入 ~/.enzyme/auth.json

# 启用 Hermes 插件
hermes plugins enable enzyme

# 初始化 vault
cd ~/Documents/Obsidian\ Vault
enzyme init

# 验证
enzyme status
enzyme petri
enzyme catalyze "关键词"
enzyme refresh
```

## 验证清单

### 验证 1：symlink 连通性
```bash
readlink -f ~/Documents/Obsidian\ Vault/knowledge  # → /home/andymao/knowledge
head -3 ~/Documents/Obsidian\ Vault/knowledge/DeepSeek_API_完整参考.md
```

### 验证 2：文件数量
```bash
echo "原目录: $(find ~/knowledge -name '*.md' -type f | wc -l)"
echo "Vault symlink（有 -L）: $(find -L ~/Documents/Obsidian\ Vault/knowledge -name '*.md' -type f 2>/dev/null | wc -l)"
echo "Vault 总 .md: $(find -L ~/Documents/Obsidian\ Vault/ -name '*.md' -type f 2>/dev/null | wc -l)"
```

### 验证 3：子目录完整性
```bash
for d in research notes articles articles_baidu daily sources; do
  echo "$d: $(find -L ~/Documents/Obsidian\ Vault/knowledge/$d -name '*.md' 2>/dev/null | wc -l) 个"
done
```

### 验证 4~7：环境变量 / wikilink / 图谱配置 / CLI socket
```bash
grep OBSIDIAN_VAULT_PATH ~/.hermes/.env && echo "✅" || echo "❌"
echo "含 wikilink 文件: $(grep -rl '\[\[' ~/knowledge/ 2>/dev/null | wc -l)"
cat ~/Documents/Obsidian\ Vault/.obsidian/graph.json | python3 -m json.tool 2>/dev/null
ls -la /run/user/1000/.obsidian-cli.sock 2>/dev/null && echo "✅ CLI socket 存在"
```

---

## Obsidian CLI 用法（v1.12+）

需要 Obsidian 桌面在运行。CLI socket 在 `/run/user/1000/.obsidian-cli.sock`。

```bash
# 搜索
obsidian search "关键词" --vault "Obsidian Vault"
# 读取笔记
obsidian read path="知识库/research/IMS_SIP信令流程与排障指南.md"
# 创建笔记
obsidian create path="笔记/新笔记" content="# 标题\n\n正文"
# 今日日记
obsidian daily:prepend "- 完成了什么"
obsidian daily:read
# 标签查询
obsidian search "tag:#通信" --vault "Obsidian Vault"
# 反向链接
obsidian backlinks "IMS SIP信令流程" --vault "Obsidian Vault"
```

### obsidian eval — 查询图谱结构

```javascript
// 孤岛节点
obsidian eval 'Object.entries(app.metadataCache.resolvedLinks).filter(([k,v]) => Object.keys(v).length === 0).map(([k]) => k)'
// 枢纽节点
obsidian eval 'Object.entries(app.metadataCache.resolvedLinks).sort((a,b) => Object.keys(b[1]).length - Object.keys(a[1]).length).slice(0,10).map(([k,v]) => `${k}: ${Object.keys(v).length} links`)'
// 图谱统计
obsidian eval 'const links=app.metadataCache.resolvedLinks; const n=Object.keys(links).length; const e=Object.values(links).reduce((a,v)=>a+Object.keys(v).length,0); const o=Object.values(links).filter(v=>Object.keys(v).length===0).length; `节点:${n} 边:${e} 孤岛:${o}`'
```

### snap CLI 排障

如果报 "The CLI is unable to find Obsidian"：见 `references/obsidian-snap-cli-troubleshooting.md`。

---

## 图谱状态评估

| 指标 | 预期值 | 说明 |
|------|--------|------|
| 节点数 | ~422 | 知识库中所有 .md 文件 |
| 边数 | 0-7 | 只有 7 个文件含 `[[wikilink]]` |
| 孤岛节点 | ~415 | 多数节点无出链/入链 |

| 阶段 | 节点关联度 | 价值 |
|------|-----------|------|
| 初始（当前） | <5% | 中——看到全景但缺少关联发现 |
| 活跃 | 20-30% | 高——反向链接暴露有价值关联 |
| 成熟 | 50%+ | 极高——孤岛检测、桥接、知识网络韧性 |

**提升方法**：调研时加入 `## 参见\n- [[相关笔记]]`；在 Obsidian 手动链接；每月跑孤岛检测清 5-10 个。

---

## 分步实践指南（从零到三层记忆）

如果你决定引入 Obsidian 作为 Hermes 的知识层，建议分阶段演进：

| 阶段 | 操作 | 时间 |
|------|------|------|
| 第一步 | 只用 Obsidian 存你需要查的笔记，Hermes memory 维持原样 | 1天 |
| 第二步 | 配置 `OBSIDIAN_VAULT_PATH` 环境变量 + symlink ~/knowledge/ 到 vault | 5分钟 |
| 第三步 | 用 Hermes 内置 `obsidian` skill 让 Agent 读写 vault（读笔记、搜索、创建） | 加载即可 |
| 第四步 | 建立 LLM Wiki 索引：每次调研后说「写入知识库」，自动生成结构化笔记 | 每次调研 |
| 第五步 | 有多 Agent 需求时，设计共享写入规范 + 安装 Open Second Brain | 按需 |
| 第六步 | 安装 Enzyme 插件实现编译时语义搜索（8ms 查询，零 LLM 成本） | 按需 |

不要一步到位，演进式架构永远比大爆炸设计更稳。

## 日常使用三法则

1. **存东西** — 内容 + 「写入知识库」 → Hermes 自动提取实体、创建 [[双向链接]] 到 Obsidian
2. **查东西** — 「结合知识库」 + 问题 → Hermes 先检索 ~/knowledge/ 再回答
3. **看关联** — 打开 Obsidian 图谱视图，顺着双向链接探索知识网络

### 在 config.yaml 中注册自动提示（必配）

配置 `prefill_messages_file` 让每次搜索后自动询问是否写入知识库：

```bash
hermes config set prefill_messages_file prefill_knowledge_prompt.json
```

配置文件内容（`~/.hermes/prefill_knowledge_prompt.json`）：
```json
[{"role": "system", "content": "每次你完成搜索、调研、查资料、看文章、分析内容等涉及外部信息获取的任务后，必须询问用户是否要将搜索结果写入知识库(Obsidian vault)。询问格式统一为: 本次搜索到 X 条结果。是否要将这些内容整理后写入知识库？如果用户同意: 1.提取关键信息 2.生成结构化 Markdown 笔记 3.添加双向链接 4.写入 knowledge 对应目录 5.enzyme refresh。如果用户拒绝不再追问。临时性内容(天气/时间)和与知识库主题完全无关的不需要询问。"}]
```

这会使 Hermes 在每轮搜索/调研完成后自动提示「是否写入知识库」，无需用户每次主动说。`OBSIDIAN_VAULT_PATH` 和 `ENZYME_VAULT_ROOT` 已配置在 `.env` 文件中自动加载。

### 什么时候不需要 Obsidian

- 简单个人助理：上下文窗口够大，内置 memory 已满足
- 没遇到记忆瓶颈：不要提前加复杂度
- 纯 Agent 内部状态：行为偏好、用户习惯用内置 memory 更高效

核心判断标准：**你自己需不需要看那些记忆？** 需要就上 Obsidian，不需要就用内置 memory。

---

## 社区方案全景对比

以下是在 GitHub 和 Google 上搜索到的 Hermes ↔ Obsidian 协同方案综合对比。

### 全景表

| 方案 | 类型 | 复杂度 | 核心价值 | 适用性 |
|------|------|--------|---------|--------|
| **本 skill (symlink + FTS5)** | 目录同步 | 极低 | 零配置让 422 个文件出现在 Obsidian 图谱 | 基础层，已部署 |
| **Open Second Brain** | memory provider | 中 | Brain/ 下 .md 文件记忆，dream 自动归并，50+ CLI | 多 Agent 共享记忆 | 
| **Enzyme** | 编译型搜索 | 低 | 预计算关系→0 LLM 调用/8ms 查询 | 最推荐补充 |
| **obsidian-wiki** | 跨 Agent 框架 | 低 | 一套 skill 装到所有 Agent | 多 Agent 用户 |
| **obsidian-agent-memory-skills** | Agent skill | 低 | `/obs recap` `/obs lookup` | 轻量增强 |
| **Icarus** | Hermes plugin | 高 | 捕获决策→导出→微调模型 | 微调场景才需 |
| **hermes-kanban** | Obsidian plugin | 中 | Obsidian 内 Kanban，Hermes REST API 操控 | 项目管理需求 |
| **Hermes v0.14 内置 obsidian provider** | 内置 | 最低 | 一行命令启用 | 经测试不存在 |

### 各方案详细调研

#### Open Second Brain（已安装激活）
- 仓库: https://github.com/itechmeat/open-second-brain
- 安装: `hermes plugins install itechmeat/open-second-brain` → 需 Bun 运行时 → `o2b install-cli` → `o2b init --vault <path>` → 设置 `memory.provider: open-second-brain`
- 核心: 记忆存为 `Brain/` 的 .md 文件；3 次相同信号→确认为规则；`dream` 夜间自动归并；50+ CLI 动词；rollback 回滚；跨 Agent
- **注意**: O2B 的索引器不跟踪 symlink 目录，422 个 knowledge 文件不被索引，新写入 Brain/ 的记忆正常工作

#### Enzyme 安装步骤与验证（已验证 v0.5.15）
- **前提**: Git + 网络可达 GitHub
- **安装 CLI**: `bash ~/.hermes/plugins/enzyme-skill/install.sh`（自动下载 Linux x86_64 二进制，33MB）
- **登录**: install.sh 会自动打开浏览器，引导完成 enzyme.garden 账号注册（需邮箱验证）
- **插件启用**: `hermes plugins enable enzyme`（插件已自动识别，git 源，not enabled 初始状态）
- **Vault 初始化**: `cd ~/Documents/Obsidian Vault && enzyme init`
- **验证**:
  - `enzyme status` — 确认 Documents/Embedded/Entities/Catalysts
  - `enzyme petri` — vault 概览 JSON
  - `enzyme catalyze "关键词"` — 语义搜索，返回 processing_time < 1ms
  - `enzyme refresh` — 增量更新（~100ms 无变化时）

**Pitfalls:**
- `.env` 文件中的 `export OBSIDIAN_VAULT_PATH=...` 如果后续有其他非 key=value 行（如 `Agent:` 或注释行），用 `source` 会报错。Python 脚本中逐行读取 `key=value` 解析 + `os.environ[k]=v` 更稳妥。
- **`.env source 崩溃`**：WHATSAPP_ALLOWED_USERS 等行含 `!^)#%` 等特殊字符，`source ~/.hermes/.env` 会报语法错误中断执行。解决：使用 `set -a; . ~/.hermes/.env 2>/dev/null; set +a` 忽略错误，或用 Python `subprocess.run` 手动注入 env var。
- **`enzyme refresh` segfault**：当 enzyme 未登录（`enzyme status` 显示 `API key: not configured`）时，无参数 `enzyme refresh` 会段错误。必须传 `--use-env-llm` 且环境中有 `OPENROUTER_API_KEY`/`OPENAI_API_KEY`。如果 `source .env` 失败，用 Python 脚本逐行读取 key 后通过 `subprocess.run(env=...)` 执行。
- **`enzyme init` 全量重建**：添加新文件后若 `enzyme refresh` 不生效，直接 `cd ~/knowledge && enzyme init --use-env-llm` 全量重建（需 30-60s）。重置催化剂但确保所有文件入索引。
- Enzyme 的 `SKILL.md` 和 `hooks.py` 从 [enzyme-rust](https://github.com/jshph/enzyme-rust) 同步，不要在 plugins/ 目录直接修改，会被覆盖。
- `enzyme scan` 是只读探测，`enzyme init` 才会实际创建 `.enzyme/enzyme.db`
- `hermes plugins enable enzyme` 只在下次 gateway 启动时生效（`systemctl --user restart hermes-gateway` 后可立即加载）
- `OBSIDIAN_VAULT_PATH` 环境变量已在 `.env` 中，`obsidian` skill 自动读取；若 vault 路径含空格，file tools 比 shell 命令可靠

#### obsidian-wiki
- 仓库: https://github.com/Ar9av/obsidian-wiki
- 安装: pip install → `obsidian-wiki setup`，一次性配置在所有 Agent
- 技能: wiki-ingest（摄入）、wiki-query（查询）、wiki-update（更新）、claude-history-ingest（会话导入）
- 设计: 配置解析协议→`AGENTS.md` 获取领域词汇/写作风格/偏好

#### obsidian-agent-memory-skills
- 仓库: https://github.com/adamtylerlynch/obsidian-agent-memory-skills
- 兼容: 35+ Agent（Claude/Cursor/Cline/Windsurf/Copilot 等）
- 命令: `/obs recap`（摘要）`/obs lookup`（搜索）`/obs project`（脚手架）

#### hermes-kanban
- 仓库: https://github.com/GumbyEnder/hermes-kanban
- 架构: Obsidian 插件 (port 27124 REST API) → Hermes 操作板/卡
- 测试: 105 tests, 55% coverage, mock API 可离线验证

#### Icarus
- 仓库: https://github.com/esaradev/icarus-plugin
- 工具: 16 tools + 4 auto hooks
- 场景: 自动捕获决策→写入 Fabric→导出训练数据→微调替代模型

#### Hermes v0.14 obsidian provider（不存在）
- 来源: X/Twitter @DamiDefi 报道
- 实际测试: `hermes memory setup --provider obsidian` 不被识别。官方文档列出 8 个 provider 中无 obsidian
- 结论: 当前 Hermes v0.x 无内置 obsidian memory provider

### 如何发现以上方案

```bash
# GitHub 搜索
# site:github.com hermes obsidian memory provider plugin skill
# site:github.com "hermes agent" obsidian
# 通用搜索
# "hermes agent" "obsidian" integration workflow 2026
# "hermes agent" "obsidian" memory setup provider v0.14
# 社交平台
# site:x.com hermes obsidian memory provider
# site:reddit.com r/hermesagent obsidian memory
# 中文平台（本次搜索发现）
# site:csdn.net hermes agent obsidian
# site:zhihu.com hermes obsidian 知识库
# site:zhuanlan.zhihu.com Hermes Obsidian 笔记
```

### 调研来源（文章/帖子）

| 来源 | 核心贡献 |
|------|---------|
| [Hermes 官方 Obsidian SKILL.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/note-taking/obsidian/SKILL.md) | 官方内置 skill 完整定义——read_file/write_file/patch/search_files 操作 vault |
| [CSDN 三层记忆体系](https://blog.csdn.net/weixin_41736460/article/details/161049415) | 冷/暖/热三层设计——Hermes memory(热) + Obsidian索引(暖) + vault归档(冷) |
| [CSDN 终身知识库](https://blog.csdn.net/xx_nm98/article/details/161714968) | 实操教程：Hermes + Obsidian + Gemini 多模态构建 AI 知识库 |
| [知乎 AI Agent 管理 Obsidian](https://zhuanlan.zhihu.com/p/2037828050532967882) | 完全由 AI Agent 管理 Obsidian 资料库的实践指南 |
| [知乎 Hermes+Obsidian+LLM wiki](https://zhuanlan.zhihu.com/p/2039314541968888057) | 用 LLM Wiki skill 自动提取实体、创建索引、添加 [[双向链接]] |
| [知乎 三层记忆实战](https://zhuanlan.zhihu.com/p/2038669171052000565) | Obsidian 作为 AI 助手长期记忆的三层方案实战 |
| [知乎 Hermes+Obsidian+NAS](https://zhuanlan.zhihu.com/p/2045504049928222717) | NAS+微信+Hermes+Obsidian 网页自动变知识库 |
| [Reddit 三级记忆体系](https://www.reddit.com/r/hermesagent/comments/1stz6gd/how_i_use_obsidian_as_the_longterm_memory) | Hot Memory → Vault → Daily Notes 三级，操作分类 |
| [Hermes LLM Wiki](https://medium.com/@jsong_49820/how-i-built-a-self-improving-llm-wiki-with-hermes-agent-and-why-im-not-using-obsidian-1e9a7fa438c1) | Hermes FTS5 + markdown 本身就是第二大脑 |
| [Obsidian CLI 70K 成本优化](https://prokopov.me/posts/obsidian-cli-changes-everything-for-ai-agents) | CLI 比 grep 快 60x，节省 70Kx tokens |
| [Hermes+Obsidian 第二大脑](https://artemxtech.substack.com/p/i-stopped-teaching-my-agent-who-i) | 自动学习偏好写入 USER.md，skill review agent |
| [obsidian-graph-query](https://forum.obsidian.md/t/obsidian-graph-query-let-your-ai-agent-query-your-vaults-knowledge-graph-bfs-shortest-path-bridges-hubs-orphans/111828) | BFS/桥接/孤岛检测，7 JS 查询模板 |
| [symlink 挂入 vault](https://www.ssp.sh/brain/add-external-folders-git-blog-book-to-my-obsidian-vault-via-symlink) | 实操: symlink 外部目录挂入 Obsidian vault |
| [pjeby/obsidian-symlinks (archived)](https://github.com/pjeby/obsidian-symlinks) | 旧插件（Obsidian 0.11.1+ 已内置） |

---

## 已知问题

| 问题 | 表现 | 解决 |
|------|------|------|
| Obsidian snap 远程无法启动 GUI | CLI 报 "unable to find Obsidian" | 桌面手动启动 Obsidian |
| snap socket 残留 | socket 存在但 ECONNREFUSED | Obsidian 异常退出，不影响功能 |
| symlink 首次索引性能 | 400+ 文件打开较慢 | Obsidian 自动建立缓存 |
| rsync 双向往返循环 | 同步产生重复文件 | `-not -path "*/knowledge/*"` 排除 |
| wikilink 极少 | 图谱 415 孤岛 | 参见"提升图谱价值" |
| O2B 索引不跟 symlink | 脑索引只有 1 文件 | FTS5 和老知识搜索不变 |
| Hermes 无内置 obsidian provider | `--provider obsidian` 不被识别 | 不存在该功能 |

---

## 排障参考

- `references/obsidian-snap-cli-troubleshooting.md` — snap CLI 排障（socket/桌面/strace）
- `references/open-second-brain-install-records.md` — O2B 安装步骤、验证、symlink 限制
- `references/hermes-obsidian-skill-official.md` — Hermes 内置 obsidian skill 官方文档（操作工具速查表）
- `references/enzyme-plugin.md` — Enzyme 编译时语义记忆插件（安装/钩子/工具）
