# Cleanup Verification

After running the cleanup commands, verify space was actually freed:

```bash
df -h /
echo "---"
journalctl --disk-usage
du -sh /var/cache/apt/ /home/$USER/.cache/pip/ /tmp/ 2>/dev/null
```

Expected after clean:
- pip cache: < 20M (down from 1-4 GB)
- journal: ~100M (down from 400M+)
- apt cache: < 1M (down from 300M+)
- /tmp: typically < 100M

Real example from a session (2026-06-07):

| Item | Before | After | Freed |
|------|--------|-------|-------|
| pip cache | 3.3G | 12M | 3.3G |
| journal logs | 409M | 100M | 309M |
| apt cache | 318M | 64K | 318M |
| /var/log old logs | 50M | 0 | 50M |
| System disk total | 51G | 47G | 4.0G |
