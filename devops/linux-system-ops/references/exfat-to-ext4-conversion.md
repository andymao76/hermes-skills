# exFAT → ext4 磁盘格式转换

将备份数据盘从 exFAT 转换为 ext4 的完整流程。exFAT 的不支持符号链接、文件锁、Unix 权限，可能导致 Docker 容器（如 Open WebUI）崩溃循环。

## 前置条件

| 条件 | 要求 |
|------|------|
| 数据量 | 确认当前 exfat 盘已用空间 |
| 临时空间 | 系统盘需有足够空间暂存全部数据 |
| 依赖服务 | 需检查并停止所有依赖该盘的服务 |

## 评估命令

```bash
# 盘信息
lsblk -o NAME,FSTYPE,SIZE,MOUNTPOINT,LABEL
df -hT /mnt/backup

# 系统盘剩余空间（需 > 数据量 + 5G）
df -h /

# 检查哪些服务/脚本依赖该挂载点
grep -rls "/mnt/backup" ~/.hermes/scripts/ 2>/dev/null
mount | grep backup

# 检查 fstab
cat /etc/fstab | grep backup
```

## 完整步骤

### 阶段 1：备份数据到系统盘

```bash
# 创建临时目录
mkdir -p /tmp/backup-restore

# rsync 复制（排除回收站等 Windows 垃圾目录）
# 注意：exFAT 读取慢，大文件显示分块传输；输出过大时加 | tail -5
rsync -avh --progress \
  --exclude='.Trash-1000' \
  --exclude='$RECYCLE.BIN' \
  --exclude='System Volume Information' \
  /mnt/backup/ /tmp/backup-restore/
```

**耗时参考：** 从 exFAT 读取 59G 数据约需 10-20 分钟。可通过以下命令查看实时进度：

```bash
du -sh /tmp/backup-restore/        # 已复制数据量
ls -la /tmp/backup-restore/        # 已复制的目录结构
df -h /                            # 根分区剩余空间
```

**rsync 中断恢复：** rsync 是增量同步，中断后可重新运行相同命令，自动跳过已完成的文件。

### 阶段 2：完整性校验

**文件数对比（最可靠校验方法）：**

```bash
# 源盘文件数（排除回收站）
echo "源: $(find /mnt/backup/ -not -path '*/.Trash*' -not -path '*/$RECYCLE*' -not -path '*/System Volume Information*' -type f 2>/dev/null | wc -l)"
# 备份文件数
echo "备份: $(find /tmp/backup-restore/ -type f 2>/dev/null | wc -l)"
```

**exFAT vs ext4 空间差异说明：**
- exFAT 使用 256K 分配单元 → du 报告分配空间（如 60G）
- ext4 使用 4K 分配单元 → du 报告实际数据大小（如 32G）
- 差异是正常的，**不是漏数据**，文件数一致即可证明完整性

**最终校验（rsync 增量模式确认无遗漏）：**

```bash
rsync -avhn --delete \
  --exclude='.Trash-1000' \
  --exclude='$RECYCLE.BIN' \
  --exclude='System Volume Information' \
  /mnt/backup/ /tmp/backup-restore/
# 输出为空 = 无遗漏。末尾 to-chk=0/xxxxx 确认全检查完毕
```

### 阶段 3：卸载并格式化

```bash
# 卸载
sudo umount /mnt/backup

# 格式化为 ext4（标签保持 BACKUP）
sudo mkfs.ext4 -L BACKUP /dev/sda2
```

耗时：< 1 分钟。

### 阶段 4：挂载并恢复

```bash
# 挂载
sudo mount /dev/sda2 /mnt/backup

# 恢复数据
sudo rsync -avh /tmp/backup-restore/ /mnt/backup/

# 修复权限
sudo chown -R $(whoami):$(whoami) /mnt/backup/
```

### 阶段 5：更新 fstab

```bash
# 查看新 UUID
sudo blkid /dev/sda2

# 编辑 /etc/fstab，将 exfat 行改为：
# UUID=新UUID /mnt/backup ext4 defaults 0 2

# 验证挂载配置
sudo findmnt --verify

# 重新挂载
sudo mount -a
```

### 阶段 6：清理临时数据

```bash
# 确认恢复完成后删除临时目录
rm -rf /tmp/backup-restore
```

## 注意事项

### 必须暂停/调整的服务

- **Open WebUI Docker 容器：** 如果其数据目录在备份盘上，先 `docker stop open-webui && docker rm open-webui`
- **Docker 崩溃循环修复：** 如果 Open WebUI 容器启动时报 `ValueError: No embedding model is loaded`，这是嵌入模型在 exFAT 缓存中下载失败。重启时添加 `RAG_EMBEDDING_ENGINE=openai` 和 `OPENAI_API_BASE_URL` 指向本地 API 桥解决
- **备份脚本（daily-backup.sh, weekly-full-backup.sh）：** 路径不变，无需修改
- **Hermes 相关脚本：** 路径引用不变，正常工作

### 已知陷阱

- **`lsof +D /mnt/backup` 在 exFAT 上会超时：** exFAT 元数据操作极慢，不要用 lsof 检查占用，用 `fuser` 或直接卸载
- **`sudo umount /mnt/backup` 可能被占用：** 用 `sudo umount -l /mnt/backup`（lazy 卸载）强制分离
- **数据盘大小在 exFAT 上看起来更大：** 这是 256K 簇分配开销，不是数据膨胀

### fstab 修改要点

| 字段 | exFAT | ext4 |
|------|-------|------|
| 文件系统类型 | `exfat` | `ext4` |
| 挂载选项 | `defaults,uid=1000,gid=1000,dmask=022,fmask=133` | `defaults` |
| dump | 0 | 0 |
| pass | 0 | **2**（需要 fsck 检查） |

### 耗时预估（以 59G 数据为例）

| 阶段 | 耗时 | 注意事项 |
|------|------|---------|
| ① 数据备份 | 10～20 min | rsync 中断可续传，用 `du -sh` 看进度 |
| ② 校验 | 1～2 min | 文件数对比最可靠，exFAT 空间差异正常 |
| ③ 格式化 | < 1 min | |
| ④ 数据恢复 | 5～10 min | |
| ⑤ fstab + 清理 | < 1 min | |
| **总计** | **20～35 min** | |

### 转换后的好处

- ✅ 支持符号链接（HuggingFace 模型缓存正常）
- ✅ 支持 Unix 权限（容器运行更稳定）
- ✅ 支持 POSIX 文件锁（SQLite 正常）
- ✅ 元数据操作快（ls/find/du 不再卡顿）
- ✅ 日志文件系统（意外断电后自动恢复）
