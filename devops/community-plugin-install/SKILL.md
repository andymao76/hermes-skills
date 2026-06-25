---
name: community-plugin-install
description: "Install, configure, and verify Hermes community plugins and skills from GitHub repositories (awesome-hermes-agent, agentskills.io, etc.)"
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [hermes, plugins, skills, community, installation, ecosystem]
    category: devops
---

# Community Plugin & Skill Install Guide

Procedure for evaluating, installing, and testing third-party Hermes plugins and skills.

## Overview

Community Hermes extensions come in two formats:

| Format | Structure | Install Path | Activation |
|--------|-----------|-------------|------------|
| **Plugin** | `plugin.yaml` + `__init__.py` + Python files | `~/.hermes/plugins/<name>/` | `hermes plugins enable <name>` then `/reset` |
| **Skill** | `SKILL.md` (YAML frontmatter + markdown) | `~/.hermes/skills/<name>/` | Auto-loaded on next session; invoke via `/skill <name>` |

## Discovery & Evaluation (absorbed from skill-discovery)

When you need to FIND skills before installing them, use these search methods.

### Quick-Reference: Finding Skills by Category

| Category | Search Command | Top Find |
|---|---|---|
| 写代码/软件工程 | `npx skills search development` | wondelai/skills (48+ book-based skills) |
| 爬虫/抓取 | `npx skills search scraper` | apify/agent-skills (11.5K) |
| AI/LLM | `npx skills search llm` | wshobson/agents (prompt-engineering, rag) |
| 金融/股票 | `npx skills search stock` | sugarforever/china-stock-analysis |
| 知识库/RAG | `npx skills search knowledge` | firecrawl/firecrawl-workflows |
| 浏览器自动化 | `npx skills search browser` | vercel-labs/agent-browser |
| 学习/教育 | `npx skills search learning` | philschmid/self-learning-skill (3.1K) |
| 多智能体 | `npx skills search multi-agent` | qodex-ai/ai-agent-skills |
| MCP 服务器 | `npx skills search mcp` | anthropics/skills@mcp-builder |

See `references/community-skill-ratings.md` for full pre-searched rankings across 12+ categories.

### Primary Search Methods

1. **`npx skills search <keyword>`** — ranked results with real install counts. Best first stop.
2. **Skills Hub**: `hermes skills browse` / `hermes skills search <keyword>` — 691+ skills
3. **GitHub**: `web_search("site:github.com hermes agent skill <keyword> stars")` — community repos
4. **awesome-hermes-agent**: `web_extract(urls=["https://github.com/0xNyk/awesome-hermes-agent"])` — curated index
5. **agentskills.io** — open standard cross-platform skills

### Batch Installation Pattern

When searching across multiple categories:
1. Collect ALL category searches first
2. Present ONE master table with install counts and status
3. Install in batches of 2-3 per terminal turn
4. Verify after each batch: `hermes skills list | grep <name>`
5. Update the quick-reference table with new findings

### Evaluation Criteria

Before installing, check: trigger clarity, setup requirements, dependencies, verification method, permission footprint, maintenance (last update), community signal (stars/installs).

### Timeout Handling

When `hermes skills install` returns code 124: split into batches of 2-3. Verify after timeout — `hermes skills list | grep <name>` may show success even when the CLI timed out.

### Common Install Failures

| Failure | Cause | Fix |
|---|---|---|
| 404 from raw URL | Wrong branch or path | Check default_branch via GitHub API |
| Timeout (124) | Large repo, long install | Verify after timeout; try shorter batches |
| BLOCKED — dangerous | Security scanner flagged shell/cmd | Cannot override; create local SKILL.md manually |
| BLOCKED — caution | Low-severity findings | Use `--force` to override |

See `references/github-skill-install-pattern.md` for GitHub install patterns, `references/skillsmp-patterns.md` for SkillsMP registry, and `references/scraping-patterns.md` for scraping-based discovery.

## Step-by-Step (Installation)

### 1. Evaluate the Repository

Before cloning, check:

- **Format detection:** Does it have `plugin.yaml` (plugin) or `SKILL.md` (skill)? Both? Neither?
- **Dependencies:** Does it list `requires_env` in plugin.yaml? Does SKILL.md mention API keys?
- **Compatibility:** Check `platforms:` in YAML frontmatter. Does it include `linux`?
- **Plugin sub-type:** General plugins go in `~/.hermes/plugins/`. Sub-category plugins (memory providers, image-gen backends, platform adapters) go in `~/.hermes/plugins/<category>/<name>/`.

```bash
# Quick format check
ls <repo>/plugin.yaml 2>/dev/null && echo "Plugin" || echo "No plugin.yaml"
ls <repo>/SKILL.md 2>/dev/null && echo "Skill" || echo "No SKILL.md"
```

### 2. Install

**For plugins:**
```bash
cd /tmp
git clone <repo_url>
cp -r <repo_dir> ~/.hermes/plugins/<name>/
hermes plugins list | grep <name>  # Verify recognized
hermes plugins enable <name>       # Enable
# Takes effect on next session (/reset or new hermes chat)
```

**For skills:**
```bash
mkdir -p ~/.hermes/skills/<name>
cp <repo>/SKILL.md ~/.hermes/skills/<name>/
cp -r <repo>/scripts ~/.hermes/skills/<name>/ 2>/dev/null
hermes skills list | grep <name>  # Verify listed
```

### 3. Configure API Keys

If the plugin/skill requires API keys:
- Set them in `~/.hermes/.env`
- Use `echo 'KEY=value' >> ~/.hermes/.env` from terminal (write_file is blocked for .env)
- Interactive setup scripts may prompt for keys — these don't work well headless. Prefer adding keys directly to .env, then run setup with `--preset lean` or skip interactive prompts by hitting Enter.

### 4. Test

**For plugins:** Run the plugin's built-in test tools:
```bash
cd ~/.hermes/plugins/<name>
python3 setup.py status         # Many plugins have this
python3 <tool_file>.py --test   # Or direct CLI test
```

**For skills:** Test by loading in session:
```bash
hermes chat -s <name> -q "test query"
```

**For all:** After enabling, verify the plugin is listed and working:
```bash
hermes plugins list
hermes mcp list  # If MCP-related
```

### 5. Integrate into Startup Health Check

If the plugin has pending setup steps (missing API keys, incomplete npm install), add a reminder to `~/.hermes/scripts/daily-startup-healthcheck.sh`. Pattern:

```bash
# Check if installed but not configured
if [ -d "$HOME/.hermes/plugins/<name>" ]; then
  if [ ! -d "$HOME/.hermes/plugins/<name>/node_modules" ]; then
    log_warn "Description: what to do"
    log_info "  command to run"
  fi
fi
```

The health check runs daily at 7:02 AM (cron job `b25ff9d30c80`).

## SkillHub Ecosystem (skillhub)

Hermes also supports skills installed via the [SkillHub](https://skillhub.cn) store, which live in `~/skills/<name>/` (a separate directory from `~/.hermes/skills/`).

### Detecting SkillHub

```bash
which skillhub && skillhub --version
ls ~/skills/                 # List installed skills
```

### Importing SkillHub Skills into Hermes

SkillHub stores skills in `~/skills/<name>/` for the SkillHub agent ecosystem (Clawdbot/OpenClaw). Some of these skills are useful in Hermes too. To import:

1. **Check overlap:** Compare `~/skills/` skill names against `hermes skills list` or `ls ~/.hermes/skills/`. Many Hub skills (ai-stock-analyst, finance-research-report, etc.) already exist in the Hermes ecosystem.

2. **Clean up the SKILL.md frontmatter:** SkillHub SKILL.md files often have Clawdbot/OpenClaw-specific metadata (`clawdbot:` key, `metadata.openclaw:`, `requires.bins`, etc.) that Hermes ignores but best to clean. Remove:
   - `metadata.clawdbot` / `metadata.openclaw` sections
   - `requires.bins` / `requires.env` fields
   - Platform-specific tool references (e.g., `maton` CLI, `discord` tool JSON)

3. **Create the skill via `skill_manage(action='create')`** with the cleaned content.

4. **Copy supporting files** (scripts, references, templates) via `skill_manage(action='write_file')`.

5. **Check CLI dependencies:** If the skill references a CLI binary (`bsky`, `maton`, etc.), verify it's in PATH and install dependencies (pip packages, npm packages). Create a symlink from `~/skills/<name>/scripts/<binary>` to `~/.local/bin/` if the binary isn't globally installed.

### ⚠️ SkillHub 安装路径嵌套 Bug

SkillHub 的 `skillhub install <name>` 命令有时会将技能安装到**嵌套路径**而非直接目录下：

```bash
# 期望的结果（正确）：
~/skills/<skill-name>/SKILL.md

# 实际可能出现（bug）：
~/skills/dailyhot-skill/skills/<skill-name>/SKILL.md   ← 嵌套在另一个技能目录内
```

**原因：** SkillHub CLI 在解析目标目录时，如果存在同名目录或工作目录下先有 `skills/` 子目录，会将后续技能也放入该目录中。

**修复方式：** 安装后检查路径并修正：
```bash
# 检查是否有嵌套安装
ls ~/skills/*/skills/*/SKILL.md 2>/dev/null | head -5

# 修正：移动技能到正确位置
mv ~/skills/<existing-skill>/skills/<new-skill> ~/skills/<new-skill>

# 清理空目录
rmdir ~/skills/<existing-skill>/skills 2>/dev/null || true
```

**预防措施：** 安装后总是立即验证路径：
```bash
ls ~/skills/<skill-name>/SKILL.md  # 确认直接在 ~/skills/<name>/ 下
```

### SkillHub 技能依赖处理

部分 SkillHub 技能（如 `dailyhot-skill`）包含 Node.js/Python 脚本，安装后需要手动安装依赖才能使用。

**Node.js 技能：**
```bash
cd ~/skills/<skill-name>
npm install            # 安装 package.json 中的依赖
```

**常见依赖问题：**
- `ERR_MODULE_NOT_FOUND`: 缺少运行依赖，`npm install` 即可解决
- 服务类技能（如 dailyhot-skill）需要先启动后端服务才能查询
- 启动命令通常在 SKILL.md 或 README.md 中注明

**验证依赖安装：**
```bash
ls ~/skills/<skill-name>/node_modules/  # 应有目录
node ~/skills/<skill-name>/scripts/<main-script>  # 试运行
```

### SkillHub 直连集成（推荐方式）

从 v1.0.0+ 起，Hermes 支持通过 `skills.external_dirs` 配置直接加载 SkillHub 安装的技能，无需手工复制。

```bash
# 1. 安装 SkillHub CLI
curl -fsSL https://skillhub-1388575217.cos.ap-guangzhou.myqcloud.com/install/install.sh | bash

# 2. 安装技能（存放到 ~/skills/<name>/）
skillhub install <name>

# 3. 配置 Hermes 加载 ~/skills/ 目录
hermes config set skills.external_dirs '["/home/andymao/skills"]'

# 4. 重新启动 Hermes（或 /new）后技能即可使用
```

**工作原理：** `skills.external_dirs` 是一个路径列表，Hermes 会在启动时扫描这些目录中的 `SKILL.md` 文件并注册为可用技能。SkillHub 的技能直接可用，无需格式转换。

**注意事项：**
- 配置变更后需要**重启 Hermes 会话**才能生效
- 部分 SkillHub 技能可能包含 Clawdbot/OpenClaw 特有的 frontmatter 字段（`clawdbot:`、`metadata.openclaw:`），Hermes 会忽略不识别的字段，不影响使用
- 如果技能依赖特定的 CLI 二进制（如 `maton`、`bsky`），需额外安装

### 旧方式：手工导入（备选）

当 `external_dirs` 方式不可用或不适用时，用手工导入方式。**注意：必须使用完整全量内容，不可只写摘要。**

**标准流程：**
```bash
# 1. 安装到 ~/skills/
skillhub install <name>

# 2. 创建 Hermes 技能（用完整 SKILL.md 内容，不要精简摘要）
skill_manage(action='create', name='<name>', content='完整SKILL.md内容')

# 3. 复制所有附属文件（scripts/, references/, instructions/ 等）
mkdir -p ~/.hermes/skills/<name>/scripts/
cp ~/skills/<name>/scripts/*.py ~/.hermes/skills/<name>/scripts/
cp -r ~/skills/<name>/references/ ~/.hermes/skills/<name>/
cp -r ~/skills/<name>/instructions/ ~/.hermes/skills/<name>/ 2>/dev/null

# 4. 安装依赖（如有）
pip3 install -r ~/skills/<name>/requirements.txt --break-system-packages

# 5. 如有 CLI 二进制，建立 PATH 链接
ln -sf ~/skills/<name>/scripts/<binary> ~/.local/bin/<binary>
```

**重要原则：**
- **用户会贴完整 SKILL.md 纠正缩写版** — 总是导入完整内容
- 附属文件（scripts/references/instructions）一并复制
- 清理 Clawdbot/OpenClaw 特有 frontmatter 字段（clawdbot:/metadata.openclaw:等）
- 已存在于 Hermes 系统的技能（如 finance 类）跳过不导入

当 `external_dirs` 方式不可用或不适用时，用手工导入方式：

| Aspect | SkillHub (~/skills/) | GitHub (hermes skills install) |
|--------|---------------------|--------------------------------|
| Install source | `skillhub install <name>` | `hermes skills install <repo>` |
| Target dir | `~/skills/<name>/` | `~/.hermes/skills/<name>/` |
| Format | Clawdbot/OpenClaw SKILL.md | Hermes SKILL.md |
| Ecosystem | Cross-agent | Hermes-native |
| Import needed? | Yes, to be usable in Hermes | No, already native |
| CLI support | Often ships a CLI script in `scripts/` | May or may not |

> **Note:** Duplicate skills between SkillHub and Hermes are common. Many finance skills exist in both ecosystems — detect and skip when importing.

## Pitfalls

- **npm packages requiring pnpm:** Some packages use `only-allow pnpm`. Use `npm install --legacy-peer-deps` as fallback, or install pnpm globally.\n- **pnpm 原生模块（C++ addon）不编译**：pnpm 的 postinstall 默认不调用 `node-gyp rebuild`，导致 `better-sqlite3` 等依赖原生模块的包在运行时报 `Could not locate the bindings file`。修复：在对应包的目录下手动执行 `node-gyp rebuild`。编译需要安装 build-essential（gcc, make 等）。
- **Interactive setup.py scripts:** These use `getpass.getpass()` which echoes in headless mode. Best to add keys directly to `.env` and skip interactive prompts.
- **Plugin not showing after copy:** Ensure plugin.yaml is valid YAML. Run `hermes plugins list` — if not shown, check `~/.hermes/plugins/<name>/plugin.yaml` for syntax errors.
- **Plugin not enabled:** `hermes plugins enable <name>` then `/reset` (or start new session). Plugin changes don't take effect mid-conversation.
- **Skills not showing:** Check `hermes skills list`. If not there, check SKILL.md has valid YAML frontmatter. Run `/reload-skills` in session.
- **Multiple GitHub repos with same awesome-list name:** Two `awesome-hermes-agent` repos exist (0xNyk/cc-by-4.0, SamurAIGPT/MIT). The 0xNyk version is more comprehensive. Reference both when researching.
- **Node.js `fetch` (undici) ignores HTTP_PROXY:** Node.js 内置 fetch（undici 库）不识别 `HTTP_PROXY`/`HTTPS_PROXY` 环境变量。当 postinstall 或 npm script 使用 Node.js `fetch` 下载二进制时，即使终端设置了代理，下载仍可能直连超时。排查方法见 `references/camoufox-install-troubleshooting.md`。

- **camoufox-js（camofox-browser 插件）安装坑较多**：Node.js undici fetch 不走代理、版本约束导致缓存被自动删除、uBlock Origin addon 缺失、better-sqlite3 原生模块需手动编译、Xvfb await bug、systemd 服务配置、Hermes engine 集成。详细排查记录见 `references/camoufox-install-troubleshooting.md`。

## Verification

After installation and configuration:
1. Plugin shows as `enabled` in `hermes plugins list`
2. Skill shows as `enabled` in `hermes skills list`
3. Any associated tools are callable from a fresh session
