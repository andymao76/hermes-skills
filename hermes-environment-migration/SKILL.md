---
name: hermes-environment-migration
description: Migrating Hermes Agent between machines and platforms — backup strategy, knowledge base transfer, skills sync, LI data isolation, Git-based sync workflow, and platform-specific config adaptation.
version: 1.0
author: agent
category: hermes
---

# Hermes 环境迁移

将 Hermes Agent 从一台机器/平台迁移到另一台（如 Ubuntu ↔ Windows），涉及 config、skills、knowledge base、memory、sessions 等多层数据，每层的迁移策略不同。

## 迁移策略总览

| 数据层 | 位置 | 跨平台兼容 | 推荐同步方式 |
|--------|------|-----------|-------------|
| **config.yaml** | `~/.hermes/config.yaml` | ❌ 路径差异 | **各自维护**，不同步 |
| **.env** | `~/.hermes/.env` | ✅ API Key 通用 | 手动复制 |
| **Skills** | `~/.hermes/skills/` | ✅ 纯 Markdown | GitHub 仓库双向同步 |
| **知识库（通用）** | `~/knowledge/`（非 LI） | ✅ 纯文本/图片 | GitHub 仓库或 Syncthing |
| **记忆数据库** | `~/.hermes/state.db` | ✅ SQLite 兼容 | **单向备份**（不支持并发写入） |
| **会话历史** | `~/.hermes/sessions/` | ✅ SQLite | 可不同步（会话只在当前机） |
| **LI 机密知识** | `~/knowledge/telecom/lawful_interception/` + `hi2/` + `li/` | ✅ 纯文本 | **仅离线传输**（U盘/局域网） |

## 前提

- 目标机器上已安装 Hermes Agent
- 源机器上有 git 客户端（`gh auth status` 确认）
- 源机器和目标机器之间有传输通道（网络/SMB/U盘）

## 步骤

### 1. 数据分类：哪些可以上云

在开始迁移前先划分数据敏感性：

- **GREEN 级别**：skills、通用知识（电信原理、编程笔记、LLM API 文档）→ 可放 GitHub 私有仓库
- **RED 级别**：LI 文档（LICENSE 5 数据）、密码/Key 文件、项目敏感信息 → 仅离线传输

### 2. 建立同步中转

```bash
# 创建同步目录
cd ~ && mkdir hermes-sync && cd hermes-sync
git init && git branch -m main

# 创建私有仓库
gh repo create <username>/hermes-sync --private --description "Hermes sync" --source=. --remote=origin --push
```

### 3. 配置 .gitignore

必须排除：
- LI 机密目录（`telecom/lawful_interception/`、`hi2/`、`li/`）
- 缓存索引（`.enzyme/`、`.kb-search/`、`.obsidian/`、`skills/.hub/`）
- 二进制大文件（`*.pdf`、`*.jpg`、`*.png`、`*.zip`、`*.tar.gz`）
- 嵌入的 git 子仓库
- 密码文件（`.env`、`*.env`）

### 4. 知识库迁移

**通用知识（GitHub 同步）：**

```bash
rsync -av --delete \
  --exclude='telecom/lawful_interception/' \
  --exclude='hi2/' \
  --exclude='li/' \
  --exclude='ima-sync/downloads/' \
  --exclude='.enzyme/' \
  --exclude='.kb-search/' \
  --exclude='.obsidian/' \
  ~/knowledge/ ./knowledge/
git add . && git commit -m "sync: knowledge" && git push
```

**LI 机密知识（离线传输）：**

```bash
tar czvf hermes-li-knowledge-$(date +%Y%m%d).tar.gz \
  --exclude='.git' \
  knowledge/telecom/lawful_interception/ \
  knowledge/hi2/ \
  knowledge/li/
# 通过 U 盘拷贝到目标机
```

### 5. Skills 迁移

推荐在目标机使用**目录链接**，这样 git pull 后自动生效：

```powershell
# Windows (mklink /J)
rmdir /S /Q %USERPROFILE%\.hermes\skills
mklink /J %USERPROFILE%\.hermes\skills %USERPROFILE%\hermes-sync\skills

# Linux (ln -s)
rm -rf ~/.hermes/skills
ln -s ~/hermes-sync/skills ~/.hermes/skills
```

### 6. 日常同步脚本

保存 `sync.sh` 在同步仓库根目录：

```bash
#!/bin/bash
rsync -av --delete --exclude='...' ~/.hermes/skills/ ./skills/
rsync -av --delete --exclude='...' ~/knowledge/ ./knowledge/
git add . && git commit -m "sync $(date +%Y-%m-%d_%H:%M)" && git push
```

### 7. 目标机恢复

```powershell
# 1. 克隆仓库
git clone https://github.com/<username>/hermes-sync.git

# 2. 部署 skills（软链接或复制）

# 3. 部署知识库
xcopy /E /I hermes-sync\knowledge %USERPROFILE%\knowledge\

# 4. 解压 LI 机密包
tar -xzf hermes-li-knowledge-*.tar.gz -C %USERPROFILE%\knowledge\

# 5. 重建酶索引
cd %USERPROFILE%\knowledge
enzyme refresh

# 6. 配置 config.yaml 和 .env（各自维护）
```

## 迁移文档编写标准

任何迁移/交接类文档必须包含以下三部分：

1. **最终交付物总览** — 表格列出每项内容的位置、大小、说明
2. **完整操作步骤** — 按顺序编号，每一步给出精确命令（PowerShell / bash 分开标注）
3. **注意点** — 至少涵盖：数据安全约束、平台差异说明、后续日常同步方式

## 陷阱

- **`hermes backup` 不包含知识库**：知识库（`~/knowledge/`）在 Hermes 外部，需要单独打包
- **config.yaml 不跨平台**：Linux 路径 `/home/user/` 和 Windows 路径 `C:\Users\user\` 不同，MCP 命令的 Python 路径也完全不同。两边各自维护 config
- **SQLite 不支持并发写入**：state.db 不能双向同步，只能用单向备份
- **GitHub 对大文件不友好**：超过 50MB 的单个文件会警告，100MB 被拒绝。二进制文件（PDF/JPG）用 .gitignore 排除
- **Windows 符号链接有限制**：mklink /J 需要管理员权限或开发者模式。知识库中的 symlink（如 `0sinovatio`）在 Windows 上可能报错
- **酶索引跨平台**：enzyme 的语义索引（`.enzyme/`）依赖模型 API，跨平台后需要重新 `enzyme refresh`
- **转义字符差异**：Windows PowerShell 用反引号或双引号转义，bash 用反斜杠。脚本中的路径字符串需区分平台

## 相关技能

- `user-conventions` — 用户输出偏好（迁移文档编写标准在此定义）
- `backup-rollback-sop` — 通用备份/回滚标准流程
- `hermes-agent` — Hermes 配置和 CLI 参考
