# Hermes GitHub 中转同步工作流

> 场景：Ubuntu 24.04 ↔ Windows 11 原生 Hermes 的持续同步

## 数据分类策略

| 分类 | 内容 | 同步方式 | 安全等级 |
|------|------|---------|---------|
| Skills | `~/.hermes/skills/` | GitHub 私有仓库 | 可公开 |
| 通用知识 | `~/knowledge/` 排除 LI | GitHub 私有仓库 | 可公开 |
| LI 机密 | `telecom/lawful_interception/`, `hi2/`, `li/` | 压缩包+U盘/直连 | LEVEL 5 |
| 配置 | `config.yaml`, `.env` | 各自维护（平台差异大） | 含 API Key |

## GitHub 仓库结构

```
hermes-sync/
├── skills/          ← ~/.hermes/skills/（排除 .hub/ .usage.json .backup/）
├── knowledge/       ← ~/knowledge/（排除 LI 目录、缓存、二进制文件）
├── sync.sh          ← 日常同步脚本
└── .gitignore       ← 排除 LI/缓存/二进制/嵌入 git 仓库
```

## .gitignore 关键规则

```gitignore
# LI 机密数据（不上 GitHub）
telecom/lawful_interception/
hi2/
li/

# Skills 缓存
skills/.hub/
skills/.usage.json
skills/.backup/

# 知识库缓存
.enzyme/
.kb-search/
.obsidian/

# 二进制文件（膨胀 git）
*.pdf *.jpg *.png *.zip *.tar.gz *.docx *.pptx *.xlsx

# 嵌入 git 子仓库
skills/superpowers/
skills/research/personal-api-skill/
```

## 首次设置

```bash
# Ubuntu
cd ~
gh repo create andymao76/hermes-sync --private --source=hermes-sync --remote=origin --push

# Windows
cd %USERPROFILE%
git clone https://github.com/andymao76/hermes-sync.git
mklink /J %USERPROFILE%\.hermes\skills %USERPROFILE%\hermes-sync\skills
xcopy /E /I %USERPROFILE%\hermes-sync\knowledge %USERPROFILE%\knowledge\
```

## 日常同步（sync.sh）

```bash
#!/bin/bash
cd ~/hermes-sync

# 同步 skills
rsync -av --delete \
  --exclude='.hub/' --exclude='.usage.json' --exclude='.backup/' \
  ~/.hermes/skills/ ./skills/

# 同步知识库（排除 LI 机密）
rsync -av --delete \
  --exclude='telecom/lawful_interception/' \
  --exclude='hi2/' --exclude='li/' \
  --exclude='ima-sync/downloads/' \
  --exclude='.enzyme/' --exclude='.kb-search/' --exclude='.obsidian/' \
  ~/knowledge/ ./knowledge/

git add . && git commit -m "sync $(date +%Y-%m-%d_%H:%M)" && git push
```

## Windows 端拉取

```powershell
cd %USERPROFILE%\hermes-sync
git pull
# skills 通过软链接自动生效
# knowledge 需手动复制或也用软链接
```

## LI 机密知识同步

不适合走 GitHub，用压缩包手动传输：

```bash
# Ubuntu 端打包（24MB 压缩后）
tar czvf ~/hermes-li-knowledge-$(date +%Y%m%d).tar.gz \
  knowledge/telecom/lawful_interception/ \
  knowledge/hi2/ \
  knowledge/li/

# 通过 U 盘 / SMB 共享 / 局域网 HTTP 传输
cd ~ && python3 -m http.server 8000  # 临时 HTTP 下载

# Windows 端解压
tar -xzf hermes-li-knowledge-*.tar.gz -C %USERPROFILE%
```

## 跨平台适配注意

- **config.yaml 不共享**：Windows 用 Python venv 路径不同
- **.env 不共享**：API Key 相同但各自独立管理
- **skills 用软链接**：Windows 上 mklink /J 后 git pull 自动生效
- **知识库用复制**：Windows 酶索引路径不同
- **Windows 特殊坑**：Alt+Enter=全屏（用 Ctrl+Enter 换行）、config.yaml 不用 Notepad 编辑（UTF-8 BOM 问题）

## 与一次性迁移的区别

| 特性 | `hermes profile export` 方案 | GitHub 同步方案 |
|------|---------------------------|----------------|
| 适用场景 | 一次迁移 | 持续双向同步 |
| 数据完整度 | 全部（含 sessions/memory/auth） | 仅 skills+知识库 |
| sessions | 包含 | 不包含（每台设备独立） |
| memory (state.db) | 包含 | 不包含 |
| 配置文件 | 包含 | 各自维护 |
| LI 机密 | 包含在 tar.gz | 独立压缩包 |
| 增量更新 | 每次全量 | git pull 增量 |
