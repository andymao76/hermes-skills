#!/usr/bin/env python3
"""
BER-TLV TAG 解码分析工具 — 三种 TAG 长度假设对比

2位假设：TAG = 首字节 & 0x1F（BER 短格式低5位）
4位假设：首字节低5位=11111 ? 取第2字节低7位 : 取低5位
6位假设：标准 BER 长格式多字节拼接（continuation bytes）

适用于 MAP/CAP/TCAP 码流的 BER TAG 字段试探分析。

用法:
  python3 ber-tag-analyzer.py "30 2D 80 08 64 10 00 00 00 00 20 F4"
  python3 ber-tag-analyzer.py --mode bytewise --step 20 "9F 1F 81 7F 48 80 81 82"
  python3 ber-tag-analyzer.py --interactive
"""

import sys
import argparse
from typing import List, Tuple


# ═══════════════════════════════════════════════════════════════
# BER 编解码核心
# ═══════════════════════════════════════════════════════════════

def decode_tag_ber(data: bytes, offset: int) -> Tuple[int, int, str]:
    """BER 标准 Tag 解码（短格式 + 长格式）"""
    if offset >= len(data):
        raise ValueError("Offset beyond data")
    first = data[offset]
    low5 = first & 0x1F
    raw = [first]
    if low5 < 31:
        return (low5, 1, fmt_hex(raw))
    tag = 0
    while offset + len(raw) < len(data):
        b = data[offset + len(raw)]
        raw.append(b)
        tag = (tag << 7) | (b & 0x7F)
        if not (b & 0x80):
            break
    return (tag, len(raw), fmt_hex(raw))


def decode_length_ber(data: bytes, offset: int) -> Tuple[int, int]:
    """BER 长度字段解码。返回 (length, consumed_bytes)。"""
    if offset >= len(data):
        raise ValueError("Offset beyond data")
    first = data[offset]
    if first & 0x80:
        n = first & 0x7F
        if n == 0:
            return (-1, 1)
        length = 0
        for i in range(1, n + 1):
            length = (length << 8) | data[offset + i]
        return (length, 1 + n)
    return (first, 1)


# ═══════════════════════════════════════════════════════════════
# 三种 TAG 假设解码
# ═══════════════════════════════════════════════════════════════

def tag_assumption_2byte(data: bytes, offset: int) -> Tuple[int, str]:
    """2位TAG假设：TAG = 首字节 & 0x1F (BER 短格式低5位)"""
    if offset >= len(data):
        return (0, "")
    b = data[offset]
    return (b & 0x1F, f"{b:02X}")


def tag_assumption_4byte(data: bytes, offset: int) -> Tuple[int, str]:
    """4位TAG假设：首字节低5位=11111 ? 取第2字节低7位 : 取低5位"""
    if offset >= len(data):
        return (0, "")
    first = data[offset]
    raw = [first]
    if (first & 0x1F) < 31:
        return (first & 0x1F, fmt_hex(raw))
    if offset + 1 >= len(data):
        return (0, fmt_hex(raw))
    second = data[offset + 1]
    raw.append(second)
    return (second & 0x7F, fmt_hex(raw))


def tag_assumption_6byte(data: bytes, offset: int) -> Tuple[int, str]:
    """6位TAG假设：标准 BER 长格式多字节拼接"""
    if offset >= len(data):
        return (0, "")
    first = data[offset]
    raw = [first]
    if (first & 0x1F) < 31:
        return (first & 0x1F, fmt_hex(raw))
    tag = 0
    pos = offset + 1
    while pos < len(data):
        b = data[pos]
        raw.append(b)
        tag = (tag << 7) | (b & 0x7F)
        if not (b & 0x80):
            break
        pos += 1
    return (tag, fmt_hex(raw))


# ═══════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════

def fmt_hex(bytes_list: List[int]) -> str:
    return " ".join(f"{b:02X}" for b in bytes_list)


def parse_hex(text: str) -> bytes:
    for sep in [' ', '\n', '\t', ',', '0x', '0X', '\\x', '-', ':']:
        text = text.replace(sep, '')
    return bytes.fromhex(text)


# ═══════════════════════════════════════════════════════════════
# 分析引擎
# ═══════════════════════════════════════════════════════════════

def analyze_structure(data: bytes, base: float = 4005, start_seq: int = 215):
    """按 BER TLV 结构遍历码流。在每个 TAG 位置输出三种假设的对比结果。"""
    buf_offset = 0
    seq = start_seq
    entries = []

    header = (
        f"{'序列':>6} | {'偏移量':>10} | {'增量':>8} | {'16进制':>6} | {'10进制':>4} | "
        f"{'2位TAG':>6} | {'2位原值':>8} | {'4位tag':>6} | {'4位原值':>12} | "
        f"{'6位tag':>6} | {'6位原值':>18}"
    )
    print(header)
    print("-" * len(header))

    while buf_offset < len(data):
        calc = base + buf_offset
        delta = buf_offset - entries[-1][0] if entries else buf_offset
        byte_hex = f"{data[buf_offset]:02X}"
        byte_dec = data[buf_offset]

        t2_val, t2_raw = tag_assumption_2byte(data, buf_offset)
        t4_val, t4_raw = tag_assumption_4byte(data, buf_offset)
        t6_val, t6_raw = tag_assumption_6byte(data, buf_offset)

        print(
            f"{seq:>6} | {calc:>10.3f} | {delta:>8.3f} | {byte_hex:>6} | {byte_dec:>4} | "
            f"{t2_val:>6} | {t2_raw:>8} | {t4_val:>6} | {t4_raw:>12} | "
            f"{t6_val:>6} | {t6_raw:>18}"
        )

        entries.append((buf_offset, seq))

        # 跳过 TLV 到下一个结构
        try:
            _, tag_consumed, _ = decode_tag_ber(data, buf_offset)
            buf_offset += tag_consumed
            if buf_offset >= len(data):
                break
            length, len_consumed = decode_length_ber(data, buf_offset)
            buf_offset += len_consumed
            if buf_offset >= len(data):
                break
            if length == 0:
                # NULL 或空 value（如 SS-Status NULL）: 不调整偏移
                # buf_offset 已在下一个 TAG 位置，继续遍历
                pass
            elif length > 0:
                tag_byte = data[buf_offset - tag_consumed - len_consumed]
                is_constructed = bool(tag_byte & 0x20)
                if is_constructed and length > 0:
                    pass
                else:
                    buf_offset += length
            else:
                buf_offset += 1
        except (ValueError, IndexError):
            break

        seq += 1
        if buf_offset >= len(data):
            break

    print(f"\n共 {len(entries)} 个 BER 结构位置")


def analyze_bytewise(data: bytes, base: float = 4005, start_seq: int = 215,
                     step: float = 20.0, max_rows: int = 50):
    """逐字节遍历（固定步进），用于模拟等距采样分析。"""
    header = (
        f"{'序列':>6} | {'偏移量':>10} | {'增量':>8} | {'16进制':>6} | {'10进制':>4} | "
        f"{'2位TAG':>6} | {'2位原值':>8} | {'4位tag':>6} | {'4位原值':>12} | "
        f"{'6位tag':>6} | {'6位原值':>18}"
    )
    print(header)
    print("-" * len(header))

    calc = base
    seq = start_seq
    n = 0
    offset = 0
    while offset < len(data) and n < max_rows:
        byte_hex = f"{data[offset]:02X}"
        byte_dec = data[offset]

        t2_val, t2_raw = tag_assumption_2byte(data, offset)
        t4_val, t4_raw = tag_assumption_4byte(data, offset)
        t6_val, t6_raw = tag_assumption_6byte(data, offset)

        print(
            f"{seq:>6} | {calc:>10.3f} | {step:>8.3f} | {byte_hex:>6} | {byte_dec:>4} | "
            f"{t2_val:>6} | {t2_raw:>8} | {t4_val:>6} | {t4_raw:>12} | "
            f"{t6_val:>6} | {t6_raw:>18}"
        )

        offset += 1
        calc += step
        seq += 1
        n += 1


# ═══════════════════════════════════════════════════════════════
# 交互模式
# ═══════════════════════════════════════════════════════════════

def interactive():
    print("=" * 70)
    print("BER-TLV TAG 解码分析工具 （交互模式）")
    print("=" * 70)
    print("输入16进制码流（可含空格/换行），空行或 Ctrl+D 结束：")
    lines = []
    try:
        while True:
            line = input()
            if not line.strip():
                break
            lines.append(line)
    except EOFError:
        pass

    text = " ".join(lines)
    if not text.strip():
        print("未输入数据。")
        return

    data = parse_hex(text)
    print(f"\n输入: {len(data)} bytes")
    if len(data) <= 64:
        print(f"码流: {' '.join(f'{b:02X}' for b in data)}")
    print()

    while True:
        print("\n分析模式：")
        print("  1) BER 结构遍历（自动跳转 TAG）")
        print("  2) 逐字节遍历（固定步进）")
        print("  q) 退出")
        choice = input("选择 [1]: ").strip()
        if choice == 'q':
            break
        if not choice or choice == '1':
            analyze_structure(data)
            break
        elif choice == '2':
            try:
                step = float(input("偏移步进值 [20]: ") or "20")
                rows = int(input("最大行数 [50]: ") or "50")
                analyze_bytewise(data, step=step, max_rows=rows)
            except ValueError:
                print("输入无效。")
            break


def main():
    parser = argparse.ArgumentParser(
        description="BER-TLV TAG 解码分析 — 三种 TAG 长度假设对比",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 %(prog)s "30 2D 80 08 64 10 00 00 00 00 20 F4"
  python3 %(prog)s "9F 1F 81 7F 48 80 81 82" --mode bytewise --step 20
  echo "30 2D 80 08" | python3 %(prog)s --stdin
  python3 %(prog)s --interactive
        """)
    parser.add_argument("hex", nargs="?", help="16进制码流")
    parser.add_argument("--stdin", "-i", action="store_true", help="从 stdin 读取")
    parser.add_argument("--interactive", "-I", action="store_true", help="交互模式")
    parser.add_argument("--mode", choices=["structure", "bytewise"], default="structure")
    parser.add_argument("--base", type=float, default=4005, help="基地址 (默认 4005)")
    parser.add_argument("--start-seq", type=int, default=215, help="起始序列号")
    parser.add_argument("--step", type=float, default=20.0, help="bytewise 步进")
    parser.add_argument("--max-rows", type=int, default=50, help="最大行数")
    args = parser.parse_args()

    if args.interactive:
        interactive()
        return

    hex_text = ""
    if args.stdin or not args.hex:
        hex_text = sys.stdin.read().strip()
    else:
        hex_text = args.hex

    if not hex_text:
        parser.print_help()
        sys.exit(1)

    data = parse_hex(hex_text)
    print(f"输入: {len(data)} bytes")
    print()

    if args.mode == "bytewise":
        analyze_bytewise(data, base=args.base, start_seq=args.start_seq,
                          step=args.step, max_rows=args.max_rows)
    else:
        analyze_structure(data, base=args.base, start_seq=args.start_seq)


if __name__ == "__main__":
    main()
