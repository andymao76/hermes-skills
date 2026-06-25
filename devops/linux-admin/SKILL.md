---
name: linux-admin
description: Linux system administration — backup, disk management, desktop app installation, and filesystem maintenance on Ubuntu/Debian systems.
category: devops
tags: [linux, ubuntu, backup, disk, mount, fstab, desktop, apt, systemd]
---

# Linux System Administration

Umbrella skill covering common Linux administration tasks: backup strategies, disk discovery and mounting, and desktop application installation on Ubuntu 24.04.

## When to Use

- Backing up directories to external drives
- Discovering, mounting, or configuring persistent mounts for disks
- Installing Linux desktop applications (deb, AppImage)
- Configuring input methods and locale on Ubuntu desktop
- Checking disk usage and cleaning up system storage

---

## Section 1: Backup (rsync-based)

Rsync-based backup workflows for local disks, removable drives, and scheduled automation.

### Rsync to exfat/NTFS

exfat and NTFS filesystems do NOT support Linux symlinks or certain file attributes. Expect these rsync warnings — they are harmless:

```
rsync: symlink "...CLAUDE.md" -> "AGENTS.md" failed: Operation not permitted (1)
rsync error: some files/attrs were not transferred (code 23)
```

Recommended rsync flags for backup to exfat:

```bash
rsync -av --delete SOURCE/ DEST/
```

Add exclusions for large generated directories:

```bash
rsync -av --delete \
  --exclude='.git/objects/' \
  --exclude='node_modules/' \
  --exclude='__pycache__/' \
  /home/user/code/ /mnt/backup/code/
```

### Cron Job Setup

Create a self-contained rsync script and schedule:

```bash
#!/bin/bash
SOURCE=/home/user/code/
DEST=/mnt/backup/code/
LOG=/home/user/code/rsync-backup.log
rsync -av --delete --exclude='.git/objects/' "$SOURCE" "$DEST" > "$LOG" 2>&1
echo "[$(date)] rsync exit code: $?" >> "$LOG"
```

Common cron schedules: `0 3 * * *` (daily 3AM), `0 */12 * * *` (every 12h), `0 4 * * 0` (weekly Sun 4AM).

### Verification

```bash
echo "Source: $(find /home/user/code/ -type f | wc -l)"
echo "Dest:   $(find /mnt/backup/code/ -type f | wc -l)"
```

File counts may differ slightly due to symlinks not being readable on exfat. Actual code files will match.

### Pitfalls

- **Proxy required for GitHub in China**: Set `HTTPS_PROXY=http://127.0.0.1:7897` before git clone operations
- **exfat doesn't support symlinks**: Expected behavior — ignore rsync code 23
- **Old cron processes**: Kill stale ones before retrying with proxy

See `references/batch-clone-backup-reference.md` for batch clone backup patterns.

---

## Section 2: Desktop Application Installation

Ubuntu 24.04 desktop app installation and system configuration. Covers .deb, .AppImage, input method setup, and GNOME shortcuts.

### General Install Flow

1. Find download source (APT repos first, then official site)
2. Determine architecture: `dpkg --print-architecture`
3. Download: `curl -L -o <file> <url>`
4. Install deps: `dpkg-deb --info <file>` → `sudo apt install -f`
5. Install: `sudo dpkg -i <file>` → `sudo apt install -f`
6. Verify: `which <binary>` → test launch

### WeChat Linux (official 4.1.1.4+)

```bash
curl -L -o wechat.deb "https://dldir1v6.qq.com/weixin/Universal/Linux/WeChatLinux_x86_64.deb"
sudo apt-get install -y fonts-noto-cjk
sudo dpkg -i wechat.deb
```

Binary path: `/opt/wechat/wechat`

| Problem | Cause | Fix |
|---------|-------|-----|
| □□□ blocks | Missing CJK font | `sudo apt install fonts-noto-cjk` |
| FUSE error | AppImage needs FUSE | `sudo apt install libfuse2` or use deb |
| Download URL hidden | JS-rendered page | grep for `.deb` in page source |

### Input Method Configuration

Ubuntu 24.04 defaults to IBus. Quick setup (English default + Ctrl+Shift toggle):

```bash
gsettings set org.gnome.desktop.input-sources sources "[('xkb', 'us'), ('ibus', 'libpinyin')]"
gsettings set org.gnome.desktop.input-sources mru-sources "[('xkb', 'us')]"
gsettings set org.gnome.desktop.wm.keybindings switch-input-source "['<Control>Shift_L']"
ibus restart
```

See `references/ubuntu-input-method-config.md` for detailed IBus configuration.

---

## Section 3: Disk Management

Full lifecycle: discovery → mount → fstab persistence → verification.

### Discover Disks

```bash
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE,LABEL,MODEL
sudo blkid /dev/sdXN
```

### Mount

```bash
sudo mkdir -p /mount/point
sudo mount -t <fstype> /dev/sdXN /mount/point
```

### Persistent Mount (fstab)

**Always use UUID**, never device name:

```
UUID=<uuid> /mount/point <fstype> defaults 0 0
```

**exfat — requires uid/gid:**

```
UUID=<uuid> /mount/point exfat defaults,uid=1000,gid=1000,dmask=022,fmask=133 0 0
```

| Option | Meaning |
|--------|---------|
| uid=1000 | Owner user ID |
| gid=1000 | Owner group ID |
| dmask=022 | Dir perms → 755 |
| fmask=133 | File perms → 644 |

Test and apply:

```bash
sudo findmnt --verify
sudo mount -a
sudo systemctl daemon-reload
```

### System Cleanup

```bash
pip cache purge                              # 1-4 GB
sudo journalctl --vacuum-size=100M            # keep 100MB
sudo apt-get clean                            # 200-500MB
sudo rm -f /var/log/syslog.* /var/log/kern.log.*
find /tmp -type f -atime +7 -delete 2>/dev/null
```

### Finding Large Files

```bash
# Top-level dirs
du -sh /* 2>/dev/null | sort -rh | head -15

# Large files on root partition only (don't cross mount points)
find / -xdev -type f -printf '%s\t%p\n' 2>/dev/null | sort -rn | head -30 | awk -F'\t' '{printf "%8.1fM  %s\n", $1/1048576, $2}'
```

### Pitfalls

- **exfat write denied**: exfat needs `uid=` and `gid=` mount options. Remount after adding them — fstab alone isn't enough if already mounted.
- **Never use /dev/sdXN in fstab**: Device names change between boots. Always use UUID.
- **systemd stale fstab**: Run `sudo systemctl daemon-reload` after edits.
- **sudo in terminal tool**: Write to `/tmp/` first, ask user to run sudo command.

See `references/cleanup-verification.md` for post-cleanup verification.

---

## Reference Files

| File | Topic |
|------|-------|
| `references/batch-clone-backup-reference.md` | Batch git clone with proxy + backup patterns |
| `references/ubuntu-input-method-config.md` | IBus input method detailed config |
| `references/cleanup-verification.md` | Post-cleanup disk verification |
| `references/hermes-agent-china-deploy.md` | Deploy Hermes Agent to Chinese cloud servers (GitHub blocked → PyPI mirror, SSH ControlMaster, rsync skills) |

## Related Skills

- [[cron-job-ops]] — scheduling backup and maintenance cron jobs
- [[hardware-diagnostics]] — full system health checks including disk SMART
- [[systemd-user-service]] — deploying persistent background services
