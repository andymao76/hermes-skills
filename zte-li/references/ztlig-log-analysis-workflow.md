# ZTLIG2 日志全量分析工作流

从多个 ztlig2.*.txt 文件中批量分析指定 LIID 或 MSISDN 的结构化分析方法。

## 四步工作流

```
定位文件 → 统计分布 → 深度分析 → 输出报告
```

## 第一步：定位含目标数据的文件

```bash
grep -l 'LIID.:.14029\|120120415' ztlig2.*.txt
```

也可用 Python 脚本逐文件扫描统计记录数、CIN 数、MSISDN 数、时间范围。

## 第二步：提取与统计

用 `extract_ligcdr.py` 的 `--stats` 模式快速看分布：

```bash
python3 extract_ligcdr.py ztlig2.462.txt --liid 14029 --stats
python3 extract_ligcdr.py ztlig2.465.txt --msisdn 249120120415 --stats
```

或写 Python 脚本批量加载所有对象，去重后统计：

```python
import json, re
from collections import Counter

seen = set()
objs = []
for fpath in files:
    with open(fpath, errors='replace') as f:
        for line in f:
            if 'TARGET_TEXT' not in line: continue
            for m in re.finditer(rb'\{[^{}]*\}', line.encode()):
                js = json.loads(m.group())
                sig = json.dumps(js, sort_keys=True)
                if js.get('CdrType')=='LigCdr' and sig not in seen:
                    seen.add(sig); objs.append(js)
```

## 第三步：深度分析

### 号码角色分析
判断目标号码是 MSISDN（被监听目标）、CallingNum（主叫方）还是 CalledNum（被叫方）：

```python
for obj in objs:
    msisdn = str(obj.get('MSISDN',''))
    calling = str(obj.get('CallingNum',''))
    called = str(obj.get('CalledNum',''))
    if '120120415' in msisdn: role['MSISDN'] += 1
    elif '120120415' in calling: role['Calling'] += 1
```

### 呼叫时序分析
按 CIN 分组后看 EventDetail 序列分布，判断典型呼叫模式：

```python
cin_seq = Counter()
for obj in objs:
    cin = obj.get('CidNum','')
    seq.add(cin, obj.get('EventDetail'))
# 统计每通呼叫的事件数
seq_count = Counter(len(s) for s in seq.values())
# 查看典型序列
seq_pattern = Counter(tuple(sorted(s)) for s in seq.values())
```

### MSISDN 格式归一
同一个号码可能有三种格式：
- `249120120415`（国际格式）
- `0120120415`（本地格式，缺国家码）
- `00249120120415`（国际拨号前缀）

分析时需全部搜索，输出时合并统计。

### 网元与方向
```python
Counter(o.get('Neid') for o in objs).most_common()
Counter(o.get('NetworkType') for o in objs)  # 11=VoWiFi, 13=IMS
Counter(o.get('EventDirection') for o in objs)  # 1=MO, 2=MT
```

## 第四步：输出报告

用纯文本 TXT 格式，章节用 `=` 和 `-` 分隔线。关键数据用表格：

```
一、总体概况
--------------------------------
  指标        数值
  ----        ----
  ...
二、文件分布
--------------------------------
  文件        记录数    CIN数    时间范围
  ----        ------   -----    ----------
  ...
```

## 注意点

- 多个文件中的同一条 LigCdr 会被 JSON 去重（`sort_keys=True` 序列化后做 set）
- 同一 LIID 可能对应多个 MSISDN 格式（国际/本地/前缀），需全部搜索
- CIN 值跨文件出现表示同一次呼叫的多条事件被不同 ztlig2 实例处理
- `A1-ztlig/` 下有伪造的 `.gz` 文件（纯文本），扫描时需排除或只选 `.txt` 文件
