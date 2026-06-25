#!/usr/bin/env python3
"""
从IMA知识库同步的QA PDF中提取内容，整理成结构化文档。

用法: python3 ima_qa_extract.py
输入: ~/knowledge/ima-sync/Andymao的个人知识库/ 下的 Q*.meta.json
输出: ~/knowledge/telecom/ima-qa/ 下的分类markdown文件
依赖: pdftotext (poppler-utils)
"""

import json
import os
import subprocess
import glob
import re
from pathlib import Path

KB_DIR = Path.home() / "knowledge/ima-sync/Andymao的个人知识库"
OUTPUT_DIR = Path.home() / "knowledge/telecom/ima-qa"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CATEGORIES = {
    "5G核心网": ["5GC", "SMF", "AMF", "UPF", "PCF", "NRF", "NSSF", "UDM", "AUSF", "CHF", "BSF"],
    "VoLTE/IMS": ["VoLTE", "IMS", "VoNR", "VoWiFi", "SBC", "CSCF", "MMTel", "SIP", "P-CSCF", "I-CSCF", "S-CSCF", "MGCF", "BGCF"],
    "信令与协议": ["NAS", "RRC", "NGAP", "N4", "N2", "PFCP", "GTP", "Diameter", "SDP", "RTP"],
    "计费": ["计费", "Rating", "Charging", "CDR", "OCS", "OFCS"],
    "网络切片": ["切片", "Slice", "S-NSSAI", "NSI", "TSN"],
    "安全": ["安全", "Security", "NAS重放", "完整性保护"],
    "切换与移动性": ["切换", "Handover", "SRVCC", "TAU", "Paging", "Mobility"],
    "QoS与承载": ["QoS", "QCI", "Bearer", "GBR", "MBR", "AMBR", "专载"],
    "漫游": ["漫游", "Roaming", "GRX", "IPX", "SEPP"],
    "基础概念": ["什么是", "定义", "概念", "TSN", "APN", "DNN"],
}

def download_pdf(url, headers, output_path):
    cmd = ["curl", "-s", "-o", str(output_path)]
    for key, value in headers.items():
        cmd.extend(["-H", f"{key}: {value}"])
    cmd.append(url)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result.returncode == 0

def extract_pdf_text(pdf_path):
    result = subprocess.run(
        ["pdftotext", str(pdf_path), "-"],
        capture_output=True, text=True, timeout=10
    )
    text = "\n".join(
        line for line in result.stdout.split("\n")
        if not line.startswith("Syntax Warning")
    ).strip()
    return text

def clean_text(text):
    noise_patterns = [
        r"51学通信飞书知识库.*",
        r"公众号：51学通信",
        r"站长微信.*",
        r"扫码加.*",
        r"查看更多",
        r"爱卫生",
        r"来自：.*",
        r"\d{4}年\d{2}月\d{2}日\s+\d{2}:\d{2}",
    ]
    for pattern in noise_patterns:
        text = re.sub(pattern, "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def categorize_qa(title, content):
    combined = title + " " + content[:500]
    for cat, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw.lower() in combined.lower():
                return cat
    return "其他"

def safe_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name)[:200]

def main():
    qa_files = sorted(glob.glob(str(KB_DIR / "Q*.meta.json")))
    print(f"找到 {len(qa_files)} 个QA文件")
    
    all_qa = []
    success = 0
    failed = 0
    
    for meta_file in qa_files:
        with open(meta_file) as f:
            meta = json.load(f)
        
        title = meta.get("title", "").replace(".pdf", "").strip()
        url_info = meta.get("url_info", {})
        url = url_info.get("url", "")
        headers = url_info.get("headers", {})
        
        if not url:
            print(f"  ⚠️  无URL: {title}")
            failed += 1
            continue
        
        pdf_path = Path(f"/tmp/qa_{success}.pdf")
        if not download_pdf(url, headers, pdf_path):
            print(f"  ❌ 下载失败: {title}")
            failed += 1
            continue
        
        text = extract_pdf_text(pdf_path)
        if not text or len(text) < 50:
            print(f"  ⚠️  内容过短: {title}")
            failed += 1
            continue
        
        text = clean_text(text)
        category = categorize_qa(title, text)
        
        all_qa.append({
            "title": title,
            "category": category,
            "content": text,
            "media_id": meta.get("media_id", ""),
        })
        
        success += 1
        print(f"  ✅ [{category}] {title[:50]}...")
        pdf_path.unlink(missing_ok=True)
    
    # 按分类整理
    categories = {}
    for qa in all_qa:
        cat = qa["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(qa)
    
    # 生成总文档
    lines = []
    lines.append("# IMA知识库 QA 问答集\n")
    lines.append(f"> 来源：Andymao的个人知识库（IMA）  ")
    lines.append(f"> 整理日期：2026-06-14  ")
    lines.append(f"> 共计 {len(all_qa)} 个问答\n")
    lines.append("---\n")
    lines.append("## 目录\n")
    
    for cat, qas in sorted(categories.items()):
        lines.append(f"### {cat}（{len(qas)}条）\n")
        for qa in qas:
            lines.append(f"- {qa['title']}")
        lines.append("")
    
    lines.append("---\n")
    
    for cat, qas in sorted(categories.items()):
        lines.append(f"## {cat}\n")
        for qa in qas:
            lines.append(f"### {qa['title']}\n")
            lines.append(qa["content"])
            lines.append("\n---\n")
    
    doc_path = OUTPUT_DIR / "ima-qa-collection.md"
    with open(doc_path, "w") as f:
        f.write("\n".join(lines))
    
    # 按分类生成单独文件
    for cat, qas in categories.items():
        cat_lines = [f"# {cat} — QA问答集\n", f"> 共 {len(qas)} 条\n", "---\n"]
        for qa in qas:
            cat_lines.append(f"## {qa['title']}\n")
            cat_lines.append(qa["content"])
            cat_lines.append("\n---\n")
        
        safe_cat = cat.replace("/", "_").replace(" ", "_")
        cat_path = OUTPUT_DIR / f"{safe_cat}.md"
        with open(cat_path, "w") as f:
            f.write("\n".join(cat_lines))
    
    print(f"\n{'='*50}")
    print(f"📊 QA整理完成!")
    print(f"   成功提取: {success}")
    print(f"   失败: {failed}")
    print(f"   分类数: {len(categories)}")
    print(f"   输出目录: {OUTPUT_DIR}")
    print(f"{'='*50}")
    for cat, qas in sorted(categories.items(), key=lambda x: -len(x[1])):
        print(f"   {cat}: {len(qas)}条")

if __name__ == "__main__":
    main()
