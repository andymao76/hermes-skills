---
name: obsidian
description: Read, search, create, and edit notes in the Obsidian vault.
platforms: [linux, macos, windows]
---

# Obsidian Vault

Use this skill for filesystem-first Obsidian vault work: reading notes, listing notes, searching note files, creating notes, appending content, and adding wikilinks.

## Vault path

Use a known or resolved vault path before calling file tools.

The documented vault-path convention is the `OBSIDIAN_VAULT_PATH` environment variable, for example from `~/.hermes/.env`. If it is unset, use `~/Documents/Obsidian Vault`.

File tools do not expand shell variables. Do not pass paths containing `$OBSIDIAN_VAULT_PATH` to `read_file`, `write_file`, `patch`, or `search_files`; resolve the vault path first and pass a concrete absolute path. Vault paths may contain spaces, which is another reason to prefer file tools over shell commands.

If the vault path is unknown, `terminal` is acceptable for resolving `OBSIDIAN_VAULT_PATH` or checking whether the fallback path exists. Once the path is known, switch back to file tools.

## Read a note

Use `read_file` with the resolved absolute path to the note. Prefer this over `cat` because it provides line numbers and pagination.

## List notes

Use `search_files` with `target: "files"` and the resolved vault path. Prefer this over `find` or `ls`.

- To list all markdown notes, use `pattern: "*.md"` under the vault path.
- To list a subfolder, search under that subfolder's absolute path.

## Search

Use `search_files` for both filename and content searches. Prefer this over `grep`, `find`, or `ls`.

- For filenames, use `search_files` with `target: "files"` and a filename `pattern`.
- For note contents, use `search_files` with `target: "content"`, the content regex as `pattern`, and `file_glob: "*.md"` when you want to restrict matches to markdown notes.

## Create a note

Use `write_file` with the resolved absolute path and the full markdown content. Prefer this over shell heredocs or `echo` because it avoids shell quoting issues and returns structured results.

## Append to a note

Prefer a native file-tool workflow when it is not awkward:

- Read the target note with `read_file`.
- Use `patch` for an anchored append when there is stable context, such as adding a section after an existing heading or appending before a known trailing block.
- Use `write_file` when rewriting the whole note is clearer than constructing a fragile patch.

For an anchored append with `patch`, replace the anchor with the anchor plus the new content.

For a simple append with no stable context, `terminal` is acceptable if it is the clearest safe option.

## Targeted edits

Use `patch` for focused note changes when the current content gives you stable context. Prefer this over shell text rewriting.

## Wikilinks

Obsidian links notes with `[[Note Name]]` syntax. When creating notes, use these to link related content.

## Obsidian CLI (v1.12+)

当 Obsidian 桌面应用正在运行时，可以通过 `obsidian` 命令在终端中操作 vault。

**前提条件**：Obsidian 桌面应用必须在运行中（CLI 通过 Unix socket IPC 通信）。

```bash
# 搜索
obsidian search "关键词" --vault "Obsidian Vault"

# 读取笔记
obsidian read path="folder/note.md"

# 创建笔记
obsidian create path="folder/note" content="# 标题"

# 今日日记
obsidian daily:prepend "- 待办事项"

# 反向链接查询
obsidian backlinks "笔记名" --vault "Obsidian Vault"

# 孤岛/枢纽检测（eval 在 Obsidian 内部执行 JS）
obsidian eval 'Object.entries(app.metadataCache.resolvedLinks).filter(([k,v]) => Object.keys(v).length === 0).map(([k]) => k)' --vault "Obsidian Vault"
```

**注意**：snap 版 Obsidian 的 CLI 需要通过 `/run/user/$UID/.obsidian-cli.sock` socket 通信。
- 如果 CLI 报 "The CLI is unable to find Obsidian"，先确认桌面中 Obsidian 正在运行。
- snap 版无法在非桌面会话（后台进程、CLI 终端、SSH 等）中启动 GUI，CLI 依赖已有桌面会话。
- 排障：`ls -la /run/user/$UID/.obsidian-cli.sock` 检查 socket + `ps aux | grep obsidian` 检查进程。
- socket 文件存在但 `connect` 被拒绝（ECONNREFUSED）说明是前一次 Obsidian 退出后残留的 socket 文件，需在桌面中启动 Obsidian。

## Vault 与 External Knowledge 同步

Hermes Agent 的知识库 `~/knowledge/` 可以通过 symlink 挂入 Obsidian vault，实现双向打通：

```bash
cd ~/Documents/Obsidian\\ Vault/
ln -sf ~/knowledge knowledge
```

## 日报/周报/月报路径

日报、周报、月报统一写入 `0sinovatio/` 目录（Obsidian 文件浏览器排名第一）：

```
0sinovatio/
├── 日报/    YYYYMMDD.md   # 每天下班前生成
├── 周报/                   # 每周五生成
└── 月报/                   # 每月最后一天生成
```

写入路径（二选一均可）：
- `~/Documents/Obsidian Vault/0sinovatio/日报/YYYYMMDD.md`（原生）
- `~/knowledge/0sinovatio/日报/YYYYMMDD.md`（通过 symlink）

## Windows 远程访问（不存副本）

Samba 共享本机 `~/Documents/Obsidian Vault/`，Windows 映射网络驱动器后直接打开 vault。

详见 `knowledge-base` skill 的 `references/obsidian-samba-network-share.md`。

挂载后：
- Hermes 调研产物（写入 `~/knowledge/`）自动出现在 Obsidian 图谱
- Obsidian 图谱显示全部 400+ 知识节点
- 反向链接面板揭示知识关联

详见 skill `hermes-obsidian-sync`，CLI 排障见其 `references/obsidian-snap-cli-troubleshooting.md`。

## Local REST API + MCP 集成

通过 Obsidian Local REST API 插件 + obsidian-mcp-server，Hermes 可以直接读写/搜索 Obsidian 笔记库。安装后 Hermes 自动注册 12 个 `mcp_obsidian_*` 工具。

**关键 Pitfalls（详见参考文档）：**
- `hermes config set` 无法设置嵌套 MCP env 路径（如 `mcp_servers.obsidian.env.OBSIDIAN_API_KEY`）→ 用 sed 直接改 config.yaml
- 更新 config.yaml 后需 `/reload-mcp` 或 kill 旧 MCP 进程才能生效（旧进程仍持有旧 env）
- `hermes mcp test obsidian` 只测试 stdio 连接，不验证 REST API 认证 → 必须调用实际工具做端到端验证
- API Key 64 字符 hex，容易串位（如 `4c83a` vs `44c83`）→ 用 `diff <(echo key1) <(echo key2)` 对比
- snap 版 Obsidian 无法用 foreground & 重启 → 用 terminal(background=true, command="snap run obsidian")，等待 8-12 秒

完整配置指南和排障流程：`references/obsidian-local-rest-api-mcp.md`
