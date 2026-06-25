---
name: obsidian-vault-maintenance
description: Obsidian vault 结构维护、Samba 共享、GitHub 备份策略、密钥安全策略
trigger: 清理 Obsidian、同步 Obsidian、备份策略、Samba 配置、密钥管理
---

# Obsidian Vault 维护手册

## 一、 vault 结构（三分类）

```
📁 Obsidian vault (~/Documents/Obsidian Vault/)
├── 工作/          ← 日报/周报/月报/项目笔记
│   ├── 日报/YYYYMMDD.md     ← Hermes 写入路径
│   ├── 周报/                 ← 周五生成
│   ├── 月报/                 ← 月底生成
│   └── 项目/                 ← 项目笔记
├── 知识/          ← symlink → ~/knowledge（852MB，本地）
├── 技能/          ← skill 文档/工作流指南
├── Brain/         ← 系统记忆
└── 📖 知识库主页.md
```

## 二、 路径一致性保障

双入口，指向同一位置：

| 入口 | 路径 |
|------|------|
| Obsidian 原生 | `~/Documents/Obsidian Vault/工作/日报/YYYYMMDD.md` |
| kb-search 索引 | `~/knowledge/工作/ → symlink →` |

自动修复脚本：
```bash
bash ~/.hermes/scripts/ensure-vault-structure.sh
```
每天 06:00 cron 自动执行（`sinovatio-path-check`）。

## 三、 Windows 远程访问（Samba）

Ubuntu 端配置：
```bash
# 安装（已完成）
sudo apt install samba
sudo smbpasswd -a andymao

# 配置（已完成）：/etc/samba/smb.conf 中 [obsidian] 共享
# path = /home/andymao/Documents/Obsidian Vault

# 防火墙
sudo ufw allow samba
```

Windows 端：
- 映射网络驱动器 `\\192.168.1.53\obsidian`
- 用户名 `andymao`，密码为 smbpasswd 设置的密码
- Obsidian 中打开 Z 盘作为仓库
- 知识库/技能目录轻量，秒级加载

## 四、 GitHub 备份策略

| 仓库 | 可见性 | 备份内容 |
|------|:------:|---------|
| `hermes-worklog-skills` | 🔒 私有 | worklog/日报/周报/月报 技能包 |
| `hermes-config` | 🔒 私有 | 配置脱敏模板 + 脚本 + memory + cron 清单 |
| `hermes-community-skills` | 🌍 公开 | 社区技能索引 |

## 五、 密钥安全策略

**API Key / 密码/Token 仅存本地，永不推送 GitHub：**

```
/mnt/backup/secrets/
├── hermes-config.yaml    ← 完整 config.yaml（含所有 Key）
├── hermes-env.txt        ← .env 环境变量
└── README.md
```

恢复命令：
```bash
cp /mnt/backup/secrets/hermes-config.yaml ~/.hermes/config.yaml
cp /mnt/backup/secrets/hermes-env.txt ~/.hermes/.env
```

## 六、 知识库备份策略

| 数据 | 备份方式 | 位置 |
|------|---------|------|
| 知识库 852MB | 每日增量 03:00 | `/mnt/backup/backups/` |
| 每周完整备份 | 周日 04:00 | `/mnt/backup/backups/` |
| 保留周期 | 60 天 | 自动清理 |
| >20MB 单文件 | 本地备份 | 不推 GitHub |

## 七、 工作日志节奏

| 时间 | 命令 |
|------|------|
| 每天下班前 | `生成今天的日报` |
| 每周五下班前 | `生成本周周报` |
| 每月最后一天 | `生成本月月报` |

默认项目：A1 PC项目（苏丹NISS）

## 八、 Copilot CLI 集成与 ACP 认证修复

### 8.1 认证修复（经典 PAT 冲突）

Copilot CLI 不支持 `ghp_` 经典 PAT。当 `GITHUB_TOKEN` 环境变量中为经典 PAT 时，Copilot 会拒绝认证：
```
Error: Classic Personal Access Tokens (ghp_) are not supported by Copilot.
```

**修复步骤：**
```bash
# 清除经典 PAT 环境变量
unset GITHUB_TOKEN GH_TOKEN

# 确保 COPILOT_GITHUB_TOKEN 使用 OAuth token (gho_)
export COPILOT_GITHUB_TOKEN=$(gh auth token)
```

### 8.2 ACP 包装器（delegate_task 集成）

当通过 `delegate_task(acp_command="copilot")` 调用 Copilot 时，子进程会继承父进程的完整环境，包括 `GITHUB_TOKEN` 经典 PAT。ACP 包装器解决此问题。

**脚本：** `~/.hermes/scripts/copilot-acp-wrapper.py`
- 从 `gh auth token` 获取 `gho_` OAuth token
- 清除 `GITHUB_TOKEN` / `GH_TOKEN` 环境变量
- 用干净的 env 启动 Copilot ACP

**配置（写入 ~/.hermes/.env）：**
```
HERMES_COPILOT_ACP_COMMAND=python3 /home/andymao/.hermes/scripts/copilot-acp-wrapper.py
```

需重启 Hermes 会话生效。

### 8.3 Token 优先级

| 变量 | 优先级 | 类型 | 说明 |
|------|:------:|------|------|
| `COPILOT_GITHUB_TOKEN` | 1 | `gho_` 或 fine-grained PAT | 用于 Copilot CLI |
| `GH_TOKEN` | 2 | 任意 | gh CLI 使用 |
| `GITHUB_TOKEN` | 3 | `ghp_` 经典 PAT | GitHub MCP 使用（Copilot 不支持） |

## 九、 快速修复命令

```bash
# 修复 vault 目录结构
bash ~/.hermes/scripts/ensure-vault-structure.sh

# 恢复密钥
cp /mnt/backup/secrets/hermes-config.yaml ~/.hermes/config.yaml

# 刷新知识库索引
cd ~/knowledge && python3 ~/.hermes/scripts/kb-search.py refresh

# 重启 Samba
sudo systemctl restart smbd
```
