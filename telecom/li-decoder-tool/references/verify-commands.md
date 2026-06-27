# 解码工具验证参考

## PCAP 解码验证

```bash
# 上传测试（TCP重组 + 端口8890）
curl -s -F "pcap_file=@test.pcap" \
  -F "decode_type=hw-ims" \
  -F "tcp_fragment=tcp_fragment" \
  -F "port_filter=8890" \
  http://127.0.0.1:5000/ | grep -oP '报文格式错误|解码失败|packet-card' | sort | uniq -c
```

预期：成功包数 >> 错误数。7.6MB PCAP 过滤后约 60 包、1 个错误（TCP FIN）。

## X 接口日志验证

```bash
# 分析 ztlig1 日志前5MB
python3 -c "
import requests
with open('ztlig1.300.txt','rb') as f:
    c = f.read(5*1024*1024).decode('utf-8',errors='replace')
r = requests.post('http://127.0.0.1:5000/x-interface-analyze',
    json={'content':c,'subtype':'ztlig1','interface':'x1','filename':'ztlig1.300.txt'},timeout=30)
s = r.json()['stats']
print(f'行:{s[\"total_lines\"]} LIID:{len(s.get(\"liids\",[]))} ERR:{s[\"errors\"]}')
"
```

预期：行 >25000, LIID >100, 命令识别 >20000。

## 服务状态检查

```bash
lsof -i :5000                    # 检查服务进程
curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/  # 检查HTTP
curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/x-interface  # 检查X接口
```
