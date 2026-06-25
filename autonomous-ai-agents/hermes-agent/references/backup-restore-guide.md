# 增量备份核心逻辑模板

> 从此模板派生备份脚本时，注意 `find_latest_backup()` 必须在 `mkdir` 之前调用。

```python
#!/usr/bin/env python3
"""增量备份核心模板"""

import hashlib, shutil, json, logging
from pathlib import Path
from datetime import datetime

BACKUP_ROOT = Path("/mnt/backup/target-backup")
SOURCE_ROOT = Path.home() / ".target-dir"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# ── 日志双输出 ──
logger = logging.getLogger("backup")
logger.setLevel(logging.INFO)
logger.addHandler(logging.FileHandler(
    BACKUP_ROOT / "logs" / f"{TIMESTAMP}-backup.log"))
logger.addHandler(logging.StreamHandler())
try:
    from systemd import journal
    logger.addHandler(journal.JournalHandler(SYSLOG_IDENTIFIER="backup"))
except ImportError:
    pass

def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def find_latest_backup():
    all_b = sorted(BACKUP_ROOT.glob("backups/*"))
    return all_b[-1] if all_b else None

def copy_if_changed(src, dst, force=False, prev_dst=None):
    if not src.exists():
        return False, "missing"
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not force and prev_dst and prev_dst.exists():
        if file_hash(src) == file_hash(prev_dst):
            return False, "unchanged"
    shutil.copy2(src, dst)
    return True, "copied"

def main():
    # ⚠️ 关键：在 mkdir 之前找前次备份
    backup_dir = BACKUP_ROOT / "backups" / f"{TIMESTAMP}-incremental"
    prev_backup = find_latest_backup()
    
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # 增量对比
    for item in SOURCE_ROOT.rglob("*"):
        if item.is_file():
            rel = item.relative_to(SOURCE_ROOT)
            prev_file = prev_backup / rel if prev_backup else None
            ok, reason = copy_if_changed(item, backup_dir / rel, False, prev_file)
            logger.info(f"  {'✅' if ok else '⏭'} {rel} ({reason})")
    
    # 清单
    manifest = {
        "backup_time": datetime.now().isoformat(),
        "backup_type": "incremental",
        "base": str(prev_backup) if prev_backup else None,
    }
    with open(backup_dir / "MANIFEST.json", "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
```

## 集成到 cron

```bash
# ~/.hermes/scripts/backup-wrapper.sh
#!/usr/bin/env bash
exec python3 /mnt/backup/target-backup/backup.py

# 创建 cron
hermes cronjob create \
  --name "每日备份" \
  --schedule "0 3 * * *" \
  --script "backup-wrapper.sh" \
  --no-agent \
  --deliver local
```
