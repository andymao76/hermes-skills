---
name: 'raspberry-pi-openwrt'
description: '树莓派安装/配置 OpenWRT 完整生命周期 — 固件选择、刷机、首次启动、WiFi 国家码、网络配置（旁路由/主路由）、TF 卡扩容、安全加固、常见踩坑'
author: 'Hermes Agent'
tags: [openwrt, raspberry-pi, router, networking, pi4, pi5, ImmortalWrt]
---

# Raspberry Pi OpenWRT Setup

> 全生命周期指南：从零开始将树莓派变为 OpenWRT 路由器 / 旁路由。
> 涵盖 Pi 3/4/5，支持官方 OpenWRT 与 ImmortalWrt 固件。

---

## 触发条件

用户提到「树莓派装 OpenWRT」「Pi 刷 OpenWRT」「旁路由」「ImmortalWrt」「Pi 扩容」「OpenWRT TF 卡」等关键词时加载此 skill。

---

## 1. 型号与固件选择

OpenWRT 使用 `bcm27xx` 目标架构：

| 型号 | Subtarget | 说明 |
|------|-----------|------|
| Pi 1 / Pi Zero | bcm2708 | ARMv6，性能有限 |
| Pi 2 | bcm2709 | ARMv7 |
| Pi 3/3B+ | bcm2710 | 内置 WiFi，需设国家码 |
| Pi 4 | bcm2711 | 推荐，USB 3.0 |
| Pi 5 | bcm2711 | 最强，内置 RTC/电源键 |

**64-bit 固件**是主流选择。Pi 4/5 性能足够跑 OpenWRT + 插件（OpenClash / AdGuard / Tailscale）。

## 2. 固件下载

### 官方 OpenWRT
- 固件选择器: https://firmware-selector.openwrt.org/
- Target: `bcm27xx/bcm2711` → 选具体 Subtarget
- 首次安装: **FACTORY (EXT4)** 版本
- 升级: **SYSUPGRADE** 版本（保留配置）

### ImmortalWrt（国内用户推荐）
- 固件选择器: https://firmware-selector.immortalwrt.org/
- 对中国用户有本地化优化，默认集成更多软件包

**EXT4 vs SQUASHFS:**
- EXT4 → 可读写，灵活方便修改系统文件
- SQUASHFS → 只读压缩文件系统 + 可写分区，系统损坏可恢复出厂

## 3. 刷入 TF 卡

### Linux
```bash
gzip -d *-ext4-factory.img.gz
sudo dd if=*-ext4-factory.img of=/dev/sdX bs=4M conv=fsync
sync
```

### Windows
使用 **Rufus** (https://rufus.ie/) 直接刷 .img.gz 文件，保持默认设置。

### Raspberry Pi Imager
支持自定义镜像烧录，操作最直观。

## 4. 首次启动与初始化

1. 插卡通电
2. **用网线**连接树莓派与电脑（默认不创建 WiFi 热点）
3. 浏览器访问 `http://192.168.1.1`
4. 默认 root/空密码 → 登录后修改密码

## 5. ⚠️ WiFi 国家码（必需步骤）

Pi 3B+/4/5 的 **Broadcom 无线芯片必须设置国家码**才能启用 WiFi。LuCI 里设无效。

**方法一（推荐）:** 先刷 Raspberry Pi OS 启动一次设好国家码，再换 OpenWRT。

**方法二（SSH 直设）:**
```bash
uci set wireless.radio0.country='CN'
uci commit wireless && wifi reload
```

如果不设置，WiFi 设备可能完全不启动（dmesg 无无线相关输出）。

## 6. 网络配置

登录 LuCI → **网络 → 接口**，编辑 LAN 接口。

### 旁路由模式（旁路网关）
```
协议: 静态地址
IPv4 地址: 192.168.1.2（不与主路由冲突的 IP）
IPv4 网关: 192.168.1.1（主路由 IP）
DNS: 192.168.1.1 或 114.114.114.114
DHCP 服务器 → 勾选"忽略此接口"（避免 DHCP 冲突）
```

### 主路由模式
```
协议: 静态地址
IPv4 地址: 192.168.1.1
IPv4 网关: 留空
```

配置后用网线将树莓派连接到主路由 LAN 口。

## 7. TF 卡扩容

OpenWRT factory 镜像只建约 104MB RootFS，刷入大容量 TF 卡后绝大部分空间浪费。

### 方法 A：在树莓派上在线扩容
```bash
opkg update
opkg install fdisk resize2fs losetup

fdisk /dev/mmcblk0
  p          # 打印分区表，记下第二分区起始扇区
  d          # 删除第二分区
  n          # 重建（起始扇区与原值相同，结束扇区回车用默认）
  w          # 写入

losetup /dev/loop0 /dev/mmcblk0p2
resize2fs -f /dev/loop0
reboot
```

### 方法 B：在工作站上离线扩容（不用在 OpenWRT 上装工具）
```bash
sudo parted /dev/sdb
  print
  resizepart 2 100%
  Yes
  quit

sudo e2fsck -f /dev/sdb2
sudo resize2fs -f /dev/sdb2
```

扩容后 `df -h` 应显示 TF 卡的真实容量。

参考 references/rpi5-tfcard-expand.md 获得更详细的离线扩容步骤和错误排查。

## 8. 验证

```bash
df -h               # /dev/root 应为 TF 卡实际大小
block info          # /dev/mmcblk0p2 SIZE 应对
```

## 9. 后续推荐

- **安全加固**: 加载 `openwrt-hardening-checklist` skill
  - SSH 改端口 + 密钥登录
  - LuCI 启用 HTTPS
  - 防火墙最小化
  - DNS over TLS（Stubby）
- **插件安装**: OpenClash / PassWall / SSR-Plus / AdGuard Home / Tailscale / ZeroTier / Samba
- **定期备份**: `sysupgrade -b /tmp/backup-$(date +%Y%m%d).tar.gz`

## 10. 常见踩坑速查

| 问题 | 原因 | 解决 |
|------|------|------|
| 无法访问 192.168.1.1 | 电脑 IP 不在同一网段 | 手动设电脑 IP 为 192.168.1.x/24 |
| WiFi 设备不启动 | 未设国家码 | `uci set wireless.radio0.country='CN'` |
| `df -h` 显示 99M | 只扩了分区没跑 resize2fs | 执行 `resize2fs -f` |
| 装包报空间不足 | 未扩容 | 先执行第 7 节 |
| Pi 4 USB 慢 | 插错了 USB 口 | Pi 4 的蓝色口才是 USB 3.0 |
| resize2fs: Device busy | 分区已挂载 | 先 `umount` 再 resize |

## 11. 参考资源

- [OpenWRT Wiki - Raspberry Pi](https://openwrt.org/toh/raspberry_pi_foundation/raspberry_pi)
- [ImmortalWrt 固件选择器](https://firmware-selector.immortalwrt.org/)
- Wulu's Blog - 树莓派安装 OpenWrt 及扩容教程
