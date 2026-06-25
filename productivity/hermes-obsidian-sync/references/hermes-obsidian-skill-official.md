# Hermes 内置 Obsidian Skill 官方文档

来源：https://github.com/NousResearch/hermes-agent/blob/main/skills/note-taking/obsidian/SKILL.md
文档：https://hermes-agent.nousresearch.com/docs/user-guide/skills/bundled/note-taking/note-taking-obsidian

## 概述

- **Skill 名称**: `obsidian`
- **说明**: 读、搜索、创建、编辑 Obsidian vault 中的笔记
- **平台**: linux, macos, windows
- **状态**: 内置（默认安装）

## Vault 路径

- 环境变量: `OBSIDIAN_VAULT_PATH`（来自 `~/.hermes/.env`）
- 默认路径: `~/Documents/Obsidian Vault`
- 核心规则: 文件工具不展开 shell 变量。解析 vault 路径为具体绝对路径后再传给 `read_file`/`write_file`/`patch`/`search_files`
- 路径含空格时优先用文件工具而非 shell 命令

## 支持的操作

| 操作 | 推荐工具 | 避免 |
|------|---------|------|
| 读笔记 | `read_file`（带行号和分页） | `cat` |
| 列笔记 | `search_files(target="files", pattern="*.md")` | `find` / `ls` |
| 搜索内容 | `search_files(target="content", file_glob="*.md")` | `grep` |
| 创建笔记 | `write_file`（绝对路径 + markdown） | heredoc / `echo` |
| 追加内容 | `read_file` → `patch`（有锚点） 或 `write_file`（重写） | shell 文本重写 |
| 定向编辑 | `patch`（有稳定上下文时） | shell |
| 双向链接 | 使用 `[[Note Name]]` 语法 | — |

## 关键原则

1. 文件工具优先：`read_file`/`write_file`/`patch`/`search_files` 优于 shell 命令
2. 解析路径：绝不传 `$OBSIDIAN_VAULT_PATH` 给文件工具
3. 结构化结果：文件工具返回结构化数据，避免 shell 引号问题
4. 有上下文才用 `patch`：确保有稳定的锚点文本
