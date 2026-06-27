---
name: ubuntu24-pcie-aer-iwlwifi-freeze-fix
description: Ubuntu 24 因 Intel AC3165 WiFi 网卡 PCIe AER 错误风暴导致整机冻结（鼠标/键盘/SSH 均无响应）的排查与修复方案
category: devops
related_skills:
  - systemd-service-restart-storm
  - hardware-diagnostics
trigger: 用户反馈 Ubuntu 系统死机、冻结、鼠标键盘无响应、SSH 无法连接
---

# Ubuntu 24 死机故障排查（Intel AC3165 WiFi / PCIe AER 错误风暴）

## ⚠️ 症状重叠警告

**鼠标/键盘/SSH 全卡死** 这个表象有两个完全不同的根因，且 AER 修复应用后仍可能因另一个根因死机：

| 根因 | 排查入口 | 所属 skill |
|------|---------|-----------|
| WiFi AER 风暴 ← 本 skill | `journalctl -k \| grep AER` | 当前 |
| systemd 服务重启风暴 | `journalctl \| grep "Under memory pressure"` | `systemd-service-restart-storm` |

**先做快速鉴别再往下走：**

```bash
# 查 AER
journalctl -k -b -1 --no-pager | grep -c "pcieport.*AER"
# 若 > 100 → AER 风暴，继续本 skill

# 查服务重启风暴
journalctl -b -1 --no-pager | grep "Under memory pressure, flushing caches"
# 若有多条 → 服务重启风暴，换用 systemd-service-restart-storm skill
```

如果 **两者都无** → 检查 OOM / 文件系统 / 其他内核问题。

---

## 适用场景

**现象：**
- Ubuntu 24 桌面随机卡死
- 鼠标无响应
- 键盘无响应
- SSH 无法连接
- Ping 无响应
- 只能强制重启

**硬件环境：**
- Intel Sunrise Point-LP
- Intel Wireless-AC 3165
- Ubuntu 24.x
- Linux Kernel 6.x

## 典型症状

```bash
sudo dmesg -T | grep -Ei "AER|RxErr|BadDLLP"
```

发现以下错误：
```
pcieport 0000:00:1c.0: AER: Correctable error message received
  [0] RxErr
  [7] BadDLLP
AER: Multiple Correctable error message received
```

错误持续出现，每秒 1~10 次以上。

## 根因分析

```
PCIe 拓扑:
  00:1c.0 Intel Root Port #5
      └── 01:00.0 Intel Wireless-AC 3165

链路错误 RxErr + BadDLLP
  → AER 事件
  → IRQ 中断风暴
  → CPU 陷入内核中断处理
  → 用户态进程无法调度
  → 鼠标失效 → 键盘失效 → SSH 失联
  → 系统假死
```

## 确认设备

```bash
lspci -nn | grep Wireless
# 输出示例: 01:00.0 Network controller: Intel Corporation Wireless 3165 [8086:3165]

lspci -vv -s 01:00.0 | grep "Kernel driver"
# Kernel driver in use: iwlwifi
```

## 修复方案

编辑 GRUB 配置：

```bash
sudo nano /etc/default/grub
```

修改 `GRUB_CMDLINE_LINUX_DEFAULT` 行：

```
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash pcie_aspm=off pci=noaer"
```

更新 GRUB 并重启：

```bash
sudo update-grub
sudo reboot
```

### 参数说明

| 参数 | 作用 | 类型 |
|------|------|------|
| `pcie_aspm=off` | 关闭 PCIe ASPM 省电机制，降低链路错误概率，修复 AC3165 兼容性问题 | 根因修复 |
| `pci=noaer` | 关闭 AER 错误上报，停止日志风暴和中断风暴 | 止血方案 |

## 验证方法

### 验证 GRUB 生效
```bash
cat /proc/cmdline
# 应包含 pcie_aspm=off 和 pci=noaer
```

### 验证 WiFi 正常
```bash
nmcli device
# wlp1s0 wifi 已连接
```

### 验证 AER 消失
```bash
sudo journalctl -k -b | grep -Ei "AER|RxErr|BadDLLP"
# 正常：无输出
```

### 验证驱动正常
```bash
sudo dmesg -T | grep -Ei "iwlwifi|firmware"
# 正常：Detected Intel(R) Dual Band Wireless-AC 3165
# 不应出现：Microcode SW error / Firmware crash / Failed to wake NIC
```

### 验证中断情况
```bash
grep -i iwl /proc/interrupts
# 正常：缓慢增长
# 异常：每秒数万增长
```

## 本次案例数据

| 项目 | 内容 |
|------|------|
| CPU | Intel UHD620 平台 |
| WiFi | Intel AC3165 |
| Kernel | 6.17.0-35-generic |
| 最终参数 | `pcie_aspm=off pci=noaer` |
| 修复后 | AER 错误消失，WiFi 正常，SSH 稳定 |
| 成功率 | 80%~90% |

## 后恢复检查：强制关机后的磁盘健康验证

系统因 AER 风暴假死后被强制断电，可能造成文件系统未正常卸载。重启后必须验证磁盘健康：

```bash
# 1. 检查 ext4 文件系统错误计数（无需 sudo）
cat /sys/fs/ext4/dm-*/errors_count
# 正常: 0

# 2. 检查内核日志中的磁盘 I/O 错误
dmesg -T | grep -Ei "i/o error|buffer I/O|sd.*error|ata.*error|nvme.*error"
# 正常: 无输出

# 3. 检查块设备 I/O 统计（无 error 字段为正常）
cat /sys/block/nvme0n1/stat
cat /sys/block/sda/stat

# 4. 检查文件系统挂载状态
mount | grep -E "ext4|exfat"
# 应显示 rw 读写模式

# 5. 查看上次关机是否正常
journalctl -k -b -1 --no-pager | grep "unmounting filesystem"
# 如果有 clean unmount 则说明上次 shutdown 正常
```

若 `errors_count` 非零或查到 I/O 错误，需要进入恢复模式执行 `sudo fsck -f`。

## 长期观察

连续观察 24h → 48h → 72h，确认以下指标则判定修复成功：
- 无死机
- 无 SSH 失联
- 无鼠标键盘冻结

## 经验总结

Intel Wireless-AC 3165 + Ubuntu 24 + Kernel 6.x 属于已知兼容性组合。推荐固定参数 `pcie_aspm=off pci=noaer` 作为长期运行 Hermes Agent / Docker / SSH 服务器的稳定配置。

## 配套工具

同目录下 `scripts/check_iwlwifi.sh` 提供了中断监控脚本，出问题前后执行即可追踪 iwlwifi 中断增长情况：

```bash
# 直接运行（无需安装）
bash ~/.hermes/skills/devops/ubuntu24-pcie-aer-iwlwifi-freeze-fix/scripts/check_iwlwifi.sh

# 安装到系统（需要 sudo）
sudo cp ~/.hermes/skills/devops/ubuntu24-pcie-aer-iwlwifi-freeze-fix/scripts/check_iwlwifi.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/check_iwlwifi.sh
```

## 同类故障鉴别

死机表象（鼠标/键盘/SSH 全卡）有另一个常见根因 — **systemd 服务重启风暴**，症状完全相同但根因不同：

| 特征 | AER 风暴 | 服务重启风暴 |
|------|---------|------------|
| 触发 | WiFi AC3165 PCIe 错误 | `Restart=always` + 可执行文件丢失 |
| 核心日志 | `dmesg \| grep AER` | `journalctl \| grep "Under memory pressure"` |
| libinput 延迟 | 少见 | 常见（`lagging behind by Nms`） |
| 修复 | `pcie_aspm=off pci=noaer` | 停服务 + `StartLimitBurst=3` |

详见技能: `systemd-service-restart-storm`
