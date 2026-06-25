---
name: tech-bug-log-analyzer
description: 日志分析工具集 — 解析文本日志/JSON日志/堆栈跟踪，多服务关联，实时监控，错误频率报告。覆盖 grep/awk/jq/Python 四种引擎的命令模板。
category: software-development
tags: [日志, 调试, 排查, grep, jq, awk]
---

# Log Analyzer — 日志分析工具集

文本日志、JSON 结构化日志、堆栈跟踪、多服务关联、实时监控。

## 快速搜索模式

### 查找错误和异常

```bash
# 所有错误
grep -i 'error\|exception\|fatal\|panic\|fail' app.log

# 带上下文的错误
grep -i -C 3 'error\|exception' app.log

# 最近1小时的错误（ISO时间戳）
HOUR_AGO=$(date -u -d '1 hour ago' '+%Y-%m-%dT%H:%M')
awk -v t="$HOUR_AGO" '$0 ~ /^[0-9]{4}-[0-9]{2}-[0-9]{2}T/ && $1 >= t' app.log | grep -i 'error'

# 按错误类型统计
grep -oP '(?:Error|Exception): \K[^\n]+' app.log | sort | uniq -c | sort -rn | head -20

# HTTP 5xx
awk '$9 >= 500' access.log
```

### 按请求/关联ID搜索

```bash
# 单文件追踪
grep 'req-abc123' app.log

# 多文件
grep -r 'req-abc123' /var/log/myapp/

# 跨服务
grep -rH 'correlation-id-xyz' /var/log/service-a/ /var/log/service-b/ /var/log/service-c/
```

### 时间范围过滤

```bash
# 两个时间戳之间
awk '$0 >= "2026-02-03T10:00" && $0 <= "2026-02-03T11:00"' app.log

# 最近N行
tail -1000 app.log | grep -i error

# 特定时间后
awk -v start="$(date -d '30 minutes ago' '+%Y-%m-%dT%H:%M')" '$1 >= start' app.log
```

## JSON / 结构化日志

### jq 解析

```bash
# 格式化
cat app.log | jq '.'

# 按级别过滤
cat app.log | jq 'select(.level == "error")'

# 时间范围
cat app.log | jq 'select(.timestamp >= "2026-02-03T10:00:00Z")'

# 提取字段
cat app.log | jq -r '[.timestamp, .level, .message] | @tsv'

# 按级别统计
cat app.log | jq -r '.level' | sort | uniq -c | sort -rn

# 嵌套字段
cat app.log | jq 'select(.context.userId == "user-123")'

# 按错误消息分组
cat app.log | jq -r 'select(.level == "error") | .message' | sort | uniq -c | sort -rn

# 请求耗时统计
cat app.log | jq -r 'select(.duration != null) | .duration' | awk '{sum+=$1; count++; if($1>max)max=$1} END {print "count="count, "avg="sum/count, "max="max}'
```

### 混合格式日志（JSON + 文本混排）

```bash
# 仅提取有效JSON行
while IFS= read -r line; do echo "$line" | jq '.' 2>/dev/null && continue; done < app.log

# 或以 { 开头的行
grep '^\s*{' app.log | jq '.'
```

## 堆栈跟踪分析

### 提取去重

```bash
# Java/Kotlin
awk '/Exception|Error/{trace=$0; while(getline && /^\t/) trace=trace"\n"$0; print trace"\n---"}' app.log

# Python
awk '/^Traceback/{p=1} p{print} /^[A-Za-z].*Error/{if(p) print "---"; p=0}' app.log

# Node.js
awk '/Error:/{trace=$0; while(getline && /^    at /) trace=trace"\n"$0; print trace"\n---"}' app.log

# 按根因去重
awk '/Exception|Error:/{cause=$0} /^\tat|^    at /{next} cause{print cause; cause=""}' app.log | sort | uniq -c | sort -rn
```

### Python 堆栈解析脚本

```python
#!/usr/bin/env python3
"""Parse Python tracebacks, group by root cause."""
import sys, re
from collections import Counter

def extract_tracebacks(filepath):
    tracebacks = []
    current = []
    in_trace = False
    with open(filepath) as f:
        for line in f:
            if line.startswith('Traceback (most recent call last):'):
                in_trace = True; current = [line.rstrip()]
            elif in_trace:
                current.append(line.rstrip())
                if re.match(r'^[A-Za-z]\w*(Error|Exception|Warning)', line):
                    tracebacks.append('\n'.join(current))
                    in_trace = False; current = []
    return tracebacks

if __name__ == '__main__':
    filepath = sys.argv[1] if len(sys.argv) > 1 else '/dev/stdin'
    traces = extract_tracebacks(filepath)
    causes = Counter()
    for t in traces:
        cause = t.split('\n')[-1]
        causes[cause] += 1
    print(f"Found {len(traces)} tracebacks, {len(causes)} unique causes:\n")
    for cause, count in causes.most_common(20):
        print(f"  {count:4d}x  {cause}")
```

## 实时监控

```bash
# 实时跟踪，高亮错误
tail -f app.log | grep --color=always -i 'error\|warn\|$'

# 仅显示错误
tail -f app.log | grep --line-buffered -i 'error\|exception'

# JSON 实时错误
tail -f app.log | while IFS= read -r line; do
  level=$(echo "$line" | jq -r '.level // empty' 2>/dev/null)
  [ "$level" = "error" ] && echo "$line" | jq '.'
done

# 多文件跟踪
tail -f /var/log/service-a/app.log /var/log/service-b/app.log

# 错误时蜂鸣
tail -f app.log | grep --line-buffered -i 'error' | while read line; do echo -e "\a$line"; done
```

## 访问日志解析 (Apache/Nginx)

```bash
# IP/状态/路径
awk '{print $1, $9, $7}' access.log

# 最多请求的IP
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -20

# 最热路径
awk '{print $7}' access.log | sort | uniq -c | sort -rn | head -20

# 慢请求
awk '{if ($NF > 1000000) print $0}' access.log

# 每分钟请求数
awk '{split($4,a,":"); print a[1]":"a[2]":"a[3]}' access.log | uniq -c

# 状态码分布
awk '{print $9}' access.log | sort | uniq -c | sort -rn

# 4xx/5xx + 路径
awk '$9 >= 400 {print $9, $7}' access.log | sort | uniq -c | sort -rn | head -20
```

## 自定义分隔符日志

```bash
# 管道分隔
awk -F'|' '{print $2, $3, $4}' app.log

# Tab 分隔
awk -F'\t' '$2 == "ERROR" {print $1, $4}' app.log

# CSV
python3 -c "import csv, sys
with open(sys.argv[1]) as f:
    for row in csv.DictReader(f):
        if row.get('level') == 'error':
            print(f\"{row['timestamp']} {row['message']}\")" app.csv
```

## 多服务日志关联

```bash
# 按时间戳合并
sort -m -t'T' -k1,1 service-a.log service-b.log > merged.log

# 合并JSON日志 + 来源标记
for f in service-*.log; do
  svc=$(basename "$f" .log)
  jq --arg svc "$svc" '. + {source: $svc}' "$f"
done | jq -s 'sort_by(.timestamp)[]'

# 跨服务追踪请求
grep -rH "$REQUEST_ID" /var/log/services/ | sort -t: -k2
```

## 错误频率报告

```bash
#!/bin/bash
LOG="${1:?Usage: error-report.sh <logfile>}"
echo "=== $(basename "$LOG") ==="
total=$(wc -l < "$LOG")
errors=$(grep -ci 'error\|exception\|fatal' "$LOG")
echo "Total: $total | Errors: $errors"

echo "--- Top 15 ---"
grep -i 'error\|exception' "$LOG" | \
  sed 's/^[0-9TZ:.+\-]* //' | sed 's/\b[0-9a-f]\{8,\}\b/ID/g' | \
  sed 's/[0-9]\{1,\}/N/g' | sort | uniq -c | sort -rn | head -15

echo "--- Per Hour ---"
grep -i 'error\|exception' "$LOG" | grep -oP '\d{4}-\d{2}-\d{2}T\d{2}' | sort | uniq -c
```

## 日志轮转和大文件

```bash
# 压缩日志中搜索
zgrep -i 'error' /var/log/app.log*

# 随机采样1000行
shuf -n 1000 huge.log > sample.log

# 每100行取一行
awk 'NR % 100 == 0' huge.log > sample.log

# 首尾各500行
{ head -500 huge.log; echo "--- TRUNCATED ---"; tail -500 huge.log; } > excerpt.log
```

## 提示

- 先搜请求ID/关联ID → 比时间戳或错误消息更快缩小范围
- `tail -f` 管道时加 `--line-buffered` 防止输出延迟
- 分组前用 `sed` 归一化ID/数字 → `sed 's/[0-9a-f]\{8,\}/ID/g'`
- JSON 日志必备 `jq`：`apt install jq`
- 生产排查：先确定时间窗口 + 受影响用户/请求ID → 再读日志
- 大文件统计用 `awk` 比 `grep | sort | uniq -c` 管道快得多
