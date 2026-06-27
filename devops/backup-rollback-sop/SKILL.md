---
name: backup-rollback-sop
description: 备份与回滚标准操作流程，涵盖操作前自动备份、系统级配置快照、目录级备份、回滚步骤、备份保留策略及验证流程，并与 Hermes 现有 cron 备份联动。
category: devops
author: Hermes Agent
version: 1.0.0
created: 2026-06-17
---

# 备份与回滚标准操作流程 (SOP)

> 本文档定义所有运维操作前后的备份与回滚规范，确保任何变更可追溯、可恢复。

---

## 目录

- [1. 操作前自动备份规范](#1-操作前自动备份规范)
- [2. 系统级配置快照](#2-系统级配置快照)
- [3. 目录级备份](#3-目录级备份)
- [4. 回滚操作步骤](#4-回滚操作步骤)
- [5. 备份保留策略](#5-备份保留策略)
- [6. 备份验证流程](#6-备份验证流程)
- [7. 与 Hermes Cron 备份的联动](#7-与-hermes-cron-备份的联动)
- [8. 紧急恢复速查表](#8-紧急恢复速查表)

---

## 1. 操作前自动备份规范

### 1.1 文件级备份

**任何修改操作前，必须先备份原始文件：**

```bash
# 单文件备份（推荐）
cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak-$(date +%Y%m%d-%H%M%S)

# 批量文件备份（进入目录后操作）
for f in *.yaml *.yml *.conf; do
  [ -f "$f" ] && cp "$f" "$f.bak-$(date +%Y%m%d-%H%M%S)"
done

# 使用备份管理器（如果已配置）
bash ~/.hermes/skills/devops/backup-rollback-sop/scripts/pre-backup.sh \
  /path/to/target/file.conf
```

### 1.2 Hermes 配置自动备份

Hermes 自身配置文件在每次变更前自动创建 `.bak-*` 副本（已有 24 个历史版本）：

```bash
# 手动触发 Hermes 配置备份
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak-$(date +%Y%m%d-%H%M%S)

# 查看历史备份版本
ls -la ~/.hermes/config.yaml.bak-*
```

### 1.3 Git 仓库操作前备份

```bash
# Git 仓库修改前，确保工作区干净或已暂存
git stash push -m "pre-backup-$(date +%Y%m%d-%H%M%S)"

# 或创建临时分支
git checkout -b backup/pre-$(date +%Y%m%d-%H%M%S)
git checkout main  # 回到目标分支继续操作
```

### 1.4 操作前置检查清单

| 检查项 | 命令 | 说明 |
|--------|------|------|
| 原始文件存在 | `ls -la <file>` | 确认源文件可访问 |
| 备份创建成功 | `ls -la <file>.bak-*` | 确认备份已生成 |
| 备份磁盘空间 | `df -h <backup_dir>` | 确认可用空间 > 1GB |
| 备份文件完整性 | `wc -c <file>.bak-*` | 确认备份文件非空 |

---

## 2. 系统级配置快照

### 2.1 关键配置文件快照

```bash
# 创建系统配置快照目录
SNAP_DIR="/root/config-snapshot-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$SNAP_DIR"

# 备份系统关键配置
cp -a /etc/ssh/sshd_config "$SNAP_DIR/"
cp -a /etc/nginx/ "$SNAP_DIR/nginx/"
cp -a /etc/systemd/ "$SNAP_DIR/systemd/"
cp -a /etc/cron.d/ "$SNAP_DIR/cron.d/"
cp -a /etc/hosts "$SNAP_DIR/"
cp -a /etc/resolv.conf "$SNAP_DIR/"
cp -a /etc/fstab "$SNAP_DIR/"

# 打包快照
tar czf "/backup/snapshots/system-config-$(date +%Y%m%d-%H%M%S).tar.gz" \
  -C "$SNAP_DIR" .
rm -rf "$SNAP_DIR"
```

### 2.2 软件包清单快照

```bash
# Debian/Ubuntu
dpkg --get-selections > "/backup/snapshots/packages-$(date +%Y%m%d).list"
dpkg -l > "/backup/snapshots/packages-verbose-$(date +%Y%m%d).txt"

# RHEL/CentOS
rpm -qa --queryformat '%{NAME}-%{VERSION}-%{RELEASE}.%{ARCH}\n' \
  > "/backup/snapshots/packages-$(date +%Y%m%d).list"

# Homebrew (macOS)
brew list --formula > "/backup/snapshots/brew-formula-$(date +%Y%m%d).list"
brew list --cask > "/backup/snapshots/brew-cask-$(date +%Y%m%d).list"
```

### 2.3 服务状态快照

```bash
# 系统服务状态
systemctl list-units --type=service --state=running \
  > "/backup/snapshots/services-$(date +%Y%m%d).txt"

# 网络连接状态
ss -tuln > "/backup/snapshots/network-listen-$(date +%Y%m%d).txt"

# 磁盘挂载状态
df -h > "/backup/snapshots/disk-usage-$(date +%Y%m%d).txt"
mount > "/backup/snapshots/mounts-$(date +%Y%m%d).txt"
```

### 2.4 使用 etckeeper（推荐）

```bash
# 安装 etckeeper（自动跟踪 /etc 所有变更）
apt install etckeeper   # Debian/Ubuntu
yum install etckeeper   # RHEL

# 查看 /etc 变更历史
cd /etc && git log --oneline

# 比较两个版本间的差异
cd /etc && git diff HEAD~1..HEAD

# 回滚 /etc 中特定文件
cd /etc && git checkout <commit-hash> -- nginx/nginx.conf
```

---

## 3. 目录级备份

### 3.1 使用 tar 打包备份

```bash
# 标准目录备份
BACKUP_DIR="/backup/manual"
mkdir -p "$BACKUP_DIR"

tar czf "$BACKUP_DIR/project-$(date +%Y%m%d-%H%M%S).tar.gz" \
  -C /path/to/parent \
  --exclude='node_modules' \
  --exclude='.git' \
  --exclude='*.log' \
  project-dir/

# 增量备份（基于日期）
tar czf "$BACKUP_DIR/project-$(date +%Y%m%d).tar.gz" \
  -N "$(date -d '1 day ago' +%Y-%m-%d)" \
  -C /path/to/parent \
  project-dir/
```

### 3.2 使用 rsync 备份

```bash
# 本地目录同步（保留权限、硬链接）
rsync -avz --delete --link-dest=/backup/latest \
  /source/project/ \
  "/backup/rsync/$(date +%Y%m%d-%H%M%S)/"

# 更新 latest 软链接（用于下次增量）
ln -snf "/backup/rsync/$(date +%Y%m%d-%H%M%S)" /backup/latest
```

### 3.3 数据库备份

```bash
# MySQL 全库备份
mysqldump -u root --all-databases --single-transaction --routines \
  | gzip > "/backup/db/mysql-full-$(date +%Y%m%d).sql.gz"

# PostgreSQL 全库备份
pg_dumpall -U postgres \
  | gzip > "/backup/db/pg-full-$(date +%Y%m%d).sql.gz"
```

### 3.4 LVM 快照备份（生产系统推荐）

```bash
# 创建 LVM 快照（需 VG 有剩余空间）
lvcreate -L 10G -s -n data_snap /dev/vg_data/lv_data

# 挂载快照并打包
mkdir -p /mnt/snapshot
mount -o ro /dev/vg_data/data_snap /mnt/snapshot
tar czf "/backup/lvm-snap-$(date +%Y%m%d-%H%M%S).tar.gz" \
  -C /mnt/snapshot .
umount /mnt/snapshot
lvremove -f /dev/vg_data/data_snap
```

---

## 4. 回滚操作步骤

### 4.1 文件级回滚（从 .bak 备份恢复）

```bash
# 查看可用备份
ls -la /etc/nginx/nginx.conf.bak-*

# 恢复指定版本
cp /etc/nginx/nginx.conf.bak-20260617-143000 /etc/nginx/nginx.conf

# 验证差异
diff /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak-20260617-143000

# 重载服务
nginx -t && systemctl reload nginx
```

### 4.2 Git 回滚

```bash
# 方式一：git revert（推荐，保留历史）
git revert HEAD          # 回滚最近一次提交
git revert <commit-hash> # 回滚指定提交
git revert HEAD~3..HEAD  # 回滚最近 3 次提交

# 方式二：git reset（仅本地未推送时使用）
git reset --hard HEAD~1    # 放弃最近一次提交
git reset --hard <commit>  # 回到指定提交

# 方式三：从 stash 恢复
git stash pop             # 恢复最近一次 stash
git stash apply stash@{0} # 恢复特定 stash

# 方式四：从备份分支恢复
git log --oneline backup/pre-*  # 查看备份分支
git cherry-pick <commit-hash>   # 挑选需要的提交
```

### 4.3 目录级回滚（从 tar 备份恢复）

```bash
# 列出备份文件
ls -la /backup/manual/project-*.tar.gz

# 查看备份内容（先验证）
tar tzf /backup/manual/project-20260617-143000.tar.gz | head -30

# 恢复到临时目录确认
mkdir -p /tmp/restore-check
tar xzf /backup/manual/project-20260617-143000.tar.gz \
  -C /tmp/restore-check

# 确认无误后正式恢复
tar xzf /backup/manual/project-20260617-143000.tar.gz \
  -C /path/to/target --overwrite

# 或分步恢复（先备份当前版本再回滚）
mv /path/to/target/project-dir /path/to/target/project-dir.failed
tar xzf /backup/manual/project-20260617-143000.tar.gz \
  -C /path/to/target
```

### 4.4 系统配置回滚

```bash
# 从快照恢复
SNAPSHOT="/backup/snapshots/system-config-20260617-143000.tar.gz"
tar tzf "$SNAPSHOT"                              # 验证快照内容
tar xzf "$SNAPSHOT" -C /tmp/restore-config       # 解压到临时目录
diff -r /tmp/restore-config/nginx/ /etc/nginx/   # 对比差异

# 确认后复制
cp -a /tmp/restore-config/nginx/ /etc/nginx/

# 使用 etckeeper 回滚
cd /etc && git log --oneline
cd /etc && git checkout <commit-hash>

# 使用软件包清单恢复
dpkg --clear-selections
dpkg --set-selections < /backup/snapshots/packages-20260617.list
apt-get dselect-upgrade
```

### 4.5 服务启动验证（回滚后必做）

```bash
# 检查配置语法
nginx -t
sshd -t
systemctl status nginx

# 检查服务运行状态
systemctl is-active nginx
systemctl is-enabled nginx

# 检查端口监听
ss -tuln | grep -E ':(80|443|22)\s'

# 检查日志有无异常
journalctl -u nginx --since "5 minutes ago" --no-pager | tail -20
```

---

## 5. 备份保留策略

### 5.1 手动备份保留策略

| 备份类型 | 保留期限 | 清理条件 |
|---------|---------|---------|
| 操作前 .bak 文件 | 7 天 | `find . -name "*.bak-*" -mtime +7 -delete` |
| 系统配置快照 | 30 天 | `find /backup/snapshots -name "*.tar.gz" -mtime +30 -delete` |
| 目录级 tar 备份 | 14 天 | `find /backup/manual -name "*.tar.gz" -mtime +14 -delete` |
| 数据库备份 | 30 天 | `find /backup/db -name "*.sql.gz" -mtime +30 -delete` |
| 项目回滚备份 | 直到确认稳定后 | 手动删除 |

### 5.2 清理脚本

```bash
#!/usr/bin/env bash
# cleanup-old-backups.sh — 清理过期手动备份

BACKUP_DIRS=(
  "/backup/manual:14"
  "/backup/snapshots:30"
  "/backup/db:30"
)

for entry in "${BACKUP_DIRS[@]}"; do
  dir="${entry%%:*}"
  days="${entry##*:}"
  if [ -d "$dir" ]; then
    count=$(find "$dir" -name "*.tar.gz" -o -name "*.sql.gz" -mtime "+$days" | wc -l)
    find "$dir" -name "*.tar.gz" -o -name "*.sql.gz" -mtime "+$days" -delete
    echo "[$(date)] 清理 $dir 中 $count 个超过 ${days} 天的备份文件"
  fi
done

# 清理备份历史中的 .bak 文件（扫描家目录和 /etc）
find /etc ~ -maxdepth 5 -name "*.bak-*" -mtime +7 -delete 2>/dev/null
```

### 5.3 磁盘空间预警

```bash
# 当备份目录使用率 > 85% 时触发告警
BACKUP_DISK_USAGE=$(df /backup | awk 'NR==2{print $5}' | tr -d '%')
if [ "$BACKUP_DISK_USAGE" -gt 85 ]; then
  echo "⚠️ 警告：备份磁盘使用率已达 ${BACKUP_DISK_USAGE}%"
  echo "建议手动清理或扩大存储空间"
fi
```

---

## 6. 备份验证流程

### 6.1 tar 归档验证

```bash
# 基本验证：列出内容
tar tzf /backup/manual/project-20260617.tar.gz | head -20

# 完整性验证（创建时需加校验）
tar czf /backup/manual/project-20260617.tar.gz \
  --checkpoint=1000 \
  /path/to/project/

# 解压测试到临时目录
TMPDIR=$(mktemp -d)
tar xzf /backup/manual/project-20260617.tar.gz -C "$TMPDIR"
echo "解压验证：文件数 $(find "$TMPDIR" -type f | wc -l)"
rm -rf "$TMPDIR"
```

### 6.2 文件差异对比验证

```bash
# 备份前后对比
diff -rq /original/path/ /tmp/restore-check/ 2>/dev/null

# 仅对比关键文件
diff /etc/nginx/nginx.conf /tmp/restore-check/etc/nginx/nginx.conf

# 使用 md5sum 验证
find /path/to/project -type f -exec md5sum {} \; | sort > /tmp/md5-before.txt
# ... 执行备份 ...
md5sum -c /tmp/md5-before.txt > /tmp/md5-check-result.txt 2>&1
grep -v ": OK" /tmp/md5-check-result.txt  # 检查不一致的文件

# 统计文件数量与大小
echo "源目录: $(find /original/path -type f | wc -l) 个文件"
echo "备份中: $(tar tzf backup.tar.gz | grep -v '/$' | wc -l) 个文件"
```

### 6.3 自动化验证脚本

```bash
# verify-backup.sh — 备份验证工具
# 用法: bash verify-backup.sh <backup.tar.gz> <original_dir>

BACKUP_FILE="$1"
ORIGINAL_DIR="$2"

if [ -z "$BACKUP_FILE" ] || [ -z "$ORIGINAL_DIR" ]; then
  echo "用法: $0 <backup.tar.gz> <original_dir>"
  exit 1
fi

TMPDIR=$(mktemp -d)
echo "=== 开始验证: $(date) ==="
echo "备份文件: $BACKUP_FILE"
echo "原始目录: $ORIGINAL_DIR"

# 1. 文件完整性
echo "[1/4] 验证归档完整性..."
tar tzf "$BACKUP_FILE" > /dev/null 2>&1
if [ $? -eq 0 ]; then
  echo "  ✅ 归档完整性通过"
else
  echo "  ❌ 归档损坏"
  rm -rf "$TMPDIR"
  exit 1
fi

# 2. 解压测试
echo "[2/4] 解压测试..."
tar xzf "$BACKUP_FILE" -C "$TMPDIR"
BACKUP_COUNT=$(find "$TMPDIR" -type f | wc -l)
ORIG_COUNT=$(find "$ORIGINAL_DIR" -type f | wc -l)
echo "  备份文件数: $BACKUP_COUNT, 原始文件数: $ORIG_COUNT"

# 3. 文件对比
echo "[3/4] 文件对比..."
DIFF_COUNT=$(diff -rq "$ORIGINAL_DIR" "$TMPDIR" 2>/dev/null | wc -l)
if [ "$DIFF_COUNT" -eq 0 ]; then
  echo "  ✅ 文件完全一致"
else
  echo "  ⚠️  存在 $DIFF_COUNT 处差异"
  diff -rq "$ORIGINAL_DIR" "$TMPDIR" 2>/dev/null | head -10
fi

# 4. 清理
echo "[4/4] 清理..."
rm -rf "$TMPDIR"
echo "=== 验证完成: $(date) ==="
```

### 6.4 特殊场景验证

```bash
# 验证数据库备份文件
gunzip -t /backup/db/mysql-full-20260617.sql.gz && echo "✅ SQL 压缩包完好"
head -5 /backup/db/mysql-full-20260617.sql             # 检查 SQL 头部

# 验证加密备份（borg）
borg list /backup/borg-repo                            # 列出备份
borg check /backup/borg-repo                           # 完整验证
borg extract --dry-run /backup/borg-repo::backup-name  # 干运行测试

# 验证 restic 备份
restic snapshots --repo /backup/restic-repo
restic check --repo /backup/restic-repo
```

---

## 7. 与 Hermes Cron 备份的联动

### 7.1 Hermes 现有 Cron 备份概览

Hermes 已配置以下自动备份任务，与本 SOP 中的手动操作互补：

| Cron 任务 | 脚本 | 调度 | 说明 |
|-----------|------|------|------|
| **每日备份** | `daily-backup.sh` | 每天 03:00 | 增量备份关键数据 |
| **每周完整备份** | `weekly-full-backup.sh` | 每周日 04:00 | 全量备份，完整快照 |

### 7.2 联动使用场景

#### 场景一：日常操作前后

```bash
# 1. 操作前检查 Cron 备份是否正常完成
bash ~/.hermes/cron/output/*/latest 2>/dev/null \
  | grep "备份" || echo "检查 ~/.hermes/cron/jobs.json"

# 2. 执行本文档第 1 节的操作前备份
cp target.conf target.conf.bak-$(date +%Y%m%d-%H%M%S)

# 3. 执行变更操作
# 4. 操作后验证（本文档第 6 节）
```

#### 场景二：Cron 备份失败时手动触发

```bash
# 查看 Cron 任务状态
cat ~/.hermes/cron/jobs.json | python3 -c "
import json,sys
jobs = json.load(sys.stdin)['jobs']
for j in jobs:
    if '备份' in j['name']:
        print(f\"{j['name']}: {j['last_status']} (下次: {j['next_run_at']})\")
"

# 手动执行每日备份脚本
bash ~/.hermes/skills/scripts/daily-backup.sh  # 如果脚本路径可访问
```

#### 场景三：大变更前的完整快照

```bash
# 在执行重大变更前，手动触发每周完整备份级别的快照
# 参考本文档第 2 节，创建系统配置快照
bash -c "$(cat <<'SNAPEOF'
SNAP_DIR="/root/pre-change-snapshot-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$SNAP_DIR"
cp -a /etc/ "$SNAP_DIR/etc/"
dpkg --get-selections > "$SNAP_DIR/packages.list"
systemctl list-units --type=service --state=running > "$SNAP_DIR/services.txt"
ss -tuln > "$SNAP_DIR/network.txt"
tar czf "/backup/snapshots/pre-change-$(date +%Y%m%d-%H%M%S).tar.gz" -C "$SNAP_DIR" .
rm -rf "$SNAP_DIR"
echo "快照已创建"
SNAPEOF
)"
```

### 7.3 备份依赖关系图

```
┌──────────────────────────────────────────────────────────┐
│                   Hermes 备份体系                        │
├─────────────────┬─────────────────┬─────────────────────┤
│  每日备份       │  每周完整备份   │  操作前手动备份     │
│  (03:00 cron)   │  (周日 04:00)   │  (按需执行)         │
├─────────────────┼─────────────────┼─────────────────────┤
│ 增量备份        │  全量快照       │  文件 .bak          │
│ 节省空间        │  完整可恢复     │  目录 tar.gz        │
│ 保留 7 天       │  保留 4 周      │  按策略保留         │
└─────────────────┴─────────────────┴─────────────────────┘
        ↑                    ↑                 ↑
        └──────────── 三层防护 ────────────────┘
```

### 7.4 建议的完整工作流

```bash
# ═══════════════════════════════════════════════
#   推荐操作流程 (变更管理 Checklist)
# ═══════════════════════════════════════════════

# [前置检查] ── 确认 Cron 备份最近成功
#   → cat ~/.hermes/cron/jobs.json | grep -A5 '每日备份'
#   → 检查 last_status 是否为 "ok"

# [Step 1]  ── 操作前备份（本文档第 1 节）
#   → cp file.conf file.conf.bak-$(date +%Y%m%d-%H%M%S)

# [Step 2]  ── 系统快照（本文档第 2 节，重大变更必做）
#   → 创建 /backup/snapshots/pre-*.tar.gz

# [Step 3]  ── 执行操作
#   → 修改配置 / 升级软件 / 部署代码

# [Step 4]  ── 验证（本文档第 6 节）
#   → 服务状态检查、功能测试

# [Step 5]  ── 如有问题，立即回滚（本文档第 4 节）
#   → cp file.conf.bak-* file.conf && systemctl reload <service>

# [Step 6]  ── 确认稳定后，保留 .bak 7 天后自动清理
```

---

## 8. 紧急恢复速查表

```bash
# ┌──────────────────────────────────────────────────────┐
# │  紧急情况快速恢复命令                                 │
# └──────────────────────────────────────────────────────┘

# 场景 1：配置文件改坏了
cp /etc/nginx/nginx.conf.bak-$(ls -t /etc/nginx/*.bak-* | head -1 | xargs basename) \
  /etc/nginx/nginx.conf && nginx -t && systemctl reload nginx

# 场景 2：Git 提交有问题
git revert --no-edit HEAD

# 场景 3：目录被误删
ls -t /backup/manual/*.tar.gz | head -1 | xargs tar xzf - -C /target/path

# 场景 4：系统配置混乱
tar xzf /backup/snapshots/$(ls -t /backup/snapshots/*.tar.gz | head -1) \
  -C /tmp/restore && cp -a /tmp/restore/etc/* /etc/

# 场景 5：包管理器损坏
apt list --installed 2>/dev/null > /tmp/current-pkgs.txt
diff /backup/snapshots/packages-*.list /tmp/current-pkgs.txt

# 场景 6：查看最近 3 次每日 Cron 备份输出
ls -t ~/.hermes/cron/output/ | head -3 | while read dir; do
  echo "=== $dir ==="
  cat ~/.hermes/cron/output/$dir/$(ls ~/.hermes/cron/output/$dir/)
done
```

## 9. Hermes Agent 跨平台迁移

### 9.1 三种备份方式对比

| 命令 | 输出格式 | 覆盖范围 | 适用场景 |
|------|---------|---------|---------|
| `hermes backup` | .zip | 整个 `~/.hermes/`（config + skills + sessions + auth + state.db + logs + plugins + cron + 所有数据） | 全量灾备 / 整机迁移 |
| `hermes backup --quick` | .zip | 仅关键状态文件：config, state.db, .env, auth, cron | 快速快照 |
| `hermes profile export` | .tar.gz | 当前 profile 的 config + skills + sessions + memories + auth + cron | 多 profile 环境下的单 profile 迁移 |

**实测数据**（Ubuntu 24.04，~/.hermes 约 2.1GB）：
- `hermes backup`: 7510 文件 → 817MB .zip（耗时 ~79s）
- `hermes profile export default`: 实测 664MB .tar.gz（~3 分钟）

### 9.2 迁移范围清单

`hermes backup` 和 `hermes profile export` 都 **不包含** 以下关键数据：

| 组件 | 路径 | 独立备份原因 |
|------|------|-------------|
| **知识库** | `~/knowledge/` | Obsidian vault，完全独立于 Hermes 目录 |
| MCP Servers | `~/.hermes/mcp-servers/` | 外部 Python 项目，不随 profile 导出 |
| JD MCP | `~/.hermes/jd_mcp/` | 外部项目 |
| Taobao MCP | `~/.hermes/taobao_mcp/` | 外部项目（含 .git） |
| Open Second Brain | `~/.hermes/open-second-brain/` | 插件数据，不随 profile 导出 |
| OSB Plugin | `~/.hermes/plugins/open-second-brain/` | 插件代码 |
| API Keys | `~/.hermes/.env` | `.env` 在备份文件中但被压缩；Win11 上需重新配置 |

### 9.3 推荐迁移流程：两步法

**核心思路**：用 `hermes backup` 代替多步手动打包（一步搞定 config+skills+sessions），知识库独立处理。

#### Step 1 — 备份 Hermes 配置 + Skills

```bash
# 全量备份（含 config, skills, sessions, auth, state.db 等所有 ~/.hermes/ 内容）
hermes backup -o ~/hermes-backup-$(date +%Y%m%d).zip
```

恢复：`hermes import hermes-backup-20260627.zip`

优点：
- 一步替代了 profile export + mcp + brain 三步
- 7510 文件自动处理，不受断链 symlink 影响
- MCP/插件可在目标机重新安装（或单独打包传输）

#### Step 2 — 备份知识库

```bash
# 打包知识库（排除可重建索引，节省 ~2GB）
tar czf /tmp/knowledge-backup-$(date +%Y%m%d).tar.gz \
  --exclude=.enzyme \
  --exclude=.kb-search \
  --exclude=.git \
  -C ~ knowledge/
```

索引说明：
- `.enzyme/`（~1.5G）、`.kb-search/`（~529M）是搜索引擎索引，**不需要备份**
- 恢复后在目标机运行 `cd ~/knowledge && enzyme refresh` 重建

#### Step 3 — 传输到目标机

```bash
# 方式 A：局域网 HTTP
cd ~ && python3 -m http.server 8000

# 方式 B：USB 拷贝
cp ~/hermes-backup-*.zip /media/usb/
cp /tmp/knowledge-backup-*.tar.gz /media/usb/

# 方式 C：SCP / 百度网盘
```

#### Step 4 — 目标机恢复（以 Windows 11 为例）

```powershell
# 1. 安装 Hermes（如未装）
winget install NousResearch.HermesAgent

# 2. 恢复 Hermes 配置 + skills
hermes import hermes-backup-20260627.zip

# 3. 恢复知识库
tar xzf knowledge-backup-20260627.tar.gz -C %USERPROFILE%

# 4. 重建搜索索引
cd %USERPROFILE%\knowledge
enzyme refresh

# 5. 手动配置 .env（各环境 API Key 不同）
# 记事本打开 %USERPROFILE%\.hermes\.env，填入自己的 API Key

# 6. 验证
hermes doctor
```

### 9.4 备选流程：分模块打包（`hermes profile export` 方式）

当需要按模块独立恢复时，采用分步打包：

**Step 1 — 清理断链 skill（否则 profile export 会崩溃）**
```bash
find ~/.hermes/skills/ -xtype l -delete
```

**Step 2 — 导出 profile**
```bash
mkdir -p ~/hermes-migration
hermes profile export default -o ~/hermes-migration/hermes-profile.tar.gz
```

**Step 3 — 备份 MCP 服务**
```bash
tar czf ~/hermes-migration/hermes-mcp.tar.gz \
  -C ~/.hermes mcp-servers \
  -C ~/.hermes jd_mcp \
  -C ~/.hermes taobao_mcp
```

**Step 4 — 备份 Second Brain**
```bash
tar czf ~/hermes-migration/hermes-brain.tar.gz \
  -C ~/.hermes open-second-brain \
  -C ~/.hermes plugins/open-second-brain
```

**Step 5 — 备份知识库**
```bash
tar czf ~/hermes-migration/knowledge.tar.gz \
  --exclude='.DS_Store' \
  --exclude='.git' \
  --exclude='.enzyme' \
  --exclude='.kb-search' \
  -C ~ knowledge/
```

**Step 6 — 备份 .env**
```bash
cp ~/.hermes/.env ~/hermes-migration/hermes-env.txt
```

### 9.5 验证打包完整性

```bash
# .zip 校验
unzip -t hermes-backup-*.zip | tail -3
# 应显示 "No errors detected in compressed data"

# .tar.gz 校验
for f in ~/hermes-migration/*.tar.gz; do
  echo -n "$(basename $f): "
  gzip -t "$f" && echo "✅ 正常" || echo "❌ 损坏"
done
```

### 9.6 迁移陷阱

- **`hermes backup` 不包含知识库**：知识库（`~/knowledge/`）在 Hermes 外部，必须单独打包
- **`hermes profile export` 不包含 MCP/插件/知识库**：profile export 只导出 profile 管理的组件
- **Broken skill symlinks**: `hermes profile export` 遇到断链 symlink 会直接崩溃（`shutil.Error`）。`hermes backup` 不会因此崩溃（它打包整个 ~/.hermes/ 而非逐文件复制）
- **大文件打包超时**: 知识库（~1.7G）和 profile（~664M）打包需几分钟，用 `background=true + notify_on_complete=true`
- **Windows 原生 vs WSL**: Windows 原生 Hermes 不支持 systemd cron；WSL 2 则 cron 原样工作
- **`.env` 不能走网络传输**: API key 安全敏感，必须手动复制
- **Windows Terminal 特性**: `Alt+Enter` 被拦截用作全屏切换，用 `Ctrl+Enter` 代替；`config.yaml` 不要用 Notepad 编辑（可能写入 UTF-8 BOM）
- **路径约定**: 所有工具和 Windows API 接受正斜杠 `C:/Users/...`，优先使用
- **酶索引跨平台重建**: `.enzyme/` 和 `.kb-search/` 不必备份，但恢复后必须运行 `enzyme refresh` 重建

---

## 10. GitHub 中转持续同步策略

### 10.1 适用场景

当需要 **持续双向同步** Hermes 的 skills 和知识库（非 LI 部分）时，GitHub 私有仓库比 `hermes profile export` 更适合：

- 日常增量更新（git pull/push 而非全量打包）
- Ububtu ↔ Windows 等多台设备的同步
- 技能文件的版本历史追踪

### 10.2 数据分类与同步方式

| 分类 | 内容 | 同步方式 | 安全等级 |
|------|------|---------|---------|
| Skills | `~/.hermes/skills/` | GitHub 私有仓库 | 可公开 |
| 通用知识 | `~/knowledge/` 排除 LI 内容 | GitHub 私有仓库 | 可公开 |
| LI 机密 | `lawful_interception/`, `hi2/`, `li/` | 压缩包+U盘/直连 | LEVEL 5 |
| 配置文件 | `config.yaml`, `.env` | 各自维护 | 含 API Key |

### 10.3 仓库 .gitignore 关键规则

```
# LI 机密数据 — 绝对不上 GitHub
telecom/lawful_interception/
hi2/
li/

# Skills 缓存
skills/.hub/
skills/.usage.json
skills/.backup/

# 知识库缓存
.enzyme/ .kb-search/ .obsidian/

# 二进制文件（膨胀 git 仓库）
*.pdf *.jpg *.png *.zip *.tar.gz *.docx *.pptx *.xlsx

# 嵌入 git 子仓库
skills/superpowers/
skills/research/personal-api-skill/
```

### 10.4 首次设置与日常同步

```bash
# Ubuntu 端首次推送
cd ~ && mkdir hermes-sync && cd hermes-sync
# 初始化 + 复制 skills 和知识库 + 推送
gh repo create andymao76/hermes-sync --private --source=. --remote=origin --push

# Windows 端首次克隆
git clone https://github.com/andymao76/hermes-sync.git %USERPROFILE%\hermes-sync
mklink /J %USERPROFILE%\.hermes\skills %USERPROFILE%\hermes-sync\skills
```

日常同步脚本 `sync.sh` 见 `references/hermes-github-sync-workflow.md`。

### 10.5 LI 机密知识传输

```bash
# Ubuntu 端打包（含 lawful_interception + hi2 + li）
tar czvf ~/hermes-li-knowledge-$(date +%Y%m%d).tar.gz \
  knowledge/telecom/lawful_interception/ knowledge/hi2/ knowledge/li/
```

### 10.6 陷阱

- **skills 用软链不是复制**: Windows 上 `mklink /J` 后 `git pull` 自动生效
- **config.yaml 不共享**: Windows 和 Linux 的 Python 路径不同，各自维护
- **.env 不共享**: API Key 相同但各自管理
- **知识库不软链**: 酶索引路径平台相关，用复制
- **超大 .git**: 首次推送 4000+ 文件约 2GB，若包含 ima-sync/downloads/ 的 PDF 会更大，必须在 .gitignore 中排除

### 10.7 策略选择

| | `hermes profile export` | GitHub 同步 |
|---|---|---|
| 适用 | 一次迁移 | 持续同步 |
| sessions/memory/auth | 包含 | 不包含 |
| 增量更新 | 每次全量 | git pull 增量 |
| 配置文件 | 包含 | 各自维护 |

完整工作流参考：`references/hermes-github-sync-workflow.md`

---

> **文档版本**: 1.3.0  \n> **更新**: 2026-06-27 — 新增 `hermes backup` 两步迁移模式，重构第 9 节三种备份方式对比  \n> **创建日期**: 2026-06-17  \n> **维护者**: Hermes Agent  \n> **关联 Skill**: `security-audit-sop`（安全审计流程）、`linux-sysadmin/scripts/backup_manager.sh`（备份管理脚本）、`linux-sysadmin/references/backup_recovery.md`（备份恢复参考）
