# LigCdr 分析命令速查

## 定位目标分布

```bash
cd ~/PCAP/20260623-A1-VOWIFI

# 快速定位含 LIID 的文件
grep -l 'LIID.:.14029' A1-ztlig/*.txt

# 快速定位含 MSISDN 的文件
grep -l '120120415' A1-ztlig/*.txt

# 扫描文件总记录数
wc -l A1-ztlig/*.txt
```

## 创建软链接目录（解决 argparse 多文件限制）

```bash
mkdir -p /tmp/ztlig_4files
for f in ztlig2.461.txt ztlig2.465.txt ztlig2.466.txt ztlig2.467.txt; do
    ln -sf "A1-ztlig/$f" "/tmp/ztlig_4files/$f"
done
```

## 提取数据

```bash
# 按 LIID 提取（去重）
python3 extract_ligcdr.py /tmp/ztlig_4files/ --liid 14029 --unique -o /tmp/ztlig_14029

# 按 MSISDN 提取（精确匹配国际格式）
python3 extract_ligcdr.py /tmp/ztlig_4files/ --msisdn 249120120415 --unique -o /tmp/ztlig_msisdn

# 按 MSISDN 补扫本地格式
python3 -c "
import json, re
files = ['ztlig2.461.txt','ztlig2.465.txt','ztlig2.466.txt','ztlig2.467.txt']
seen = set()
for fname in files:
    with open(f'A1-ztlig/{fname}') as f:
        for line in f:
            for m in re.finditer(rb'\{[^{}]*\}', line.encode('utf-8')):
                try:
                    obj = json.loads(m.group())
                    if obj.get('CdrType')=='LigCdr' and str(obj.get('MSISDN',''))=='0120120415':
                        sig = json.dumps(obj, sort_keys=True)
                        if sig not in seen:
                            seen.add(sig)
                            print(f'LIID={obj[\"LIID\"]} CT={obj.get(\"CaptureTime\")} ED={obj.get(\"EventDetail\")}')
                except: pass
print(f'额外: {len(seen)} 条')
"

# 带统计
python3 extract_ligcdr.py A1-ztlig/ztlig2.467.txt --liid 14029 --stats
```

## 深度分析（Python 脚本要点）

分析脚本关键维度：

```python
from collections import Counter, defaultdict

# 1. MSISDN 分布
msisdn_count = Counter()
for obj in objects:
    msisdn_count[str(obj.get('MSISDN',''))] += 1

# 2. LIID 分组
liid_data = defaultdict(list)
for obj in objects:
    liid_data[str(obj.get('LIID',''))].append(obj)

# 3. 呼叫时序 (按 CIN)
cin_groups = defaultdict(list)
for obj in objects:
    cin_groups[str(obj.get('CidNum',''))].append(obj)

# 4. 典型 EventDetail 序列
seq_count = Counter()
for cin, objs in cin_groups.items():
    seq = tuple(sorted([o.get('EventDetail') for o in objs]))
    seq_count[seq] += 1

# 5. 时间分布
dates = Counter()
for obj in objects:
    ct = obj.get('CaptureTime','')
    if ct: dates[ct[:8]] += 1

# 6. 号码角色分析
role = Counter()
for obj in objects:
    msisdn = str(obj.get('MSISDN',''))
    calling = str(obj.get('CallingNum',''))
    called = str(obj.get('CalledNum',''))
    if '120120415' in msisdn: role['MSISDN(目标)'] += 1
    elif '120120415' in calling: role['CallingNum(主叫)'] += 1
    elif '120120415' in called: role['CalledNum(被叫)'] += 1
```

## 报告结构（TXT 格式）

```
标题行
=======

一、总体概况
二、文件/数据分布
三、LIID 维度 / 号码角色
四、呼叫时序 / EventDetail
五、网元与方向
六、时间分布
七、关联号码
八、关键发现
九、输出文件
```

# 6. 号码角色分析

```python
role = Counter()
for obj in objects:
    msisdn = str(obj.get('MSISDN',''))
    calling = str(obj.get('CallingNum',''))
    called = str(obj.get('CalledNum',''))
    if '120120415' in msisdn: role['MSISDN(被监听目标)'] += 1
    elif '120120415' in calling: role['CallingNum(主叫)'] += 1
    elif '120120415' in called: role['CalledNum(被叫)'] += 1
```

# 7. 关联号码（通话对方）

```python
peers = Counter()
for obj in objects:
    calling = str(obj.get('CallingNum',''))
    called = str(obj.get('CalledNum',''))
    msisdn = str(obj.get('MSISDN',''))
    # 如果 120120415 是目标
    if '120120415' in msisdn:
        for n in [calling, called]:
            if n and '120120415' not in n: peers[n] += 1
    # 如果 120120415 是对方
    else:
        if '120120415' in calling or '120120415' in called:
            peers[msisdn] += 1
```

## 非 JSON 行提取（V1.2）

```bash
# 按 LIID 提取 + 非JSON关联行
python3 extract_ligcdr.py /tmp/ztlig_4files/ --liid 14029 --unique -o /tmp/output
# 输出包含 raw_matches_filtered.txt

# 按 CIN 精确过滤（能捕获 P-Charging-Vector 等 SIP 头）
python3 extract_ligcdr.py /tmp/ztlig_4files/ --cin "psdpcscf02.xxx" -o /tmp/output

# 按 EventDetail 过滤
python3 extract_ligcdr.py /tmp/ztlig_4files/ --event-detail 10,11,13 -o /tmp/output
```

## 大文件处理

```bash
# 270MB+ 文件必须用 background
python3 extract_ligcdr.py ... --liid 14029 --unique -o /tmp/out &
# 或设置足够 timeout
```

```python
ED_NAMES = {
    1: 'Begin(Bearer)', 2: 'Continue(Bearer)', 4: 'Begin(SMS)',
    10: 'Begin', 11: 'Answer', 12: 'Redirection',
    13: 'Release', 14: 'T38', 17: 'Partial', 18: 'CallRelease',
}
```
