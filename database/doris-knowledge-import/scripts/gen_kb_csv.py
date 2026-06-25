#!/usr/bin/env python3
"""
遍历 ~/knowledge/ → knowledge_chunks.csv + telecom_skill.csv
用于 Doris Stream Load 导入或 SQLite 重建
"""
import csv, os, re, hashlib

KB = os.path.expanduser("~/knowledge")
TELECOM_PREFIXES = ["/telecom/", "/li/", "/移动通信相关/", "/3gpp-references/", "/3gpp-ts33108/", "/hi2/", "/A1/"]
EXCLUDE_DIRS = {".obsidian", ".git", "_system", "secrets", "cache", "__pycache__", ".trash", "04_ARCHIVE", "00_INBOX"}
TEXT_EXT = {".md", ".txt", ".json", ".yaml", ".yml", ".cfg", ".conf", ".ini"}

def truncate_bytes(s, max_bytes=250):
    encoded = s.encode('utf-8')[:max_bytes]
    while encoded and (encoded[-1] & 0xC0) == 0x80:
        encoded = encoded[:-1]
    return encoded.decode('utf-8', errors='replace')

def is_telecom(path):
    rel = path.replace(KB, "")
    return any(p in rel for p in TELECOM_PREFIXES)

def chunk_content(content, title, source_path, max_chars=3000):
    chunks = []
    content = content.strip()
    if len(content) < 20:
        return chunks
    sections = re.split(r'\n(?=##\s)', content)
    if len(sections) <= 1:
        chunks.append((truncate_bytes(title, 250), content[:max_chars], source_path))
    else:
        for sec in sections:
            sec = sec.strip()
            if len(sec) < 20:
                continue
            h2 = re.search(r'^##\s+(.+)', sec, re.MULTILINE)
            subtitle = title[:200]
            if h2:
                subtitle = f"{title[:100]} > {h2.group(1).strip()[:180]}"[:200]
            for i in range(0, len(sec), max_chars):
                chunk_text = sec[i:i+max_chars]
                chunk_title = subtitle if i == 0 else f"{subtitle[:180]} (续{i//max_chars+1})"[:200]
                chunks.append((truncate_bytes(chunk_title, 250), chunk_text, source_path))
    return chunks

seen_hashes = set()
total_files = 0

with open("/tmp/knowledge_chunks.csv", "w", newline="", encoding="utf-8") as f_kb, \
     open("/tmp/telecom_skill.csv", "w", newline="", encoding="utf-8") as f_tel:
    w_kb = csv.writer(f_kb, quoting=csv.QUOTE_ALL)
    w_tel = csv.writer(f_tel, quoting=csv.QUOTE_ALL)
    for root, dirs, files in os.walk(KB):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for fname in files:
            if os.path.splitext(fname)[1].lower() not in TEXT_EXT:
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except:
                continue
            if len(content.strip()) < 20:
                continue
            total_files += 1
            title = fname.replace(".md", "").replace(".txt", "")[:200]
            path_parts = fpath.replace(KB, "").strip("/").split("/")
            tags = path_parts[0] if path_parts else "unknown"
            rel_path = fpath.replace(KB, "~")
            for chunk_title, chunk_text, src in chunk_content(content, title, rel_path):
                h = hashlib.md5(chunk_text.encode()).hexdigest()
                if h in seen_hashes:
                    continue
                seen_hashes.add(h)
                if is_telecom(fpath):
                    li_level = "5" if ("/li/" in rel_path or "/A1/" in rel_path) else "0"
                    w_tel.writerow([chunk_title, chunk_text, tags, rel_path, li_level])
                else:
                    w_kb.writerow([chunk_title, chunk_text, tags, rel_path])

print(f"总文件: {total_files}")
print(f"knowledge_chunks.csv: {os.path.getsize('/tmp/knowledge_chunks.csv')/1024/1024:.1f} MB")
print(f"telecom_skill.csv: {os.path.getsize('/tmp/telecom_skill.csv')/1024/1024:.1f} MB")
