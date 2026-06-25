# Batch Clone & Backup Session Reference

## Environment

- Disk: `/dev/sda2` exfat 895G (863G free), mounted at `/mnt/backup`
- Proxy: `http://127.0.0.1:7897` for GitHub access in China
- OS: Ubuntu 24.04.4 LTS

## Batch Clone with Proxy

Set proxy BEFORE git operations:

```bash
export HTTPS_PROXY=http://127.0.0.1:7897
export HTTP_PROXY=http://127.0.0.1:7897

# Shallow clone all repos
cd ~/code
git clone --depth 1 https://github.com/codecrafters-io/build-your-own-x.git learning/build-your-own-x
git clone --depth 1 https://github.com/EbookFoundation/free-programming-books.git learning/free-programming-books
# ... etc
```

## TOP 10 Projects Cloned

| # | Project | Stars | Size |
|---|---------|------:|------|
| 1 | codecrafters-io/build-your-own-x | 513k | 320K |
| 2 | sindresorhus/awesome | 474k | 744K |
| 3 | freeCodeCamp/freeCodeCamp | 446k | 167M |
| 4 | public-apis/public-apis | 440k | 676K |
| 5 | EbookFoundation/free-programming-books | 390k | 3.8M |
| 6 | openclaw/openclaw | 377k | 287M |
| 7 | nilbuild/developer-roadmap | 356k | 239M |
| 8 | donnemartin/system-design-primer | 352k | 24M |
| 9 | jwasham/coding-interview-university | 350k | 9.3M |
| 10 | vinta/awesome-python | 302k | 1.1M |

Total: ~730M (depth 1), ~14G on exfat backup (with git objects)

## Cron Setup

Job name: `code-backup-rsync` (ID via cronjob list)
Schedule: `0 3 * * *` (daily 3 AM)
Script: `/home/andymao/code/rsync-backup.sh`

## Knowledge Base Files Created

- `~/knowledge/research/github-top-10-starred-2026.md`
- `~/knowledge/research/github-top-projects-codebase.md`

## GitHub Desktop

Not installed (user declined apt install). Manual install option: download .deb from https://github.com/shiftkey/desktop/releases
