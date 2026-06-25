---
name: hardware-diagnostics
description: Full system health check for Linux — CPU, memory, disk, network, processes, temperature, SMART, zombie processes, services, Docker, swap, kernel errors, and security audit. Covers both hardware diagnostics and general system health reporting. Use when asked for a health check, system report, performance audit, or hardware diagnostic.
category: devops
tags: [hardware, smart, sensors, temperature, disk-health, diagnostics, health-check, system-audit]
related_skills: []
---
# Hardware Diagnostics & System Health Check

Comprehensive hardware health check and full system health audit covering disks, temperatures, kernel errors, filesystem integrity, CPU, memory, network, processes, services, Docker, swap, and security.

## Triggers

- "检查磁盘健康" / "check disk health" / "硬盘有没有故障"
- "传感器温度" / "CPU温度" / "硬件温度" / "sensor readings"
- "是否有坏道" / "SMART状态" / "硬件自检"
- "系统硬件报告" / "hardware report"
- "系统健康检查" / "health check" / "全面检查" / "系统报告"
- "性能检查" / "performance audit"

## Prerequisites

Install required tools if missing:

```bash
sudo apt-get install -y nvme-cli smartmontools lm-sensors exfatprogs
```

## Workflow

### 1. SMART Disk Health

#### NVMe Drives

```bash
sudo nvme smart-log /dev/nvme0n1
```

Key fields to inspect:
| Field | Healthy Range | Critical |
|-------|---------------|----------|
| critical_warning | 0 | Non-zero = failing |
| available_spare | ≥ 10% | Below threshold = replace soon |
| percentage_used | < 90% | Nearing 100% = endurance exhausted |
| media_errors | 0 | Non-zero = bad blocks |
| temperature | < 70°C | > 78°C typical critical threshold |

#### SATA Drives

```bash
sudo smartctl -a /dev/sda
```

Key attributes:
| ID | Name | Meaning | Healthy |
|----|------|---------|---------|
| 5 | Reallocated_Sector_Ct | Remapped bad sectors | 0 |
| 197 | Current_Pending_Sector | Unstable sectors | 0 |
| 198 | Offline_Uncorrectable | Unrecoverable errors | 0 |
| 199 | CRC_Error_Count | Cable/connection errors | 0 |
| 177 | Wear_Leveling_Count | SSD wear (vendor-specific) | Low number |
| 194 | Temperature_Celsius | Drive temperature | < 65°C |

The overall assessment is at the top: `SMART overall-health self-assessment test result: PASSED`.

### 2. Temperature Sensors

```bash
sensors
```

Typical output includes:

| Sensor | Source | Warning |
|--------|--------|---------|
| coretemp (Package/Core 0-3) | CPU | > 90°C = throttling risk |
| nvme-pci (Composite/Sensor 1/2) | NVMe SSD | > 70°C |
| pch_skylake | Chipset | > 75°C |
| iwlwifi | WiFi module | > 75°C |

Also check raw thermal zones (supplements `sensors`):

```bash
for z in /sys/class/thermal/thermal_zone*/; do
  echo -n "$(cat ${z}type): "
  cat ${z}temp | awk '{printf "%.1f°C\n", $1/1000}'
done
```

Check cooling device states:

```bash
for c in /sys/class/thermal/cooling_device*/; do
  echo "$(cat ${c}type): state=$(cat ${c}cur_state)/$(cat ${c}max_state)"
done
```

Key cooling indicators:
- **Processor** state > 0: CPU is being throttled
- **intel_powerclamp** state > 0: forced idle injection (thermal emergency)
- **TCC Offset**: temperature at which throttling begins (e.g., 5 means throttling at Tjmax - 5°C)

### 3. Kernel Error Scan

```bash
sudo dmesg | grep -iE "ata|nvme|scsi|i/o error|bad block|media error|uncorrectable|read.only|buffer i/o"
```

**Fallback when `dmesg` is restricted** (`kernel.dmesg_restrict=1`):
```bash
journalctl -k -p err --no-pager | tail -30
journalctl -k --since "24 hours ago" -p err --no-pager | tail -80
```

Look for:
- `I/O error` or `media error` → disk hardware failure
- `read-only` filesystem remount → filesystem corruption detected
- `Buffer I/O error` → block device issues
- PCIe correctable errors (common, typically WiFi-related, not disk)

**⚠️ PCIe AER Correctable Error STORM** — when error count is very high (thousands per boot), these are NOT harmless. High-volume AER floods cause:
  - Mouse, keyboard unresponsive (GUI frozen)
  - SSH connections dead
  - System appears completely frozen — but actually saturated handling AER interrupts
  - Reboot required to recover

### 3a. PCIe AER Error Storm Diagnosis

When the user reports random freezes where mouse, keyboard, and SSH all stop responding:

**Step 1: Check for AER error flood**

```bash
# Count errors in previous boot (use -b -1 for last boot)
journalctl -k -b -1 --no-pager 2>&1 | grep -c "pcieport.*AER"

# Count in current boot
journalctl -k -b --no-pager 2>&1 | grep -c "pcieport.*AER"
```

If count > 1000 per boot, it's a storm.

**Step 2: Identify the culprit device**

```bash
# Find which PCIe root port is flooding
journalctl -k -b --no-pager 2>&1 | grep "pcieport.*AER" | head -5

# Get full AER details
journalctl -k -b --no-pager 2>&1 | grep -A3 "pcieport.*AER: Correctable error message"

# Trace the PCIe tree to find the downstream device
lspci -t -vv 2>&1 | grep -B1 -A2 "1c\["
```

The root port address (e.g., `0000:00:1c.0`) tells you which bus. Look it up:

```bash
# Check what device is behind the flooding root port
lspci -v -s <bus>:00.0     # e.g., 01:00.0 for WiFi behind root port 00:1c.0
```

**Step 3: Assess severity**

Common AER error types:
| Error Type | Severity | Meaning |
|------------|----------|---------|
| RxErr (Physical Layer) | Correctable | Signal integrity issue on PCIe lane |
| BadDLLP (Data Link Layer) | Correctable | Packet corruption on data link |
| Bad TLP (Transaction Layer) | Uncorrectable | Data corruption — reboot recommended |

**Step 4: Identify the offending device**

Common AER storm culprits:
| Device | Typical Symptoms | Fix |
|--------|-----------------|-----|
| **Intel Wireless 3165/3168 (iwlwifi)** | RxErr + BadDLLP floods, 65K+ errors/boot | Replace with AX200/AX210, or disable WiFi in BIOS |
| **Realtek RTL8111 (r8169)** | Intermittent AER, network drops | Update firmware, disable ASPM |
| **NVMe SSD (Samsung PM961/etc.)** | Rare AER, usually link power state | Disable ASPM: `pcie_aspm=off` |

**Step 5: Apply fix**

| Fix | Method | Effect |
|-----|--------|--------|
| Disable AER reporting | Add `pci=noaer` to `GRUB_CMDLINE_LINUX_DEFAULT` in `/etc/default/grub`, then `sudo update-grub` | Stops AER interrupt flood — safest software fix |
| Disable PCIe ASPM | Add `pcie_aspm=off` to kernel cmdline | Prevents link power state transitions that trigger errors |
| Replace the device | Swap WiFi card (Intel 3165 -> AX210, M.2 slot) | Hardware fix, eliminates root cause |
| BIOS disable | Turn off WiFi in BIOS | If wired Ethernet is available |

### Step 6: Monitor iwlwifi interrupt growth (post-fix)

Create and run this script when suspecting a recurrence:

```bash
check_iwlwifi.sh
```

It captures `uptime`, `free -h`, and `grep iwl /proc/interrupts`. The key indicator is iwlwifi interrupt count growth rate — if it spikes to tens of thousands per second, the AER storm has returned despite the kernel parameters.

See `scripts/check_iwlwifi.sh` and a full reproduction case at `references/ubuntu24-pcie-aer-iwlwifi-freeze-case.md` (Intel AC3165 + Kernel 6.x, documented fix with before/after data).

### Step 7: When AER count is 0 but freezes still happen → service restart storm

After applying the AER fix (`pcie_aspm=off pci=noaer`), confirm AER is truly gone:

```bash
journalctl -k -b -1 --no-pager | grep -c "pcieport.*AER"
```

If count is 0 but the **same symptoms persist** (mouse/keyboard/SSH all dead), the cause is likely a **systemd service restart storm** — not AER.

**Check:**
```bash
# 1. journald memory pressure (primary signal)
journalctl -b -1 --no-pager | grep "Under memory pressure, flushing caches"

# 2. libinput input lag (secondary signal)
journalctl -b -1 --no-pager | grep "lagging behind"

# 3. service restart counters
journalctl -b -1 --no-pager | grep "Scheduled restart job" | head -5
systemctl status <offending-service> --no-pager | grep "restart counter"
```

A restart counter > 1000 with `Restart=always` and a missing executable causes a self-inflicted denial of service:
1. systemd retries every 5-8 seconds → each attempt logs to journald
2. journald floods memory → `"Under memory pressure, flushing caches"`
3. libinput processing lags (1000ms+) → mouse/keyboard freeze
4. system fully thrashing → SSH drops

**Fix:** `systemctl stop <service> && systemctl disable <service>`, then add `StartLimitBurst=3` via override.conf. See **`systemd-service-restart-storm`** skill for full diagnosis and prevention.

### 4. Filesystem Integrity

#### Non-sudo alternative (when sudo password unavailable)

When `sudo` is unavailable, ext4 health can be checked via sysfs:

```bash
# Find the root device mapper name
LV=$(findmnt / -o SOURCE -n | awk -F/ '{print $NF}')
echo "Root LV: $LV"

# Check ext4 error count (0 = clean)
cat /sys/fs/ext4/$LV/errors_count 2>/dev/null || echo "no sysfs ext4 entry"

# Check NVMe block device I/O stats (no error field in standard stat,
# but zero discards + no abnormal I/O pattern = healthy)
cat /sys/block/nvme0n1/stat

# Check last boot's filesystem unmount status
grep "EXT4-fs.*unmounting filesystem" /proc/fs/ext4/$LV/... 2>/dev/null
# Or check dmesg for clean unmount at last reboot:
journalctl -k -b -1 --no-pager 2>/dev/null | grep "EXT4-fs.*unmounting"

# Check if filesystem was cleanly mounted in current boot
grep "EXT4-fs.*mounted filesystem" /proc/fs/ext4/$LV/... 2>/dev/null

# Check dmesg for disk I/O errors (both current and previous boot)
for boot_flag in "" "-b -1"; do
  count=$(journalctl -k $boot_flag --no-pager 2>/dev/null | grep -ciE "buffer I/O error|i/o error|media error|uncorrectable|read.only")
  echo "Boot $boot_flag: $count I/O errors"
done

# Check block device stat format (17 fields):
# read_ios, read_merges, read_sectors, read_ticks,
# write_ios, write_merges, write_sectors, write_ticks,
# in_flight, io_ticks, time_in_queue,
# discard_ios, discard_merges, discard_sectors, discard_ticks,
# flush_ios, flush_ticks
```

#### exfat

```bash
sudo fsck.exfat /dev/sdXN
# Expected: "clean. directories N, files M"
```

#### ext4 (online check — no unmount needed)

```bash
sudo tune2fs -l /dev/mapper/<lv-name> | grep -iE "state|check|error"
# "Filesystem state: clean" = healthy
```

For the root filesystem, find the device mapper name:

```bash
findmnt / -o SOURCE -n
```

Check /boot too:

```bash
sudo tune2fs -l /dev/nvme0n1p2 | grep -iE "state|check|error"
```

### 5. System Context

Always include for context in a diagnostic report:

```bash
lscpu | grep "Model name"          # CPU model
free -h | head -2                  # RAM
df -h /                            # root disk usage
```

## Report Format

Present diagnostics in a structured table format:

```
┌──────────────────────────────────────────────────────┐
│  传感器          │ 当前   │ 阈值       │ 状态  │
├──────────────────┼────────┼────────────┼───────┤
│ CPU Package      │ 78°C   │ 100°C      │ ⚠️ 偏高 │
│ Core 0-3         │ 72-78°C│ 100°C      │ 正常  │
│ NVMe SSD         │ 52°C   │ 78.8°C     │ 正常  │
└──────────────────┴────────┴────────────┴───────┘
```

See `references/example-output-intel-laptop.md` for a complete real-world diagnostic report with annotated output.

## 6. Full System Health Check (Expanded)

When asked for a complete system health check, run all 13+ categories below and compile a structured report.

### 6.1 System Basics

```bash
uname -a                       # Kernel version
cat /etc/os-release            # Distro version
uptime                         # Uptime + load average
hostname
```

### 6.2 CPU

```bash
lscpu | grep -iE "Model|Core|Thread|MHz"
cat /proc/loadavg              # 1min / 5min / 15min loads
top -bn1 | head -5
mpstat -P ALL 1 1              # Per-core utilization (install: sysstat)
```

Chinese locale fallback for `lscpu`:
```bash
lscpu | grep -iE "型号名称|Model name"
cat /proc/cpuinfo | grep "model name" | head -1
```

### 6.3 Memory

```bash
free -h
cat /proc/meminfo | head -10
```

### 6.4 Disk

```bash
df -h
lsblk
findmnt
```

### 6.5 Network

```bash
ip addr show | grep 'inet '
ss -tlnp                        # Listening ports (omit -n to show service names)
ping -c 1 -W 2 8.8.8.8          # Internet connectivity
```

### 6.6 Process Top

```bash
ps aux --sort=-%mem | head -15  # Memory top 15
ps aux --sort=-%cpu | head -15  # CPU top 15
```

Note the PID of any process exceeding 100% CPU (multi-threaded) for deeper investigation.

### 6.7 Zombie / Defunct Processes

```bash
count=$(ps aux | awk '$8=="Z"' | wc -l)
echo "Zombie count: $count"
if [ "$count" -gt 0 ]; then
  ps -eo pid,stat,ppid,comm | awk '$2=="Z" || $2=="Z+"'
fi
```

**Cleaning zombie processes:**

Zombies (state `Z`) are already dead — they cannot be killed directly. They persist because the parent process hasn't called `wait()` to reap them.

| Action | Command | Notes |
|--------|---------|-------|
| Kill the parent | `kill -9 <PPID>` | The PPID is the parent process ID. Killing the parent causes init (PID 1) to inherit and reap the zombies. |
| Kill by process name | `kill -9 <PPID>` then `pkill -f <process-name>` | Use when multiple zombie children share the same parent. |
| Verify cleanup | `ps aux \| awk '$8=="Z"' \| wc -l` | Should return 0 after parent is killed. |

**Important:** If the parent is a critical service (systemd, init, a daemon), do NOT kill it directly — restart the service instead:
```bash
sudo systemctl restart <service-name>
```

### 6.8 System Services

```bash
systemctl list-units --type=service --state=running --no-pager | head -30
systemctl --user list-units --type=service --state=running --no-pager 2>/dev/null | head -20
```

### 6.9 Temperature / Hardware (see Section 2 above)

### 6.10 Docker

```bash
docker info --format '{{.ServerVersion}}' 2>/dev/null
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null
```

### 6.11 Security

```bash
last -10                        # Recent logins
who                              # Current users
journalctl --no-pager -n 5      # Recent system logs (requires sudo for full view)
```

### 6.12 System Errors

```bash
sudo dmesg --level=err,warn -T 2>/dev/null | tail -10
```

### 6.13 Swap

```bash
swapon --show
free -h | grep Swap
```

### 6.14 Report Format

Collect all data above and compile into a structured report with:

| Category | Status | Key Data |
|----------|--------|----------|
| System | ✅/⚠️/❌ | kernel, distro, uptime, load |
| CPU | ✅/⚠️/❌ | utilization %, top consumer |
| Memory | ✅/⚠️/❌ | used %, available |
| Disk | ✅/⚠️/❌ | max partition % |
| Network | ✅/⚠️/❌ | IP, connectivity, listening ports |
| Processes | ✅/⚠️/❌ | top CPU/MEM consumers |
| Zombies | ✅/❌ | count |
| Services | ✅/⚠️/❌ | count, key services |
| Temperature | ✅/⚠️/❌ | CPU temp / threshold |
| Docker | ✅/⚠️/❌ | version, running containers |
| Security | ✅/⚠️/❌ | recent logins, anomalies |
| System Errors | ✅/⚠️/❌ | dmesg errors |
| Swap | ✅/⚠️/❌ | used % |

Include a **Priority Issues** section near the top:
- 🔴 HIGH — zombie processes, critical disk failure, OOM
- 🟡 MEDIUM — high CPU load, elevated temps, PCIe errors
- 🟢 LOW — near-threshold values, single service down

## Automated Scheduling

For setting up a recurring weekly health check with automatic boot catchup (runs on next boot if the scheduled time was missed due to shutdown), see `references/weekly-health-check-cron.md`.

## Pitfalls

### Missing sensors after install

After `apt-get install lm-sensors`, run `sudo sensors-detect --auto` to probe for available sensors. On laptops and some desktops, fan speed and voltage sensors may not be exposed — this is normal and not an error.

### GPU temperature on integrated graphics

Intel integrated GPUs (UHD, Iris) share the CPU die — their temperature is reflected in the CPU package sensor. No separate GPU hwmon sensor will appear in `/sys/class/drm/`. Use the CPU package temp as a proxy.

### dmesg requires sudo

`dmesg` needs root on modern kernels (`kernel.dmesg_restrict=1`). Always use `sudo dmesg`.

### fsck.exfat not found

Install `exfatprogs` (not `exfat-utils`, which is the older package):

```bash
sudo apt-get install -y exfatprogs
```

### nvme not found

NVMe management CLI is in `nvme-cli`:

```bash
sudo apt-get install -y nvme-cli
```

### Chinese locale breaks command-line parsing

On systems with `LANG=zh_CN.UTF-8`, several common commands produce Chinese header text that breaks `grep`/`awk` patterns written for English. Always use dual-pattern matching:

| Command | English pattern | Chinese pattern | Fixed grep |
|---------|----------------|-----------------|------------|
| `lscpu` | `Model name` | `型号名称` | `grep -iE "型号名称\|Model name"` |
| `free -h` | `Mem:` | `内存：` | `awk '/Mem:\|内存/'` |
| `free -h` | `Swap:` | `交换：` | `awk '/Swap:\|交换/'` |
| `df -h` | `Mounted on` | `挂载点` | Not needed (positional) |

**Fallback pattern**: always provide a second extraction method (e.g., `/proc/cpuinfo` for CPU model, `NR==2` for memory) as a safety net.

### systemd mask stops auto-restart

Some user services (e.g., `gnome-remote-desktop`) auto-restart after `systemctl stop`. To permanently stop:

```bash
systemctl --user mask <service>   # Symlinks to /dev/null — prevents ANY start
systemctl --user stop <service>   # Kills current instance
kill -9 <pid>                     # Force-kill if still running
```

A mask is stronger than `disable` — it prevents manual starts too. Use `unmask` to reverse.
