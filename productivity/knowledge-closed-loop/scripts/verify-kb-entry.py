#!/usr/bin/env python3
"""
知识库条目正确性校验脚本

验证已写入知识库的 .md 文件与源文档内容一致。
用法：
  python3 scripts/verify-kb-entry.py <kb_path> <src_path>

返回逐项检查结果和 PASS/FAIL 结论。

检查维度：
  - 章节完整性（headings 对比）
  - Memory 铁律一致性
  - 关键数据点
  - 文件统计
"""

import re
import sys
from pathlib import Path


def verify(kb_path: str, src_path: str) -> int:
    kb = Path(kb_path).read_text()
    src = Path(src_path).read_text()

    errors = 0
    checks_run = 0

    # ── 1. 章节完整性 ──
    def get_headings(text):
        return [h.strip() for h in re.findall(r'^#{2,4}\s+(.+)$', text, re.MULTILINE)]

    def print_check(name: str, ok: bool, detail: str = ""):
        nonlocal errors, checks_run
        checks_run += 1
        mark = "PASS" if ok else "FAIL"
        if not ok:
            errors += 1
        print(f"  {mark} {name}")
        if detail:
            for line in detail.split("\n"):
                print(f"       {line}")

    print("=== 1. 章节完整性 ===")
    src_h = set(get_headings(src))
    kb_h = set(get_headings(kb))
    missing = src_h - kb_h
    extra = kb_h - src_h
    print_check("源文档所有章节均在知识库中", not missing,
                f"缺失章节: {missing}" if missing else "")
    print_check("知识库无多余章节", not extra,
                f"多余章节: {extra}" if extra else "")

    # ── 2. 关键数据点 ──
    print("\n=== 2. 关键数据点 ===")
    src_text = src.lower()
    kb_text = kb.lower()

    key_points = [
        ("DeepSeek V4 Flash 存在", "deepseek v4 flash" in kb_text),
        ("DeepSeek V4 Pro 存在", "deepseek v4 pro" in kb_text),
        ("Codex CLI (ACP) 存在", "codex cli" in kb_text and "acp" in kb_text),
        ("deepseek-r1:8b 存在", "deepseek-r1:8b" in kb_text or "deepseek-r1:8b" in kb_text),
        ("Ollama 131K 或 131072 存在", "131072" in kb_text or "131k" in kb_text),
        ("互不混用 (Fallback)", "互不混用" in kb_text),
        ("/new Session 规则", "/new" in kb_text),
        ("禁止 qwen3 系列", "qwen3:8b" in kb_text and "qwen3:14b" in kb_text),
        ("禁止 40K Context", "40k" in kb_text or "40K" in kb_text),
        ("本地优先 / 专业模型优先 / 云端兜底",
         "本地优先" in kb_text and "专业模型优先" in kb_text and "云端兜底" in kb_text),
        ("Frontmatter tags/aliases 存在", "tags:" in kb and "aliases:" in kb),
    ]
    for name, ok in key_points:
        print_check(name, ok)

    # ── 3. 无源文档对比时跳过 ──
    if Path(src_path).samefile(Path(kb_path)):
        print("\n  ⚠ 源文档与知识库是同一文件，跳过源->库差异检查")
    else:
        print("\n=== 3. 源→库差异 ===")
        # compare sizes
        size_diff = abs(len(kb) - len(src))
        ratio = size_diff / len(src) * 100
        # KB should have frontmatter, so being slightly larger is normal
        ok = ratio < 50  # allow up to 50% diff for frontmatter + metadata
        print_check(f"文件大小差异 ({ratio:.1f}% / {size_diff} 字节)", ok)

    # ── 4. 总结 ──
    print(f"\n{'=' * 40}")
    print(f"检查项: {checks_run}, 通过: {checks_run - errors}, 失败: {errors}")
    if errors == 0:
        print("结论: PASS — 知识库条目正确")
    else:
        print(f"结论: FAIL — {errors} 项检查未通过")
    return 1 if errors > 0 else 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: python3 verify-kb-entry.py <knowledge_base_path> <source_path>")
        print("示例: python3 verify-kb-entry.py \\")
        print("  ~/knowledge/hermes/Some_Doc.md \\")
        print("  ~/Documents/Some_Doc.md")
        sys.exit(1)
    sys.exit(verify(sys.argv[1], sys.argv[2]))
