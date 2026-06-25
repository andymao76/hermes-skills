#!/usr/bin/env python3
"""
format-checker.py — 通用格式检查修复脚本

用法:
  format-checker.py scan <目录>  [选项]     # 批量校验
  format-checker.py check <文件>            # 检查单个文件
  format-checker.py fix <文件>  [选项]      # 修复单个文件

选项:
  -r, --recursive           递归扫描子目录
  -t, --types yaml,json,xml 仅检查指定类型（默认全部）
  -f, --fix                 自动修复可修复的问题
  -b, --backup              修复前备份原文件
  -o, --output <文件>        输出校验报告到文件
  -v, --verbose             显示详细信息
  -q, --quiet               仅显示错误文件列表
"""

import os
import sys
import re
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime

# ─── 依赖检查 ────────────────────────────────────────────────────────────────

try:
    import yaml
except ImportError:
    print("错误: 需要 PyYAML 库，请执行: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

try:
    import xml.etree.ElementTree as ET
except ImportError:
    print("错误: 需要 xml.etree.ElementTree（Python 标准库）", file=sys.stderr)
    sys.exit(1)


# ─── 常量 ────────────────────────────────────────────────────────────────────

EXT_MAP = {
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".xml": "xml",
}


# ─── 日志 ────────────────────────────────────────────────────────────────────

class Logger:
    def __init__(self, verbose=False, quiet=False):
        self.verbose = verbose
        self.quiet = quiet
        self.lines = []

    def info(self, msg):
        if not self.quiet:
            print(msg)
        self.lines.append(("INFO", msg))

    def detail(self, msg):
        if self.verbose and not self.quiet:
            print(msg)
        self.lines.append(("DETAIL", msg))

    def warn(self, msg):
        if not self.quiet:
            print(f"  {msg}", file=sys.stderr)
        self.lines.append(("WARN", msg))

    def error(self, msg):
        if not self.quiet:
            print(f"  {msg}", file=sys.stderr)
        self.lines.append(("ERROR", msg))

    def ok(self, msg):
        if not self.quiet:
            print(f"  {msg}")
        self.lines.append(("OK", msg))

    def get_report(self):
        return "\n".join(f"[{t}] {m}" for t, m in self.lines)


# ─── 备份 ────────────────────────────────────────────────────────────────────

def backup_file(path: Path, backup_dir: Path = None) -> Path:
    if backup_dir is None:
        backup_dir = Path("/tmp/format-checker-backups")
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak_path = backup_dir / f"{path.name}.{ts}.bak"
    shutil.copy2(str(path), str(bak_path))
    return bak_path


# ═══════════════════════════════════════════════════════════════════════════════
# YAML 校验与修复
# ═══════════════════════════════════════════════════════════════════════════════

def validate_yaml(filepath: Path, log: Logger):
    issues = []
    try:
        raw = filepath.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        for enc in ["utf-8-sig", "gbk", "gb2312", "latin-1"]:
            try:
                raw = filepath.read_text(encoding=enc)
                issues.append({
                    "type": "encoding", "line": 1,
                    "msg": f"文件编码非 UTF-8（检测到 {enc}），已转码",
                    "fixable": True,
                    "fix_fn": lambda t=raw, e=enc: filepath.write_text(t, encoding="utf-8")
                })
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        else:
            return False, [{"type": "encoding", "line": 0, "msg": "无法解码文件（未知编码）", "fixable": False}]

    # 检查制表符缩进
    for i, line in enumerate(raw.split("\n"), 1):
        if "\t" in line and line.strip() and line[0] == "\t":
            issues.append({
                "type": "tabs", "line": i,
                "msg": f"第{i}行使用了制表符缩进",
                "fixable": True,
                "fix_fn": lambda f=filepath: fix_yaml_tabs(f)
            })
            break

    # 用 PyYAML 验证
    try:
        yaml.safe_load(raw)
    except yaml.YAMLError as e:
        if hasattr(e, "problem_mark"):
            line = e.problem_mark.line + 1
            msg = str(e)
        else:
            line = 1
            msg = str(e)

        fix_info = try_fix_yaml_syntax(raw, filepath, line)
        if fix_info:
            issues.append({
                "type": "yaml_syntax", "line": line,
                "msg": f"YAML: {msg.strip()}",
                "fixable": True,
                "fix_msg": fix_info["fix_msg"],
                "fix_fn": fix_info["fix_fn"],
                "context": fix_info.get("context", ""),
            })
        else:
            issues.append({
                "type": "yaml_syntax", "line": line,
                "msg": f"YAML: {msg.strip()}",
                "fixable": False,
                "context": get_context_line(raw, line),
            })

    ok = len([i for i in issues if i["type"] in ("yaml_syntax", "encoding", "tabs")]) == 0
    return ok, issues


def try_fix_yaml_syntax(raw: str, filepath: Path, error_line: int):
    lines = raw.split("\n")

    if error_line <= len(lines):
        line = lines[error_line - 1]

        # 修复1: 值中含未引号冒号 → 加引号
        colon_match = re.match(r"^(\s*)([\w_-]+):\s*(.*)", line)
        if colon_match:
            indent = colon_match.group(1)
            key = colon_match.group(2)
            val = colon_match.group(3)
            if ":" in val and not val.strip().startswith(("'", '"')):
                def fix_fn():
                    new_lines = lines.copy()
                    new_val = val.strip()
                    new_lines[error_line - 1] = f"{indent}{key}: \"{new_val}\""
                    filepath.write_text("\n".join(new_lines), encoding="utf-8")
                return {
                    "fix_msg": f"值中包含未引号冒号 \"{val.strip()}\" → 已加引号",
                    "fix_fn": fix_fn,
                    "context": line,
                }

        # 修复2: 纯冒号未引号字符串
        if ":" in line and not line.strip().startswith("#"):
            parts = line.split(":")
            if len(parts) > 2:
                def fix_fn():
                    new_lines = lines.copy()
                    indent_match = re.match(r"^(\s*)([\w_-]+):\s*(.*)", line)
                    if indent_match:
                        ind = indent_match.group(1)
                        k = indent_match.group(2)
                        v = indent_match.group(3)
                        new_lines[error_line - 1] = f'{ind}{k}: "{v}"'
                        filepath.write_text("\n".join(new_lines), encoding="utf-8")
                return {
                    "fix_msg": f"行中包含未引号包围的冒号值 → 已加引号",
                    "fix_fn": fix_fn,
                    "context": line,
                }

    return None


def fix_yaml_tabs(filepath: Path):
    raw = filepath.read_text(encoding="utf-8")
    fixed = raw.replace("\t", "    ")
    filepath.write_text(fixed, encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════════════════
# JSON 校验与修复
# ═══════════════════════════════════════════════════════════════════════════════

def validate_json(filepath: Path, log: Logger):
    issues = []
    try:
        raw = filepath.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False, [{"type": "encoding", "line": 0, "msg": "无法解码文件", "fixable": False}]

    try:
        json.loads(raw)
        return True, []
    except json.JSONDecodeError as e:
        line = e.lineno if hasattr(e, "lineno") and e.lineno else 1
        msg = str(e)

        fix_info = try_fix_json(raw, filepath, line, msg)
        if fix_info:
            issues.append({
                "type": "json_syntax", "line": line,
                "msg": f"JSON: {msg}",
                "fixable": True,
                "fix_msg": fix_info["fix_msg"],
                "fix_fn": fix_info["fix_fn"],
                "context": get_context_line(raw, line),
            })
        else:
            issues.append({
                "type": "json_syntax", "line": line,
                "msg": f"JSON: {msg}",
                "fixable": False,
                "context": get_context_line(raw, line),
            })

    return False, issues


def try_fix_json(raw: str, filepath: Path, error_line: int, error_msg: str):
    """尝试修复 JSON 常见问题（组合多步修复）"""

    def chain_fixes(text, fixes, success_msg):
        """依次应用多个修复，若最终解析成功则返回修复闭包"""
        current = text
        applied = []
        for name, pattern, replacement in fixes:
            new_text = re.sub(pattern, replacement, current)
            if new_text != current:
                applied.append(name)
                current = new_text
        if current != text:
            try:
                json.loads(current)
                msg = f"{success_msg}: {', '.join(applied)}"
                return {"fix_msg": msg, "fix_fn": lambda c=current: filepath.write_text(c, encoding="utf-8")}
            except json.JSONDecodeError:
                pass
        return None

    # 修复组合1: 尾逗号 + Python 字面量
    result = chain_fixes(raw, [
        ("尾逗号", r",(\s*[}\]])", r"\1"),
        ("Python字面量(True→true)", r"\bTrue\b", "true"),
        ("Python字面量(False→false)", r"\bFalse\b", "false"),
        ("Python字面量(None→null)", r"\bNone\b", "null"),
    ], "已修复")
    if result:
        return result

    # 修复组合2: 单引号key + 单引号值 + 尾逗号 + Python字面量
    result = chain_fixes(raw, [
        ("单引号key→双引号", r"'([^']+)'\s*:", lambda m: f'"{m.group(1)}":'),
        ("单引号值→双引号", r":\s*'([^']+)'(\s*[,}\]])", lambda m: f': "{m.group(1)}"{m.group(2)}'),
        ("尾逗号", r",(\s*[}\]])", r"\1"),
        ("Python字面量(True→true)", r"\bTrue\b", "true"),
        ("Python字面量(False→false)", r"\bFalse\b", "false"),
        ("Python字面量(None→null)", r"\bNone\b", "null"),
    ], "已修复")
    if result:
        return result

    # 修复3: 仅移除注释
    result = chain_fixes(raw, [
        ("注释(//)", r"//[^\n]*", ""),
        ("注释(/* */)", r"/\*.*?\*/", ""),
    ], "已修复")
    if result:
        return result

    return None


# ═══════════════════════════════════════════════════════════════════════════════
# XML 校验与修复
# ═══════════════════════════════════════════════════════════════════════════════

def validate_xml(filepath: Path, log: Logger):
    issues = []
    try:
        raw = filepath.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            raw = filepath.read_text(encoding="utf-8-sig")
            issues.append({
                "type": "bom", "line": 1,
                "msg": "文件包含 UTF-8 BOM 头，已处理",
                "fixable": True,
                "fix_fn": lambda f=filepath, c=raw: f.write_text(c.lstrip("\ufeff"), encoding="utf-8")
            })
        except UnicodeDecodeError:
            return False, [{"type": "encoding", "line": 0, "msg": "无法解码 XML 文件", "fixable": False}]

    # 移除控制字符
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", raw)
    if cleaned != raw:
        issues.append({
            "type": "control_chars", "line": 0,
            "msg": "文件中包含无效控制字符，已移除",
            "fixable": True,
            "fix_fn": lambda f=filepath, c=cleaned: f.write_text(c, encoding="utf-8"),
        })
        raw = cleaned

    try:
        ET.parse(str(filepath))
    except ET.ParseError as e:
        line = e.position[0] if e.position else 1
        fix_info = try_fix_xml(raw, filepath, line)
        if fix_info:
            issues.append({
                "type": "xml_syntax", "line": line,
                "msg": f"XML: {e}",
                "fixable": True,
                "fix_msg": fix_info["fix_msg"],
                "fix_fn": fix_info["fix_fn"],
                "context": get_context_line(raw, line),
            })
        else:
            issues.append({
                "type": "xml_syntax", "line": line,
                "msg": f"XML: {e}",
                "fixable": False,
                "context": get_context_line(raw, line),
            })

    ok = len([i for i in issues if i["type"] == "xml_syntax"]) == 0
    return ok, issues


def try_fix_xml(raw: str, filepath: Path, error_line: int):
    # 修复1: 属性值缺少引号 <tag attr=value> → <tag attr="value">
    fixed = re.sub(r'(\w+)=(\w+(?:\.\w+)*(?:-\w+)*)(?=\s|/?>)', r'\1="\2"', raw)
    if fixed != raw:
        try:
            ET.fromstring(fixed)
            return {"fix_msg": "属性值补充了引号", "fix_fn": lambda: filepath.write_text(fixed, encoding="utf-8")}
        except ET.ParseError:
            pass

    # 修复2: 自闭合标签格式
    fixed2 = re.sub(r"<(\w+)([^>]*)\s/>", r"<\1\2/>", raw)
    if fixed2 != raw:
        try:
            ET.fromstring(fixed2)
            return {"fix_msg": "修复了自闭合标签格式", "fix_fn": lambda: filepath.write_text(fixed2, encoding="utf-8")}
        except ET.ParseError:
            pass

    # 修复3: & 转义
    fixed3 = re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;|#x?[\da-fA-F]+;)", "&amp;", raw)
    if fixed3 != raw:
        try:
            ET.fromstring(fixed3)
            return {"fix_msg": "修复了未转义的 & 符号", "fix_fn": lambda: filepath.write_text(fixed3, encoding="utf-8")}
        except ET.ParseError:
            pass

    return None


# ═══════════════════════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════════════════════

def get_context_line(raw: str, line_no: int, context_lines: int = 2):
    lines = raw.split("\n")
    start = max(0, line_no - 1 - context_lines)
    end = min(len(lines), line_no + context_lines)
    ctx = []
    for i in range(start, end):
        marker = ">>>" if i == line_no - 1 else "   "
        ctx.append(f"  {marker} {i+1:4d}| {lines[i]}")
    return "\n".join(ctx)


def collect_files(directory: Path, file_types: set, recursive: bool):
    files = []
    if recursive:
        iterator = directory.rglob("*")
    else:
        iterator = directory.glob("*")

    for f in iterator:
        if f.is_file() and f.suffix.lower() in EXT_MAP:
            if EXT_MAP[f.suffix.lower()] in file_types:
                files.append(f)
    return sorted(files)


# ═══════════════════════════════════════════════════════════════════════════════
# 主命令
# ═══════════════════════════════════════════════════════════════════════════════

VALIDATORS = {
    "yaml": validate_yaml,
    "json": validate_json,
    "xml": validate_xml,
}


def cmd_check(args, log: Logger):
    filepath = Path(args.file)
    if not filepath.exists():
        log.error(f"文件不存在: {filepath}")
        return 1

    ext = filepath.suffix.lower()
    ftype = EXT_MAP.get(ext)
    if not ftype:
        log.error(f"不支持的文件类型: {ext}（支持 yaml/yml/json/xml）")
        return 1

    validator = VALIDATORS[ftype]
    is_valid, issues = validator(filepath, log)

    print(f"\n{'='*55}")
    print(f"  检查: {filepath}")
    print(f"  类型: {ftype.upper()}")
    print(f"  状态: {'✓ 通过' if is_valid else '✗ 有错误'}")
    print(f"{'='*55}")

    if issues:
        for iss in issues:
            line_info = f":L{iss['line']}" if iss.get("line") else ""
            print(f"\n  [{iss['type'].upper()}]{line_info} {iss['msg']}")
            if iss.get("context"):
                print(f"\n{iss['context']}")
            if iss.get("fix_msg"):
                print(f"  → 修复方案: {iss['fix_msg']}")

    return 0 if is_valid else 1


def cmd_fix(args, log: Logger):
    filepath = Path(args.file)
    if not filepath.exists():
        log.error(f"文件不存在: {filepath}")
        return 1

    ext = filepath.suffix.lower()
    ftype = EXT_MAP.get(ext)
    if not ftype:
        log.error(f"不支持的文件类型: {ext}")
        return 1

    validator = VALIDATORS[ftype]

    if args.backup:
        bak = backup_file(filepath)
        log.info(f"备份: {bak}")

    # 循环修复：每次修复后重新验证，直到没有可修复的问题
    total_fixed = 0
    max_rounds = 10

    for rnd in range(1, max_rounds + 1):
        is_valid, issues = validator(filepath, log)
        if is_valid:
            if total_fixed > 0:
                log.ok(f"修复后验证通过（共 {total_fixed} 处修复）")
            else:
                log.ok("文件格式正确，无需修复")
            return 0

        fixable = [i for i in issues if i.get("fixable") and i.get("fix_fn")]
        unfixable = [i for i in issues if not i.get("fixable")]

        if unfixable and not fixable:
            log.warn(f"有 {len(unfixable)} 个问题无法自动修复:")
            for u in unfixable:
                print(f"    L{u.get('line', '?')}: {u['msg']}")
            log.error("没有可自动修复的问题")
            return 1

        round_fixed = 0
        for iss in fixable:
            try:
                iss["fix_fn"]()
                round_fixed += 1
                total_fixed += 1
                log.ok(iss.get("fix_msg", "已修复"))
            except Exception as e:
                log.error(f"修复失败: {e}")

        if round_fixed == 0:
            log.warn("未能进一步修复，剩余问题需手动处理")
            return 1

    log.warn(f"达到最大修复轮次（{max_rounds}），仍有问题未修复")
    return 1


def cmd_scan(args, log: Logger):
    directory = Path(args.scan_dir)
    if not directory.exists() or not directory.is_dir():
        log.error(f"目录不存在: {directory}")
        return 1

    file_types = set(args.types.split(",")) if args.types else {"yaml", "json", "xml"}
    recursive = args.recursive

    files = collect_files(directory, file_types, recursive)

    if not files:
        log.warn(f"在 {directory} 中未找到 {file_types} 文件" +
                 ("（含子目录）" if recursive else "（仅当前目录）"))
        return 0

    log.info(f"扫描 {directory} — 找到 {len(files)} 个文件")
    log.info(f"文件类型: {', '.join(sorted(file_types))}")
    if recursive:
        log.info("模式: 递归扫描")

    print()
    results = []
    total_errors = 0
    total_fixed = 0
    backup_dir = Path("/tmp/format-checker-backups")

    for f in files:
        ext = f.suffix.lower()
        ftype = EXT_MAP[ext]
        validator = VALIDATORS[ftype]

        is_valid, issues = validator(f, log)

        errors = [i for i in issues if not i.get("fixable")]
        fixable = [i for i in issues if i.get("fixable")]

        if issues:
            total_errors += 1
            relpath = f.relative_to(directory) if directory in f.parents else f
            print(f"  {relpath}  ({ftype.upper()}, {len(errors)} 语法错误, {len(fixable)} 可修复)")

            results.append({
                "file": str(f), "type": ftype,
                "errors": len(errors), "fixable": len(fixable), "fixed": 0,
            })

            if log.verbose:
                for iss in issues:
                    line_info = f":L{iss.get('line', '?')}"
                    print(f"    [{iss['type']}]{line_info} {iss['msg']}")
                    if iss.get("fix_msg"):
                        print(f"    → {iss['fix_msg']}")

            if args.fix and fixable:
                if args.backup:
                    bak = backup_file(f, backup_dir)
                    print(f"    备份: {bak}")
                # 循环修复
                max_r = 10
                file_fixed_total = 0
                for rnd in range(1, max_r + 1):
                    iss_fixable = [i for i in fixable if i.get("fix_fn")]
                    if not iss_fixable:
                        break
                    for iss in iss_fixable:
                        try:
                            iss["fix_fn"]()
                            file_fixed_total += 1
                            total_fixed += 1
                            print(f"    ✅ 已修复: {iss.get('fix_msg', '')}")
                        except Exception as e:
                            print(f"    ❌ 修复失败: {e}")
                    # 重新验证
                    _, new_issues = validator(f, log)
                    fixable = [i for i in new_issues if i.get("fixable")]
                    if not fixable:
                        break
                results[-1]["fixed"] = file_fixed_total
            print()

    print(f"{'='*55}")
    print(f"  扫描完成")
    print(f"  目录:  {directory}")
    print(f"  文件:  {len(files)} 个 ({', '.join(sorted(file_types))})")
    print(f"  错误:  {total_errors} 个文件有问题")
    if args.fix:
        print(f"  已修复: {total_fixed} 处")
    else:
        print(f"  可修复: {sum(r['fixable'] for r in results)} 处")
        print(f"  要启用自动修复，请加 --fix 参数")
    print(f"{'='*55}")

    if args.output:
        output_path = Path(args.output)
        report_lines = [
            "=" * 55,
            f" Format Checker Report",
            f" 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f" 扫描目录: {directory}",
            f" 文件总数: {len(files)}",
            f" 问题文件: {total_errors}",
            f" 已修复: {total_fixed}",
            "=" * 55,
            "",
        ]
        for r in results:
            report_lines.append(f"  {'✓' if r['errors'] == 0 else '✗'} {r['file']}")
            if r['errors'] > 0:
                report_lines.append(f"     {r['errors']} 语法错误, {r['fixed']} 已修复")
        output_path.write_text("\n".join(report_lines), encoding="utf-8")
        log.info(f"报告已保存到: {output_path}")

    return 0 if total_errors == 0 else 1


# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Format Checker — XML / YAML / JSON 格式校验与修复",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例:
  format-checker.py scan .                          # 扫描当前目录
  format-checker.py scan ~/.hermes -r               # 递归扫描 ~/.hermes
  format-checker.py scan ./configs --types yaml     # 仅检查 YAML
  format-checker.py scan . -rf --backup             # 递归扫描并修复，备份
  format-checker.py scan . -o report.txt            # 输出报告
  format-checker.py check config.yaml               # 检查单个文件
  format-checker.py fix data.json --backup          # 修复单个文件
""")

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    p_scan = subparsers.add_parser("scan", help="扫描目录批量校验")
    p_scan.add_argument("scan_dir", nargs="?", default=".", help="要扫描的目录（默认当前目录）")
    p_scan.add_argument("-r", "--recursive", action="store_true", help="递归扫描子目录")
    p_scan.add_argument("-t", "--types", default="yaml,json,xml", help="文件类型（逗号分隔，默认: yaml,json,xml）")
    p_scan.add_argument("-f", "--fix", action="store_true", help="自动修复可修复的问题")
    p_scan.add_argument("-b", "--backup", action="store_true", help="修复前备份文件")
    p_scan.add_argument("-o", "--output", help="输出校验报告到文件")
    p_scan.add_argument("-v", "--verbose", action="store_true", help="显示详细信息")
    p_scan.add_argument("-q", "--quiet", action="store_true", help="仅显示错误文件列表")

    p_check = subparsers.add_parser("check", help="检查单个文件")
    p_check.add_argument("file", help="文件路径")
    p_check.add_argument("-v", "--verbose", action="store_true", help="显示详细信息")

    p_fix = subparsers.add_parser("fix", help="修复单个文件")
    p_fix.add_argument("file", help="文件路径")
    p_fix.add_argument("-b", "--backup", action="store_true", help="修复前备份文件")
    p_fix.add_argument("-v", "--verbose", action="store_true", help="显示详细信息")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    log = Logger(
        verbose=getattr(args, 'verbose', False),
        quiet=getattr(args, 'quiet', False),
    )

    cmds = {"scan": cmd_scan, "check": cmd_check, "fix": cmd_fix}
    return cmds[args.command](args, log)


if __name__ == "__main__":
    sys.exit(main())
