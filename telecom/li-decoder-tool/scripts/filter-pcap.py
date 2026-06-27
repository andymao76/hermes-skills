#!/usr/bin/env python3
"""PCAP 端口过滤 + 解码验证脚本
用法:
  python3 scripts/filter-pcap.py /path/to/input.pcap 8890
  → 输出 /path/to/TCP重组+端口8890/xxx_port8890.pcap

依赖: dpkt
"""
import dpkt, os, sys

def filter_pcap_by_port(in_path, out_path, target_port):
    count_in = count_out = 0
    with open(in_path, 'rb') as f:
        reader = dpkt.pcap.Reader(f)
        writer = dpkt.pcap.Writer(open(out_path, 'wb'))
        for ts, buf in reader:
            try:
                eth = dpkt.ethernet.Ethernet(buf)
                if not isinstance(eth.data, dpkt.ip.IP): continue
                ip = eth.data
                if not isinstance(ip.data, dpkt.tcp.TCP): continue
                tcp = ip.data
                count_in += 1
                if tcp.sport == target_port or tcp.dport == target_port:
                    writer.writepkt(buf, ts)
                    count_out += 1
            except: continue
    return count_in, count_out

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f"用法: {sys.argv[0]} <input.pcap> <port>")
        sys.exit(1)
    in_path = sys.argv[1]
    port = int(sys.argv[2])
    base = os.path.dirname(in_path)
    name = os.path.basename(in_path).replace('.pcap', '')
    out_dir = os.path.join(base, f'TCP重组+端口{port}')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f'{name}_port{port}.pcap')
    total, matched = filter_pcap_by_port(in_path, out_path, port)
    in_sz = os.path.getsize(in_path)
    out_sz = os.path.getsize(out_path)
    print(f"输入: {in_path} ({in_sz/1024/1024:.1f}MB, {total} TCP包)")
    print(f"输出: {out_path} ({out_sz/1024:.0f}KB, {matched} 端口{port}包)")
    print(f"压缩率: {out_sz/in_sz*100:.1f}%")
