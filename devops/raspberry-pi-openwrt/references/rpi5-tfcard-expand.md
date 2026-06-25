# Raspberry Pi 5 OpenWrt TF卡全盘扩容（从工作站操作）

> 原 skill `openwrt-rpi5-tfcard-expand` 的内容，已合并入 `raspberry-pi-openwrt` 主 skill。
> 保留此文件作为离线扩容操作的详细参考。

## 适用场景
- Raspberry Pi 5
- OpenWrt Factory IMG
- Ubuntu 24 工作站
- TF卡容量大于镜像容量（16GB/32GB/64GB/128GB）
- 典型现象：`lsblk` 看到 sdb2 只有 104MB，但 TF 卡实际有 16-128GB

## 原因分析
OpenWrt Factory IMG 只创建最小 RootFS（boot ≈64MB, rootfs ≈104MB），刷入大容量 TF 卡后大部分空间未使用。

## 扩容步骤

### Step 1 查看当前状态
```bash
lsblk
sudo parted /dev/sdb print
```

### Step 2 扩展 RootFS 分区
```bash
sudo parted /dev/sdb
(parted) print
(parted) resizepart 2 100%
(parted) Yes
(parted) quit
```

### Step 3 验证分区扩容
```bash
sudo fdisk -l /dev/sdb
# 或
sudo blockdev --getsize64 /dev/sdb2
```

### Step 4 卸载分区（如已自动挂载）
```bash
sudo umount /dev/sdb1
sudo umount /dev/sdb2
mount | grep sdb   # 确认无输出
```

### Step 5 检查文件系统
```bash
sudo e2fsck -f /dev/sdb2
# 如有 Inode 位图修复提示，输入"是"
```

### Step 6 扩展 EXT4 文件系统（关键步骤）
```bash
sudo resize2fs -f /dev/sdb2
```

### Step 7 验证扩容成功
```bash
sudo tune2fs -l /dev/sdb2 | grep "Block count"
sudo mount /dev/sdb2 /mnt
df -h /mnt
```

### 树莓派启动验证
```bash
df -h
# /dev/root 应显示 30G
block info
# /dev/mmcblk0p2 TYPE="ext4" SIZE="30G"
```

## 常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| df -h 显示 99M | 仅扩展分区未执行 resize2fs | `sudo resize2fs -f /dev/sdb2` |
| Block count: 26624 | 文件系统仍为 104MB | `sudo resize2fs -f /dev/sdb2` |
| resize2fs: Device or resource busy | 分区已挂载 | 先 `sudo umount /dev/sdb2` |
