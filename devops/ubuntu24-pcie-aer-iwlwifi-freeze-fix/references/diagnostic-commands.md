# Diagnostic Commands & Expected Outputs

Proven commands from the rhino01 case. Use these when confronted with a suspected PCIe AER freeze.

## Quick Health Check (no sudo needed)

```bash
# Check kernel parameters active
cat /proc/cmdline
# Expected: contains pcie_aspm=off pci=noaer

# Check WiFi connection
nmcli device
# Expected: wlp1s0 wifi 已连接

# Check NVMe disk errors
cat /sys/fs/ext4/dm-*/errors_count
# Expected: 0

# Check PCIe errors in current boot
dmesg -T | grep -c -i "pcieport 0000:00:1c.0"
# Expected: 0 (after fix)

# Check iwlwifi interrupt growth rate
grep -i iwl /proc/interrupts
# Expected: slow growth, not tens of thousands/second

# System resources
free -h
uptime
```

## Full Diagnostics (needs sudo)

```bash
# Previous boot AER errors
sudo journalctl -k -b -1 | grep -Ei "AER|RxErr|BadDLLP"

# iwlwifi firmware status
sudo dmesg -T | grep -Ei "iwlwifi|firmware"

# SATA/NVMe errors
sudo journalctl -k -b | grep -Ei "ata|scsi|nvme|i/o error|buffer I/O"

# Filesystem check info
sudo dumpe2fs -h /dev/mapper/ubuntu--vg-ubuntu--lv | grep -iE "mount count|filesystem state|errors behavior"

# NVMe SMART
sudo nvme smart-log /dev/nvme0n1
```

## Reference Data (rhino01, 2026-06-11)

| Parameter | Value |
|-----------|-------|
| CPU | Intel UHD620 platform |
| WiFi | Intel AC3165 (8086:3165) |
| Kernel | 6.17.0-35-generic |
| System disk | Samsung SSD 960 EVO 250GB |
| Backup disk | SAMSUNG MZ7L3960HCJR 894.3GB (exfat) |
| GRUB fix | `pcie_aspm=off pci=noaer` |
| Pre-fix errors | ~200+ AER correctable errors per boot |
| Post-fix errors | 0 |
| Ext4 errors | 0 (after multiple forced shutdowns) |
