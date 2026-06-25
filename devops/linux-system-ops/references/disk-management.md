# 磁盘管理 — 空间分析、清理、Snap 维护

## 系统盘空间分析方法论

当需要分析系统盘空间占用时，采用分层排查法：

### 第一层：根目录一级

```bash
du -sh /* 2>/dev/null | sort -rh | head -20
```

重点关注：`/home`、`/snap`、`/var`、`/usr`、`/opt`。

### 第二层：大目录分解

```bash
# 用户主目录
du -sh ~/*/ 2>/dev/null | sort -rh | head -20
du -sh ~/.* 2>/dev/null | sort -rh | head -10   # 隐藏目录

# ~/.cache 子目录
du -sh ~/.cache/*/ 2>/dev/null | sort -rh

# /opt 手动安装软件
du -sh /opt/*/ 2>/dev/null | sort -rh

# /var 日志和缓存
sudo du -sh /var/log/ /var/cache/apt/ 2>/dev/null
```

### 第三层：最大文件扫描

```bash
sudo find / -xdev -type f -size +100M -exec ls -lh {} \; 2>/dev/null | sort -k5 -rh | head -20
```

### 分类决策矩阵

找到空间占用后，按以下三类决策：

| 类别 | 判断标准 | 处理方式 |
|------|---------|---------|
| **安全可清理** | apt 缓存、旧日志、pip/npm/go 构建缓存、Snap 旧版本 | 直接清理 |
| **可迁移到外置盘** | 浏览器缓存、模型缓存、npm 包、大型用户数据目录 | 移 + symlink |
| **系统不可迁移** | Snap 安装包、/usr、apt 安装软件、~/.config | 留在系统盘 |

---

## Snap 旧版本清理

Snap 包管理器会保留旧版本（禁用状态），占用大量系统盘空间。

### 查看所有版本

```bash
snap list --all
```

输出中标记为「已禁用」的是旧版本，可以安全删除。

### 单条删除

```bash
sudo snap remove <package_name> --revision=<revision_number>
```

示例：
```bash
sudo snap remove chromium --revision=3444
```

### 批量删除所有已禁用版本

```bash
snap list --all | grep "已禁用" | while read name ver rev rest; do
  echo "删除: $name (修订 $rev)"
  sudo snap remove "$name" --revision="$rev"
done
```

### 可释放空间参考

常见已禁用旧版合计约 500MB-1GB（取决于安装的应用数量）。

---

## 系统日志维护 (journalctl)

`journalctl` 是 systemd 的日志系统，默认无上限，可能占用数 GB。

### 查看当前占用

```bash
journalctl --disk-usage
```

### 限制日志大小

```bash
# 限制到 200MB
sudo journalctl --vacuum-size=200M

# 或保留最近 7 天
sudo journalctl --vacuum-time=7d
```

### 持久化限制配置（可选）

```bash
sudo sed -i 's/^#SystemMaxUse=/SystemMaxUse=200M/' /etc/systemd/journald.conf
sudo systemctl restart systemd-journald
```

### 其他可清理日志

```bash
# apt 下载缓存
sudo apt clean

# 旧的日志轮转文件
sudo find /var/log/ -name "*.log" -type f -mtime +30 -delete 2>/dev/null
```

---

## 其他缓存清理

### Python pip 缓存

```bash
# 查看大小
du -sh ~/.cache/pip/
# 清理
rm -rf ~/.cache/pip/
```

### Go 构建缓存

```bash
# 查看大小
du -sh ~/.cache/go-build/
# 清理
rm -rf ~/.cache/go-build/
```

### npm/pnpm 缓存

```bash
# npm
npm cache clean --force
# pnpm
pnpm store prune
```

---

## 目录迁移到外部磁盘（symlink 模式）

对于可迁移的大目录，流程如下：

```bash
# 1. 在目标盘创建同名目录
mkdir -p /mnt/backup/<dir_name>

# 2. 复制数据
rsync -avh ~/<dir_name>/ /mnt/backup/<dir_name>/

# 3. 验证
diff <(find ~/<dir_name>/ -type f | sort) <(find /mnt/backup/<dir_name>/ -type f | sort) && echo "OK"

# 4. 重命名原目录
mv ~/<dir_name> ~/<dir_name>.bak

# 5. 创建软链接
ln -s /mnt/backup/<dir_name> ~/<dir_name>

# 6. 验证
ls -la ~/<dir_name>   # 应指向 /mnt/backup/<dir_name>

# 7. 确认无误后删除备份
rm -rf ~/<dir_name>.bak
```

### 校验完整性

`diff` 对比会因路径前缀不同（如 `/tmp/backup/` vs `/mnt/backup/`）每行都报差异，所以用文件数 + rsync dry run 验证：

```bash
# 文件数对比
echo "源: $(find ~/<dir_name>/ -type f | wc -l)"
echo "目标: $(find /mnt/backup/<dir_name>/ -type f | wc -l)"

# rsync 增量检查（--dry-run 模式，无输出 = 无遗漏）
rsync -avhn --delete ~/<dir_name>/ /mnt/backup/<dir_name>/
```

> **注意：** `du -sh` 在 exFAT 和 ext4 上显示不同。exFAT 的 256K 分配单元会导致\"数据量\"虚高。文件数 + rsync 校验才是可靠的。

### 批量迁移多个大目录

当需要迁移 ~/.cache/、~/.npm/、~/Downloads/ 等多个大目录时，逐个重复上述流程。推荐以下顺序（按占用从大到小）：

```
1. ~/.cache/hermes-chrome/    # 浏览器 CDP 缓存
2. ~/.npm/                    # npm 包缓存
3. ~/.cache/camoufox/         # 浏览器缓存
4. ~/.cache/huggingface/      # 模型缓存
5. ~/Downloads/               # 下载文件
6. ~/.cache/下的其他缓存
```

### 注意事项

- **应用运行时不要迁移** — 确保目标应用/进程未运行
- **不要迁移系统配置目录** — `~/.config/`、`~/.local/` 等应留在系统盘
- **symlink 对大部分应用透明** — 但某些应用（如 snap 包）可能不跟随 symlink
- **重启后需验证** — 系统重启后确认 symlink 有效
- **显示进度** — 大数据量（10G+）迁移时，rsync 加 `--progress` 参数或定期报告进度，让用户知道操作仍在进行中
- **exFAT 读取慢** — 从 exFAT 盘读取时速度慢（尤其在大量小文件场景下），提前告知用户预计耗时
