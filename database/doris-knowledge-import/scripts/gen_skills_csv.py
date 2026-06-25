#!/usr/bin/env python3
"""
遍历 ~/.hermes/skills/ → hermes_skills.csv
用于导入到 knowledge_chunks（tags='hermes-skills/{skill_name}'）
"""
import csv, os, re, hashlib

SKILLS_DIR = os.path.expanduser("~/.hermes/skills")
TEXT_EXT = {".md", ".txt", ".yaml", ".yml", ".toml", ".json", ".cfg", ".conf", ".py", ".sh", ".ini", ".env"}
EXCLUDE_DIRS = {".git", "__pycache__", "node_modules", ".trash"}

def truncate_bytes(s, max_bytes=250):
    encoded = s.encode('utf-8')[:max_bytes]
    while encoded and (encoded[-1] & 0xC0) == 0x80:
        encoded = encoded[:-1]
    return encoded.decode('utf-8', errors='replace')

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
rows = []

for root, dirs, files in os.walk(SKILLS_DIR):
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
    for fname in files:
        ext = os.path.splitext(fname)[1].lower()
        if ext not in TEXT_EXT:
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
        rel = fpath.replace(SKILLS_DIR, "").strip("/")
        parts = rel.split("/")
        skill_name = parts[0] if parts else "unknown"
        title = fname.replace(".md", "").replace(".txt", "")[:200]
        rel_path = f"~/.hermes/skills/{rel}"
        for chunk_title, chunk_text, src in chunk_content(content, title, rel_path):
            h = hashlib.md5(chunk_text.encode()).hexdigest()
            if h in seen_hashes:
                continue
            seen_hashes.add(h)
            rows.append((chunk_title, chunk_text, f"hermes-skills/{skill_name}", rel_path))

print(f"总文件: {total_files}, 总切片: {len(rows)}")
with open("/tmp/hermes_skills.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, quoting=csv.QUOTE_ALL)
    for r in rows:
        w.writerow(r)
print(f"CSV: {os.path.getsize('/tmp/hermes_skills.csv')/1024/1024:.1f} MB")
