# ZTLIG1 X1 日志模式发现方法论

> 基于对 521MB/473万行 ztlig1.300.txt 的逆向分析经验总结

## 核心思路：从数据反推格式

ZTLIG1 日志无官方格式文档，格式由二进制日志函数 `printf`/`sprintf` 模板决定。分析流程：

### 第一步：看大图（文件头 + 统计）

```bash
# 文件大小和行数
wc -l ztlig1.300.txt      # 521MB, 473万行

# 头 100 行了解启动阶段
head -100 ztlig1.300.txt | cat -A   # 检查换行符、空行模式

# 跳过启动段，看运行时内容
tail -n +10000 ztlig1.300.txt | head -50
```

### 第二步：分段采样（5MB 切片法）

521MB 文件不能用单次 `grep`/`read` 全量加载，按时间/功能区段采样：

```python
# 5MB 切片：启动阶段
with open(f, 'rb') as fh:
    seg1 = fh.read(5 * 1024 * 1024).decode('utf-8', errors='replace')

# 5MB后500KB：运行阶段
    fh.seek(5 * 1024 * 1024)
    seg2 = fh.read(500 * 1024).decode('utf-8', errors='replace')
```

### 第三步：body 前缀聚类

用正则匹配 LOG_HEADER 后，对 body 做前缀聚类发现操作类型：

```python
from collections import Counter
body_prefixes = Counter()
for line in lines:
    m = LOG_HEADER_RE.match(line)
    if not m: continue
    body = line[m.end():].strip()
    prefix = body[:60]  # 取前60字符
    body_prefixes[prefix] += 1

# 输出频率最高的模式
for prefix, cnt in body_prefixes.most_common(30):
    print(f'{cnt:>5}x | {prefix}')
```

### 第四步：子模块提取

ZTLIG1 body 第一个 `[...]` 是子模块名，但 LOG_HEADER_RE 可能已吃掉它：

```python
# 检查 LOG_HEADER 第5组的值
fn = result.get("function", "")
LOG_LEVELS = {"INFORM", "ERROR", "WARNING", "DEBUG", "ALARM", "INFO", "TRACE"}

if fn in LOG_LEVELS:
    # 格式 A: 第5组是日志级别, body开头才是子模块
    m = re.search(r'^\[([^\]]+)\]', body)
    sub_module = m.group(1) if m else None
elif fn:
    # 格式 B: 第5组已经是子模块
    sub_module = fn
else:
    # 格式 C: 无子模块
    sub_module = None
```

### 第五步：关键信息提取

通过 body 样本归纳出所有关键字段格式：

```python
# 用搜索找出所有含特定模式的行
for line in lines:
    if 'liid=' in line.lower():
        print(line[:200])
    if 'tneid=' in line.lower() or 'tneID=' in line:
        print(line[:200])
```

### 第六步：验证

为每种格式和操作类型构造独立测试用例，覆盖所有发现的正则路径：

```python
tests = [
    ("格式A: INFORM+子模块", log_line, expected_dict),
    ("格式B: 直接子模块", log_line, expected_dict),
    ("格式C: 裸body", log_line, expected_dict),
]
for label, line, expected in tests:
    result = parse_log_line(line)
    for key, val in expected.items():
        assert result.get(key) == val, f"{label}.{key}"
```

## 已知的 ZTLIG1 日志陷阱

| 陷阱 | 表现 | 处理 |
|------|------|------|
| `[INFO ]` 尾随空格 | `[INFO ]` 而不是 `[INFO]` | 正则中用 `\s*` 处理 |
| `[INFORM]` 作为函数名 | LOG_HEADER 第5组是 `INFORM` 而非子模块 | 用白名单过滤日志级别关键词 |
| 空行分隔 | 日志行间有空行 | `splitlines()` 后 `.strip()` 跳过空行 |
| 超长单行 | JSON 设控消息可达数KB | 不截断 body，前端做显示截断 |
| 5MB 限制截断 | 521MB 文件浏览器只读前5MB | 前端分片上传或提示用户 |
| `liid=` vs `liid[` | 两种 LIID 格式混用 | 正则同时覆盖两种分隔符 |

## ETSI-ASN1-Assistant V4 修复速查

```python
# x_interface_decoder.py 中 ZTLIG1_CMD_RE 修复要点:
# 1. 单一 CMD_RE → 14 个分类正则（注意优先级）
# 2. LIID 正则: liid(?:\[|=)(\d+)\]? 覆盖两种格式
# 3. 子模块名: 用 LOG_LEVELS 白名单判断格式 A/B
# 4. 新增字段: sub_module, vneid, account, reason, cin
```

## 相关文件

- `zte-li/SKILL.md` — ETSI-ASN1-Assistant V4 章节含完整 ZTLIG1 格式说明
- `ztlig-debug-flow.md` — ZTLIG 调试方法论
- `ber-tlv-analysis/SKILL.md` — BER 码流分析
