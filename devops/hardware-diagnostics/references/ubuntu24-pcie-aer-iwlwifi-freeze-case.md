# 案例：Ubuntu 24 死机故障排查（Intel AC3165 / PCIe AER 错误风暴）

**设备**：rhino01 — Intel i7-8550U / UHD620 平台
**WiFi**：Intel Wireless-AC 3165 [8086:3165]（驱动 iwlwifi）
**Kernel**：6.17.0-35-generic
**系统**：Ubuntu 24.x

---

## 症状

- Ubuntu 24 桌面随机卡死
- 鼠标无响应
- 键盘无响应
- SSH 无法连接
- Ping 无响应
- 只能强制重启

## 根因分析（PCIe 拓扑）

```
00:1c.0 Intel Sunrise Point-LP Root Port #5
    └── 01:00.0 Intel Wireless-AC 3165
```

PCIe 链路不稳定 → RxErr（物理层可纠正）→ BadDLLP（数据链路层可纠正）→ 每秒 1~10+ 次 AER 事件 → IRQ 中断风暴 → CPU 陷入内核处理 → 用户态进程无法调度 → 整机假死

## 日志特征

```bash
sudo dmesg -T | grep -Ei "AER|RxErr|BadDLLP"
```

输出：
```
pcieport 0000:00:1c.0: AER: Correctable error message received
[0] RxErr
[7] BadDLLP
AER: Multiple Correctable error message received
```

错误计数：一次启动可达 **65K+** 条（`journalctl -k -b | grep -c "pcieport.*AER"`）

## 确认设备

```bash
lspci -nn | grep -i wireless
# → 01:00.0 Network controller: Intel Corporation Wireless 3165 [8086:3165]
lspci -vv -s 01:00.0 | grep "Kernel driver"
# → Kernel driver in use: iwlwifi
```

## 修复方案

编辑 `/etc/default/grub`，修改 `GRUB_CMDLINE_LINUX_DEFAULT`：

```
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash pcie_aspm=off pci=noaer"
```

```bash
sudo update-grub
sudo reboot
```

### 参数说明

| 参数 | 作用 | 类型 |
|------|------|------|
| `pcie_aspm=off` | 关闭 PCIe ASPM 省电机制，降低链路错误概率，修复 AC3165 兼容性 | 根因修复 |
| `pci=noaer` | 关闭 AER 错误上报，停止中断风暴 | 止血方案 |

## 验证方法

### 验证 GRUB 生效
```bash
cat /proc/cmdline
# 应包含: pcie_aspm=off pci=noaer
```

### 验证 WiFi 正常
```bash
nmcli device
# → wlp1s0 wifi 已连接 MIFI_5B81
```

### 验证 AER 消失
```bash
sudo journalctl -k -b | grep -Ei "AER|RxErr|BadDLLP"
# → 无输出
```

### 验证驱动正常
```bash
sudo dmesg -T | grep -Ei "iwlwifi|firmware"
# 应包含: Detected Intel(R) Dual Band Wireless-AC 3165
# 应包含: loaded firmware version
# 不应出现: Microcode SW error / Firmware crash / Failed to wake NIC
```

### 监控脚本（出问题时采集）

```bash
#!/bin/bash
# /usr/local/bin/check_iwlwifi.sh
echo "==== $(date) ===="
uptime
free -h | head -2
grep iwl /proc/interrupts
echo
```

观察 `/proc/interrupts` 中 `iwlwifi` 的中断增长速度：
- **正常**：缓慢增长
- **异常**：每秒数万增长（AER 风暴正在发生）

## 结果

| 项目 | 修复前 | 修复后 |
|------|--------|--------|
| AER 错误数 | 65K+/boot | 0 |
| WiFi 连接 | 正常（但引发风暴） | 正常（无风暴） |
| 系统负载 | 正常但偶发冻结 | 正常 |
| SSH 稳定性 | 随机失联 | 稳定 |

## 长期观察标准

连续运行 72 小时，确认：
- 无死机
- 无 SSH 失联
- 无鼠标键盘冻结

→ 则判定修复成功。

## 经验总结

**Intel Wireless-AC 3165 + Ubuntu 24 + Kernel 6.x** 属于已知兼容性问题组合。推荐固定参数 `pcie_aspm=off pci=noaer` 作为长期运行 Hermes Agent / Docker / SSH 服务器的稳定配置。
