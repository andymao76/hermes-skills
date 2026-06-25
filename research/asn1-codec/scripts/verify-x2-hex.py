#!/usr/bin/env python3
"""
HW CS X2 HEX 数据 PER 解码 + 规范性验证
针对 ETSI TS 102 232-1 HI2 PDU (ASN.1 PER Unaligned)

用法:
  python3 verify-x2-hex.py <HEX_STRING>
  python3 verify-x2-hex.py '83010203041fa950e780221a99818188'
"""

import sys
import binascii
import asn1tools

# ETSI TS 102 232-1 HI2 PDU ASN.1 (简化版，不含 ... 扩展标记)
ETSI_HI2_ASN1 = """
HI2-PDU DEFINITIONS AUTOMATIC TAGS ::= BEGIN

LawfulInterceptionIdentifier ::= OCTET STRING (SIZE(1..128))

Timestamp ::= SEQUENCE {
    year    INTEGER (0..9999),
    month   INTEGER (1..12),
    day     INTEGER (1..31),
    hour    INTEGER (0..23),
    minute  INTEGER (0..59),
    second  INTEGER (0..59)
}

ServiceType ::= ENUMERATED {
    csCall              (0),
    sms                 (1),
    mms                 (2),
    lcs                 (3),
    pS                  (4),
    supplementaryService(5)
}

ServiceData ::= SEQUENCE {
    serviceIdentifier  OCTET STRING (SIZE(1..32)),
    serviceType        ServiceType
}

HI2-PDU ::= SEQUENCE {
    lawfulInterceptionIdentifier  LawfulInterceptionIdentifier,
    timestamp                      Timestamp,
    serviceData                    ServiceData OPTIONAL
}

END
"""


def validate_x2_hex(hex_str):
    clean_hex = hex_str.replace(' ', '').replace('\n', '').replace('0x', '')

    results = {
        "hex_length_chars": len(clean_hex),
        "hex_length_bytes": len(clean_hex) // 2,
        "checks": [],
        "errors": [],
        "warnings": [],
        "decoded": None,
        "verdict": "PASS"
    }

    # 检查1: HEX 格式
    try:
        raw = binascii.unhexlify(clean_hex)
    except binascii.Error as e:
        results["errors"].append("\u274c HEX \u683c\u5f0f\u9519\u8bef: {}".format(e))
        return results

    # 检查2: 长度
    n = len(raw)
    if n < 10:
        results["errors"].append("\u274c \u6570\u636e\u8fc7\u77ed ({} bytes)".format(n))
    elif n > 5000:
        results["warnings"].append("\u26a0 \u6570\u636e\u8fc7\u957f ({} bytes)".format(n))
    else:
        results["checks"].append("\u2705 \u957f\u5ea6\u5408\u7406: {} bytes".format(n))

    # 检查3: 首字节
    fb = raw[0]
    if fb == 0x30:
        results["warnings"].append("\u26a0 \u9996\u5b57\u8282 0x30 = BER SEQUENCE Tag")
    elif fb == 0x00:
        results["warnings"].append("\u26a0 \u9996\u5b57\u8282\u4e3a 0x00")
    else:
        results["checks"].append("\u2705 \u9996\u5b57\u8282 0x{:02X}".format(fb))

    # 检查4: PER 解码
    try:
        compiled = asn1tools.compile_string(ETSI_HI2_ASN1, "uper")
        decoded = compiled.decode("HI2-PDU", raw)
        results["decoded"] = decoded
        results["checks"].append("\u2705 PER Unaligned \u89e3\u7801\u6210\u529f")

        # 检查5: 字段约束
        ts = decoded.get('timestamp', {})
        if ts:
            year = ts.get('year', 0)
            month = ts.get('month', 0)
            day = ts.get('day', 0)
            results["checks"].append("\u2705 Timestamp: {}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
                year, month, day,
                ts.get('hour', 0), ts.get('minute', 0), ts.get('second', 0)))
            if not (1 <= month <= 12):
                results["errors"].append("\u274c month \u8d8a\u754c: {}".format(month))
            if not (1 <= day <= 31):
                results["errors"].append("\u274c day \u8d8a\u754c: {}".format(day))

        sd = decoded.get('serviceData')
        if sd:
            results["checks"].append("\u2705 ServiceType: {}".format(sd.get('serviceType', '?')))

    except Exception as e:
        results["errors"].append("\u274c PER \u89e3\u7801\u5931\u8d25: {}".format(e))
        results["verdict"] = "FAIL"

    # 判定
    if results["errors"]:
        results["verdict"] = "FAIL"
    elif results["warnings"]:
        results["verdict"] = "WARN"

    return results


def print_report(results):
    print()
    print("=" * 66)
    print("HW CS X2 HEX \u6570\u636e\u89c4\u8303\u6027\u9a8c\u8bc1\u62a5\u544a")
    print("=" * 66)
    print("  \u8f93\u5165: {} bytes".format(results['hex_length_bytes']))
    print()

    verdict_map = {
        "PASS": ("\u2705 \u901a\u8fc7", "\033[32m"),
        "WARN": ("\u26a0 \u8b66\u544a", "\033[33m"),
        "FAIL": ("\u274c \u4e0d\u901a\u8fc7", "\033[31m"),
    }
    label, color = verdict_map.get(results["verdict"], ("\u672a\u77e5", "\033[0m"))
    print("  \u5224\u5b9a: {}{}\033[0m".format(color, label))
    print()

    print("--- \u68c0\u67e5\u660e\u7ec6 ---")
    for c in results["checks"]:
        print("  {}".format(c))
    for w in results["warnings"]:
        print("  {}".format(w))
    for e in results["errors"]:
        print("  {}".format(e))

    if results["decoded"]:
        print()
        print("--- PER \u89e3\u7801\u7ed3\u679c ---")
        d = results["decoded"]
        liid = d.get("lawfulInterceptionIdentifier", b"")
        if isinstance(liid, bytes):
            print("  LIID:              {} ({})".format(liid.hex(), liid.decode('utf-8', errors='replace')))
        ts = d.get("timestamp", {})
        if ts:
            print("  \u65f6\u95f4\u6233:              {}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
                ts.get('year', '?'), ts.get('month', '?'), ts.get('day', '?'),
                ts.get('hour', '?'), ts.get('minute', '?'), ts.get('second', '?')))
        sd = d.get("serviceData")
        if sd:
            si = sd.get("serviceIdentifier", b"")
            if isinstance(si, bytes):
                si = si.hex()
            print("  \u4e1a\u52a1\u7c7b\u578b:           {}".format(sd.get('serviceType', '?')))
            print("  \u4e1a\u52a1\u6807\u8bc6\u7b26:         {}".format(si))

    print()


def main():
    if len(sys.argv) < 2:
        print("usage: python3 verify-x2-hex.py <HEX_STRING>")
        print("  example: python3 verify-x2-hex.py '83010203041fa950e780221a99818188'")
        sys.exit(1)

    results = validate_x2_hex(sys.argv[1])
    print_report(results)
    sys.exit(0 if results["verdict"] == "PASS" else 1)


if __name__ == "__main__":
    main()
