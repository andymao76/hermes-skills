# exFAT 在备份场景的已知限制

> 适用于 /dev/sda2 (894 GB, 卷标 BACKUP, 挂载于 /mnt/backup)

## 不支持的功能

| 功能 | 状态 | 替代方案 |
|------|------|---------|
| 符号链接 (`os.symlink`) | ❌ 不支持 | 纯文本文件记录路径 |
| Unix 权限 (`chmod`) | ❌ 无实际效果 | 无需处理，exFAT 忽略权限 |
| 硬链接 (`os.link`) | ❌ 不支持 | 完整复制文件 |
| 扩展属性 (`xattr`) | ❌ 不支持 | 不使用扩展属性 |

## 已知行为

### 1. `du` 报告不准确

exFAT 使用固定簇大小分配空间。一个只含 1 个小文件的目录可能被 `du` 报告为 82 MB（实际数据仅几 KB）。

```bash
# 不准确的报告
$ du -sh backup_dir/
82M    backup_dir/

# 使用 find 获取真实大小
$ find backup_dir/ -type f -exec stat -c%s {} + | awk '{s+=$1} END {print s}'
1234   # 实际字节数
```

### 2. `shutil.copy2` 元数据

`copy2` 可复制文件内容和部分元数据，但权限位和时间戳可能被 exFAT 忽略。

### 3. 文件名限制

- 大小写不敏感
- 不支持 `:` `<` `>` `|` `"` `?` `*` 等字符
- 路径最长 255 个 UTF-16 字符

### 4. 时间戳精度

exFAT 存储的时间戳精度为 10ms（2 秒分辨率），不如 ext4 的纳秒精度。

## 磁盘检查

```bash
# 查看磁盘信息
lsblk /dev/sda -o NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE,LABEL

# 检查文件系统
sudo fsck.exfat /dev/sda2

# 查看使用情况
df -h /mnt/backup
```
