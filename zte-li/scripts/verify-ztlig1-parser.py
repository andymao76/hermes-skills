#!/usr/bin/env python3
"""
ZTLIG1 X1 日志解析器验证脚本 — 可重复运行

用法:
    python3 scripts/verify-ztlig1-parser.py                    # 仅单行测试
    python3 scripts/verify-ztlig1-parser.py /path/to/ztlig1.300.txt  # 单行+大文件测试
    python3 scripts/verify-ztlig1-parser.py --unit-only        # 仅单行测试

依赖: 需要在 ETSI-ASN1-Assistant 的 venv 中运行
    cd ~/projects/ETSI-ASN1-Assistant && source venv/bin/activate
"""
import sys
import os
from collections import Counter

# 将 x_interface_decoder.py 所在目录加入路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from x_interface_decoder import parse_log_line, parse_log_file, generate_summary, detect_log_type


def test_unit():
    """13 个单行解析测试用例"""
    errors = []

    tests = [
        # (label, log_line, expected_fields)
        ("A-INFORM+ztlig-1",
         r'[2025-12-22 08:01:23][DEBUG][ztlig1:300][INFORM][ztlig-1][lig1_process_msg]:recv start init req msg',
         {"module":"ztlig1","command":"process_init","sub_module":"ztlig-1"}),

        ("A-INFORM+ztlig-1_hwne",
         r'[2025-12-23 10:24:30][DEBUG][ztlig1:300][INFORM][ztlig-1_hwne][hwmsc_x1_addTargetRsp]:hw msc ne add target succ,tneid=1,liid=10066',
         {"module":"ztlig1","command":"set_target","neid":"1","liid":"10066","sub_module":"ztlig-1_hwne","result":"success"}),

        ("A-Kafka设控",
         r'[2025-12-22 10:41:33][DEBUG][ztlig1:300][INFORM][ztlig-1_web][WebProcKafkaHi1msgSingle]:recv an add target message,lea=1,vne=8',
         {"module":"ztlig1","command":"set_target","sub_module":"ztlig-1_web"}),

        ("A-Kafka停控",
         r'[2025-12-22 16:05:20][DEBUG][ztlig1:300][INFORM][ztlig-1_web][WebProcKafkaHi1msgSingle]:recv an del target message,lea=1,vne=36',
         {"module":"ztlig1","command":"del_target","sub_module":"ztlig-1_web"}),

        ("A-链路错误",
         r'[2025-12-22 08:04:35][DEBUG][ztlig1:300][ERROR][ztlig-1_hwne][hwmsc_x1_linkcheck]:the link to ne:31 error',
         {"module":"ztlig1","command":"link_error","sub_module":"ztlig-1_hwne","result":"failed"}),

        ("A-列出目标",
         r'[2025-12-23 01:01:31][DEBUG][ztlig1:300][INFORM][ztlig-1_hwne][hwmsc_x1_listTargetRsp]:hua wei msc list target succ,tneID=32',
         {"module":"ztlig1","command":"list_target_rsp","neid":"32","result":"success","sub_module":"ztlig-1_hwne"}),

        ("B-停控响应",
         r'[2025-12-23 10:34:30][INFO][ztlig1:300][ztlig-1_hwne][hwmsc_x1_delTargetRsp]:hua wei msc del target succ,tneID=1,liid=8137',
         {"module":"ztlig1","command":"del_target","neid":"1","liid":"8137","sub_module":"ztlig-1_hwne","result":"success"}),

        ("B-网元无响应",
         r'[2025-12-22 10:30:21][ERROR][ztlig1:300][ztlig-1_hwne]not receive ne response in 3 seconds,tneid=6,vneid=6',
         {"module":"ztlig1","command":"ne_no_response","neid":"6","vneid":"6","sub_module":"ztlig-1_hwne"}),

        ("B-ETSI检查",
         r'[2025-12-22 10:30:21][DEBUG][ztlig1:300][ztlig-1_etsi][lig1_etsi_check_liid_TtTi]:liid+tt+ti is the same',
         {"module":"ztlig1","command":"etsi_liid_check","sub_module":"ztlig-1_etsi"}),

        ("B-Redis同步",
         r'[2025-12-22 08:01:28][DEBUG][ztlig1:300][ztlig-1_web][redis_syn_db_handle]:get redis target[{"account":"249123694629"}]',
         {"module":"ztlig1","command":"redis_sync","sub_module":"ztlig-1_web","account":"249123694629"}),

        ("B-DB删除通知",
         r'[2025-12-23 10:34:30][INFO][ztlig1:300][ztlig-1][lig1_notify_del2db]:notify db to del target success! liid=8137',
         {"module":"ztlig1","command":"del_target","liid":"8137","sub_module":"ztlig-1","result":"success"}),

        ("C-连接检查",
         r'[2025-12-22 08:01:28][DEBUG][ztlig1:300]:check connection to ne:31 fail!',
         {"module":"ztlig1","command":"link_check","result":"failed","sub_module":None}),

        ("C-启动",
         r'[2025-12-22 08:01:23][INFO ][ztlig1:300]ztlig1 module is starting...',
         {"module":"ztlig1","command":"process_init","level":"INFO","sub_module":None}),
    ]

    for label, line, expected in tests:
        result = parse_log_line(line)
        if result is None:
            errors.append(f"[FAIL] {label}: parse_log_line returned None")
            continue
        for key, val in expected.items():
            actual = result.get(key)
            if actual != val:
                errors.append(f"[FAIL] {label}.{key}: expect={val!r} got={actual!r}")

    return errors


def test_large_file(filepath):
    """用真实日志前5MB进行验证"""
    errors = []
    with open(filepath, "rb") as f:
        content = f.read(5 * 1024 * 1024).decode("utf-8", errors="replace")
    parsed = parse_log_file(content)
    stats = generate_summary(parsed)
    total = len(parsed)
    cmd_count = sum(1 for p in parsed if p.get("command"))
    liid_count = len(stats.get("liids", []))
    sub_covered = sum(1 for p in parsed if p.get("sub_module"))

    if cmd_count < 20000:
        errors.append(f"命令识别不足: {cmd_count} < 20000")
    if liid_count < 100:
        errors.append(f"LIID提取不足: {liid_count} < 100")
    if sub_covered < total * 0.95:
        errors.append(f"子模块覆盖率不足: {sub_covered}/{total}")

    return errors, {"total": total, "commands": cmd_count, "liids": liid_count, "sub_covered": sub_covered}


def test_report_generation():
    """测试 generate_ztlig1_report 报告生成"""
    errors = []
    from x_interface_decoder import generate_ztlig1_report
    
    # 用真实日志行构造 parsed 数据
    parsed = []
    for line in [
        r'[2025-12-22 08:01:23][DEBUG][ztlig1:300][INFORM][ztlig-1][lig1_process_msg]:recv start init req msg',
        r'[2025-12-23 10:24:30][DEBUG][ztlig1:300][INFORM][ztlig-1_hwne][hwmsc_x1_addTargetRsp]:hw msc ne add target succ,tneid=1,liid=10066',
        r'[2025-12-22 08:01:28][DEBUG][ztlig1:300]:check connection to ne:31 fail!',
        r'[2025-12-22 10:41:33][DEBUG][ztlig1:300][INFORM][ztlig-1_web][WebProcKafkaHi1msgSingle]:recv an add target message,lea=1,vne=8',
        r'[2025-12-23 10:34:30][INFO][ztlig1:300][ztlig-1][lig1_notify_del2db]:notify db to del target success! liid=8137',
        r'[2025-12-22 08:04:35][DEBUG][ztlig1:300][ERROR][ztlig-1_hwne][hwmsc_x1_linkcheck]:the link to ne:31 error',
    ]:
        r2 = parse_log_line(line)
        if r2:
            parsed.append(r2)
    
    report = generate_ztlig1_report(parsed)
    
    checks = [
        ("total_lines", report.get("total_lines"), 6, "=="),
        ("commands", len(report.get("commands", [])), 4, ">="),
        ("sub_modules", len(report.get("sub_modules", [])), 2, ">="),
        ("liid_count", report.get("liid_count"), 2, ">="),
        ("ne_faults.link_check", report.get("ne_faults", {}).get("link_check"), 1, ">="),
        ("ne_faults.link_error", report.get("ne_faults", {}).get("link_error"), 1, ">="),
        ("samples.kafka_msg", bool(report.get("samples", {}).get("kafka_msg")), True, "=="),
        ("samples.add_success", bool(report.get("samples", {}).get("add_success")), True, "=="),
        ("samples.ne_fault", bool(report.get("samples", {}).get("ne_fault")), True, "=="),
    ]
    for label, actual, expected, op in checks:
        if op == "==" and actual != expected:
            errors.append(f"[FAIL] report.{label}: expect={expected} got={actual}")
        elif op == ">=" and actual < expected:
            errors.append(f"[FAIL] report.{label}: {actual} < {expected}")
    
    return errors


if __name__ == "__main__":
    unit_only = "--unit-only" in sys.argv

    print("═══ ZTLIG1 解析器验证 ═══\n")

    # 单行测试
    print(">>> 单行测试 (13 cases)")
    unit_errors = test_unit()
    
    # 报告生成测试
    print("\\n>>> 报告生成测试 (generate_ztlig1_report)")
    report_errors = test_report_generation()
    for e in report_errors:
        print(f"  {e}")
    if not report_errors:
        print("  OK")
    for label, _, _ in [
        ("A-INFORM+ztlig-1","",""),
        ("A-INFORM+ztlig-1_hwne","",""),
        ("A-Kafka设控","",""),
        ("A-Kafka停控","",""),
        ("A-链路错误","",""),
        ("A-列出目标","",""),
        ("B-停控响应","",""),
        ("B-网元无响应","",""),
        ("B-ETSI检查","",""),
        ("B-Redis同步","",""),
        ("B-DB删除通知","",""),
        ("C-连接检查","",""),
        ("C-启动","",""),
    ]:
        fail = any(label in e for e in unit_errors)
        print(f"  {'FAIL' if fail else 'OK'} | {label}")

    if unit_errors:
        for e in unit_errors:
            print(f"    {e}")

    # 大文件测试
    if not unit_only and len(sys.argv) > 1 and os.path.isfile(sys.argv[-1]):
        logpath = sys.argv[-1]
        print(f"\n>>> 大文件测试: {os.path.basename(logpath)}")
        file_errors, stats = test_large_file(logpath)
        print(f"  行:{stats['total']} 命令:{stats['commands']} LIID:{stats['liids']} 子模块:{stats['sub_covered']}")
        for e in file_errors:
            print(f"  {e}")

    all_errors = unit_errors + report_errors + (file_errors if not unit_only and len(sys.argv) > 1 else [])
    if all_errors:
        print(f"\n═══ 失败 ({len(all_errors)}) ═══")
        sys.exit(1)
    else:
        print(f"\n═══ 全部通过 ═══")
