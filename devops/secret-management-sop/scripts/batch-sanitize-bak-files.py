#!/usr/bin/env python3
"""
批量脱敏备份文件中的明文 API Key

用法:
  python3 batch-sanitize-bak-files.py <glob-pattern>

示例:
  python3 batch-sanitize-bak-files.py "~/.hermes/config.yaml.bak.*"
  python3 batch-sanitize-bak-files.py "~/**/*.bak.*"

原理:
  用正则匹配 api_key: <value> 模式，将实际密钥替换为 [REDACTED]。
  保留空值 ('') 和环境变量引用（api_key_env）。
  只改写文件中的 api_key 行，不修改其他配置。

适用场景:
  - config.yaml.bak.* 等历史备份文件中残留明文 API Key
  - 已完成密钥迁移到 .env 后清理旧备份
  - 配合 'find' 批量处理多目录备份

注意事项:
  - 操作不可逆 — 原始密钥值将被永久替换
  - 确保当前 config.yaml 中密钥已迁移到 api_key_env 后再执行
  - 建议先备份原文件或确认当前密钥在 .env 中安全存储
"""

import re
import os
import sys
import glob


def sanitize_file(fpath: str) -> int:
    """
    脱敏单个文件中的所有 api_key 明文值。
    返回脱敏的密钥条目数。
    """
    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    original = content
    count_before = content.count('[REDACTED]')

    # 模式1: api_key: sk-xxxxx  (YAML 带空格)
    content = re.sub(
        r'^(\s*api_key:\s*)(?![\'"])(?!\s*$)(.+)$',
        r'\1[REDACTED]',
        content,
        flags=re.MULTILINE
    )

    # 模式2: api_key: 'sk-xxxxx' 或 api_key: "sk-xxxxx" (YAML 引号)
    content = re.sub(
        r'^(\s*api_key:\s*["\'])(?!\s*$)(.+?)(["\'])$',
        r'\1[REDACTED]\3',
        content,
        flags=re.MULTILINE
    )

    # 模式3: api_key:sk-xxxxx (无空格)
    content = re.sub(
        r'^(\s*api_key:)(?!\s)(sk-[^\s"\']+)',
        r'\1[REDACTED]',
        content,
        flags=re.MULTILINE
    )

    count_after = content.count('[REDACTED]')
    replaced = count_after - count_before

    if replaced > 0:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)

    return replaced


def verify_no_plaintext(pattern: str) -> bool:
    """验证 glob 匹配的文件中是否还有明文密钥残留"""
    files = glob.glob(os.path.expanduser(pattern), recursive=True)
    has_plaintext = False
    for fpath in sorted(files):
        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        # 检查未被脱敏的 api_key 行
        matches = re.findall(
            r'^(\s*api_key:\s*)(?!\[REDACTED\])(?![\'"]\s*[\'"])(?![\'"]\s*$)(.+)$',
            content,
            re.MULTILINE
        )
        # 过滤掉 api_key_env 行
        real_matches = [m for m in matches if m[1].strip() and not m[1].startswith('[')]
        if real_matches:
            print(f"  ⚠  {os.path.basename(fpath)}: 仍有未脱敏条目")
            has_plaintext = True

    return not has_plaintext


def main():
    if len(sys.argv) < 2:
        print("用法: python3 batch-sanitize-bak-files.py <glob-pattern>")
        print("示例: python3 batch-sanitize-bak-files.py '~/.hermes/config.yaml.bak.*'")
        sys.exit(1)

    pattern = sys.argv[1]
    files = glob.glob(os.path.expanduser(pattern), recursive=True)

    if not files:
        print(f"未找到匹配的文件: {pattern}")
        sys.exit(0)

    print(f"找到 {len(files)} 个文件")
    total_replaced = 0

    for fpath in sorted(files):
        n = sanitize_file(fpath)
        if n > 0:
            print(f"  ✅ {os.path.basename(fpath)}: {n} 个密钥已脱敏")
        else:
            print(f"  ➖ {os.path.basename(fpath)}: 无变化")
        total_replaced += n

    print(f"\n总计处理 {len(files)} 个文件，脱敏 {total_replaced} 个密钥条目")

    # 验证
    print("\n=== 残留验证 ===")
    if verify_no_plaintext(pattern):
        print("✅ 无残留明文密钥")
    else:
        print("⚠  部分文件仍有残留，请手动检查")
        sys.exit(2)


if __name__ == '__main__':
    main()
