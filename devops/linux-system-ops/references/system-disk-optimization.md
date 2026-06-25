# 系统盘空间优化工作流

系统盘空间不足时，按以下三层流程分析并执行优化。

## 总览

1. **分析** — 分层扫描找到空间占用大户
2. **分类** — 按 安全可清理 / 可迁移到外置盘 / 系统不可动 三类决策
3. **执行** — 清理 + 迁移（symlink 模式），每一步让用户确认

---

## 第一步：分层空间分析

### 第一层：根目录一级

```bash
du -sh /* 2>/dev/null | sort -rh | head -20
```

重点盯：`/home`、`/snap`、`/var`、`/usr`、`/opt`。

### 第二层：用户主目录

```bash
# 普通目录
du -sh ~/*/ 2>/dev/null | sort -rh | head -20
# 隐藏目录
du -sh ~/.* 2>/dev/null | grep -v "\.cache$\|\.config$\|\.local$" | sort -rh | head -10
# 缓存目录细分
du -sh ~/.cache/*/ 2>/dev/null | sort -rh
```

### 第三层：大文件

```bash
sudo find / -xdev -type f -size +100M -exec ls -lh {} \; 2>/dev/null | sort -k5 -rh | head -20
```

---

## 第二步：分类决策

按三类整理发现，用表格呈现给用户：

| 类别 | 判断标准 | 处理方式 | 示例 |
|------|---------|---------|------|
| 🟢 安全可清理 | 临时文件、旧版本、构建缓存、系统日志 | 直接删除 | Snap 旧版本、journalctl、apt 缓存、pip/go-build 缓存 |
| 🟡 可迁移到外置盘 | 浏览器缓存、模型缓存、npm 包、用户数据 | 移 + symlink | ~/.cache/、~/.npm/、~/Downloads/、~/Pictures/ |
| ⚠️ 不可迁移 | Snap 包本体、系统安装程序、~/.config、~/.hermes | 留在系统盘 | /snap/、/opt/、~/.hermes/ |

### 安全可清理项命令速查

```bash
# Snap 旧版本（批量删除已禁用版本）
snap list --all | grep "已禁用" | while read n v r t; do
  sudo snap remove "$n" --revision="$r"
done

# journalctl 日志压缩
sudo journalctl --vacuum-size=200M

# apt 下载缓存
sudo apt clean

# pip / go 构建缓存
rm -rf ~/.cache/pip/ ~/.cache/go-build/

# Hermes 更新快照（保留最新 1 个）
ls -t ~/.hermes/state-snapshots/ | tail -n +2 | while read snap; do
  rm -rf ~/.hermes/state-snapshots/"$snap"
done
```

---

## 第三步：批量迁移到外置盘（symlink 模式）

### 迁移主流程

```
系统盘目录 → rsync 到 BACKUP → rm 原目录 → ln -s 建软链接 → 验证
```

### 批量迁移脚本模板

```bash
# 先在 BACKUP 创建目标目录
mkdir -p /mnt/backup/home-sync/cache
mkdir -p /mnt/backup/home-sync/data
mkdir -p /mnt/backup/home-sync/config

# 定义迁移列表
migrate() {
  local src="$1" dst="$2" name="$3"
  local expanded_src=$(eval echo "$src")
  
  echo "📦 $name..."
  rsync -ah "$expanded_src/" "$dst/" 2>&1 | tail -1
  
  # 验证文件数
  local src_count=$(find "$expanded_src" -type f 2>/dev/null | wc -l)
  local dst_count=$(find "$dst" -type f 2>/dev/null | wc -l)
  
  if [ "$src_count" -eq "$dst_count" ]; then
    rm -rf "$expanded_src"
    ln -s "$dst" "$expanded_src"
    echo "   ✅ $(ls -la "$expanded_src" 2>&1 | head -1)"
  else
    echo "   ❌ 文件数不匹配: $src_count vs $dst_count"
  fi
}

# 批量迁移缓存目录
migrate '~/.cache/hermes-chrome' '/mnt/backup/home-sync/cache/hermes-chrome' 'hermes-chrome'
migrate '~/.npm' '/mnt/backup/home-sync/cache/npm' 'npm'
# ... 继续添加其他目录
```

### 验证全部软链接

```bash
for d in ~/.cache/hermes-chrome ~/.npm ~/Downloads ~/Pictures ~/Documents; do
  if [ -L "$d" ]; then
    echo "✅ $d -> $(readlink "$d")"
  elif [ -d "$d" ]; then
    echo "❌ $d (未迁移)"
  fi
done
```

### 注意事项

- **显示进度** — 大数据量（10G+）迁移时，rsync 加 `--progress` 参数
- **exFAT 读取慢** — 从 exFAT 盘读取时告知用户预计耗时
- **分批操作** — 一次展示所有选项，让用户决定哪些要迁移
- **应用运行时不可迁移** — 确保目标应用未运行
- **symlink 对大部分应用透明** — 但 snap 包可能不跟随 symlink
- **rsync 中断可续传** — 中断后重新运行相同命令即可

---

## 报告模板

优化完成后用以下格式呈现：

```
## 优化报告

### 总变化
| 指标 | 优化前 | 优化后 | 变化 |
|------|--------|--------|------|
| 系统盘 | 83G/227G (39%) | 48G/227G (23%) | 🔽 释放 35G |
| BACKUP 盘 | 32G/880G (4%) | 64G/880G (8%) | 承接缓存+数据 |

### 清理项
| 项目 | 大小 | 操作 |
|------|------|------|
| Snap 旧版本 | ~500M | ✅ 删除 |
| journalctl 日志 | 958M→141M | ✅ 压缩 |

### 迁移项
| 目录 | 大小 | 目标 |
|------|------|------|
| ~/.cache/hermes-chrome | 4.4G | /mnt/backup/home-sync/cache/ |
| ~/.npm | 2.1G | /mnt/backup/home-sync/cache/ |
```

---

## 参考

- `references/disk-management.md` — 磁盘空间分析基础命令
- `references/exfat-to-ext4-conversion.md` — exFAT→ext4 格式转换
- `docker-storage-ops` skill — Docker 数据根目录迁移到 BACKUP 盘
