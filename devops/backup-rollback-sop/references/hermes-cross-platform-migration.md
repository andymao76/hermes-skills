# Hermes Agent 跨平台迁移现场记录

## 背景

将 Linux 服务器上的 Hermes Agent 完整迁移到 Windows 11 原生环境（非 WSL）。

## 源环境

- OS: Ubuntu 24.04 LTS
- Hermes 版本: 最新源码安装（`~/.hermes/hermes-agent/`）
- Provider: DeepSeek（deepseek-v4-flash）
- Profile: default

## 数据总览

| 项目 | 大小 | 压缩后 |
|------|------|--------|
| `~/.hermes/` (含 skills/sessions/logs/plugins) | 4.6G | 664M (profile export) |
| `~/knowledge/` (Obsidian vault) | 1.7G | 648M |
| MCP services (3 个) | ~500K | 196K |
| Open Second Brain | ~3.5M | 7.7M |
| `.env` | 2.5K | 2.5K (明文复制) |

## 已知陷阱

### 1. Broken skill symlinks 导致 profile export 崩溃

**现象**: `hermes profile export default -o ...` 抛出 `shutil.Error`，报 `[Errno 2] No such file or directory`

**根因**: skill 目录中存在指向不存在的目录的 symlink（之前手动删除过某些技能目录但 symlink 残留）

**修复**:
```bash
find ~/.hermes/skills/ -xtype l -delete
```

发现的 3 个断链:
- `~/.hermes/skills/software-development/find-skills`
- `~/.hermes/skills/research/jiekou-docs`
- `~/.hermes/skills/creative/drawio`

### 2. 大文件打包超时

`hermes profile export` 和 `knowledge.tar.gz` 打包各需约 3 分钟。用普通 foreground 模式会在 120 秒后超时。

**解决**: 使用 `terminal(background=true, notify_on_complete=true)` 后台运行，然后 `process(action="wait")` 等待。

### 3. 用户纠正超出 profile export 范围的内容

用户明确指出了以下不在 `hermes profile export` 中的关键数据：
- MCP 外部项目（`~/.hermes/mcp-servers/`, `jd_mcp/`, `taobao_mcp/`）
- Open Second Brain（`~/.hermes/open-second-brain/` + `plugins/open-second-brain/`）
- 知识库（`~/knowledge/`）
- `.env` API 密钥

**教训**: `hermes profile export` 只导出 Hermes 内部管理的组件，不包含外部项目/插件数据。

### 4. 用户选择 Windows 原生而非 WSL

用户明确选择 Windows 原生 Hermes（`winget install`），这意味着 cron 任务不自动迁移（Windows 无 systemd）。如果用 WSL 2 则 cron 原样工作。

## Windows 11 恢复要点

1. 安装: `winget install NousResearch.HermesAgent`
2. 不要用 WSL，直接在 PowerShell / Windows Terminal 运行
3. `.env` 必须手动编辑（`write_file` 工具会拦截）
4. `config.yaml` 不要用 Notepad 编辑（可能写入 UTF-8 BOM）

## 文件传输推荐

- 局域网 HTTP 下载: `cd ~/hermes-migration && python3 -m http.server 8000`
- 云盘/SCP 中转
- U 盘/SMB 共享直接拷贝

## 验证命令

```bash
gzip -t hermes-profile.tar.gz && echo "✅ OK"
gzip -t knowledge.tar.gz && echo "✅ OK"
gzip -t hermes-mcp.tar.gz && echo "✅ OK"
gzip -t hermes-brain.tar.gz && echo "✅ OK"
```
