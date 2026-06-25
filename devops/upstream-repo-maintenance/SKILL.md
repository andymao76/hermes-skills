---
name: upstream-repo-maintenance
title: 上游仓库维护
description: 管理从 GitHub 克隆的上游仓库 — 自定义脚本隔离、.gitignore 管控、git status 清理，确保 git pull 无冲突
category: devops
trigger: 当发现 git status 显示未跟踪的自定义脚本、日志文件、诊断输出等非上游文件时
---

# 上游仓库维护

## 核心原则

克隆的上游仓库（非 fork）必须保持干净，不允许直接 commit 本地自定义文件，否则 `git pull` 会产生冲突。

```
用户：dify 目录下有未跟踪的文件 → 发现是自添加的诊断脚本
→ 正确处理：
  1. 脚本移到 ~/scripts/{项目名}/
  2. 临时日志直接删除
  3. .gitignore 追加模式防再出现
  4. 确认 git status 干净
```

## 判断标准

| 条件 | 处理方式 |
|------|---------|
| 脚本类（.sh/.py 等可执行文件） | 移到 `~/scripts/{项目名}/` |
| 日志文件（.log/.txt 等诊断输出） | 直接删除 |
| 配置文件修改（.env 等） | 保留在 .gitignore 中，不入 track |
| 上游跟踪文件的本地修改 | 用 `git stash` 暂存，upstream 更新后视情况合并 |
| node_modules/ 等构建产物 | 确认已在 .gitignore 中 |

## 操作步骤

### 1. 检查 git 状态

```bash
cd ~/{仓库目录}
git status --short
```

### 2. 分类处理未跟踪文件

```bash
# 脚本类：移动到 ~/scripts/{项目名}/
mkdir -p ~/scripts/{项目名}/
mv docker/*.sh ~/scripts/{项目名}/

# 日志类：直接删除
rm docker/*.log docker/*.txt

# 确认清理结果
git status --short
```

### 3. 更新 .gitignore

追加**具体文件模式**而非通配，避免意外屏蔽上游的 .log/.txt 文件：

```bash
# 追加到 .gitignore 末尾（使用具体模式，不用 *.log/*.txt）
cat >> .gitignore << 'EOF'

# User-added diagnostic scripts (moved to ~/scripts/{project}/)
docker/diagnose.sh
docker/dify-diagnose.sh
docker/manage.sh
docker/quick_diagnose.sh
docker/view_logs.sh
docker/*.txt
EOF
```

**原则：** 宁用具体文件名，不用通配。`*.log` 可能屏蔽上游的正式日志文件。

### 4. 最终验证

```bash
git status --short
# 理想结果：只有 .gitignore 显示 modified（如果是初次修改）
```

## 已知仓库

| 仓库 | 路径 | 类型 |
|------|------|------|
| langgenius/dify | `~/dify/` | 上游克隆 |
| googleapis/python-genai | `~/python-genai/` | 上游克隆 |
| jo-inc/camofox-browser | `~/camofox-browser/` | 上游克隆 |

## 注意

- ❌ 不要直接 git add 自定义文件并 commit — 下次 git pull 100% 冲突
- ❌ 不要使用 `*.log` 或 `*.txt` 等宽泛通配（可能屏蔽上游正式日志文件）
- ✅ 宁用具体文件名，不用通配。一组脚本用行级精确模式
- ✅ 脚本统一放 `~/scripts/{项目名}/` ，方便日后查找
- ✅ 日志文件超过 100KB 的尤其要删除，不入版本控制

## 参考案例

- `references/repos/dify-example.md` — Dify 仓库诊断脚本处理完整记录（5个脚本迁移 + 835KB日志删除 + 逐行 .gitignore）
