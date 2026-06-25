#!/usr/bin/env python3
"""
BER TAG 解码数学验证脚本

验证 2位/4位/6位 三种 TAG 假设解码规则的正确性。
在所有已知测试数据集上运行，输出 PASS/FAIL 结果。

用法：
  python3 ber-tag-verify.py                    # 运行标准验证
  python3 ber-tag-verify.py --verbose           # 详细输出
"""

import sys

# ── 2位假定：TAG = 首字节 & 0x1F ────────────────────────────

TAG_2BYTE_TESTS = [
    # (byte, expected_tag, description)
    (0x80, 0,  "Context [0] primitive"),
    (0x81, 1,  "Context [1] primitive"),
    (0x82, 2,  "Context [2] primitive"),
    (0x83, 3,  "Context [3] primitive"),
    (0x85, 5,  "Context [5] primitive"),
    (0x89, 9,  "Context [9] primitive"),
    (0x90, 16, "Context [16] primitive"),
    (0x8F, 15, "Context [15] primitive"),
    (0x8D, 13, "Context [13] primitive"),
    (0x8A, 10, "Context [10] primitive"),
    (0x8B, 11, "Context [11] primitive"),
    (0x8C, 12, "Context [12] primitive"),
    (0x93, 19, "Context [19] primitive"),
    (0x97, 23, "Context [23] primitive"),
    (0xA4, 4,  "Context [4] constructed"),
    (0xAE, 14, "Context [14] constructed"),
    (0xB2, 18, "Context [18] constructed"),
    # Universal class tests
    (0x01, 1,  "Universal BOOLEAN"),
    (0x02, 2,  "Universal INTEGER"),
    (0x04, 4,  "Universal OCTET STRING"),
    (0x05, 5,  "Universal NULL"),
    (0x30, 16, "Universal SEQUENCE (constructed!)"),
    (0x31, 17, "Universal SET (constructed!)"),
    # Application class
    (0x40, 0,  "Application [0]"),
    (0x41, 1,  "Application [1]"),
    # Private class
    (0xC0, 0,  "Private [0]"),
    (0xC1, 1,  "Private [1]"),
]

# ── 4位假定：取第2字节低7位 ────────────────────────────────

TAG_4BYTE_TESTS = [
    # (bytes, expected_tag, description)
    ([0x9F, 0x80], 0,     "Context Primitive, long-form, tag=0"),
    ([0x9F, 0x81], 1,     "Context Primitive, long-form, tag=1"),
    ([0x9F, 0x50], 80,    "Context Primitive, long-form, tag=80"),
    ([0xBF, 0x50], 80,    "Context Constructed, long-form, tag=80"),
    ([0x1F, 0x20], 32,    "Universal, tag=32"),
    ([0x3F, 0x21], 33,    "Universal Constructed, tag=33"),
]

# ── 6位假定：多字节续码拼接 ────────────────────────────────

TAG_6BYTE_TESTS = [
    # (bytes, expected_tag, description)
    ([0x9F, 0x81, 0x48], 200, "Context Primitive, tag=200 (1<<7 | 72)"),
    ([0x9F, 0x81, 0x7F], 255, "Context Primitive, tag=255 (max 2-byte long)"),
    ([0x9F, 0x82, 0x01], 257, "Context Primitive, tag=257 (2<<7 | 1)"),
    ([0x9F, 0x80, 0x01], 1,   "Context Primitive, tag=1 (0<<7 | 1)"),
]


def verify_2byte() -> tuple:
    """验证 2位TAG 解码规则：TAG = byte & 0x1F"""
    passed = 0
    failed = 0
    errors = []

    for byte_val, expected, desc in TAG_2BYTE_TESTS:
        tag = byte_val & 0x1F
        if tag == expected:
            passed += 1
        else:
            failed += 1
            errors.append(f"  ✗ 0x{byte_val:02X}: got TAG={tag}, expected {expected} — {desc}")

    return passed, failed, errors


def verify_4byte() -> tuple:
    """验证 4位TAG 解码规则"""
    passed = 0
    failed = 0
    errors = []

    for raw_bytes, expected, desc in TAG_4BYTE_TESTS:
        first = raw_bytes[0]
        if (first & 0x1F) < 31:
            tag = first & 0x1F
        else:
            second = raw_bytes[1]
            tag = second & 0x7F

        if tag == expected:
            passed += 1
        else:
            failed += 1
            errors.append(f"  ✗ {' '.join(f'{b:02X}' for b in raw_bytes)}: got TAG={tag}, expected {expected} — {desc}")

    return passed, failed, errors


def verify_6byte() -> tuple:
    """验证 6位TAG 解码规则：多字节长格式拼接"""
    passed = 0
    failed = 0
    errors = []

    for raw_bytes, expected, desc in TAG_6BYTE_TESTS:
        tag = 0
        for b in raw_bytes[1:]:  # skip first byte (long-form marker)
            tag = (tag << 7) | (b & 0x7F)
            if not (b & 0x80):
                break

        if tag == expected:
            passed += 1
        else:
            failed += 1
            errors.append(f"  ✗ {' '.join(f'{b:02X}' for b in raw_bytes)}: got TAG={tag}, expected {expected} — {desc}")

    return passed, failed, errors


def run_all(verbose: bool = False):
    """运行全部验证"""
    total_passed = 0
    total_failed = 0

    print("=" * 65)
    print("BER TAG 解码数学验证")
    print("=" * 65)

    # 2位
    p, f, errs = verify_2byte()
    total_passed += p
    total_failed += f
    print(f"\n▶ 2位假定（TAG = byte & 0x1F）：{p}/{p+f} 通过")
    if errs and verbose:
        for e in errs:
            print(e)
    if not errs and verbose:
        print("  全部正确 ✓")

    # 4位
    p, f, errs = verify_4byte()
    total_passed += p
    total_failed += f
    print(f"\n▶ 4位假定（第2字节低7位）：{p}/{p+f} 通过")
    if errs and verbose:
        for e in errs:
            print(e)
    if not errs and verbose:
        print("  全部正确 ✓")

    # 6位
    p, f, errs = verify_6byte()
    total_passed += p
    total_failed += f
    print(f"\n▶ 6位假定（多字节续码拼接）：{p}/{p+f} 通过")
    if errs and verbose:
        for e in errs:
            print(e)
    if not errs and verbose:
        print("  全部正确 ✓")

    # 总结
    total = total_passed + total_failed
    print(f"\n{'=' * 65}")
    print(f"总计：{total} 个测试点，{total_passed} 通过，{total_failed} 失败")
    if total_failed == 0:
        print("结果：全部正确 ✓")
    else:
        print("结果：存在失败 ✗")


if __name__ == "__main__":
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    run_all(verbose)
